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
    
    # FIX-1: HARD-LOCK full generation to iteration 0 only
    if state.iteration == 0:
        state.generation_mode = "full"
    else:
        state.generation_mode = "selective"
    
    # FIX-1: Prevent full generation after iteration 0
    if state.generation_mode != "full":
        logger.error("HARD ERROR: Full generation attempted outside iteration 0. Aborting.")
        return {"content_generation_error": "Full generation only allowed on iteration 0. Use selective regeneration for iterations > 0."}
    
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
    
    # FIX-4: Hard-skip ATS validation if already passed
    if state.ats_passed:
        logger.info("[SKIPPED] ATS validation already passed in previous iteration")
        return {"ats_report": state.ats_report or {}}
    
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
    # FIX-4: Mark ATS as passed so it won't run again
    return {"ats_report": result, "ats_passed": True}

def node_validate_pdf(state: ResumeState) -> Dict[str, Any]:
    """Node 3b: Validate PDF quality."""
    logger.info("Validating PDF quality...")
    
    # FIX-4: Hard-skip PDF validation if already passed
    if state.pdf_passed:
        logger.info("[SKIPPED] PDF validation already passed in previous iteration")
        return {"pdf_report": state.pdf_report or {}}
    
    result = pdf_validator.validate(
        latex_code=state.latex_code,
        resume_content=state.resume_content
    )
    
    if not result.get("success", False):
        logger.error(f"PDF validation failed: {result.get('error')}")
        return {"pdf_report": result.get("tool_results", {})}
    
    logger.info(f"[OK] PDF validation complete: {result.get('quality_score', 0):.0f}/100")
    # FIX-4: Mark PDF as passed so it won't run again
    return {"pdf_report": result, "pdf_passed": True}

