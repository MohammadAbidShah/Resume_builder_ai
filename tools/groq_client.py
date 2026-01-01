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


def _extract_json_from_prompt(prompt: str) -> dict:
    """Extract JSON resume content from the prompt text."""
    try:
        # Look for JSON block in the prompt
        start_idx = prompt.find('{')
        if start_idx == -1:
            return {}
        # Find matching closing brace
        brace_count = 0
        end_idx = start_idx
        for i in range(start_idx, len(prompt)):
            if prompt[i] == '{':
                brace_count += 1
            elif prompt[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i + 1
                    break
        json_str = prompt[start_idx:end_idx]
        return json.loads(json_str)
    except Exception:
        return {}


def _get_personal_info_from_prompt(prompt: str) -> dict:
    """Extract personal_info dict from prompt JSON."""
    data = _extract_json_from_prompt(prompt)
    # Check if personal_info is nested in the extracted JSON
    if isinstance(data.get("personal_info"), dict):
        return data["personal_info"]
    return data


def _get_mock_response(prompt: str) -> str:
    """Return deterministic mock resume content based on prompt type.
    
    This enables full workflow testing without network access.
    Detects prompt type from system prompt markers.
    Extracts actual resume data from the prompt to use real names, emails, etc.
    """
    prompt_lower = prompt.lower()
    
    # Extract personal info from JSON in prompt
    personal_info = _get_personal_info_from_prompt(prompt)
    name = personal_info.get("name", "Jane Doe")  # Fallback to dummy if not found
    email = personal_info.get("email", "jane@example.com")
    phone = personal_info.get("phone", "(555) 123-4567")
    location = personal_info.get("location", "Seattle, WA")
    
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
        # For content generation, extract job keywords and personal info from prompt
        # and return a structured resume
        resume_data = _extract_json_from_prompt(prompt)
        personal_info = _get_personal_info_from_prompt(prompt)
        
        # Build experience from personal info
        experience = []
        if isinstance(resume_data.get("personal_info"), dict) and resume_data["personal_info"].get("experience"):
            experience = resume_data["personal_info"]["experience"][:2]  # Use up to 2 recent positions
        
        # Build skills from personal info
        skills = {
            "technical": [],
            "soft": ["Leadership", "Communication", "Problem-solving", "Mentoring"]
        }
        if isinstance(resume_data.get("personal_info"), dict):
            personal = resume_data["personal_info"]
            if personal.get("skills"):
                all_skills = []
                for skill_category, skill_list in personal.get("skills", {}).items():
                    if isinstance(skill_list, list):
                        all_skills.extend(skill_list)
                skills["technical"] = all_skills[:10] if all_skills else ["Python", "FastAPI", "Docker", "Kubernetes", "AWS"]
        
        # Build education from personal info
        education = []
        if isinstance(resume_data.get("personal_info"), dict) and resume_data["personal_info"].get("education"):
            edu = resume_data["personal_info"]["education"][0]
            education.append({
                "degree": edu.get("degree", "Bachelor of Technology"),
                "institution": edu.get("school", "University"),
                "year": edu.get("graduation_year", 2025)
            })
        
        return json.dumps({
            "professional_summary": f"Experienced professional with strong expertise in {', '.join(skills['technical'][:3])} and proven track record of delivering scalable solutions.",
            "experience": experience,
            "skills": skills,
            "education": education,
            "matched_keywords": list(resume_data.get("matched_keywords", ["Python", "Docker"]))[:7],
            "missing_keywords": [],
            "optimization_notes": "Resume optimized for job description match."
        })
    
    elif is_latex_gen:
        # Extract actual resume data from prompt
        resume_data = _extract_json_from_prompt(prompt)
        personal_info = _get_personal_info_from_prompt(prompt)
        
        # Build LaTeX from actual data
        experience_tex = ""
        if isinstance(resume_data.get("personal_info"), dict):
            for exp in resume_data["personal_info"].get("experience", []):
                title = exp.get("title", "Position")
                company = exp.get("company", "Company")
                duration = exp.get("duration", "Date")
                description = exp.get("description", "")
                
                experience_tex += f"""\\textbf{{{{{title}}}}} | {company} | {duration}
\\begin{{itemize}}
  \\item {description}
\\end{{itemize}}

"""
        
        education_tex = ""
        if isinstance(resume_data.get("personal_info"), dict):
            for edu in resume_data["personal_info"].get("education", []):
                degree = edu.get("degree", "Degree")
                school = edu.get("school", "School")
                year = edu.get("graduation_year", "Year")
                education_tex += f"\\textbf{{{{{degree}}}}} | {school} | {year}\n"
        
        skills_tex = ""
        if isinstance(resume_data.get("personal_info"), dict):
            skills_dict = resume_data["personal_info"].get("skills", {})
            for category, skill_list in skills_dict.items():
                if isinstance(skill_list, list) and skill_list:
                    skills_str = ", ".join(skill_list[:8])
                    skills_tex += f"\\textbf{{{{{category}}}}}: {skills_str} \\\\\n"
        
        return f"""Here is the LaTeX code for the resume:

```latex
\\documentclass[11pt]{{article}}
\\usepackage[margin=0.5in]{{geometry}}
\\usepackage{{hyperref}}
\\pagestyle{{empty}}

\\begin{{document}}

{{\\Large \\textbf{{{name}}}}} \\\\
{location} | {phone} | {email}

\\section*{{Professional Summary}}
Experienced professional with strong expertise in latest technologies and proven track record of delivering impactful solutions.

\\section*{{Technical Skills}}
{skills_tex}

\\section*{{Professional Experience}}

{experience_tex}

\\section*{{Education}}
{education_tex}

\\end{{document}}
```"""
    
    elif is_ats_check:
        return json.dumps({
            "ats_score": 92.5,
            "keywords_present": ["resume", "experience", "education"],
            "keywords_missing": [],
            "formatting_issues": [],
            "improvement_suggestions": [],
            "analysis_summary": "Resume parsed successfully with good keyword coverage."
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
                "subsections": 0,
                "bullet_points": 0
            },
            "recommendation": "PASS",
            "summary": "LaTeX code is valid and produces professional-quality output."
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
