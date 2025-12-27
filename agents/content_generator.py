"""Resume Content Generator Agent - Agent 1."""
import json
from typing import Dict, Any
from tools.groq_client import groq_generate
from config.settings import CONTENT_MODEL, CONTENT_GENERATION_TEMPERATURE
from config.prompts import SYSTEM_PROMPTS
from tools import parse_job_description, extract_technical_skills, extract_soft_skills
from utils.logger import logger
from utils.validators import validate_json_output

class ResumeContentGeneratorAgent:
    """
    Agent 1: Generates optimized resume content based on job description and personal info.
    """
    
    def __init__(self):
        self.system_prompt = SYSTEM_PROMPTS["content_generator"]
    
    def generate(
        self,
        job_description: str,
        personal_info: Dict[str, Any],
        feedback: str = None
    ) -> Dict[str, Any]:
        """
        Generate resume content optimized for the job description.
        
        Args:
            job_description: Raw job description text
            personal_info: User's personal information (skills, experience, education)
            feedback: Optional feedback from previous iteration
            
        Returns:
            Structured resume content as JSON
        """
        logger.info("Content Generator Agent: Starting...")
        
        # Parse job description for context
        job_context = parse_job_description(job_description)
        logger.info(f"Extracted {len(job_context['keywords'])} keywords from job description")
        
        # Build the prompt
        if feedback:
            user_prompt = self._build_prompt_with_feedback(
                job_description,
                personal_info,
                job_context,
                feedback
            )
            logger.info("Content Generator: Using feedback from previous iteration")
        else:
            user_prompt = self._build_initial_prompt(
                job_description,
                personal_info,
                job_context
            )
            logger.info("Content Generator: Creating initial resume")
        
        # Call Groq API (deterministic: temperature=0)
        try:
            prompt = self.system_prompt + "\n\n" + user_prompt
            response_text = groq_generate(prompt, max_tokens=4096, temperature=0)
            logger.info("Content Generator: Received response from Groq API")
            
            # Parse JSON output
            is_valid, resume_content = validate_json_output(response_text)
            
            if not is_valid:
                logger.error(f"Failed to parse content generator output: {resume_content}")
                # Return a structured error response
                return {
                    "success": False,
                    "error": "Failed to parse LLM output",
                    "raw_output": response_text
                }
            
            # Add metadata
            resume_content["personal_info"] = personal_info
            resume_content["source_job_keywords"] = job_context["keywords"]
            resume_content["success"] = True
            
            logger.info("Content Generator: Successfully generated resume content")
            return resume_content
            
        except Exception as e:
            logger.error(f"Content Generator Agent error: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _build_initial_prompt(
        self,
        job_description: str,
        personal_info: Dict[str, Any],
        job_context: Dict[str, Any]
    ) -> str:
        """Build initial prompt for content generation."""
        prompt = f"""
Please create an optimized resume content for the following:

JOB DESCRIPTION:
{job_description}

KEY SKILLS FROM JOB:
Technical: {', '.join(extract_technical_skills(job_description)[:10])}
Soft Skills: {', '.join(extract_soft_skills(job_description)[:5])}

APPLICANT INFORMATION:
{json.dumps(personal_info, indent=2)}

Please create a resume that:
1. Directly addresses all requirements from the job description
2. Highlights relevant experience and skills
3. Uses keywords from the job posting naturally
4. Includes a strong professional summary
5. Quantifies achievements where possible

Return the response as a JSON object with these exact fields:
{{
    "professional_summary": "...",
    "experience": [...],
    "skills": {{}},
    "education": [...],
    "matched_keywords": [...],
    "missing_keywords": [...],
    "optimization_notes": "..."
}}
"""
        return prompt
    
    def _build_prompt_with_feedback(
        self,
        job_description: str,
        personal_info: Dict[str, Any],
        job_context: Dict[str, Any],
        feedback: str
    ) -> str:
        """Build prompt that incorporates feedback for refinement."""
        prompt = f"""
Please improve the resume content based on this feedback:

FEEDBACK TO ADDRESS:
{feedback}

JOB DESCRIPTION:
{job_description}

APPLICANT INFORMATION:
{json.dumps(personal_info, indent=2)}

Please regenerate the resume to address all feedback while:
1. Maintaining all strong original elements
2. Incorporating missing keywords naturally
3. Following all other requirements from the job

Return the response as a JSON object with these exact fields:
{{
    "professional_summary": "...",
    "experience": [...],
    "skills": {{}},
    "education": [...],
    "matched_keywords": [...],
    "missing_keywords": [...],
    "optimization_notes": "..."
}}
"""
        return prompt

__all__ = ["ResumeContentGeneratorAgent"]
