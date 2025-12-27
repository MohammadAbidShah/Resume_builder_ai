"""Lightweight Groq API client wrapper with mock mode for offline testing.

This module provides a simple `groq_generate` function used by agents.
It uses the `requests` library and reads configuration from `config.settings`.

Features:
- Mock mode (GROQ_MOCK_MODE=true): Returns deterministic canned responses
- Live mode (GROQ_MOCK_MODE=false): Calls real Groq API
- Deterministic: temperature=0, top_k=1, seed=0 for reproducibility
"""
import json
from typing import Optional
import requests

from config.settings import GROQ_API_KEY, GROQ_API_URL, GROQ_MODEL, GROQ_TEMPERATURE, GROQ_MOCK_MODE
from utils.logger import logger


def _get_mock_response(prompt: str) -> str:
    """Return deterministic mock resume content based on prompt type.
    
    This enables full workflow testing without network access.
    Detects prompt type from system prompt markers.
    """
    prompt_lower = prompt.lower()
    
    # Detect prompt type - check for LaTeX first (most specific)
    if "latex document expert" in prompt_lower or "latex code that compiles" in prompt_lower:
        is_latex_gen = True
        is_content_gen = False
        is_ats_check = False
        is_pdf_validate = False
        is_feedback = False
    # Then PDF validator
    elif "pdf and latex quality expert" in prompt_lower or "validate the quality of a generated resume pdf" in prompt_lower:
        is_pdf_validate = True
        is_latex_gen = False
        is_content_gen = False
        is_ats_check = False
        is_feedback = False
    # Then ATS checker
    elif "ats (applicant tracking system) optimization expert" in prompt_lower:
        is_ats_check = True
        is_latex_gen = False
        is_content_gen = False
        is_pdf_validate = False
        is_feedback = False
    # Then feedback agent
    elif "resume optimization decision maker" in prompt_lower or "standards to check" in prompt_lower:
        is_feedback = True
        is_latex_gen = False
        is_content_gen = False
        is_ats_check = False
        is_pdf_validate = False
    # Default to content generation
    else:
        is_content_gen = True
        is_latex_gen = False
        is_ats_check = False
        is_pdf_validate = False
        is_feedback = False
    
    # Return mock responses in valid JSON format
    if is_content_gen:
        return json.dumps({
            "professional_summary": "Results-driven Senior Python Developer with 8+ years of experience building scalable backend systems. Expertise in FastAPI, PostgreSQL, and AWS cloud services. Proven track record of optimizing database queries and mentoring junior developers.",
            "experience": [
                {
                    "title": "Senior Python Developer",
                    "company": "Tech Solutions Inc.",
                    "duration": "2021-Present",
                    "description": "Designed and developed scalable REST APIs using FastAPI, handling 10M+ daily requests. Optimized database queries reducing latency by 40%. Mentored 3 junior developers."
                },
                {
                    "title": "Python Developer",
                    "company": "Data Systems Ltd.",
                    "duration": "2018-2021",
                    "description": "Implemented microservices architecture using Docker and Kubernetes. Developed CI/CD pipelines reducing deployment time by 60%."
                }
            ],
            "skills": {
                "technical": ["Python 3.9+", "FastAPI", "Django", "PostgreSQL", "MongoDB", "Docker", "Kubernetes", "AWS", "Redis", "Git"],
                "soft": ["Leadership", "Communication", "Problem-solving", "Mentoring"]
            },
            "education": [
                {
                    "degree": "B.S. Computer Science",
                    "institution": "State University",
                    "year": 2016
                }
            ],
            "matched_keywords": ["Python", "FastAPI", "PostgreSQL", "AWS", "Docker", "REST API", "Microservices"],
            "missing_keywords": ["GraphQL", "Apache Kafka"],
            "optimization_notes": "Resume emphasizes scalability and mentoring, matching senior-level requirements."
        })
    
    elif is_latex_gen:
        return """Here is the LaTeX code for the resume:

```latex
\\documentclass[11pt]{article}
\\usepackage[margin=0.5in]{geometry}
\\usepackage{hyperref}
\\pagestyle{empty}

\\begin{document}

{\\Large \\textbf{Jane Doe}} \\\\
Seattle, WA | (555) 123-4567 | jane@example.com | LinkedIn

\\section*{Professional Summary}
Results-driven Senior Python Developer with 8+ years experience building scalable backend systems and mentoring engineering teams.

\\section*{Technical Skills}
\\textbf{Languages \\& Frameworks:} Python 3.9+, FastAPI, Django, REST APIs \\\\
\\textbf{Databases:} PostgreSQL, MongoDB, Redis \\\\
\\textbf{DevOps:} Docker, Kubernetes, AWS, CI/CD \\\\
\\textbf{Other:} Git, Microservices, API Design

\\section*{Professional Experience}

\\textbf{Senior Python Developer} | Tech Solutions Inc. | 2021--Present
\\begin{itemize}
  \\item Designed and developed scalable REST APIs using FastAPI handling 10M+ daily requests
  \\item Optimized database queries reducing latency by 40\\%
  \\item Mentored 3 junior developers on best practices
\\end{itemize}

\\textbf{Python Developer} | Data Systems Ltd. | 2018--2021
\\begin{itemize}
  \\item Implemented microservices architecture using Docker and Kubernetes
  \\item Developed CI/CD pipelines reducing deployment time by 60\\%
\\end{itemize}

\\section*{Education}
\\textbf{B.S. Computer Science} | State University | 2016

\\end{document}
```"""
    
    elif is_ats_check:
        return json.dumps({
            "ats_score": 92.5,
            "keywords_present": ["Python", "FastAPI", "PostgreSQL", "AWS", "Docker", "REST API", "Microservices", "Kubernetes"],
            "keywords_missing": ["GraphQL", "Apache Kafka"],
            "formatting_issues": [],
            "improvement_suggestions": ["Consider adding GraphQL experience if applicable"],
            "analysis_summary": "Excellent ATS score with strong keyword coverage. Resume passes ATS scanning and includes all critical job requirements."
        })
    
    elif is_pdf_validate:
        return json.dumps({
            "quality_score": 88,
            "latex_valid": True,
            "formatting_issues": [],
            "ats_warnings": [],
            "visual_suggestions": ["Professional formatting maintained"],
            "structure_analysis": {
                "sections": 5,
                "subsections": 2,
                "bullet_points": 6
            },
            "recommendation": "PASS",
            "summary": "LaTeX code is valid and produces professional-quality PDF. All sections are well-formatted."
        })
    
    elif is_feedback:
        return json.dumps({
            "overall_status": "FAIL",
            "priority_fixes": ["Increase ATS score above 90%", "Fix LaTeX syntax issues", "Improve keyword coverage"],
            "content_feedback": "The resume needs more targeted keywords from the job description. Focus on adding industry-specific terms and metrics that match the role requirements.",
            "latex_feedback": "Review the LaTeX syntax for compilation errors. Ensure all special characters are properly escaped and sections are properly closed.",
            "confidence_next_iteration": 75,
            "summary": "Resume shows promise but needs refinement in keyword optimization and LaTeX formatting. Next iteration should focus on these areas.",
            "standards_met": {
                "ATS_Score_90%+": False,
                "Keywords_Complete": False,
                "LaTeX_Valid": False,
                "PDF_Quality_85+": False,
                "No_ATS_Blocking_Issues": False
            }
        })
    
    # Default fallback
    return json.dumps({"success": True, "message": "Mock response generated"})


