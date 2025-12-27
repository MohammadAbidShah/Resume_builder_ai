"""Content processing tools for Resume Builder AI."""
import re
import json
from typing import Dict, List, Any
from utils.logger import logger

def parse_job_description(job_description: str) -> Dict[str, Any]:
    """
    Parse job description to extract key information.
    
    Args:
        job_description: Raw job description text
        
    Returns:
        Structured job requirements
    """
    result = {
        "raw_description": job_description,
        "key_skills": [],
        "responsibilities": [],
        "requirements": [],
        "nice_to_have": [],
        "keywords": []
    }
    
    # Extract sections (simple heuristic-based)
    text_lower = job_description.lower()
    
    # Extract potential keywords (4+ character words)
    all_words = re.findall(r'\b[a-z]{4,}\b', text_lower)
    result["keywords"] = list(set(all_words))[:50]  # Top 50 unique keywords
    
    # Look for common requirement indicators
    lines = job_description.split('\n')
    for line in lines:
        if any(word in line.lower() for word in ['require', 'must', 'essential']):
            if line.strip():
                result["requirements"].append(line.strip())
        elif any(word in line.lower() for word in ['nice to have', 'preferred', 'desired']):
            if line.strip():
                result["nice_to_have"].append(line.strip())
        elif any(word in line.lower() for word in ['responsible', 'you will', 'you\'ll']):
            if line.strip():
                result["responsibilities"].append(line.strip())
    
    logger.info(f"Parsed job description: {len(result['keywords'])} keywords extracted")
    return result

def extract_technical_skills(text: str) -> List[str]:
    """Extract technical skills from text."""
    # Common tech keywords
    tech_keywords = [
        'python', 'java', 'javascript', 'react', 'nodejs', 'sql', 'mongodb',
        'aws', 'docker', 'kubernetes', 'git', 'linux', 'api', 'rest', 'graphql',
        'machine learning', 'tensorflow', 'pytorch', 'nlp', 'database', 'redis',
        'postgresql', 'mysql', 'azure', 'gcp', 'ci/cd', 'jenkins', 'gitlab',
        'agile', 'scrum', 'microservices', 'cloud', 'devops', 'kubernetes',
        'typescript', 'golang', 'rust', 'csharp', 'php', 'ruby', 'scala'
    ]
    
    found_skills = []
    text_lower = text.lower()
    
    for skill in tech_keywords:
        if skill in text_lower:
            found_skills.append(skill)
    
    return list(set(found_skills))

def extract_soft_skills(text: str) -> List[str]:
    """Extract soft skills from text."""
    soft_keywords = [
        'communication', 'leadership', 'teamwork', 'problem solving', 'analytical',
        'critical thinking', 'creativity', 'time management', 'organization',
        'attention to detail', 'customer service', 'collaboration', 'flexibility',
        'adaptability', 'motivation', 'reliability', 'integrity', 'project management',
        'presentation', 'negotiation', 'mentoring'
    ]
    
    found_skills = []
    text_lower = text.lower()
    
    for skill in soft_keywords:
        if skill in text_lower:
            found_skills.append(skill)
    
    return list(set(found_skills))

def match_experience_to_job(
    experience_items: List[Dict[str, Any]],
    job_requirements: List[str]
) -> Dict[str, Any]:
    """
    Match user experience to job requirements.
    
    Args:
        experience_items: List of experience entries
        job_requirements: List of job requirements
        
    Returns:
        Matched experience with relevance scores
    """
    matched = []
    
    for exp in experience_items:
        # Simple matching based on keyword overlap
        exp_text = json.dumps(exp).lower()
        relevance_score = 0
        matched_reqs = []
        
        for req in job_requirements:
            req_lower = req.lower()
            if any(word in exp_text for word in req_lower.split()):
                relevance_score += 1
                matched_reqs.append(req)
        
        if relevance_score > 0:
            matched.append({
                "experience": exp,
                "relevance_score": min(100, (relevance_score / len(job_requirements)) * 100) if job_requirements else 0,
                "matched_requirements": matched_reqs
            })
    
    # Sort by relevance
    matched = sorted(matched, key=lambda x: x["relevance_score"], reverse=True)
    
    logger.info(f"Matched {len(matched)} experience items to job")
    return {"matched_experiences": matched, "total_matched": len(matched)}

def optimize_action_verbs(text: str) -> str:
    """Replace weak verbs with strong action verbs."""
    action_verbs_map = {
        'worked': 'designed, developed, implemented',
        'helped': 'assisted, supported, facilitated',
        'did': 'executed, performed, completed',
        'made': 'created, produced, generated',
        'was responsible for': 'led, directed, managed',
        'used': 'utilized, leveraged, employed',
        'went': 'progressed, advanced, moved',
    }
    
    result = text
    for weak, strong in action_verbs_map.items():
        result = re.sub(
            r'\b' + weak + r'\b',
            strong.split(', ')[0],  # Use first strong verb as replacement
            result,
            flags=re.IGNORECASE
        )
    
    return result

def quantify_achievements(text: str) -> str:
    """
    Enhance descriptions with quantifiable metrics where possible.
    
    This is a simple placeholder - in production, use NLP/LLM for better results.
    """
    # Look for vague metrics and suggest improvements
    vague_patterns = [
        (r'improved (\w+)', lambda m: f'improved {m.group(1)} by X%'),
        (r'increased (\w+)', lambda m: f'increased {m.group(1)} by X%'),
        (r'reduced (\w+)', lambda m: f'reduced {m.group(1)} by X%'),
    ]
    
    result = text
    for pattern, replacement in vague_patterns:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    
    return result

__all__ = [
    "parse_job_description",
    "extract_technical_skills",
    "extract_soft_skills",
    "match_experience_to_job",
    "optimize_action_verbs",
    "quantify_achievements",
]
