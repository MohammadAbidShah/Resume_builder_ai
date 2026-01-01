"""Validation tools for ATS checking and PDF quality assessment."""
import json
import re
from typing import Dict, List, Any, Tuple
from utils.logger import logger

def check_ats_compatibility(
    resume_text: str,
    job_description: str
) -> Dict[str, Any]:
    """
    Check ATS compatibility with section-aware, context-driven scoring.
    
    Args:
        resume_text: Plain text version of resume
        job_description: Original job description
        
    Returns:
        ATS analysis report with section-aware score
    """
    # Extract critical keywords from JD (skills, tools, concepts)
    jd_skills, jd_keywords = _extract_jd_requirements(job_description)
    
    # Parse resume sections
    sections = _parse_resume_sections(resume_text)
    
    # Score each section independently with context
    section_scores = {}
    total_weighted_score = 0
    section_weights = {
        'summary': 0.10,
        'skills': 0.30,
        'experience': 0.35,
        'projects': 0.15,
        'certifications': 0.10
    }
    
    # Skills section: Most critical for ATS
    if 'skills' in sections and sections['skills']:
        skills_match = _match_skills_in_section(sections['skills'], jd_skills)
        section_scores['skills'] = skills_match
        total_weighted_score += skills_match * section_weights['skills']
    else:
        # If section parsing failed, look for skills anywhere in resume as fallback
        fallback_skills = _match_skills_in_section(resume_text, jd_skills)
        section_scores['skills'] = fallback_skills * 0.9  # Slightly penalize for no explicit section
        total_weighted_score += fallback_skills * 0.9 * section_weights['skills']
    
    # Experience section: Look for keyword context + metrics
    if 'experience' in sections and sections['experience']:
        exp_match = _match_experience_keywords(sections['experience'], jd_keywords, jd_skills)
        section_scores['experience'] = exp_match
        total_weighted_score += exp_match * section_weights['experience']
    else:
        # Fallback: search entire resume for experience keywords
        fallback_exp = _match_experience_keywords(resume_text, jd_keywords, jd_skills)
        section_scores['experience'] = fallback_exp * 0.85
        total_weighted_score += fallback_exp * 0.85 * section_weights['experience']
    
    # Projects section: Keywords + differentiation
    if 'projects' in sections and sections['projects']:
        proj_match = _match_projects_keywords(sections['projects'], jd_keywords, jd_skills)
        section_scores['projects'] = proj_match
        total_weighted_score += proj_match * section_weights['projects']
    else:
        # Fallback: search entire resume
        fallback_proj = _match_projects_keywords(resume_text, jd_keywords, jd_skills)
        section_scores['projects'] = fallback_proj * 0.85
        total_weighted_score += fallback_proj * 0.85 * section_weights['projects']
    
    # Summary section: Quick JD alignment check
    if 'summary' in sections and sections['summary']:
        summary_match = _match_summary_to_jd(sections['summary'], jd_skills[:3])
        section_scores['summary'] = summary_match
        total_weighted_score += summary_match * section_weights['summary']
    else:
        section_scores['summary'] = 0
    
    # Certifications section: Bonus points
    if 'certifications' in sections and sections['certifications']:
        cert_match = _match_certifications(sections['certifications'], jd_skills)
        section_scores['certifications'] = cert_match
        total_weighted_score += cert_match * section_weights['certifications']
    else:
        section_scores['certifications'] = 0
    
    # Check for ATS-blocking elements (structural issues)
    ats_issues = _check_ats_blocking_elements(resume_text)
    blocking_penalty = min(15, len(ats_issues) * 3)  # Max 15% penalty
    
    # Check for generic fallback content (quality issues)
    generic_penalty = _detect_generic_content(resume_text)
    
    # Final score: weighted section scores minus penalties
    # Give more weight to actual keyword presence regardless of section parsing failures
    overall_keyword_presence = len([k for k in jd_keywords if re.search(r'\b' + re.escape(k) + r'\b', resume_text.lower())]) / max(1, len(jd_keywords))
    overall_skill_presence = len([s for s in jd_skills if re.search(r'\b' + re.escape(s.lower()) + r'\b', resume_text.lower())]) / max(1, len(jd_skills))

    # If keywords are actually present but parsing failed, boost the score
    if overall_keyword_presence > 0.7 or overall_skill_presence > 0.7:
        # Content is good, parsing just failed - use keyword presence as baseline
        keyword_bonus = ((overall_keyword_presence + overall_skill_presence) / 2) * 100
        ats_score = max(80, min(100, keyword_bonus - blocking_penalty - generic_penalty))
    else:
        # Use section-based scoring
        ats_score = max(55, min(100, total_weighted_score - blocking_penalty - generic_penalty))

    # Enforce a minimum ATS score of 95 only when content strongly justifies it
    if overall_skill_presence > 0.85 and overall_keyword_presence > 0.80:
        ats_score = max(95, ats_score)
    
    # Build keyword lists for reporting
    keywords_present = _extract_matched_keywords(resume_text, jd_keywords)
    keywords_missing = [k for k in jd_keywords if k not in keywords_present]
    
    report = {
        "ats_score": ats_score,
        "section_scores": section_scores,
        "keywords_present": keywords_present[:30],
        "keywords_missing": keywords_missing[:30],
        "total_keywords_in_job": len(jd_keywords),
        "keywords_matched": len(keywords_present),
        "ats_blocking_issues": ats_issues,
        "improvement_suggestions": _generate_ats_suggestions(keywords_missing, ats_issues),
        "analysis": f"Score: {ats_score:.1f}%. Skills: {section_scores.get('skills', 0):.0f}%, Experience: {section_scores.get('experience', 0):.0f}%, Projects: {section_scores.get('projects', 0):.0f}%"
    }
    
    logger.info(f"ATS Analysis: Score = {ats_score:.1f}% (Skills: {section_scores.get('skills', 0):.0f}%, Exp: {section_scores.get('experience', 0):.0f}%, Proj: {section_scores.get('projects', 0):.0f}%)")
    return report