def node_evaluate_and_decide(state: ResumeState) -> Dict[str, Any]:
    """Node 4: Evaluate results and decide next action.
    
    FIX-5: Separate BLOCKING standards from NON-BLOCKING warnings
    - BLOCKING: ATS≥90%, LaTeX valid, PDF quality≥85
    - NON-BLOCKING: Keyword coverage, action verbs, formatting, optional keywords
    """
    logger.info("Evaluating quality standards...")
    
    # FIX-4: If feedback_mode is read_only, use cached feedback (don't regenerate)
    if state.feedback_mode == "read_only":
        logger.info("[READ-ONLY MODE] Using cached feedback - no regeneration")
        return {
            "overall_status": "fail",
            "feedback": state.feedback or {},
            "blocking_standards_met": state.blocking_standards_met
        }
    
    result = feedback_agent.evaluate(
        ats_report=state.ats_report or {},
        pdf_report=state.pdf_report or {},
        iteration=state.iteration
    )
    
    if not result.get("success", False):
        logger.error(f"Evaluation failed: {result.get('error')}")
        return {
            "overall_status": "error",
            "feedback": {"error": result.get("error")},
            "blocking_standards_met": False
        }
    
    # FIX-5: Compute BLOCKING standards only (not warnings)
    ats_score = (state.ats_report or {}).get("ats_score", 0)
    pdf_quality = (state.pdf_report or {}).get("quality_score", 0)
    latex_valid = (state.pdf_report or {}).get("latex_valid", False)

    # BLOCKING standards that MUST all pass to finalize with PASS status
    blocking_standards = {
        "ATS_Score_90%+": ats_score >= (MIN_ATS_SCORE * 100),
        "LaTeX_Valid": bool(latex_valid),
        "PDF_Quality_85+": pdf_quality >= PDF_QUALITY_THRESHOLD,
    }
    
    # FIX-5: Only BLOCKING standards determine if we can finalize with PASS
    blocking_standards_met = all(blocking_standards.values())
    
    # Collect NON-BLOCKING warnings for advisory reporting
    warnings = []
    
    # Non-blocking warning checks
    keywords_missing = len((state.ats_report or {}).get("keywords_missing", []))
    if keywords_missing > 0:
        warnings.append(f"Missing keywords: {keywords_missing} important keywords not found")
    
    weak_verbs = len((state.ats_report or {}).get("weak_action_verbs", []))
    if weak_verbs > 0:
        warnings.append(f"Weak action verbs: {weak_verbs} verbs could be stronger")
    
    formatting_issues = len((state.ats_report or {}).get("formatting_issues", []))
    if formatting_issues > 0:
        warnings.append(f"Formatting issues: {formatting_issues} formatting suggestions")
    
    # FIX-5: Set blocking_standards_met in state for router to use
    state.blocking_standards_met = blocking_standards_met
    state.warnings = warnings
    
    # Determine overall status: PASS only if blocking standards met
    overall_status = "pass" if blocking_standards_met else "fail"
    
    # FIX-5: Extract failed sections for selective regeneration (only on FAIL)
    failed_sections = []
    if not blocking_standards_met:
        # Extract failed sections from feedback
        if isinstance(result.get("priority_fixes"), dict):
            failed_sections = list(result["priority_fixes"].keys())
        elif isinstance(result.get("priority_fixes"), list):
            failed_sections = ["professional_summary", "experience_bullets", "project_bullets"]
        
        result["failed_sections"] = failed_sections
    
    # Attach computed standards to feedback
    result.setdefault("standards_met", blocking_standards)
    result.setdefault("warnings", warnings)
    result.setdefault("blocking_standards_met", blocking_standards_met)

    logger.info(f"[OK] Evaluation complete: {overall_status.upper()}")
    if warnings:
        logger.info(f"[WARNINGS] {'; '.join(warnings)}")

    return {
        "overall_status": overall_status,
        "feedback": result,
        "blocking_standards_met": blocking_standards_met,
        "warnings": warnings
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

def node_selective_regeneration(state: ResumeState) -> Dict[str, Any]:
    """Node 4b: Selective regeneration for failed sections only.
    
    FIX-3: Guard against regeneration at iteration cap
    - If iteration >= MAX_ITERATIONS, return CACHED content only (no LLM call)
    - Skip ATS and PDF validation in selective mode
    """
    logger.info(f"=== SELECTIVE REGENERATION: Iteration {state.iteration} ===")
    
    # FIX-3: Hard guard - if iteration cap reached, return cached content (no LLM)
    if state.iteration >= state.max_iterations:
        logger.warning(f"[FIX-3] Iteration cap reached ({state.iteration} >= {state.max_iterations}) - RETURNING CACHED CONTENT ONLY")
        return {"resume_content": state.resume_content}
    
    # FIX-4: If feedback mode is read-only, don't regenerate
    if state.feedback_mode == "read_only":
        logger.info("[READ-ONLY MODE] Returning cached content - no regeneration")
        return {"resume_content": state.resume_content}
    
    logger.info(f"Regenerating failed sections: {state.feedback.get('failed_sections', [])}")
    
    # Extract sections that failed from feedback
    sections_to_regen = state.feedback.get("failed_sections", [])
    
    if not sections_to_regen:
        logger.info("No failed sections to regenerate")
        return {"resume_content": state.resume_content}
    
    # Get regeneration feedback
    regen_feedback = state.feedback.get("content_feedback", None)
    
    # Generate content with selective mode (only failed sections)
    result = content_generator.generate(
        job_description=state.job_description,
        personal_info=state.personal_info.dict(),
        feedback=regen_feedback,
        sections_to_regenerate=sections_to_regen,
        cached_content=state.resume_content  # Reuse cached content for non-failed sections
    )
    
    if not result.get("success", False):
        logger.error(f"Selective regeneration failed: {result.get('error')}")
        return {"content_generation_error": result.get("error")}
    
    # Update resume content with regenerated sections
    updated_content = state.resume_content.copy() if state.resume_content else {}
    for key, value in result.items():
        if key not in ["success", "source_job_keywords"]:
            updated_content[key] = value
    
    updated_content["job_description"] = state.job_description
    
    logger.info(f"[OK] Selective regeneration complete for sections: {sections_to_regen}")
    return {"resume_content": updated_content}

def node_finalize(state: ResumeState) -> Dict[str, Any]:
    """Node 6: Finalize and prepare output.
    
    FIX-2: ALWAYS finalize and save outputs, regardless of success/fail status
    FIX-7: Set deterministic exit state (FINALIZED_PASS or FINALIZED_FAIL_WITH_WARNINGS)
    """
    logger.info("=== FINALIZING RESUME ===")
    
    # FIX-2: Ensure outputs are always returned (not conditional on status)
    final_state = {
        "final_latex": state.latex_code,
        "final_plain_text": state.plain_text,
        "success": state.overall_status == "pass"
    }
    
    # FIX-7: Set deterministic finalization state
    if state.overall_status == "pass":
        state.finalization_state = "FINALIZED_PASS"
        logger.info("[OK] Resume building SUCCESSFUL. Status: FINALIZED_PASS")
    else:
        state.finalization_state = "FINALIZED_FAIL_WITH_WARNINGS"
        if state.warnings:
            logger.info(f"[WARNINGS] Resume finalized with warnings: {'; '.join(state.warnings)}")
        else:
            logger.info("[FAIL] Resume finalized - review warnings and quality scores")
        logger.info(f"Status: {state.finalization_state}")
    
    # FIX-2: Mark that finalization occurred
    final_state["finalization_state"] = state.finalization_state
    final_state["warnings"] = state.warnings
    
    return final_state

__all__ = [
    "node_generate_content",
    "node_generate_latex",
    "node_validate_ats",
    "node_validate_pdf",
    "node_evaluate_and_decide",
    "node_selective_regeneration",
    "node_save_iteration",
    "node_finalize",
]
