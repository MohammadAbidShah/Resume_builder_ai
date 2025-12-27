"""Helper utilities for Resume Builder AI."""
from typing import Dict, Any, List
import json
from datetime import datetime

def save_iteration_state(state: Dict[str, Any], output_dir: str, iteration: int) -> str:
    """Save iteration state to JSON file for auditing."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"iteration_{iteration}_{timestamp}.json"
    filepath = f"{output_dir}/{filename}"
    
    with open(filepath, 'w') as f:
        json.dump(state, f, indent=2, default=str)
    
    return filepath

def format_feedback_message(feedback_data: Dict[str, Any]) -> str:
    """Format feedback data into a readable message."""
    message = "=== Iteration Feedback ===\n\n"
    
    if "standards_met" in feedback_data:
        message += "Standards Status:\n"
        for standard, met in feedback_data["standards_met"].items():
            status = "[PASS]" if met else "[FAIL]"
            message += f"  {status}: {standard}\n"
        message += "\n"
    
    if "priority_fixes" in feedback_data:
        message += "Priority Fixes:\n"
        for i, fix in enumerate(feedback_data["priority_fixes"], 1):
            message += f"  {i}. {fix}\n"
        message += "\n"
    
    if "content_feedback" in feedback_data:
        message += f"Content Improvements Needed:\n{feedback_data['content_feedback']}\n\n"
    
    if "latex_feedback" in feedback_data:
        message += f"LaTeX Formatting Improvements:\n{feedback_data['latex_feedback']}\n\n"
    
    return message

def format_validation_report(validation_results: Dict[str, Any]) -> str:
    """Format validation results into a readable report."""
    report = "=== Validation Report ===\n\n"
    
    if "ats_score" in validation_results:
        ats_score = validation_results["ats_score"]
        report += f"ATS Score: {ats_score:.1f}%\n"
        report += f"Target: 90% or higher\n"
        report += f"Status: {'[PASS]' if ats_score >= 90 else '[NEEDS IMPROVEMENT]'}\n\n"
    
    if "keywords_present" in validation_results:
        report += f"Keywords Present: {len(validation_results['keywords_present'])}\n"
        report += f"Keywords Missing: {len(validation_results['keywords_missing'])}\n"
        if validation_results['keywords_missing']:
            report += f"Missing: {', '.join(validation_results['keywords_missing'][:5])}...\n\n"
    
    if "quality_score" in validation_results:
        quality = validation_results["quality_score"]
        report += f"PDF Quality Score: {quality:.0f}/100\n"
        report += f"Status: {'✓ PASS' if quality >= 85 else '✗ NEEDS IMPROVEMENT'}\n\n"
    
    return report

def extract_section_from_content(content: Dict[str, Any], section: str) -> str:
    """Extract and format a specific section from resume content."""
    if section not in content:
        return ""
    
    section_data = content[section]
    
    if section == "professional_summary":
        return section_data
    
    elif section == "skills":
        if isinstance(section_data, dict):
            result = []
            for category, skills in section_data.items():
                if isinstance(skills, list):
                    result.append(f"{category}: {', '.join(skills)}")
            return "\n".join(result)
        return str(section_data)
    
    elif section in ["experience", "education"]:
        if isinstance(section_data, list):
            result = []
            for item in section_data:
                if isinstance(item, dict):
                    result.append(json.dumps(item, indent=2))
                else:
                    result.append(str(item))
            return "\n---\n".join(result)
        return str(section_data)
    
    return str(section_data)

def merge_feedback_into_prompt(original_content: Dict[str, Any], feedback: str) -> str:
    """Create a prompt that includes feedback for regeneration."""
    content_str = json.dumps(original_content, indent=2)
    
    prompt = f"""Based on the following feedback, please improve the resume:

FEEDBACK:
{feedback}

CURRENT RESUME:
{content_str}

Please regenerate the resume content addressing all the feedback points. 
Maintain all original strong points while improving the areas mentioned in the feedback."""
    
    return prompt

__all__ = [
    "save_iteration_state",
    "format_feedback_message",
    "format_validation_report",
    "extract_section_from_content",
    "merge_feedback_into_prompt",
]
