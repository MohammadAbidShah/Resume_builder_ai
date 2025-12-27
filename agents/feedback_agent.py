"""Feedback & Decision Agent - Agent 5."""
import json
from typing import Dict, Any
from tools.groq_client import groq_generate
from langchain_core.messages import HumanMessage, SystemMessage
from config.settings import CONTENT_MODEL, MIN_ATS_SCORE, PDF_QUALITY_THRESHOLD
from config.prompts import SYSTEM_PROMPTS
from utils.logger import logger
from utils.validators import validate_json_output

class FeedbackAgent:
    """
    Agent 5: Evaluates validation results and decides next action.
    """
    
    def __init__(self):
        self.system_prompt = SYSTEM_PROMPTS["feedback_agent"]
    
    def evaluate(
        self,
        ats_report: Dict[str, Any],
        pdf_report: Dict[str, Any],
        iteration: int = 1
    ) -> Dict[str, Any]:
        """
        Evaluate all validation results and provide feedback.
        
        Args:
            ats_report: ATS analysis report from Agent 3
            pdf_report: PDF quality report from Agent 4
            iteration: Current iteration number
            
        Returns:
            Decision and feedback for next iteration
        """
        logger.info(f"Feedback Agent: Evaluating iteration {iteration}...")
        
        # Check standards
        standards_met = self._check_standards(ats_report, pdf_report)
        
        logger.info(f"Standards Check: {sum(standards_met.values())}/{len(standards_met)} met")
        
        # Determine status
        all_passed = all(standards_met.values())
        
        if all_passed:
            result = {
                "overall_status": "PASS",
                "standards_met": standards_met,
                "message": "✓ All quality standards met! Resume is ready.",
                "success": True
            }
            logger.info("Feedback Agent: PASS - All standards met")
            return result
        
        # Get detailed feedback
        user_prompt = self._build_feedback_prompt(
            ats_report,
            pdf_report,
            standards_met,
            iteration
        )
        
        try:
            prompt = self.system_prompt + "\n\n" + user_prompt
            response_text = groq_generate(prompt, max_tokens=2048, temperature=0)
            logger.info("Feedback Agent: Received feedback from Groq API")
            
            # Parse feedback
            is_valid, feedback_data = validate_json_output(response_text)
            
            if is_valid:
                # Ensure the locally computed standards take precedence
                result = {
                    **feedback_data,
                    "standards_met": standards_met,
                    "overall_status": "FAIL",
                    "success": True
                }
            else:
                # Fallback if JSON parsing fails
                logger.warning("Failed to parse feedback, using basic feedback")
                result = self._generate_basic_feedback(standards_met, ats_report, pdf_report)
                result["success"] = True
            
            logger.info(f"Feedback Agent: FAIL - Providing feedback for iteration {iteration + 1}")
            return result
            
        except Exception as e:
            logger.error(f"Feedback Agent error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "overall_status": "FAIL",
                "standards_met": standards_met
            }
    
    def _check_standards(
        self,
        ats_report: Dict[str, Any],
        pdf_report: Dict[str, Any]
    ) -> Dict[str, bool]:
        """Check if all quality standards are met."""
        standards = {}
        
        # ATS Score Standard
        ats_score = ats_report.get("ats_score", 0)
        standards["ATS_Score_90%+"] = ats_score >= (MIN_ATS_SCORE * 100)
        
        # Keywords Standard
        keywords_missing = ats_report.get("keywords_missing", [])
        standards["Keywords_Complete"] = len(keywords_missing) < 5  # Allow small gaps
        
        # LaTeX Validity Standard
        latex_valid = pdf_report.get("latex_valid", False)
        standards["LaTeX_Valid"] = latex_valid
        
        # PDF Quality Standard
        quality_score = pdf_report.get("quality_score", 0)
        standards["PDF_Quality_85+"] = quality_score >= PDF_QUALITY_THRESHOLD
        
        # ATS Blocking Issues
        ats_issues = len(ats_report.get("ats_blocking_issues", []))
        standards["No_ATS_Blocking_Issues"] = ats_issues == 0
        
        return standards
    
    def _build_feedback_prompt(
        self,
        ats_report: Dict[str, Any],
        pdf_report: Dict[str, Any],
        standards_met: Dict[str, bool],
        iteration: int
    ) -> str:
        """Build prompt for feedback generation."""
        
        failed_standards = [k for k, v in standards_met.items() if not v]
        
        prompt = f"""
Iteration {iteration}: Evaluate these validation results and provide actionable feedback.

STANDARDS NOT MET:
{', '.join(failed_standards)}

ATS REPORT:
- Score: {ats_report.get('ats_score', 0):.1f}% (Need: 90%)
- Keywords Present: {len(ats_report.get('keywords_present', []))}
- Keywords Missing: {ats_report.get('keywords_missing', [])[:5]}
- Blocking Issues: {ats_report.get('ats_blocking_issues', [])}

PDF REPORT:
- Quality Score: {pdf_report.get('quality_score', 0):.0f}/100 (Need: 85+)
- LaTeX Valid: {pdf_report.get('latex_valid', False)}
- Formatting Issues: {pdf_report.get('formatting_issues', [])[:3]}
- ATS Warnings: {pdf_report.get('ats_warnings', [])[:3]}

Provide actionable feedback as JSON:
{{
    "priority_fixes": [...],
    "content_feedback": "Specific improvements for resume content",
    "latex_feedback": "Specific improvements for LaTeX formatting",
    "confidence_next_iteration": <0-100>,
    "summary": "Brief explanation"
}}

Focus on the most impactful fixes first. Be specific and actionable.
"""
        return prompt
    
    def _generate_basic_feedback(
        self,
        standards_met: Dict[str, bool],
        ats_report: Dict[str, Any],
        pdf_report: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate basic feedback if LLM parsing fails."""
        priority_fixes = []
        
        # Check each failed standard and add to priority fixes
        if not standards_met.get("ATS_Score_90%+"):
            priority_fixes.append("Increase ATS score by adding more matching keywords")
        
        if not standards_met.get("Keywords_Complete"):
            missing = ats_report.get("keywords_missing", [])[:3]
            priority_fixes.append(f"Add missing keywords: {', '.join(missing)}")
        
        if not standards_met.get("PDF_Quality_85+"):
            priority_fixes.append("Improve formatting and visual quality")
        
        if not standards_met.get("No_ATS_Blocking_Issues"):
            issues = ats_report.get("ats_blocking_issues", [])[:2]
            priority_fixes.append(f"Fix ATS issues: {', '.join(issues)}")
        
        if not standards_met.get("LaTeX_Valid"):
            priority_fixes.append("Fix LaTeX syntax errors")
        
        return {
            "standards_met": standards_met,
            "priority_fixes": priority_fixes or ["Continue with general improvements"],
            "content_feedback": "Incorporate missing keywords and improve relevant experience descriptions",
            "latex_feedback": "Ensure proper formatting and fix any syntax errors",
            "confidence_next_iteration": 75,
            "summary": "Multiple improvements needed - focus on listed priority fixes"
        }

__all__ = ["FeedbackAgent"]
