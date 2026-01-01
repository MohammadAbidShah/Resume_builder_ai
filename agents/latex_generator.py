"""LaTeX Generator Agent - Agent 2."""
import json
from typing import Dict, Any
from tools.groq_client import groq_generate
from tools.ats_optimizer import ATSOptimizer
from pathlib import Path
from config.settings import CONTENT_MODEL, CONTENT_GENERATION_TEMPERATURE
from config.prompts import SYSTEM_PROMPTS
from tools import (
    generate_latex_code,
    validate_latex_syntax,
    format_latex_for_ats,
    extract_plain_text_from_latex
)
from utils.logger import logger
from utils.validators import validate_json_output

class LaTeXGeneratorAgent:
    """
    Agent 2: Converts resume content into LaTeX code.
    """
    
    def __init__(self):
        self.system_prompt = SYSTEM_PROMPTS["latex_generator"]
    
    def generate(
        self,
        resume_content: Dict[str, Any],
        feedback: str = None
    ) -> Dict[str, Any]:
        """
        Generate LaTeX code from resume content.
        
        Args:
            resume_content: Structured resume content
            feedback: Optional formatting feedback from previous iteration
            
        Returns:
            Dictionary with LaTeX code and metadata
        """
        logger.info("LaTeX Generator Agent: Starting...")
        
        if feedback:
            user_prompt = self._build_prompt_with_feedback(resume_content, feedback)
            logger.info("LaTeX Generator: Applying formatting feedback")
        else:
            user_prompt = self._build_initial_prompt(resume_content)
            logger.info("LaTeX Generator: Creating initial LaTeX")
        
        try:
            # Prefer using the local LaTeX template if available
            try:
                latex_code = self._render_from_template(resume_content)
                logger.info("LaTeX Generator: Rendered LaTeX from local template")
            except FileNotFoundError:
                # Fallback to LLM generation when template is not present
                prompt = self.system_prompt + "\n\n" + user_prompt
                response_text = groq_generate(prompt, max_tokens=4096, temperature=0)
                logger.info("LaTeX Generator: Received response from Groq API")
                # Extract LaTeX code (might be wrapped in markdown code blocks)
                latex_code = self._extract_latex_code(response_text)
                if not latex_code:
                    logger.error("No LaTeX code found in response")
                    return {
                        "success": False,
                        "error": "No LaTeX code generated",
                        "raw_output": response_text
                    }
            
            # Validate LaTeX syntax
            is_valid, latex_errors = validate_latex_syntax(latex_code)
            
            # Format for ATS
            ats_formatted, ats_changes = format_latex_for_ats(latex_code)
            
            # Extract plain text for ATS parsing
            plain_text = extract_plain_text_from_latex(latex_code)
            
            result = {
                "success": True,
                "latex_code": ats_formatted,
                "original_latex": latex_code,
                "plain_text": plain_text,
                "syntax_valid": is_valid,
                "syntax_errors": latex_errors,
                "ats_changes": ats_changes,
                "character_count": len(latex_code),
            }
            
            logger.info(f"LaTeX Generator: Generated {len(latex_code)} characters of LaTeX")
            if not is_valid:
                logger.warning(f"LaTeX validation errors: {latex_errors}")
            
            return result
            
        except Exception as e:
            logger.error(f"LaTeX Generator Agent error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _extract_latex_code(self, response: str) -> str:
        """Extract LaTeX code from response (handle markdown code blocks)."""
        import re
        
        # Try to find LaTeX in code blocks
        code_block_match = re.search(r'```(?:latex|tex)?\s*(.*?)```', response, re.DOTALL)
        if code_block_match:
            return code_block_match.group(1).strip()
        
        # If no code block, try to find \documentclass as start
        if '\\documentclass' in response:
            start = response.index('\\documentclass')
            # Find the end (should be \end{document})
            if '\\end{document}' in response[start:]:
                end = response.index('\\end{document}', start) + len('\\end{document}')
                return response[start:end].strip()
        
        # Last resort: return everything that looks like LaTeX
        if '\\' in response:
            return response.strip()
        
        return ""
    
    def _build_initial_prompt(self, resume_content: Dict[str, Any]) -> str:
        """Build initial prompt for LaTeX generation."""
        content_str = json.dumps(resume_content, indent=2)
        
        prompt = f"""
Convert this resume content into production-ready LaTeX code:

{content_str}

Requirements:
1. Generate complete, compilable LaTeX document
2. Use professional, ATS-friendly template
3. Include all sections: summary, experience, skills, education
4. Use clear formatting with bullet points
5. Ensure proper spacing and alignment
6. Add the person's name and contact info in header
7. Use text-based formatting only (no tables, columns, or graphics)
8. Include proper preamble with necessary packages

Return ONLY the complete LaTeX code that can be directly compiled to PDF.
Wrap the code in ```latex ... ``` blocks.
"""
        return prompt
    
    def _build_prompt_with_feedback(
        self,
        resume_content: Dict[str, Any],
        feedback: str
    ) -> str:
        """Build prompt with formatting feedback."""
        content_str = json.dumps(resume_content, indent=2)
        
        prompt = f"""
Please fix the LaTeX code based on this feedback:

FEEDBACK:
{feedback}

RESUME CONTENT:
{content_str}

Please regenerate the LaTeX code addressing:
1. All mentioned formatting issues
2. Any structure improvements needed
3. Better ATS compatibility
4. Professional appearance

Return ONLY the complete corrected LaTeX code wrapped in ```latex ... ``` blocks.
"""
        return prompt

    def _render_from_template(self, resume_content: Dict[str, Any]) -> str:
        """Render LaTeX by filling `templates/resume_template.tex` with resume data.

        Integrates ATS optimization to ensure JD alignment and measurable impact.
        Raises FileNotFoundError if template not found.
        """
        template_path = Path("templates") / "resume_template.tex"
        if not template_path.exists():
            raise FileNotFoundError("LaTeX template not found")

        with open(template_path, 'r', encoding='utf-8') as f:
            tpl = f.read()

        # Extract personal_info and job description
        personal = resume_content.get("personal_info", {}) if isinstance(resume_content, dict) else {}
        job_description = resume_content.get("job_description", "")

        # Initialize ATS Optimizer if JD is available
        ats_optimizer = None
        if job_description:
            ats_optimizer = ATSOptimizer(job_description)
            logger.info("ATS Optimizer initialized for JD-aligned content generation")

        def escape_latex(text: Any) -> str:
            if text is None:
                return ""
            s = str(text)
            # Basic safe replacements
            replacements = [
                ('\\', '\\textbackslash{}'),
                ('%', '\\%'),
                ('&', '\\&'),
                ('$', '\\$'),
                ('#', '\\#'),
                ('_', '\\_'),
                ('{', '\\{'),
                ('}', '\\}'),
                ('~', '\\textasciitilde{}'),
                ('^', '\\textasciicircum{}')
            ]
            for old, new in replacements:
                s = s.replace(old, new)
            # Collapse multiple whitespace/newlines
            s = s.replace('\r', ' ').replace('\n', ' ').strip()
            return s

        name = escape_latex(personal.get("name", ""))
        contact_parts = []
        if personal.get("location"):
            contact_parts.append(escape_latex(personal.get("location")))
        if personal.get("phone"):
            contact_parts.append(escape_latex(personal.get("phone")))
        if personal.get("email"):
            email = personal.get("email")
            email_esc = escape_latex(email)
            contact_parts.append(f"\\href{{mailto:{email_esc}}}{{{email_esc}}}")
        if personal.get("linkedin"):
            linkedin = personal.get("linkedin")
            linkedin_url = linkedin if linkedin.startswith("http") else f"https://{linkedin}"
            contact_parts.append(f"\\href{{{escape_latex(linkedin_url)}}}{{{escape_latex(linkedin)}}}")
        if personal.get("github"):
            github = personal.get("github")
            github_url = github if github.startswith("http") else f"https://{github}"
            contact_parts.append(f"\\href{{{escape_latex(github_url)}}}{{{escape_latex(github)}}}")
        contact = " | ".join(contact_parts)

        # Generate ATS-optimized summary
        summary = ""
        if ats_optimizer:
            summary = ats_optimizer.generate_summary(personal)
            logger.info("ATS Optimizer: Generated optimized summary")
        else:
            summary = resume_content.get("professional_summary") or resume_content.get("summary") or ""
        summary = escape_latex(summary)

        # Generate ATS-optimized skills (grouped from JD)
        skills_section = ""
        skills = {}
        if isinstance(personal.get("skills"), dict):
            skills = personal.get("skills")
        elif isinstance(resume_content.get("skills"), dict):
            skills = resume_content.get("skills")
        
        # If ATS Optimizer available, always derive JD-aligned skills (even if personal skills are empty)
        if ats_optimizer:
            skills = ats_optimizer.get_skills_grouped(skills)
            logger.info("ATS Optimizer: Applied JD-aligned skill grouping")
        
        for cat, vals in skills.items():
            if isinstance(vals, list) and vals:
                clean_vals = [escape_latex(v) for v in vals]
                # produce two backslashes then newline for LaTeX linebreak
                skills_section += f"\\textbf{{{escape_latex(cat)}}}: {', '.join(clean_vals)} " + "\\\\" + "\n"

        # Generate ATS-optimized experience with measurable impact
        exp_section = ""
        experiences = personal.get("experience") or resume_content.get("experience") or []
        for exp in experiences:
            title = escape_latex(exp.get("title", ""))
            company = escape_latex(exp.get("company", ""))
            duration = escape_latex(exp.get("duration", ""))
            location = escape_latex(exp.get("location", ""))
            desc = escape_latex(exp.get("description", ""))
            
            exp_section += f"\\resumeSubheading{{{title}}}{{{duration}}}{{{company}}}{{{location}}}\n"
            exp_section += "\\resumeItemListStart\n"
            
            # Generate 3-5 ATS-optimized bullets per role
            if ats_optimizer:
                bullets = ats_optimizer.generate_experience_bullets(exp)
                logger.info(f"ATS Optimizer: Generated {len(bullets)} optimized bullets for {title}")
                for bullet in bullets:
                    exp_section += f"\\resumeItem{{{escape_latex(bullet)}}}\n"
            elif desc:
                exp_section += f"\\resumeItem{{{desc}}}\n"
            
            exp_section += "\\resumeItemListEnd\n\n"

        # Projects (ATS-optimized if available)
        projects_section = ""
        projects = personal.get("projects") or resume_content.get("projects") or []
        for proj in projects:
            proj_name = escape_latex(proj.get("name", "Project"))
            proj_duration = escape_latex(proj.get("duration", ""))
            proj_tech = proj.get("technologies", [])
            proj_desc = escape_latex(proj.get("description", ""))
            proj_url = proj.get("url", "")
            
            # Format: Project Name with technologies and duration
            tech_str = escape_latex(", ".join(proj_tech)) if proj_tech else ""
            
            projects_section += f"\\resumeProjectHeading{{\\textbf{{{proj_name}}}"
            if tech_str:
                projects_section += f" | \\textit{{{tech_str}}}"
            projects_section += f"}}{{{proj_duration}}}\n"
            projects_section += "\\resumeItemListStart\n"
            
            # If ATS optimizer available, generate optimized bullets
            if ats_optimizer:
                proj_bullets = ats_optimizer.generate_project_bullets(proj)
                for bullet in proj_bullets[:3]:  # Max 3 bullets per project
                    projects_section += f"\\resumeItem{{{escape_latex(bullet)}}}\n"
            elif proj_desc:
                # Split description by periods or newlines to create bullets
                bullets = [b.strip() for b in proj_desc.replace('\n', '. ').split('. ') if b.strip()]
                for bullet in bullets[:3]:
                    projects_section += f"\\resumeItem{{{escape_latex(bullet)}}}\n"
            
            projects_section += "\\resumeItemListEnd\n\n"

        # Awards & Certifications (combined section)
        awards_and_certifications_section = ""

        # Prefer combined field; fallback to legacy awards/certifications for backward compatibility
        combined = personal.get("awards_and_certifications") or resume_content.get("awards_and_certifications") or []
        awards = personal.get("awards") or resume_content.get("awards") or []
        certifications = personal.get("certifications") or resume_content.get("certifications") or []

        def build_award_line(entry: Dict[str, Any]) -> str:
            name_tex = escape_latex(entry.get("name", ""))
            issuer_tex = escape_latex(entry.get("issuer", ""))
            date_tex = escape_latex(entry.get("date", ""))
            desc_tex = ""

            if ats_optimizer:
                desc_tex = escape_latex(ats_optimizer.get_award_cert_description(entry))
            else:
                desc_tex = escape_latex(entry.get("description", ""))

            line = f"\\textbf{{{name_tex}}}" if name_tex else ""
            if issuer_tex:
                line += f" (\\textbf{{{issuer_tex}}})"
            if date_tex:
                line += f" | {date_tex}"
            if desc_tex:
                line += f" — {desc_tex}"
            return line

        all_entries = []

        if combined:
            for entry in combined:
                all_entries.append(build_award_line(entry))
        else:
            # Legacy paths
            for cert in certifications:
                all_entries.append(build_award_line(cert))

            for award in awards:
                all_entries.append(build_award_line(award))

        # Render all entries as single bullet points (no duplication, no omission)
        for entry_text in all_entries:
            awards_and_certifications_section += f"\\resumeItem{{{entry_text}}}\n"

        # Education (use as-is from personal_info)
        education_section = ""
        education_list = personal.get("education") or resume_content.get("education") or []
        for edu in education_list:
            degree = escape_latex(edu.get("degree", edu.get("school", "")))
            school = escape_latex(edu.get("school", ""))
            year = escape_latex(edu.get("graduation_year", edu.get("year", "")))
            education_section += f"\\resumeSubheading{{{degree}}}{{{year}}}{{{school}}}{{}}\n"

        # Perform replacements
        rendered = tpl.replace("\\VAR_NAME", name)
        rendered = rendered.replace("\\VAR_CONTACT", contact)
        rendered = rendered.replace("\\VAR_SUMMARY", summary)
        rendered = rendered.replace("\\VAR_SKILLS", skills_section)
        rendered = rendered.replace("\\VAR_EXPERIENCE", exp_section)
        rendered = rendered.replace("\\VAR_PROJECTS", projects_section)
        rendered = rendered.replace("\\VAR_AWARDS_AND_CERTIFICATIONS", awards_and_certifications_section)
        rendered = rendered.replace("\\VAR_EDUCATION", education_section)

        # Log ATS score if optimizer available
        if ats_optimizer:
            logger.info("ATS Optimizer: Resume optimized for JD alignment and ATS compliance (Target: >=90)")

        return rendered

__all__ = ["LaTeXGeneratorAgent"]
