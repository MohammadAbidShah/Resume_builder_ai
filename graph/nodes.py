"""Node functions for LangGraph workflow."""
from typing import Dict, Any
from graph.state import ResumeState
from agents import (
    ResumeContentGeneratorAgent,
    LaTeXGeneratorAgent,
    ATSCheckerAgent,
    PDFValidatorAgent,
    FeedbackAgent,
)
from utils.logger import logger
from utils.helpers import save_iteration_state
from config.settings import MIN_ATS_SCORE, PDF_QUALITY_THRESHOLD, ENABLE_HYBRID_POLICY, HYBRID_ALLOWED_FAILURES

# Initialize agents
content_generator = ResumeContentGeneratorAgent()
latex_generator = LaTeXGeneratorAgent()
ats_checker = ATSCheckerAgent()
pdf_validator = PDFValidatorAgent()
feedback_agent = FeedbackAgent()

def node_generate_content(state: ResumeState) -> Dict[str, Any]:
    """Node 1: Generate resume content."""
    logger.info(f"=== ITERATION {state.iteration + 1}: Content Generation ===")
    
    # Prepare feedback if this is a refinement iteration
    feedback = None
    if state.iteration > 0 and state.feedback:
        feedback = state.feedback.get("content_feedback", None)
    
    # Generate content
    result = content_generator.generate(
        job_description=state.job_description,
        personal_info=state.personal_info.dict(),
        feedback=feedback
    )
    
    if not result.get("success", False):
        logger.error(f"Content generation failed: {result.get('error')}")
        return {"content_generation_error": result.get("error")}
    
    # Extract and return - keep personal_info so it flows through to LaTeX generator
    # Also include job_description for ATS optimization in LaTeX generator
    resume_content = {k: v for k, v in result.items() 
                     if k not in ["success", "source_job_keywords"]}
    resume_content["job_description"] = state.job_description  # Add JD for ATS optimizer
    
    logger.info("[OK] Resume content generated successfully")
    return {"resume_content": resume_content}

def node_generate_latex(state: ResumeState) -> Dict[str, Any]:
    """Node 2: Generate LaTeX code."""
    logger.info("Generating LaTeX code...")
    
    # Prepare feedback if needed
    feedback = None
    if state.iteration > 0 and state.feedback:
        feedback = state.feedback.get("latex_feedback", None)
    
    # Generate LaTeX
    result = latex_generator.generate(
        resume_content=state.resume_content,
        feedback=feedback
    )
    
    if not result.get("success", False):
        logger.error(f"LaTeX generation failed: {result.get('error')}")
        return {"latex_generation_error": result.get("error")}
    
    logger.info("[OK] LaTeX code generated successfully")
    return {
        "latex_code": result.get("latex_code"),
        "plain_text": result.get("plain_text")
    }

def node_validate_ats(state: ResumeState) -> Dict[str, Any]:
    """Node 3a: Validate ATS compatibility."""
    logger.info("Checking ATS compatibility...")
    
    result = ats_checker.check(
        resume_content=state.resume_content,
        job_description=state.job_description,
        latex_code=state.latex_code
    )
    
    if not result.get("success", False):
        logger.error(f"ATS check failed: {result.get('error')}")
        # Use tool results as fallback
        return {"ats_report": result.get("tool_results", {})}
    
    logger.info(f"[OK] ATS check complete: {result.get('ats_score', 0):.1f}%")
    return {"ats_report": result}

def node_validate_pdf(state: ResumeState) -> Dict[str, Any]:
    """Node 3b: Validate PDF quality."""
    logger.info("Validating PDF quality...")
    
    result = pdf_validator.validate(
        latex_code=state.latex_code,
        resume_content=state.resume_content
    )
    
    if not result.get("success", False):
        logger.error(f"PDF validation failed: {result.get('error')}")
        return {"pdf_report": result.get("tool_results", {})}
    
    logger.info(f"[OK] PDF validation complete: {result.get('quality_score', 0):.0f}/100")
    return {"pdf_report": result}

def node_evaluate_and_decide(state: ResumeState) -> Dict[str, Any]:
    """Node 4: Evaluate results and decide next action."""
    logger.info("Evaluating quality standards...")
    
    result = feedback_agent.evaluate(
        ats_report=state.ats_report or {},
        pdf_report=state.pdf_report or {},
        iteration=state.iteration
    )
    
    if not result.get("success", False):
        logger.error(f"Evaluation failed: {result.get('error')}")
        return {
            "overall_status": "error",
            "feedback": {"error": result.get("error")}
        }
    
    overall_status = result.get("overall_status", "fail").lower()

    # Compute local numeric checks to support Hybrid policy
    ats_score = (state.ats_report or {}).get("ats_score", 0)
    pdf_quality = (state.pdf_report or {}).get("quality_score", 0)
    ats_blocking = len((state.ats_report or {}).get("ats_blocking_issues", []))
    keywords_missing = len((state.ats_report or {}).get("keywords_missing", []))
    latex_valid = (state.pdf_report or {}).get("latex_valid", False)

    computed_standards = {
        "ATS_Score_90%+": ats_score >= (MIN_ATS_SCORE * 100),
        "Keywords_Complete": keywords_missing < 5,
        "LaTeX_Valid": bool(latex_valid),
        "PDF_Quality_85+": pdf_quality >= PDF_QUALITY_THRESHOLD,
        "No_ATS_Blocking_Issues": ats_blocking == 0,
    }

    # Attach computed standards to feedback (ensure truth comes from validators)
    result.setdefault("standards_met", computed_standards)

    # Apply Hybrid policy: auto-pass if numeric thresholds met and
    # non-blocking failures are within allowed threshold
    if ENABLE_HYBRID_POLICY:
        non_blocking_failures = sum(1 for v in computed_standards.values() if not v)
        numeric_ok = (
            ats_score >= (MIN_ATS_SCORE * 100) and
            pdf_quality >= PDF_QUALITY_THRESHOLD
        )

        if numeric_ok and non_blocking_failures <= HYBRID_ALLOWED_FAILURES:
            overall_status = "pass"
            result["auto_passed_by_hybrid_policy"] = True

    logger.info(f"[OK] Evaluation complete: {overall_status.upper()}")

    return {
        "overall_status": overall_status,
        "feedback": result
    }

def node_save_iteration(state: ResumeState) -> Dict[str, Any]:
    """Node 5: Save iteration state for auditing."""
    from config.settings import OUTPUT_DIR
    
    iteration_data = {
        "iteration": state.iteration,
        "status": state.overall_status,
        "ats_score": state.ats_report.get("ats_score") if state.ats_report else None,
        "pdf_quality": state.pdf_report.get("quality_score") if state.pdf_report else None,
        "feedback": state.feedback
    }
    
    filepath = save_iteration_state(iteration_data, OUTPUT_DIR, state.iteration)
    logger.info(f"Iteration {state.iteration} saved to {filepath}")
    
    return {"iteration_history": state.iteration_history + [iteration_data]}

def node_finalize(state: ResumeState) -> Dict[str, Any]:
    """Node 6: Finalize and prepare output."""
    logger.info("=== FINALIZING RESUME ===")
    
    final_state = {
        "final_latex": state.latex_code,
        "final_plain_text": state.plain_text,
        "success": state.overall_status == "pass"
    }
    
    logger.info(f"[OK] Resume building complete. Status: {state.overall_status}")
    
    return final_state

__all__ = [
    "node_generate_content",
    "node_generate_latex",
    "node_validate_ats",
    "node_validate_pdf",
    "node_evaluate_and_decide",
    "node_save_iteration",
    "node_finalize",
]
