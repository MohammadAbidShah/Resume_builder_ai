"""
API/Integration layer for Resume Builder AI.
Can be used to expose the resume builder as a REST API or service.
"""

from typing import Dict, Any, Optional
from main import run_resume_builder
from graph import ResumeState, PersonalInfo
from utils.logger import logger

class ResumeBuilderAPI:
    """API interface for Resume Builder."""
    
    @staticmethod
    def build_resume(
        job_description: str,
        personal_info: Dict[str, Any],
        max_iterations: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Build a resume for a given job description.
        
        Args:
            job_description: Job posting text
            personal_info: User's personal/professional information
            max_iterations: Override max iterations
            
        Returns:
            Result dictionary with final LaTeX, content, and metadata
        """
        logger.info("API: Build resume request received")
        
        try:
            final_state = run_resume_builder(
                job_description=job_description,
                personal_info=personal_info,
                use_sample=False
            )
            
            return {
                "success": final_state.success,
                "status": final_state.overall_status,
                "iterations": final_state.iteration + 1,
                "latex_code": final_state.final_latex,
                "plain_text": final_state.final_plain_text,
                "resume_content": final_state.resume_content,
                "ats_score": final_state.ats_report.get("ats_score") if final_state.ats_report else None,
                "pdf_quality": final_state.pdf_report.get("quality_score") if final_state.pdf_report else None,
            }
        except Exception as e:
            logger.error(f"API: Error building resume: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def validate_inputs(
        job_description: str,
        personal_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate input data before building resume.
        
        Args:
            job_description: Job posting text
            personal_info: User's information
            
        Returns:
            Validation result
        """
        errors = []
        warnings = []
        
        # Check job description
        if not job_description or len(job_description.strip()) < 100:
            errors.append("Job description too short (minimum 100 characters)")
        
        required_keywords = ["skill", "requirement", "experience", "responsibility"]
        if not any(keyword in job_description.lower() for keyword in required_keywords):
            warnings.append("Job description may lack standard structure")
        
        # Check personal info
        if not personal_info:
            errors.append("Personal information missing")
        else:
            required_fields = ["name", "email", "phone"]
            for field in required_fields:
                if field not in personal_info:
                    errors.append(f"Missing required field: {field}")
            
            # Check experience
            experience = personal_info.get("experience", [])
            if not experience or len(experience) == 0:
                errors.append("No experience provided")
            
            # Check skills
            skills = personal_info.get("skills", {})
            if not skills or len(skills) == 0:
                errors.append("No skills provided")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    @staticmethod
    def get_status() -> Dict[str, Any]:
        """Get API status and configuration."""
        from config.settings import (
            MIN_ATS_SCORE, PDF_QUALITY_THRESHOLD, MAX_ITERATIONS,
            CONTENT_MODEL, VALIDATION_MODEL
        )
        
        return {
            "service": "Resume Builder AI",
            "version": "1.0.0",
            "status": "operational",
            "models": {
                "content_generation": CONTENT_MODEL,
                "validation": VALIDATION_MODEL,
            },
            "thresholds": {
                "min_ats_score": MIN_ATS_SCORE * 100,
                "min_pdf_quality": PDF_QUALITY_THRESHOLD,
            },
            "max_iterations": MAX_ITERATIONS,
        }

# Example FastAPI integration (optional)
def create_fastapi_app():
    """Create a FastAPI application for the resume builder."""
    try:
        from fastapi import FastAPI, HTTPException
        from pydantic import BaseModel
        
        app = FastAPI(
            title="Resume Builder AI",
            description="Build optimized resumes using AI agents",
            version="1.0.0"
        )
        
        class JobDescriptionInput(BaseModel):
            job_description: str
            personal_info: Dict[str, Any]
        
        class StatusResponse(BaseModel):
            service: str
            status: str
            version: str
        
        @app.get("/health", response_model=StatusResponse)
        async def health_check():
            """Health check endpoint."""
            status = ResumeBuilderAPI.get_status()
            return status
        
        @app.post("/build-resume")
        async def build_resume(request: JobDescriptionInput):
            """Build a resume."""
            # Validate inputs
            validation = ResumeBuilderAPI.validate_inputs(
                request.job_description,
                request.personal_info
            )
            
            if not validation["is_valid"]:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "errors": validation["errors"],
                        "warnings": validation["warnings"]
                    }
                )
            
            # Build resume
            result = ResumeBuilderAPI.build_resume(
                request.job_description,
                request.personal_info
            )
            
            if not result["success"]:
                raise HTTPException(
                    status_code=500,
                    detail=result.get("error", "Resume building failed")
                )
            
            return result
        
        return app
    
    except ImportError:
        logger.warning("FastAPI not installed - skipping API app creation")
        return None

if __name__ == "__main__":
    # Test the API layer
    print("\nTesting Resume Builder API...\n")
    
    # Test status
    status = ResumeBuilderAPI.get_status()
    print(f"Service Status: {status['status']}")
    print(f"Service Version: {status['version']}")
    print(f"Models: {status['models']}")
    
    # Test validation with sample data
    job_desc = "Python developer needed with 5+ years experience in Django and REST APIs"
    personal_info = {
        "name": "Test User",
        "email": "test@example.com",
        "phone": "555-1234",
        "experience": [
            {"title": "Developer", "company": "ABC", "duration": "2020-2023"}
        ],
        "skills": {"Programming": ["Python"]},
        "education": [{"degree": "BS", "school": "University", "year": "2020"}]
    }
    
    validation = ResumeBuilderAPI.validate_inputs(job_desc, personal_info)
    print(f"\nValidation Result: {validation['is_valid']}")
    if validation['errors']:
        print(f"Errors: {validation['errors']}")
    if validation['warnings']:
        print(f"Warnings: {validation['warnings']}")
