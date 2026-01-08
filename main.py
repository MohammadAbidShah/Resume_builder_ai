"""
Main entry point for Resume Builder AI.

This orchestrates the entire agentic workflow for building an optimized resume.
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from graph import app, ResumeState, PersonalInfo
from utils.logger import logger
from utils.helpers import format_validation_report, format_feedback_message, cleanup_old_outputs
from config.settings import (
    RESUME_OUTPUT_DIR,
    LATEX_OUTPUT_DIR,
    OUTPUT_DIR,
    MAX_ITERATIONS,
    INPUT_JOB_FILE,
    INPUT_PERSONAL_FILE,
)

def display_results(final_state) -> None:
    """Display the final results."""
    print("\n" + "="*80)
    print("RESUME BUILDING COMPLETE")
    print("="*80 + "\n")
    
    # Handle both dict and object access patterns
    overall_status = final_state.get("overall_status", "unknown") if isinstance(final_state, dict) else getattr(final_state, "overall_status", "unknown")
    success = final_state.get("success", False) if isinstance(final_state, dict) else getattr(final_state, "success", False)
    classified_role = final_state.get("classified_role") if isinstance(final_state, dict) else getattr(final_state, "classified_role", None)
    role_level = final_state.get("role_level") if isinstance(final_state, dict) else getattr(final_state, "role_level", None)
    
    # Check for role rejection (NEW - Step 0)
    if overall_status.lower() == "rejected":
        print(">>> ROLE CLASSIFICATION REJECTED <<<\n")
        role_error = final_state.get("role_classification_error") if isinstance(final_state, dict) else getattr(final_state, "role_classification_error", None)
        if role_error:
            print(f"Rejection Reason:\n{role_error}\n")
        print("The job description could not be classified into one of the supported roles:")
        print("  - Data Analyst")
        print("  - Data Scientist")
        print("  - Data Engineer")
        print("\nPlease provide a job description for one of these roles.\n")
        print("="*80)
        return
    
    if success:
        print(">>> SUCCESS <<<")
        iteration = final_state.get("iteration", 0) if isinstance(final_state, dict) else getattr(final_state, "iteration", 0)
        print(f"Resume built successfully in {iteration + 1} iteration(s)")
        print(f"\nRole Classification: {classified_role} ({role_level})" if role_level else f"\nRole Classification: {classified_role}")
        print(f"Final Status: {overall_status.upper()}")
        
        ats_report = final_state.get("ats_report") if isinstance(final_state, dict) else getattr(final_state, "ats_report", None)
        if ats_report:
            print(f"\nATS Score: {ats_report.get('ats_score', 0):.1f}%")
            print(f"Keywords Matched: {len(ats_report.get('keywords_present', []))}")
        
        pdf_report = final_state.get("pdf_report") if isinstance(final_state, dict) else getattr(final_state, "pdf_report", None)
        if pdf_report:
            print(f"PDF Quality: {pdf_report.get('quality_score', 0):.0f}/100")
        
        # Save outputs
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        final_latex = final_state.get("final_latex") if isinstance(final_state, dict) else getattr(final_state, "final_latex", None)
        if final_latex:
            latex_file = f"{LATEX_OUTPUT_DIR}/resume_{timestamp}.tex"
            with open(latex_file, 'w') as f:
                f.write(final_latex)
            print(f"\n[*] LaTeX saved: {latex_file}")
        
        resume_content = final_state.get("resume_content") if isinstance(final_state, dict) else getattr(final_state, "resume_content", None)
        if resume_content:
            json_file = f"{RESUME_OUTPUT_DIR}/resume_{timestamp}.json"
            with open(json_file, 'w') as f:
                json.dump(resume_content, f, indent=2)
            print(f"[*] Resume content saved: {json_file}")
        
        # Cleanup old outputs - keep only last 3 files of each type
        cleanup_old_outputs(OUTPUT_DIR, max_files=3)
        
        print(f"\n[*] All outputs saved to: {OUTPUT_DIR}/")
    else:
        print(">>> UNSUCCESSFUL <<<")
        max_iterations = final_state.get("max_iterations", 5) if isinstance(final_state, dict) else getattr(final_state, "max_iterations", 5)
        iteration = final_state.get("iteration", 0) if isinstance(final_state, dict) else getattr(final_state, "iteration", 0)
        if iteration >= max_iterations - 1:
            print(f"Max iterations ({max_iterations}) reached")
        
        print(f"\nLast Status: {overall_status}")
        
        feedback = final_state.get("feedback") if isinstance(final_state, dict) else getattr(final_state, "feedback", None)
        if feedback:
            print("\nLast Feedback:")
            print(format_feedback_message(feedback))
    
    print("\n" + "="*80)

def save_execution_report(final_state, elapsed_time: float) -> None:
    """Save a detailed execution report."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"{OUTPUT_DIR}/execution_report_{timestamp}.json"
    
    # Handle both dict and object access patterns
    overall_status = final_state.get("overall_status") if isinstance(final_state, dict) else getattr(final_state, "overall_status", "unknown")
    ats_report = final_state.get("ats_report") if isinstance(final_state, dict) else getattr(final_state, "ats_report", None)
    pdf_report = final_state.get("pdf_report") if isinstance(final_state, dict) else getattr(final_state, "pdf_report", None)
    iteration_history = final_state.get("iteration_history") if isinstance(final_state, dict) else getattr(final_state, "iteration_history", [])
    success = final_state.get("success") if isinstance(final_state, dict) else getattr(final_state, "success", False)
    iteration = final_state.get("iteration") if isinstance(final_state, dict) else getattr(final_state, "iteration", 0)
    classified_role = final_state.get("classified_role") if isinstance(final_state, dict) else getattr(final_state, "classified_role", None)
    role_level = final_state.get("role_level") if isinstance(final_state, dict) else getattr(final_state, "role_level", None)
    role_confidence = final_state.get("role_confidence") if isinstance(final_state, dict) else getattr(final_state, "role_confidence", 0)
    role_error = final_state.get("role_classification_error") if isinstance(final_state, dict) else getattr(final_state, "role_classification_error", None)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_iterations": iteration + 1,
        "elapsed_time_seconds": elapsed_time,
        "final_status": overall_status,
        "success": success,
        "role_classification": {
            "classified_role": classified_role,
            "role_level": role_level,
            "confidence": role_confidence,
            "rejection_reason": role_error
        },
        "ats_score": ats_report.get("ats_score") if ats_report else None,
        "pdf_quality": pdf_report.get("quality_score") if pdf_report else None,
        "iteration_history": iteration_history,
    }
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    # Cleanup old outputs - keep only last 3 files of each type
    cleanup_old_outputs(OUTPUT_DIR, max_files=3)
    
    print(f"\n[OK] Execution report saved: {report_file}")

