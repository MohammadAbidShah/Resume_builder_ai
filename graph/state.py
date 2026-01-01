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
    max_iterations: int = Field(default=5)
    
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