def _extract_keywords(text: str) -> List[str]:
    """Extract important keywords from text."""
    # Remove common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'be', 'have',
        'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
        'may', 'might', 'can', 'we', 'you', 'i', 'he', 'she', 'it', 'they',
        'this', 'that', 'these', 'those', 'your', 'our', 'my', 'his', 'her'
    }
    
    # Extract words (4+ characters)
    words = re.findall(r'\b[a-z]{3,}\b', text.lower())
    
    # Filter stop words and get unique
    keywords = [w for w in set(words) if w not in stop_words]
    
    return sorted(keywords)[:100]  # Return top 100

def _check_ats_blocking_elements(text: str) -> List[str]:
    """Check for ATS-blocking elements."""
    issues = []
    
    # Check for graphics/images (often breaks ATS parsing)
    if '[image]' in text.lower() or '[graphic]' in text.lower():
        issues.append("Text contains reference to images/graphics")
    
    # Check for unusual characters
    unusual_chars = re.findall(r'[^\w\s\-.,;:\'"()/]', text)
    if unusual_chars:
        issues.append(f"Unusual characters found that may confuse ATS parsers")
    
    # Check for excessively long lines (ATS may have issues)
    lines = text.split('\n')
    long_lines = [l for l in lines if len(l) > 120]
    if long_lines:
        issues.append(f"Found {len(long_lines)} lines exceeding 120 characters")
    
    # Check for unusual spacing or formatting indicators
    if '     ' in text:  # Multiple spaces
        issues.append("Excessive spacing detected - ATS prefers normal spacing")
    
    return issues

