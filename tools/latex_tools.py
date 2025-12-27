"""LaTeX generation and validation tools for Resume Builder AI."""
import re
import json
from typing import Dict, List, Any, Tuple
from utils.logger import logger

LATEX_TEMPLATE = r"""
\documentclass[11pt]{article}
\usepackage[utf-8]{inputenc}
\usepackage[margin=0.5in]{geometry}
\usepackage{xcolor}
\usepackage{hyperref}
\usepackage{enumitem}
\usepackage{fontspec}
\usepackage{titlesec}

% Section formatting
\titleformat{\section}{\large\bfseries}{\thesection}{1em}{}[\titlerule]
\titlespacing{\section}{0pt}{12pt}{6pt}

% Subsection formatting
\titleformat{\subsection}{\normalsize\bfseries}{}{0em}{}
\titlespacing{\subsection}{0pt}{6pt}{3pt}

% Remove default spacing
\setlist{nosep}

% Define colors (ATS-friendly: use basic colors)
\definecolor{darkblue}{RGB}{0, 51, 102}

\hypersetup{colorlinks=true, linkcolor=darkblue, urlcolor=darkblue}

\renewcommand{\familydefault}{\sfdefault}

\pagestyle{empty}

\begin{document}

% HEADER
\begin{center}
\Large\textbf{%NAME%}\\[2pt]
\normalsize
%EMAIL% $\mid$ %PHONE%\\[6pt]
\end{center}

% PROFESSIONAL SUMMARY
\section{Professional Summary}
%SUMMARY%

% PROFESSIONAL EXPERIENCE
\section{Professional Experience}
%EXPERIENCE%

% SKILLS
\section{Skills}
%SKILLS%

% EDUCATION
\section{Education}
%EDUCATION%

\end{document}
"""

def generate_latex_code(resume_content: Dict[str, Any]) -> str:
    """
    Generate LaTeX code from resume content.
    
    Args:
        resume_content: Structured resume content
        
    Returns:
        Valid LaTeX code as string
    """
    latex = LATEX_TEMPLATE
    
    # Replace placeholders
    personal_info = resume_content.get("personal_info", {})
    latex = latex.replace("%NAME%", personal_info.get("name", "Your Name"))
    latex = latex.replace("%EMAIL%", personal_info.get("email", "email@example.com"))
    latex = latex.replace("%PHONE%", personal_info.get("phone", "(XXX) XXX-XXXX"))
    
    # Professional Summary
    summary = resume_content.get("professional_summary", "")
    latex = latex.replace("%SUMMARY%", summary)
    
    # Experience
    experience_latex = _format_experience_latex(resume_content.get("experience", []))
    latex = latex.replace("%EXPERIENCE%", experience_latex)
    
    # Skills
    skills_latex = _format_skills_latex(resume_content.get("skills", {}))
    latex = latex.replace("%SKILLS%", skills_latex)
    
    # Education
    education_latex = _format_education_latex(resume_content.get("education", []))
    latex = latex.replace("%EDUCATION%", education_latex)
    
    logger.info("Generated LaTeX code successfully")
    return latex

def _format_experience_latex(experience: List[Dict[str, Any]]) -> str:
    """Format experience section in LaTeX."""
    if not experience:
        return "No experience provided."
    
    latex_items = []
    for exp in experience:
        title = exp.get("title", "")
        company = exp.get("company", "")
        duration = exp.get("duration", "")
        description = exp.get("description", "")
        
        item = f"""\\subsection{{{title} @ {company}}}
{duration}\\\\
{description}

"""
        latex_items.append(item)
    
    return "".join(latex_items)

def _format_skills_latex(skills: Dict[str, List[str]]) -> str:
    """Format skills section in LaTeX."""
    if not skills:
        return "No skills provided."
    
    latex_items = []
    for category, skill_list in skills.items():
        if isinstance(skill_list, list):
            skills_str = ", ".join(skill_list)
            item = f"\\textbf{{{category}:}} {skills_str}\\\\\n"
            latex_items.append(item)
    
    return "".join(latex_items)

