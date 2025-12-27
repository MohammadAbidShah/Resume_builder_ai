"""Validation tools for ATS checking and PDF quality assessment."""
import json
import re
from typing import Dict, List, Any, Tuple
from utils.logger import logger

def check_ats_compatibility(
    resume_text: str,
    job_description: str
) -> Dict[str, Any]:
    """
    Check ATS compatibility and calculate score.
    
    Args:
        resume_text: Plain text version of resume
        job_description: Original job description
        
    Returns:
        ATS analysis report
    """
    # Extract keywords from job description
    job_keywords = _extract_keywords(job_description)
    
    # Check which keywords are present in resume
    resume_lower = resume_text.lower()
    keywords_present = []
    keywords_missing = []
    
    for keyword in job_keywords:
        if keyword.lower() in resume_lower:
            keywords_present.append(keyword)
        else:
            keywords_missing.append(keyword)
    
    # Calculate ATS score
    match_percentage = (len(keywords_present) / len(job_keywords) * 100) if job_keywords else 0
    
    # Check for ATS-blocking elements
    ats_issues = _check_ats_blocking_elements(resume_text)
    
    # Base score calculation
    base_score = match_percentage
    penalty = len(ats_issues) * 5  # Each issue reduces score by 5
    ats_score = max(0, min(100, base_score - penalty))
    
    report = {
        "ats_score": ats_score,
        "match_percentage": match_percentage,
        "keywords_present": keywords_present[:30],  # Top 30
        "keywords_missing": keywords_missing[:30],  # Top 30
        "total_keywords_in_job": len(job_keywords),
        "keywords_matched": len(keywords_present),
        "ats_blocking_issues": ats_issues,
        "improvement_suggestions": _generate_ats_suggestions(keywords_missing, ats_issues),
        "analysis": f"Score: {ats_score:.1f}%. Found {len(keywords_present)} of {len(job_keywords)} keywords."
    }
    
    logger.info(f"ATS Analysis: Score = {ats_score:.1f}%")
    return report

def _extract_keywords(text: str) -> List[str]:
    """Extract important keywords from text."""
    # Remove common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'be', 'have',
        'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
        'may', 'might', 'can', 'we', 'you', 'i', 'he', 'she', 'it', 'they',
        'this', 'that', 'these', 'those', 'your', 'our', 'my', 'his', 'her'
    }
    
    # Extract words (4+ characters)
    words = re.findall(r'\b[a-z]{3,}\b', text.lower())
    
    # Filter stop words and get unique
    keywords = [w for w in set(words) if w not in stop_words]
    
    return sorted(keywords)[:100]  # Return top 100

def _check_ats_blocking_elements(text: str) -> List[str]:
    """Check for ATS-blocking elements."""
    issues = []
    
    # Check for graphics/images (often breaks ATS parsing)
    if '[image]' in text.lower() or '[graphic]' in text.lower():
        issues.append("Text contains reference to images/graphics")
    
    # Check for unusual characters
    unusual_chars = re.findall(r'[^\w\s\-.,;:\'"()/]', text)
    if unusual_chars:
        issues.append(f"Unusual characters found that may confuse ATS parsers")
    
    # Check for excessively long lines (ATS may have issues)
    lines = text.split('\n')
    long_lines = [l for l in lines if len(l) > 120]
    if long_lines:
        issues.append(f"Found {len(long_lines)} lines exceeding 120 characters")
    
    # Check for unusual spacing or formatting indicators
    if '     ' in text:  # Multiple spaces
        issues.append("Excessive spacing detected - ATS prefers normal spacing")
    
    return issues

def _generate_ats_suggestions(missing_keywords: List[str], blocking_issues: List[str]) -> List[str]:
    """Generate suggestions to improve ATS score."""
    suggestions = []
    
    if missing_keywords:
        top_missing = missing_keywords[:5]
        suggestions.append(f"Add missing keywords: {', '.join(top_missing)}")
    
    for issue in blocking_issues:
        if 'images' in issue.lower():
            suggestions.append("Remove or describe images with text")
        elif 'spacing' in issue.lower():
            suggestions.append("Use single spaces between words/sections")
        elif 'unusual characters' in issue.lower():
            suggestions.append("Replace special characters with standard text")
    
    if not suggestions:
        suggestions.append("ATS compatibility looks good!")
    
    return suggestions