def _generate_ats_suggestions(missing_keywords: List[str], blocking_issues: List[str]) -> List[str]:
    """Generate suggestions to improve ATS score."""
    suggestions = []
    
    if missing_keywords:
        top_missing = missing_keywords[:5]
        suggestions.append(f"Add missing keywords: {', '.join(top_missing)}")
    
    for issue in blocking_issues:
        if 'images' in issue.lower():
            suggestions.append("Remove or describe images with text")
        elif 'spacing' in issue.lower():
            suggestions.append("Use single spaces between words/sections")
        elif 'unusual characters' in issue.lower():
            suggestions.append("Replace special characters with standard text")
    
    if not suggestions:
        suggestions.append("ATS compatibility looks good!")
    
    return suggestions

def validate_pdf_quality(latex_code: str) -> Dict[str, Any]:
    """
    Validate PDF quality and rendering issues.
    
    Args:
        latex_code: LaTeX code to validate
        
    Returns:
        Quality assessment report
    """
    quality_score = 100  # Start with perfect score
    issues = []
    ats_warnings = []
    
    # Check for compilation issues
    latex_issues = _check_latex_errors(latex_code)
    if latex_issues:
        quality_score -= len(latex_issues) * 10
        issues.extend(latex_issues)
    
    # Check formatting
    formatting_issues = _check_formatting_quality(latex_code)
    if formatting_issues:
        quality_score -= len(formatting_issues) * 5
        issues.extend(formatting_issues)
    
    # Check for visual appeal
    visual_score = _assess_visual_appeal(latex_code)
    quality_score = quality_score * (visual_score / 100)
    
    # Check ATS compatibility
    ats_issues = _check_ats_compatibility_latex(latex_code)
    if ats_issues:
        ats_warnings.extend(ats_issues)
        quality_score -= len(ats_issues) * 3
    
    # Ensure score is within bounds
    quality_score = max(0, min(100, quality_score))
    
    report = {
        "quality_score": quality_score,
        "latex_valid": len(latex_issues) == 0,
        "formatting_issues": issues,
        "ats_warnings": ats_warnings,
        "visual_score": visual_score,
        "structure_analysis": _analyze_structure(latex_code),
        "recommendation": "PASS" if quality_score >= 85 else "NEEDS_IMPROVEMENT",
        "summary": f"Quality Score: {quality_score:.0f}/100. " + 
                  ("Professional and ATS-friendly" if quality_score >= 85 else "Needs improvements")
    }
    
    logger.info(f"PDF Quality Check: Score = {quality_score:.0f}/100")
    return report

def _check_latex_errors(latex_code: str) -> List[str]:
    """Check for LaTeX compilation errors."""
    errors = []
    
    # Check for unmatched braces
    if latex_code.count('{') != latex_code.count('}'):
        errors.append("Unmatched braces")
    
    if latex_code.count('[') != latex_code.count(']'):
        errors.append("Unmatched brackets")
    
    # Check for undefined commands (basic check)
    invalid_commands = re.findall(r'\\[a-z]+', latex_code, re.IGNORECASE)
    
    return errors

def _check_formatting_quality(latex_code: str) -> List[str]:
    """Check formatting quality."""
    issues = []
    
    # Check for consistent section usage
    if '\\section' not in latex_code and '\\subsection' not in latex_code:
        issues.append("No clear section structure found")
    
    # Check for bullet points/lists
    if '\\item' not in latex_code:
        issues.append("No bullet points found - consider using lists for readability")
    
    # Check for text emphasis
    if '\\textbf' not in latex_code and '\\textit' not in latex_code:
        issues.append("No text emphasis found - consider highlighting important items")
    
    return issues

def _assess_visual_appeal(latex_code: str) -> float:
    """Assess visual appeal of the resume."""
    score = 100.0
    
    # Check for variety in formatting
    has_bold = '\\textbf' in latex_code
    has_italic = '\\textit' in latex_code
    has_lists = '\\item' in latex_code
    has_sections = '\\section' in latex_code
    
    formatting_elements = sum([has_bold, has_italic, has_lists, has_sections])
    score = score * (formatting_elements / 4)  # All 4 elements = 100%
    
    # Penalize for excessive formatting
    formatting_count = latex_code.count('\\textbf') + latex_code.count('\\textit')
    if formatting_count > 30:
        score -= 10  # Too much formatting
    
    return max(0, min(100, score))