def _format_education_latex(education: List[Dict[str, Any]]) -> str:
    """Format education section in LaTeX."""
    if not education:
        return "No education provided."
    
    latex_items = []
    for edu in education:
        degree = edu.get("degree", "")
        school = edu.get("school", "")
        year = edu.get("year", "")
        
        item = f"\\textbf{{{degree}}} - {school} ({year})\\\\\n"
        latex_items.append(item)
    
    return "".join(latex_items)

def validate_latex_syntax(latex_code: str) -> Tuple[bool, List[str]]:
    """
    Validate LaTeX code for syntax errors.
    
    Args:
        latex_code: LaTeX code to validate
        
    Returns:
        (is_valid: bool, errors: List[str])
    """
    errors = []
    
    # Check required elements
    required_elements = [
        (r'\\documentclass', 'Missing \\documentclass declaration'),
        (r'\\begin\{document\}', 'Missing \\begin{document}'),
        (r'\\end\{document\}', 'Missing \\end{document}'),
    ]
    
    for pattern, error_msg in required_elements:
        if not re.search(pattern, latex_code):
            errors.append(error_msg)
    
    # Check for common errors
    # Unmatched braces
    open_braces = latex_code.count('{')
    close_braces = latex_code.count('}')
    if open_braces != close_braces:
        errors.append(f"Unmatched braces: {open_braces} open, {close_braces} close")
    
    # Unmatched backslashes at end of line
    bad_lines = [line for line in latex_code.split('\n') if line.strip().endswith('\\')]
    if bad_lines:
        errors.append(f"Lines ending with single backslash (potential command breaks)")
    
    # Check for common typos
    if '\\textbff' in latex_code:
        errors.append("Found '\\textbff' - did you mean '\\textbf'?")
    
    if '\\begin{document' in latex_code and '\\begin{document}' not in latex_code:
        errors.append("Malformed \\begin{document} - missing closing brace")
    
    is_valid = len(errors) == 0
    logger.info(f"LaTeX validation: {'PASS' if is_valid else 'FAIL'} ({len(errors)} errors)")
    
    return is_valid, errors

def format_latex_for_ats(latex_code: str) -> Tuple[str, List[str]]:
    """
    Format LaTeX code for ATS compatibility.
    
    Args:
        latex_code: Original LaTeX code
        
    Returns:
        (formatted_code: str, changes_made: List[str])
    """
    formatted = latex_code
    changes = []
    
    # Remove complex formatting that ATS might struggle with
    if '\\multicolumn' in formatted or 'tabular' in formatted:
        changes.append("Converted tables to text-based format")
        formatted = re.sub(r'\\begin\{tabular\}.*?\\end\{tabular\}', '', formatted, flags=re.DOTALL)
    
    # Remove graphics
    if '\\includegraphics' in formatted:
        changes.append("Removed images (ATS compatibility)")
        formatted = re.sub(r'\\includegraphics.*?\}', '', formatted)
    
    # Simplify colors
    if 'definecolor' in formatted or '\\textcolor' in formatted:
        changes.append("Simplified color usage for ATS")
    
    # Ensure consistent spacing
    formatted = re.sub(r'\n\n+', '\n', formatted)
    
    logger.info(f"ATS formatting: {len(changes)} changes made")
    return formatted, changes

def extract_plain_text_from_latex(latex_code: str) -> str:
    """Extract plain text from LaTeX code for ATS parsing."""
    # Remove LaTeX commands while preserving text
    text = latex_code
    
    # Remove documentclass, usepackage, etc.
    text = re.sub(r'\\[a-z]+\{[^}]*\}', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\\[a-z]+\[.*?\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\\[a-z]+', '', text, flags=re.IGNORECASE)
    
    # Remove environments
    text = re.sub(r'\\begin\{.*?\}.*?\\end\{.*?\}', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove special characters
    text = re.sub(r'[{}$%&#^_~]', '', text)
    
    # Clean up whitespace
    text = re.sub(r'\n\n+', '\n', text)
    text = re.sub(r' +', ' ', text)
    
    return text.strip()

__all__ = [
    "generate_latex_code",
    "validate_latex_syntax",
    "format_latex_for_ats",
    "extract_plain_text_from_latex",
]