def run_resume_builder(
    job_description: str,
    personal_info: Dict[str, Any],
    use_sample: bool = False,
    quiet: bool = False
) -> ResumeState:
    """
    Run the resume builder workflow.
    
    Args:
        job_description: Job description text
        personal_info: Personal information dictionary
        use_sample: If True, uses sample data instead
        
    Returns:
        Final state with results
    """
    import time
    
    start_time = time.time()
    
    logger.info("="*80)
    logger.info("RESUME BUILDER AI - STARTING EXECUTION")
    logger.info("="*80)
    
    if use_sample:
        logger.info("Using sample job description and personal info")
        job_description = load_sample_job_description()
        personal_info = load_sample_personal_info()
    
    # Create initial state
    initial_state = ResumeState(
        job_description=job_description,
        personal_info=personal_info if isinstance(personal_info, PersonalInfo) else PersonalInfo(**personal_info),
        max_iterations=MAX_ITERATIONS
    )
    
    # Run the workflow
    logger.info("Starting LangGraph workflow...")
    try:
        # Run the graph with increased recursion limit for mock mode
        final_state = app.invoke(initial_state, {"recursion_limit": 100})
        
        elapsed_time = time.time() - start_time
        
        # Display results (unless running in quiet/job mode)
        if not quiet:
            display_results(final_state)

        # Save report
        save_execution_report(final_state, elapsed_time)

        logger.info(f"Total execution time: {elapsed_time:.2f} seconds")

        return final_state

    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}", exc_info=True)
        raise