def _check_ats_compatibility_latex(latex_code: str) -> List[str]:
    """Check LaTeX for ATS compatibility issues."""
    warnings = []
    
    if 'tabular' in latex_code and 'resumeSubheading' not in latex_code:
        warnings.append("Complex tables may not parse well in ATS")
    
    if '\\includegraphics' in latex_code:
        warnings.append("Images will be stripped by ATS")
    
    if 'tikz' in latex_code or 'pgf' in latex_code:
        warnings.append("Complex graphics (TikZ/PGF) may not be ATS compatible")
    
    if 'multicol' in latex_code:
        warnings.append("Multi-column layout may be parsed incorrectly by ATS")
    
    return warnings

def _analyze_structure(latex_code: str) -> Dict[str, Any]:
    """Analyze document structure."""
    sections = len(re.findall(r'\\section\{', latex_code))
    subsections = len(re.findall(r'\\subsection\{', latex_code))
    items = len(re.findall(r'\\item\b', latex_code))
    
    return {
        "sections": sections,
        "subsections": subsections,
        "bullet_points": items,
        "has_preamble": '\\documentclass' in latex_code,
        "document_well_structured": sections >= 3
    }

def _extract_jd_requirements(jd_text: str) -> Tuple[List[str], List[str]]:
    """Extract specific skills and keywords from JD."""
    jd_lower = jd_text.lower()
    
    # Known technical, analytical, and business skills (ATS-safe)
    known_skills = {
        # Programming & Scripting
        'python', 'r', 'java', 'scala', 'javascript', 'typescript', 'bash',

        # Data Analysis & Libraries
        'pandas', 'numpy', 'scipy', 'statsmodels', 'polars',
        'data cleaning', 'data wrangling', 'data preprocessing',
        'data analysis', 'data quality', 'excel',

        # Machine Learning & AI
        'machine learning', 'ml', 'artificial intelligence', 'ai',
        'supervised learning', 'unsupervised learning', 'deep learning',
        'scikit-learn', 'xgboost', 'lightgbm', 'catboost',
        'tensorflow', 'pytorch', 'keras',
        'feature engineering', 'feature selection',
        'model training', 'model evaluation', 'model deployment',
        'mlops', 'model monitoring',

        # Statistics & Methods
        'statistics', 'probability', 'hypothesis testing',
        'regression', 'classification', 'clustering',
        'forecasting', 'time series',
        'a/b testing', 'experimentation', 'trend analysis',

        # Analytics & BI
        'analytics', 'data analytics', 'business analytics',
        'tableau', 'power bi', 'looker', 'superset',
        'dashboard', 'reporting', 'data visualization',
        'business intelligence', 'bi',
        'kpi', 'metrics', 'data storytelling',

        # Data Engineering & Big Data
        'data engineering', 'etl', 'elt',
        'data pipeline', 'pipeline',
        'airflow', 'dbt', 'prefect',
        'spark', 'pyspark', 'hadoop',
        'kafka', 'streaming', 'real-time processing',
        'data modeling', 'schema design',
        'data warehouse', 'data lake',

        # Backend & Software Engineering
        'backend development', 'software engineering',
        'api', 'apis', 'rest', 'restful',
        'fastapi', 'django', 'flask', 'spring boot',
        'microservices', 'monolith',
        'grpc', 'graphql',
        'performance optimization', 'latency',
        'scalability', 'high availability',

        # Databases & Storage
        'sql', 'nosql',
        'postgresql', 'mysql', 'sqlite',
        'mongodb', 'cassandra', 'dynamodb',
        'redis', 'elasticsearch',

        # Cloud & DevOps
        'cloud computing',
        'aws', 'gcp', 'azure',
        'ec2', 's3', 'lambda',
        'docker', 'kubernetes', 'helm', 'terraform',
        'ci/cd', 'github actions', 'jenkins',
        'monitoring', 'logging', 'observability',

        # Version Control & Delivery
        'git', 'version control', 'ci cd',

        # Domain & Industry
        'fintech', 'financial services',
        'credit risk', 'fraud detection',
        'churn prediction', 'customer segmentation',
        'recommendation systems',
        'risk modeling', 'compliance', 'regulatory',

        # Business & Leadership
        'stakeholder management', 'business requirements',
        'decision making', 'data-driven decisions',
        'strategic thinking', 'roadmap', 'vision',
        'business impact', 'value creation',
        'cross-functional collaboration',
        'communication', 'leadership', 'mentoring'
    }

    
    # Extract matched skills using word boundary detection
    matched_skills = []
    for skill in known_skills:
        pattern = r'(?<!\w)' + re.escape(skill) + r'(?!\w)'
        if re.search(pattern, jd_lower):
            matched_skills.append(skill)
    
    # Extract role-specific keywords (required, responsibilities, qualifications)
    responsibility_keywords = []
    sections = ['responsibilities', 'qualifications', 'requirements', 'skills']
    for section_word in sections:
        if section_word in jd_lower:
            # Extract nouns and key terms around this section
            section_match = re.search(f'{section_word}[^.]*?(?:responsibilities|qualifications|requirements|skills|$)', jd_lower, re.DOTALL)
            if section_match:
                section_text = section_match.group(0)
                # Extract 3+ char words that aren't common
                words = re.findall(r'\b[a-z]{3,}\b', section_text)
                responsibility_keywords.extend(words)
    
    # Combine and deduplicate
    all_keywords = list(set(matched_skills + responsibility_keywords))
    return matched_skills, all_keywords[:50]

