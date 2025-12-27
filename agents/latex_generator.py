"""LaTeX Generator Agent - Agent 2."""
import json
from typing import Dict, Any
from tools.groq_client import groq_generate
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

__all__ = ["LaTeXGeneratorAgent"]
