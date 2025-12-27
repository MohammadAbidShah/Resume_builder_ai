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
from utils.helpers import format_validation_report, format_feedback_message
from config.settings import RESUME_OUTPUT_DIR, LATEX_OUTPUT_DIR, OUTPUT_DIR, MAX_ITERATIONS

def load_sample_job_description() -> str:
    """Load a sample job description for testing."""
    return """
Senior Python Developer - Full Stack

We're looking for an experienced Senior Python Developer to join our team.

Required Skills:
- Python 3.9+
- FastAPI or Django
- PostgreSQL/MongoDB
- REST API development
- Docker and Kubernetes
- AWS cloud services
- Git version control
- Machine Learning basics

Responsibilities:
- Design and develop scalable backend services
- Implement REST APIs
- Optimize database queries
- Write unit tests and integration tests
- Collaborate with frontend teams
- Manage deployments and CI/CD pipelines
- Mentor junior developers

Nice to have:
- Microservices architecture
- Redis caching
- GraphQL
- Apache Kafka
- TensorFlow/PyTorch
- Leadership experience
"""

def load_sample_personal_info() -> PersonalInfo:
    """Load sample personal information for testing."""
    return PersonalInfo(
        name="John Doe",
        email="john.doe@example.com",
        phone="+1 (555) 123-4567",
        experience=[
            {
                "title": "Python Developer",
                "company": "Tech Corp",
                "duration": "2021 - Present",
                "description": "Developed REST APIs using FastAPI. Worked with PostgreSQL databases. Deployed applications using Docker."
            },
            {
                "title": "Junior Developer",
                "company": "StartUp Inc",
                "duration": "2019 - 2021",
                "description": "Built web applications using Django. Wrote unit tests. Used Git for version control."
            }
        ],
        skills={
            "Programming Languages": ["Python", "JavaScript"],
            "Backend Frameworks": ["FastAPI", "Django"],
            "Databases": ["PostgreSQL", "MongoDB"],
            "Tools": ["Docker", "Git", "AWS", "Linux"],
            "Other": ["REST APIs", "Unit Testing", "CI/CD"]
        },
        education=[
            {
                "degree": "Bachelor of Science in Computer Science",
                "school": "State University",
                "year": "2019"
            }
        ]
    )

def display_results(final_state) -> None:
    """Display the final results."""
    print("\n" + "="*80)
    print("RESUME BUILDING COMPLETE")
    print("="*80 + "\n")
    
    # Handle both dict and object access patterns
    success = final_state.get("success", False) if isinstance(final_state, dict) else getattr(final_state, "success", False)
    
    if success:
        print(">>> SUCCESS <<<")
        iteration = final_state.get("iteration", 0) if isinstance(final_state, dict) else getattr(final_state, "iteration", 0)
        print(f"Resume built successfully in {iteration + 1} iteration(s)")
        overall_status = final_state.get("overall_status", "unknown") if isinstance(final_state, dict) else getattr(final_state, "overall_status", "unknown")
        print(f"\nFinal Status: {overall_status.upper()}")
        
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
        
        print(f"\n[*] All outputs saved to: {OUTPUT_DIR}/")
    else:
        print(">>> UNSUCCESSFUL <<<")
        max_iterations = final_state.get("max_iterations", 5) if isinstance(final_state, dict) else getattr(final_state, "max_iterations", 5)
        iteration = final_state.get("iteration", 0) if isinstance(final_state, dict) else getattr(final_state, "iteration", 0)
        if iteration >= max_iterations - 1:
            print(f"Max iterations ({max_iterations}) reached")
        
        overall_status = final_state.get("overall_status", "unknown") if isinstance(final_state, dict) else getattr(final_state, "overall_status", "unknown")
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
    ats_report = final_state.get("ats_report") if isinstance(final_state, dict) else getattr(final_state, "ats_report", None)
    pdf_report = final_state.get("pdf_report") if isinstance(final_state, dict) else getattr(final_state, "pdf_report", None)
    iteration_history = final_state.get("iteration_history") if isinstance(final_state, dict) else getattr(final_state, "iteration_history", [])
    overall_status = final_state.get("overall_status") if isinstance(final_state, dict) else getattr(final_state, "overall_status", "unknown")
    success = final_state.get("success") if isinstance(final_state, dict) else getattr(final_state, "success", False)
    iteration = final_state.get("iteration") if isinstance(final_state, dict) else getattr(final_state, "iteration", 0)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_iterations": iteration + 1,
        "elapsed_time_seconds": elapsed_time,
        "final_status": overall_status,
        "success": success,
        "ats_score": ats_report.get("ats_score") if ats_report else None,
        "pdf_quality": pdf_report.get("quality_score") if pdf_report else None,
        "iteration_history": iteration_history,
    }
    
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n[OK] Execution report saved: {report_file}")

def run_resume_builder(
    job_description: str,
    personal_info: Dict[str, Any],
    use_sample: bool = False
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
        
        # Display results
        display_results(final_state)
        
        # Save report
        save_execution_report(final_state, elapsed_time)
        
        logger.info(f"Total execution time: {elapsed_time:.2f} seconds")
        
        return final_state
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}", exc_info=True)
        raise

def main():
    """
    Main entry point - can be run directly or imported.
    """
    # Example usage with sample data
    print("\n" + "="*80)
    print("RESUME BUILDER AI - AGENTIC WORKFLOW")
    print("="*80 + "\n")
    
    # Check for Groq API key
    from config.settings import GROQ_API_KEY
    if not GROQ_API_KEY:
        print("ERROR: GROQ_API_KEY not set in environment")
        print("Please set GROQ_API_KEY environment variable with your Groq API key")
        sys.exit(1)
    
    # Run with sample data
    print("Running with sample data for demonstration...\n")
    final_state = run_resume_builder(
        job_description="AIML Engineer needed for innovative projects.",
        personal_info={"Name": "Abid Shah", "Email": "abid.shah@example.com"},
        use_sample=True
    )
    
    return final_state

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    # Run main
    main()