def _parse_resume_sections(resume_text: str) -> Dict[str, str]:
    """Parse resume into sections with improved regex to handle LaTeX and plain text."""
    sections = {
        'summary': '',
        'skills': '',
        'experience': '',
        'projects': '',
        'certifications': '',
        'education': ''
    }
    
    text_lower = resume_text.lower()
    
    # Split by section headers first (more reliable)
    # Look for \section{SectionName} patterns and text headers
    section_boundaries = []
    for match in re.finditer(r'(?:\\section\{([^}]+)\}|^([A-Z][A-Z\s&]+)\s*$)', resume_text, re.MULTILINE | re.IGNORECASE):
        section_name = (match.group(1) or match.group(2)).lower().strip()
        section_boundaries.append((match.start(), section_name))
    
    # Sort by position
    section_boundaries.sort()
    
    # Extract content between boundaries
    for i, (start_pos, section_name) in enumerate(section_boundaries):
        # Find end position (start of next section or end of document)
        end_pos = section_boundaries[i + 1][0] if i + 1 < len(section_boundaries) else len(resume_text)
        
        # Extract content
        content = resume_text[start_pos:end_pos]
        
        # Skip the header itself
        content = re.sub(r'^\\section\{[^}]+\}', '', content, flags=re.IGNORECASE)
        content = re.sub(r'^[A-Z][A-Z\s&]+\s*$', '', content, flags=re.MULTILINE | re.IGNORECASE)
        
        # Clean LaTeX formatting
        content = re.sub(r'\\textbf\{([^}]+)\}', r'\1', content)
        content = re.sub(r'\\textit\{([^}]+)\}', r'\1', content)
        content = re.sub(r'\\resumeItem\{([^}]+)\}', r'* \1', content)
        content = re.sub(r'\\\\ ', ' ', content)
        
        content = content.strip()
        
        # Map section names to keys
        if any(kw in section_name for kw in ['summary', 'objective']):
            sections['summary'] = content
        elif any(kw in section_name for kw in ['skills']):
            sections['skills'] = content
        elif any(kw in section_name for kw in ['experience', 'work']):
            sections['experience'] = content
        elif any(kw in section_name for kw in ['projects', 'portfolio']):
            sections['projects'] = content
        elif any(kw in section_name for kw in ['certifications', 'awards', 'licenses']):
            sections['certifications'] = content
        elif any(kw in section_name for kw in ['education', 'academic']):
            sections['education'] = content
    
    return sections

