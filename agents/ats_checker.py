"""ATS Checker Agent - Agent 3."""
import json
from typing import Dict, Any
from tools.groq_client import groq_generate
from config.settings import VALIDATION_MODEL, MIN_ATS_SCORE
from config.prompts import SYSTEM_PROMPTS
from tools import check_ats_compatibility, extract_plain_text_from_latex
from utils.logger import logger
from utils.validators import validate_json_output

class ATSCheckerAgent:
    """
    Agent 3: Validates ATS score and keyword presence in resume.
    """
    
    def __init__(self):
        self.system_prompt = SYSTEM_PROMPTS["ats_checker"]
    
    def check(
        self,
        resume_content: Dict[str, Any],
        job_description: str,
        latex_code: str = None
    ) -> Dict[str, Any]:
        """
        Check ATS compatibility and score.
        
        Args:
            resume_content: The resume content dictionary
            job_description: Original job description
            latex_code: Optional LaTeX code for plain text extraction
            
        Returns:
            ATS analysis report
        """
        logger.info("ATS Checker Agent: Starting...")
        
        # Handle failed content generation
        if resume_content is None and latex_code is None:
            logger.warning("ATS Checker: No content available (content generation failed)")
            return {
                "success": False,
                "error": "No resume content available for ATS check",
                "ats_score": 0.0,
                "keywords_matched": []
            }
        
        # Extract plain text from content or LaTeX
        if latex_code:
            resume_text = extract_plain_text_from_latex(latex_code)
        else:
            resume_text = self._extract_text_from_content(resume_content)
        
        # Use tool for basic ATS check
        tool_results = check_ats_compatibility(resume_text, job_description)
        logger.info(f"ATS Checker Tool: Score = {tool_results['ats_score']:.1f}%")
        
        # Use LLM for detailed analysis and reasoning
        user_prompt = self._build_analysis_prompt(
            job_description,
            resume_text,
            tool_results
        )
        
        try:
            prompt = self.system_prompt + "\n\n" + user_prompt
            response_text = groq_generate(prompt, max_tokens=2048, temperature=0)
            logger.info("ATS Checker: Received analysis from Groq API")
            
            # Parse LLM response
            is_valid, llm_analysis = validate_json_output(response_text)
            
            if is_valid:
                # Merge tool results with LLM analysis
                result = {**tool_results, **llm_analysis}
            else:
                # Fall back to tool results if LLM output is invalid
                logger.warning("Failed to parse LLM output, using tool results only")
                result = tool_results
            
            result["success"] = True
            logger.info(f"ATS Checker: Final score = {result['ats_score']:.1f}%")
            
            return result
            
        except Exception as e:
            logger.error(f"ATS Checker Agent error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "tool_results": tool_results
            }
    
    def _extract_text_from_content(self, resume_content: Dict[str, Any]) -> str:
        """Extract plain text from resume content."""
        # Handle None or invalid content
        if not resume_content or not isinstance(resume_content, dict):
            logger.warning("ATS Checker: Invalid resume content format")
            return ""
        
        text_parts = []
        
        # Extract summary
        if "professional_summary" in resume_content:
            text_parts.append(resume_content["professional_summary"])
        
        # Extract experience descriptions
        if "experience" in resume_content:
            for exp in resume_content["experience"]:
                if isinstance(exp, dict):
                    text_parts.append(json.dumps(exp))
                else:
                    text_parts.append(str(exp))
        
        # Extract skills
        if "skills" in resume_content:
            skills = resume_content["skills"]
            if isinstance(skills, dict):
                for category, skill_list in skills.items():
                    if isinstance(skill_list, list):
                        text_parts.append(" ".join(skill_list))
        
        # Extract education
        if "education" in resume_content:
            for edu in resume_content["education"]:
                if isinstance(edu, dict):
                    text_parts.append(json.dumps(edu))
                else:
                    text_parts.append(str(edu))
        
        return "\n".join(text_parts)
    
    def _build_analysis_prompt(
        self,
        job_description: str,
        resume_text: str,
        tool_results: Dict[str, Any]
    ) -> str:
        """Build prompt for detailed ATS analysis."""
        prompt = f"""
Analyze this resume for ATS compatibility:

JOB DESCRIPTION (Key Requirements):
{job_description[:1000]}...

RESUME CONTENT:
{resume_text[:1500]}...

PRELIMINARY ANALYSIS:
- ATS Score: {tool_results['ats_score']:.1f}%
- Keywords Present: {len(tool_results['keywords_present'])}
- Keywords Missing: {len(tool_results['keywords_missing'])}
- Blocking Issues: {', '.join(tool_results['ats_blocking_issues'][:3]) if tool_results['ats_blocking_issues'] else 'None'}

Please provide detailed analysis as JSON:
{{
    "ats_score": <0-100>,
    "keywords_present": [...],
    "keywords_missing": [...],
    "formatting_issues": [...],
    "improvement_suggestions": [...],
    "analysis_summary": "..."
}}
"""
        return prompt

__all__ = ["ATSCheckerAgent"]
