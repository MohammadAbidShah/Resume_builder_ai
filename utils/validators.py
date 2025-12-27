"""Validation utilities for Resume Builder AI."""
from typing import Dict, List, Any, Tuple
import json
import re

def validate_json_output(output: str) -> Tuple[bool, Dict[str, Any]]:
    """Validate and parse JSON output from agents."""
    try:
        # Try to extract JSON if it's wrapped in other text
        json_match = re.search(r'\{[\s\S]*\}', output)
        if json_match:
            json_str = json_match.group(0)
            return True, json.loads(json_str)
        else:
            return False, {"error": "No JSON found in output"}
    except json.JSONDecodeError as e:
        return False, {"error": f"Invalid JSON: {str(e)}", "raw_output": output}

def validate_latex_keywords(latex_code: str) -> List[str]:
    """Extract key LaTeX elements to validate structure."""
    required_elements = [
        r'\\documentclass',
        r'\\begin{document}',
        r'\\end{document}',
    ]
    
    found = []
    missing = []
    
    for element in required_elements:
        if re.search(element, latex_code):
            found.append(element)
        else:
            missing.append(element)
    
    return missing

def extract_keywords_from_text(text: str, job_description: str) -> Dict[str, List[str]]:
    """Extract relevant keywords from resume text."""
    # Simple keyword extraction - in production, use NLP
    text_lower = text.lower()
    job_lower = job_description.lower()
    
    # Extract words from job description (simple approach)
    job_words = set(re.findall(r'\b[a-z]{4,}\b', job_lower))
    resume_words = set(re.findall(r'\b[a-z]{4,}\b', text_lower))
    
    matched = list(job_words.intersection(resume_words))
    missing = list(job_words.difference(resume_words))
    
    return {
        "matched": matched[:20],  # Top 20
        "missing": missing[:20],
        "match_percentage": len(matched) / len(job_words) * 100 if job_words else 0
    }

def calculate_ats_score(
    keywords_present: List[str],
    keywords_missing: List[str],
    formatting_issues: List[str],
    total_keywords: int
) -> float:
    """Calculate ATS compatibility score."""
    if total_keywords == 0:
        return 0.0
    
    # Keyword matching (70% of score)
    keyword_score = (len(keywords_present) / total_keywords) * 70
    
    # Formatting quality (30% of score)
    formatting_score = max(0, 30 - (len(formatting_issues) * 5))
    
    total_score = keyword_score + formatting_score
    return min(100.0, max(0.0, total_score))

def validate_resume_content(content: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate resume content structure."""
    required_fields = [
        "professional_summary",
        "experience",
        "skills",
        "education"
    ]
    
    errors = []
    for field in required_fields:
        if field not in content:
            errors.append(f"Missing required field: {field}")
        elif isinstance(content[field], (list, dict)) and len(content[field]) == 0:
            errors.append(f"Empty field: {field}")
    
    is_valid = len(errors) == 0
    return is_valid, errors

__all__ = [
    "validate_json_output",
    "validate_latex_keywords",
    "extract_keywords_from_text",
    "calculate_ats_score",
    "validate_resume_content",
]