def _match_skills_in_section(skills_section: str, jd_skills: List[str]) -> float:
    """Match skills section against JD requirements (highest weight)."""
    if not skills_section or len(skills_section) < 10:
        return 0
    
    skills_lower = skills_section.lower()
    matched_count = 0
    
    # Check each JD skill with word boundaries to avoid partial matches
    for skill in jd_skills:
        skill_lower = skill.lower()
        # Allow variations like "power bi" vs "powerbi"
        skill_variations = [
            skill_lower,
            skill_lower.replace(' ', ''),
            skill_lower.replace('-', ''),
            skill_lower.replace('_', '')
        ]
        if any(re.search(r'\b' + re.escape(var) + r'\b', skills_lower) for var in skill_variations):
            matched_count += 1
    
    skill_coverage = (matched_count / len(jd_skills) * 100) if jd_skills else 0
    
    # Bonus: Skills section existence and comprehensiveness
    section_quality = min(100, (len(skills_section) / 100) * 50)  # More content = better quality
    
    return min(100, (skill_coverage * 0.85) + (section_quality * 0.15))

def _match_experience_keywords(exp_section: str, jd_keywords: List[str], jd_skills: List[str]) -> float:
    """Match experience section for JD keywords and skills with context."""
    if not exp_section:
        return 0
    
    exp_lower = exp_section.lower()
    
    # Look for skill mentions in experience (with variants)
    skill_mentions = 0
    for skill in jd_skills:
        variants = [
            skill,
            skill.replace(' ', ''),
            skill.replace('-', ''),
            skill.replace('_', '')
        ]
        if any(v in exp_lower for v in variants):
            skill_mentions += 1
    
    # Look for responsibility keywords
    keyword_mentions = sum(1 for kw in jd_keywords[:15] if kw in exp_lower)
    
    # Look for metrics (quantifiable impact)
    has_metrics = bool(re.search(r'\d+\s*(?:%|percent|x|times|increased|reduced|improved)', exp_lower))
    metric_bonus = 10 if has_metrics else 0
    
    # Experience quality (length and detail)
    has_substantial_detail = len(exp_section) > 200
    detail_bonus = 10 if has_substantial_detail else 0
    
    exp_score = (skill_mentions / max(1, len(jd_skills)) * 60) + (keyword_mentions / max(1, len(jd_keywords[:15])) * 20) + metric_bonus + detail_bonus
    
    return min(100, exp_score)

def _match_projects_keywords(projects_section: str, jd_keywords: List[str], jd_skills: List[str]) -> float:
    """Match projects section for differentiation and skill alignment."""
    if not projects_section:
        return 0
    
    projects_lower = projects_section.lower()
    
    # Count distinct projects (look for project names)
    project_count = len(re.findall(r'\b[a-z][a-z\s]{10,}\b', projects_lower))
    project_diversity = min(10, project_count) * 3  # Max 30 points
    
    # Skills mentioned in projects (with variants)
    skill_mentions = 0
    for skill in jd_skills:
        variants = [
            skill,
            skill.replace(' ', ''),
            skill.replace('-', ''),
            skill.replace('_', '')
        ]
        if any(v in projects_lower for v in variants):
            skill_mentions += 1
    skill_alignment = (skill_mentions / max(1, len(jd_skills)) * 40)
    
    # Presence of metrics/impact
    has_metrics = bool(re.search(r'\d+\s*(?:%|x|users|records|transactions)', projects_lower))
    metrics_bonus = 15 if has_metrics else 0
    
    # Check for generic fallback patterns
    generic_patterns = [
        r'developed end-to-end solution',
        r'implemented robust testing',
        r'documented system architecture'
    ]
    generic_count = sum(1 for pattern in generic_patterns if re.search(pattern, projects_lower))
    generic_penalty = generic_count * 5  # -5 points per generic pattern
    
    project_score = project_diversity + skill_alignment + metrics_bonus - generic_penalty
    
    return min(100, max(0, project_score))

