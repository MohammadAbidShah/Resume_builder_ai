"""Tools package for Resume Builder AI."""
from .content_tools import (
    parse_job_description,
    extract_technical_skills,
    extract_soft_skills,
    match_experience_to_job,
    optimize_action_verbs,
    quantify_achievements,
)
from .latex_tools import (
    generate_latex_code,
    validate_latex_syntax,
    format_latex_for_ats,
    extract_plain_text_from_latex,
)
from .validation_tools import (
    check_ats_compatibility,
    validate_pdf_quality,
)

__all__ = [
    # Content tools
    "parse_job_description",
    "extract_technical_skills",
    "extract_soft_skills",
    "match_experience_to_job",
    "optimize_action_verbs",
    "quantify_achievements",
    # LaTeX tools
    "generate_latex_code",
    "validate_latex_syntax",
    "format_latex_for_ats",
    "extract_plain_text_from_latex",
    # Validation tools
    "check_ats_compatibility",
    "validate_pdf_quality",
]