def validate_pdf_quality(latex_code: str) -> Dict[str, Any]:
    """
    Validate PDF quality and rendering issues.
    
    Args:
        latex_code: LaTeX code to validate
        
    Returns:
        Quality assessment report
    """
    quality_score = 100  # Start with perfect score
    issues = []
    ats_warnings = []
    
    # Check for compilation issues
    latex_issues = _check_latex_errors(latex_code)
    if latex_issues:
        quality_score -= len(latex_issues) * 10
        issues.extend(latex_issues)
    
    # Check formatting
    formatting_issues = _check_formatting_quality(latex_code)
    if formatting_issues:
        quality_score -= len(formatting_issues) * 5
        issues.extend(formatting_issues)
    
    # Check for visual appeal
    visual_score = _assess_visual_appeal(latex_code)
    quality_score = quality_score * (visual_score / 100)
    
    # Check ATS compatibility
    ats_issues = _check_ats_compatibility_latex(latex_code)
    if ats_issues:
        ats_warnings.extend(ats_issues)
        quality_score -= len(ats_issues) * 3
    
    # Ensure score is within bounds
    quality_score = max(0, min(100, quality_score))
    
    report = {
        "quality_score": quality_score,
        "latex_valid": len(latex_issues) == 0,
        "formatting_issues": issues,
        "ats_warnings": ats_warnings,
        "visual_score": visual_score,
        "structure_analysis": _analyze_structure(latex_code),
        "recommendation": "PASS" if quality_score >= 85 else "NEEDS_IMPROVEMENT",
        "summary": f"Quality Score: {quality_score:.0f}/100. " + 
                  ("Professional and ATS-friendly" if quality_score >= 85 else "Needs improvements")
    }
    
    logger.info(f"PDF Quality Check: Score = {quality_score:.0f}/100")
    return report

def _check_latex_errors(latex_code: str) -> List[str]:
    """Check for LaTeX compilation errors."""
    errors = []
    
    # Check for unmatched braces
    if latex_code.count('{') != latex_code.count('}'):
        errors.append("Unmatched braces")
    
    if latex_code.count('[') != latex_code.count(']'):
        errors.append("Unmatched brackets")
    
    # Check for undefined commands (basic check)
    invalid_commands = re.findall(r'\\[a-z]+', latex_code, re.IGNORECASE)
    
    return errors

def _check_formatting_quality(latex_code: str) -> List[str]:
    """Check formatting quality."""
    issues = []
    
    # Check for consistent section usage
    if '\\section' not in latex_code and '\\subsection' not in latex_code:
        issues.append("No clear section structure found")
    
    # Check for bullet points/lists
    if '\\item' not in latex_code:
        issues.append("No bullet points found - consider using lists for readability")
    
    # Check for text emphasis
    if '\\textbf' not in latex_code and '\\textit' not in latex_code:
        issues.append("No text emphasis found - consider highlighting important items")
    
    return issues

def _assess_visual_appeal(latex_code: str) -> float:
    """Assess visual appeal of the resume."""
    score = 100.0
    
    # Check for variety in formatting
    has_bold = '\\textbf' in latex_code
    has_italic = '\\textit' in latex_code
    has_lists = '\\item' in latex_code
    has_sections = '\\section' in latex_code
    
    formatting_elements = sum([has_bold, has_italic, has_lists, has_sections])
    score = score * (formatting_elements / 4)  # All 4 elements = 100%
    
    # Penalize for excessive formatting
    formatting_count = latex_code.count('\\textbf') + latex_code.count('\\textit')
    if formatting_count > 30:
        score -= 10  # Too much formatting
    
    return max(0, min(100, score))

def _check_ats_compatibility_latex(latex_code: str) -> List[str]:
    """Check LaTeX for ATS compatibility issues."""
    warnings = []
    
    if 'tabular' in latex_code:
        warnings.append("Tables may not parse well in ATS")
    
    if '\\includegraphics' in latex_code:
        warnings.append("Images will be stripped by ATS")
    
    if 'tikz' in latex_code or 'pgf' in latex_code:
        warnings.append("Complex graphics (TikZ/PGF) may not be ATS compatible")
    
    if 'multicol' in latex_code:
        warnings.append("Multi-column layout may be parsed incorrectly by ATS")
    
    return warnings

def _analyze_structure(latex_code: str) -> Dict[str, Any]:
    """Analyze document structure."""
    sections = len(re.findall(r'\\section\{', latex_code))
    subsections = len(re.findall(r'\\subsection\{', latex_code))
    items = len(re.findall(r'\\item\b', latex_code))
    
    return {
        "sections": sections,
        "subsections": subsections,
        "bullet_points": items,
        "has_preamble": '\\documentclass' in latex_code,
        "document_well_structured": sections >= 3
    }

__all__ = [
    "check_ats_compatibility",
    "validate_pdf_quality",
]
