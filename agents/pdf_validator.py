"""PDF Quality Validator Agent - Agent 4."""
import json
from typing import Dict, Any
from tools.groq_client import groq_generate
from langchain_core.messages import HumanMessage, SystemMessage
from config.settings import VALIDATION_MODEL, PDF_QUALITY_THRESHOLD, GROQ_PDF_VALIDATOR_MODEL
from config.prompts import SYSTEM_PROMPTS
from tools import validate_latex_syntax, validate_pdf_quality
from utils.logger import logger
from utils.validators import validate_json_output

class PDFValidatorAgent:
    """
    Agent 4: Validates PDF quality and rendering issues.
    """
    
    def __init__(self):
        self.system_prompt = SYSTEM_PROMPTS["pdf_validator"]
    
    def validate(
        self,
        latex_code: str,
        resume_content: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Validate PDF quality and LaTeX formatting.
        
        Args:
            latex_code: LaTeX code to validate
            resume_content: Optional resume content for context
            
        Returns:
            Validation report with quality assessment
        """
        logger.info("PDF Validator Agent: Starting...")
        
        # Handle failed LaTeX generation
        if not latex_code:
            logger.warning("PDF Validator: No LaTeX code available (generation failed)")
            return {
                "success": False,
                "error": "No LaTeX code available for PDF validation",
                "quality_score": 0,
                "is_valid": False
            }
        
        # First, run tool-based validation
        tool_results = validate_pdf_quality(latex_code)
        logger.info(f"PDF Validator Tool: Quality Score = {tool_results['quality_score']:.0f}/100")
        
        # Also check LaTeX syntax directly
        syntax_valid, latex_errors = validate_latex_syntax(latex_code)
        logger.info(f"LaTeX Syntax: {'VALID' if syntax_valid else 'INVALID'} ({len(latex_errors)} errors)")
        
        # Build LLM analysis prompt
        user_prompt = self._build_analysis_prompt(
            latex_code,
            tool_results,
            latex_errors,
            resume_content
        )
        
        try:
            prompt = self.system_prompt + "\n\n" + user_prompt
            response_text = groq_generate(prompt, max_tokens=2048, temperature=0, model=GROQ_PDF_VALIDATOR_MODEL)
            logger.info("PDF Validator: Received analysis from Groq API")
            
            # Parse LLM response
            is_valid, llm_analysis = validate_json_output(response_text)
            
            if is_valid:
                # Merge results
                result = {**tool_results, **llm_analysis}
            else:
                logger.warning("Failed to parse validator LLM output, using tool results")
                result = tool_results
            
            # Add metadata
            result["success"] = True
            result["latex_error_count"] = len(latex_errors)
            result["syntax_errors"] = latex_errors
            
            logger.info(f"PDF Validator: Final Assessment = {result['recommendation']}")
            return result
            
        except Exception as e:
            logger.error(f"PDF Validator Agent error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "tool_results": tool_results,
                "syntax_errors": latex_errors
            }
    
    def _build_analysis_prompt(
        self,
        latex_code: str,
        tool_results: Dict[str, Any],
        syntax_errors: list,
        resume_content: Dict[str, Any] = None
    ) -> str:
        """Build prompt for detailed PDF quality analysis."""
        
        # Sample the LaTeX code (first 1000 chars)
        latex_sample = latex_code[:1000] + "\n... (truncated)" if len(latex_code) > 1000 else latex_code
        
        content_context = ""
        if resume_content:
            content_context = f"\nRESUME CONTENT:\n{json.dumps(resume_content, indent=2)[:500]}..."
        
        prompt = f"""
Analyze this LaTeX resume code for quality and rendering:

LATEX CODE SAMPLE:
{latex_sample}

TECHNICAL ANALYSIS:
- Syntax Valid: {len(syntax_errors) == 0}
- Syntax Errors: {syntax_errors if syntax_errors else 'None'}
- Quality Score: {tool_results['quality_score']:.0f}/100
- Visual Score: {tool_results['visual_score']:.0f}/100
- ATS Warnings: {tool_results['ats_warnings'] if tool_results['ats_warnings'] else 'None'}

STRUCTURE:
- Sections: {tool_results['structure_analysis'].get('sections', 0)}
- Subsections: {tool_results['structure_analysis'].get('subsections', 0)}
- Bullet Points: {tool_results['structure_analysis'].get('bullet_points', 0)}
{content_context}

Provide detailed quality analysis as JSON:
{{
    "quality_score": <0-100>,
    "latex_valid": <true/false>,
    "formatting_issues": [...],
    "ats_warnings": [...],
    "visual_suggestions": [...],
    "structure_analysis": {{...}},
    "recommendation": "PASS" or "NEEDS_IMPROVEMENT",
    "summary": "..."
}}
"""
        return prompt

__all__ = ["PDFValidatorAgent"]