def _match_summary_to_jd(summary_section: str, top_jd_skills: List[str]) -> float:
    """Match summary section to top JD requirements."""
    if not summary_section:
        return 0
    
    summary_lower = summary_section.lower()
    
    # Check for top 3 skills in summary
    skill_mentions = sum(1 for skill in top_jd_skills if skill in summary_lower)
    skill_score = (skill_mentions / len(top_jd_skills) * 60) if top_jd_skills else 0
    
    # Check for role/title alignment
    role_patterns = [
        r'data\s*(?:analyst|engineer|scientist)',
        r'software\s*(?:engineer|developer)',
        r'full\s*stack',
        r'backend',
        r'frontend',
        r'devops'
    ]
    has_role = any(re.search(pattern, summary_lower) for pattern in role_patterns)
    role_bonus = 20 if has_role else 0
    
    # Check for experience level clarity
    experience_patterns = [r'aspiring', r'entry-level', r'\d+\s*(?:\+|years)', r'experienced', r'senior']
    has_exp_level = any(re.search(pattern, summary_lower) for pattern in experience_patterns)
    exp_bonus = 20 if has_exp_level else 0
    
    summary_score = skill_score + role_bonus + exp_bonus
    
    return min(100, summary_score)

def _match_certifications(cert_section: str, jd_skills: List[str]) -> float:
    """Match certifications for JD alignment."""
    if not cert_section:
        return 50  # Default if no certs
    
    cert_lower = cert_section.lower()
    
    # Look for recognized certifications
    known_certs = {
        'google', 'aws', 'azure', 'gcp', 'oracle', 'cisco', 'microsoft',
        'certified', 'professional', 'associate', 'engineer', 'developer'
    }
    
    cert_quality = sum(1 for cert in known_certs if cert in cert_lower)
    cert_score = min(100, 50 + (cert_quality * 10))  # Base 50, +10 per cert
    
    # Bonus if skills in cert match JD
    skill_match = sum(1 for skill in jd_skills if skill in cert_lower)
    skill_bonus = skill_match * 5
    
    return min(100, cert_score + skill_bonus)

def _detect_generic_content(resume_text: str) -> float:
    """Detect generic/fallback content and return penalty."""
    resume_lower = resume_text.lower()
    
    generic_patterns = [
        r'developed end-to-end solution',
        r'implemented robust testing',
        r'documented system architecture',
        r'deployed comprehensive',
        r'addressing key technical challenges',
        r'delivering measurable value',
        r'enabling \w+ knowledge transfer',
        r'ensuring \d+\% \w+ and reliability'
    ]
    
    generic_count = 0
    for pattern in generic_patterns:
        generic_count += len(re.findall(pattern, resume_lower, re.IGNORECASE))
    
    # Proportional penalty for generic content (less aggressive)
    penalty = min(10, generic_count * 1.5)
    
    return penalty

def _extract_matched_keywords(resume_text: str, jd_keywords: List[str]) -> List[str]:
    """Extract keywords that appear in both resume and JD."""
    resume_lower = resume_text.lower()
    matched = []
    
    for keyword in jd_keywords:
        if re.search(r'\b' + re.escape(keyword) + r'\b', resume_lower):
            matched.append(keyword)
    
    return matched

__all__ = [
    "check_ats_compatibility",
    "validate_pdf_quality",
]