def groq_generate(prompt: str, max_tokens: int = 1024, temperature: float = None) -> str:
    """Generate text using Groq API or mock mode.

    Args:
        prompt: The text prompt to send.
        max_tokens: Max tokens to generate.
        temperature: Sampling temperature (None -> use default from settings).

    Returns:
        The generated text as a single string.
    """
    if temperature is None:
        temperature = GROQ_TEMPERATURE
    
    # Use mock mode for offline testing
    if GROQ_MOCK_MODE:
        logger.info("Groq client: Using MOCK MODE (offline)")
        return _get_mock_response(prompt)
    
    # Live mode: call real Groq API
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY is not configured in environment")
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    payload = {
        "prompt": prompt,
        "max_tokens": max_tokens,
        "temperature": float(temperature),
        # Ensure determinism where possible
        "top_k": 1,
        "top_p": 1.0,
        "seed": 0
    }

    try:
        resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=30)
        resp.raise_for_status()
        data = resp.json()

        # Attempt common response shapes
        if isinstance(data, dict):
            # Common location for generated text
            if "text" in data:
                return data["text"]
            if "output" in data and isinstance(data["output"], list):
                # join text segments
                return "".join([seg.get("text", "") for seg in data["output"]])
            # try choices / generations
            if "choices" in data and isinstance(data["choices"], list):
                return data["choices"][0].get("text", "")

        # Fallback to raw text
        return resp.text

    except requests.HTTPError as e:
        logger.error(f"Groq API error: {e} - {resp.text if 'resp' in locals() else ''}")
        raise
    except Exception as e:
        logger.error(f"Groq client request failed: {str(e)}")
        raise
