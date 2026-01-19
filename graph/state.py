"""State schema for Resume Builder workflow."""
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

class PersonalInfo(BaseModel):
    """User's personal information."""
    name: str
    email: str
    phone: str
    location: Optional[str] = Field(default=None)
    linkedin: Optional[str] = Field(default=None)
    github: Optional[str] = Field(default=None)
    # Ordered to match LaTeX output: Summary → Experience → Projects → Awards & Certifications → Education
    summary: Dict[str, Any] = Field(default_factory=dict)
    experience: List[Dict[str, Any]] = Field(default_factory=list)
    projects: List[Dict[str, Any]] = Field(default_factory=list)
    awards_and_certifications: List[Dict[str, Any]] = Field(default_factory=list)
    education: List[Dict[str, Any]] = Field(default_factory=list)
    # Optional legacy fields kept for backward compatibility; leave empty when using new schema
    skills: Dict[str, List[str]] = Field(default_factory=dict)
    awards: List[Dict[str, Any]] = Field(default_factory=list)
    certifications: List[Dict[str, Any]] = Field(default_factory=list)

class ResumeState(BaseModel):
    """Main state for the resume building workflow."""
    
    # Input
    job_description: str
    personal_info: PersonalInfo
    
    # Process tracking
    iteration: int = Field(default=0)
    max_iterations: int = Field(default=2)  # HARD CAP: Maximum 2 iterations
    generation_mode: str = Field(default="full")  # "full" (iteration 0 only) or "selective" (iteration 1+)
    
    # Validation pass flags
    ats_passed: bool = Field(default=False)
    pdf_passed: bool = Field(default=False)
    
    # FIX-4: Feedback mode (read_only after iteration cap)
    feedback_mode: str = Field(default="regenerate")  # "regenerate" or "read_only"
    
    # FIX-5: Track blocking vs non-blocking standards
    blocking_standards_met: bool = Field(default=False)  # Only blocking standards
    warnings: List[str] = Field(default_factory=list)  # Non-blocking warnings
    
    # FIX-7: Deterministic exit state
    finalization_state: Optional[str] = Field(default=None)  # FINALIZED_PASS or FINALIZED_FAIL_WITH_WARNINGS
    should_finalize: bool = Field(default=False)  # FIX-1: Hard signal to finalize
    
    # Content generation
    resume_content: Optional[Dict[str, Any]] = Field(default=None)
    content_generation_error: Optional[str] = Field(default=None)
    
    # LaTeX generation
    latex_code: Optional[str] = Field(default=None)
    plain_text: Optional[str] = Field(default=None)
    latex_generation_error: Optional[str] = Field(default=None)
    
    # Validation results
    ats_report: Optional[Dict[str, Any]] = Field(default=None)
    pdf_report: Optional[Dict[str, Any]] = Field(default=None)
    
    # Feedback and decision
    feedback: Optional[Dict[str, Any]] = Field(default=None)
    overall_status: str = Field(default="pending")  # pending, pass, fail
    
    # Iteration history
    iteration_history: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Final output
    final_latex: Optional[str] = Field(default=None)
    final_plain_text: Optional[str] = Field(default=None)
    success: bool = Field(default=False)

__all__ = ["ResumeState", "PersonalInfo"]