def load_personal_info(filepath: str = INPUT_PERSONAL_FILE) -> Optional[Dict[str, Any]]:
    """Load pre-stored personal info from JSON file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"{filepath} not found. Falling back to sample personal info.")
        return None
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in {filepath}")
        return None


def main():
    """
    Main entry point. Loads job description from input/input_data.txt and runs workflow.
    All output is written to the outputs folder; nothing is printed to terminal.
    """
    from config.settings import GROQ_API_KEY, GROQ_MOCK_MODE, OUTPUT_DIR

    # Enforce Groq API key when not in mock mode
    if not GROQ_MOCK_MODE and not GROQ_API_KEY:
        logger.error("GROQ_API_KEY not set in environment (required in live mode)")
        sys.exit(1)

    # Load job description from input/input_data.txt (default location)
    job_txt_path = Path(INPUT_JOB_FILE)
    if not job_txt_path.exists():
        logger.error(f"job description file not found: {job_txt_path}")
        sys.exit(1)

    try:
        with open(job_txt_path, 'r', encoding='utf-8') as f:
            job_description = f.read().strip()
    except Exception as e:
        logger.error(f"Failed to read job description: {e}")
        sys.exit(1)

    if not job_description:
        logger.error("job description file is empty")
        sys.exit(1)

    # Load personal info (must exist)
    personal_info = load_personal_info(INPUT_PERSONAL_FILE)
    if personal_info is None:
        logger.error("personal_info.json not found or invalid; personal info is required in job mode")
        sys.exit(1)

    # Run workflow in quiet mode (suppress intermediate output)
    final_state = run_resume_builder(
        job_description=job_description,
        personal_info=personal_info,
        use_sample=False,
        quiet=True
    )

    # If success, print only the final LaTeX to stdout
    success = final_state.get('success') if isinstance(final_state, dict) else getattr(final_state, 'success', False)
    final_latex = final_state.get('final_latex') if isinstance(final_state, dict) else getattr(final_state, 'final_latex', None)

    if success and final_latex:
        # Save final LaTeX and resume JSON to outputs
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Ensure output dirs exist
        Path(LATEX_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
        Path(RESUME_OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

        latex_path = Path(LATEX_OUTPUT_DIR) / f"resume_{timestamp}.tex"
        with open(latex_path, 'w', encoding='utf-8') as f:
            f.write(final_latex)

        # Save resume content if available
        resume_content = final_state.get('resume_content') if isinstance(final_state, dict) else getattr(final_state, 'resume_content', None)
        if resume_content:
            json_path = Path(RESUME_OUTPUT_DIR) / f"resume_{timestamp}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(resume_content, f, indent=2)

        # Cleanup old outputs - keep only last 3 files of each type
        cleanup_old_outputs(OUTPUT_DIR, max_files=3)

        # Log to files only (no stdout)
        logger.info(f"Final LaTeX saved to: {latex_path}")
        logger.info(f"Resume JSON saved to: {json_path if resume_content else 'N/A'}")
        return final_state
    else:
        # On failure: save diagnostics to file, do not print to stdout
        ats = final_state.get('ats_report') if isinstance(final_state, dict) else getattr(final_state, 'ats_report', None)
        pdf = final_state.get('pdf_report') if isinstance(final_state, dict) else getattr(final_state, 'pdf_report', None)
        feedback = final_state.get('feedback') if isinstance(final_state, dict) else getattr(final_state, 'feedback', None)

        out = {
            'status': final_state.get('overall_status') if isinstance(final_state, dict) else getattr(final_state, 'overall_status', 'unknown'),
            'success': success,
            'ats_score': ats.get('ats_score') if ats else None,
            'pdf_quality': pdf.get('quality_score') if pdf else None,
            'feedback': feedback
        }
        logger.error(f"Resume building failed. Diagnostics: {json.dumps(out, indent=2)}")
        return final_state

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Run main
    main()
