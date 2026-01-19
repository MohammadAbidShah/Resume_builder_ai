"""Resume Content Generator Agent - Agent 1 (Enhanced for FAANG-level resumes)."""
import json
import re
from typing import Dict, Any, List, Tuple
from tools.groq_client import groq_generate
from config.settings import CONTENT_MODEL, CONTENT_GENERATION_TEMPERATURE, GROQ_CONTENT_GENERATOR_MODEL
from config.prompts import SYSTEM_PROMPTS
from tools import parse_job_description, extract_technical_skills, extract_soft_skills
from utils.logger import logger
from utils.validators import validate_json_output


class ResumeContentGeneratorAgent:
    """
    Agent 1: Generates FAANG-optimized resume content based on job description and personal info.
    Enhanced with:
    - Strong action verb validation
    - Quantification rate tracking
    - Keyword density optimization
    - STAR method integration
    - Post-generation quality checks
    """
    
    # FAANG-approved action verbs by category
    STRONG_VERBS = {
        "achievement": ["Spearheaded", "Pioneered", "Architected", "Engineered", "Championed"],
        "improvement": ["Optimized", "Enhanced", "Accelerated", "Streamlined", "Refined", "Revolutionized"],
        "leadership": ["Led", "Directed", "Managed", "Coordinated", "Mentored", "Orchestrated"],
        "creation": ["Designed", "Developed", "Built", "Implemented", "Established", "Created"],
        "analysis": ["Analyzed", "Evaluated", "Investigated", "Diagnosed", "Assessed", "Researched"],
        "scale": ["Scaled", "Expanded", "Grew", "Increased", "Multiplied", "Amplified"],
        "technical": ["Deployed", "Automated", "Integrated", "Migrated", "Configured", "Refactored"]
    }
    
    # Weak verbs to avoid
    WEAK_VERBS = [
        "worked on", "helped with", "was responsible for", "assisted with",
        "participated in", "involved in", "dealt with", "handled"
    ]

    # No fallback rotations - all bullets must be generated dynamically by LLM
    
    def __init__(self):
        self.system_prompt = self._build_enhanced_system_prompt()
        self.all_strong_verbs = [verb for verbs in self.STRONG_VERBS.values() for verb in verbs]
        # Master bullet prompt for XYZ/STAR FAANG-style generation with hard negative constraints
        self.master_bullet_prompt = """### ROLE
Senior Technical Resume Writer (FAANG Specialty).

### TASK
Generate JD-anchored professional summary and bullets that reflect the user's real projects, roles, and certifications. Always adapt to the specific job description and personal info provided—no canned text.

### CRITICAL CONSTRAINTS (DO NOT VIOLATE)
1. NO NONSENSE: Never say "improved [Language/Tool]." You improve a BUSINESS METRIC (speed, cost, accuracy) using a tool.
2. NO ROBOTIC TEMPLATES: Every bullet must differ in verb, structure, metric, and context.
3. REAL-WORLD IMPACT: Tie outcomes to quantified gains (%, $, time, uptime, users).
4. JD-ALIGNMENT: Prioritize {target_keywords}. Mirror the role's responsibilities, tools, and focus areas from the JD.
5. PROFESSIONAL SUMMARY: Generate 2-3 sentences highlighting years of experience, key technologies from JD, and quantified achievements. Must be role-specific and keyword-rich.
6. PROJECT COVERAGE: For EACH project listed, produce exactly 3 distinct bullets (XYZ/STAR) using that project's name/tech stack.
7. CERT DESCRIPTIONS: For EACH certification listed, produce 1 concise line describing verified skills/knowledge and relevance to the JD.
8. MANDATORY GENERATION: You MUST generate professional summary, 4 experience bullets, 3 bullets per project, and 1 description per certification. Empty output is NOT acceptable.

### INPUT
User Personal Info (name, years of experience, education):
{personal_info}

User Data (experience, projects, certifications):
{raw_experience}

Project Names: {project_names}
Target Job Description: {target_jd}
TARGET_KEYWORDS: {target_keywords}

### OUTPUT FORMAT
Return ONLY valid JSON with ALL fields populated:
{{
    "professional_summary": "2-3 sentence summary with years of experience, key JD technologies, and quantified achievements tailored to target role",
    "experience_bullets": ["bullet 1 with metrics and keywords", "bullet 2 with metrics", "bullet 3 with metrics", "bullet 4 with metrics"],
    "project_bullets": {{
        "project_0": ["project bullet 1 with XYZ format", "project bullet 2 with STAR format", "project bullet 3 with metrics"],
        "project_1": ["project bullet 1 with XYZ format", "project bullet 2 with STAR format", "project bullet 3 with metrics"]
    }},
    "certification_descriptions": {{
        "cert_0": "Certification description mentioning validated skills and JD relevance",
        "cert_1": "Certification description mentioning validated skills and JD relevance"
    }}
}}

### REMEMBER
- NEVER return empty strings, arrays or objects
- ALWAYS generate professional summary (2-3 sentences, keyword-rich, quantified)
- ALWAYS generate exactly 4 experience bullets
- ALWAYS generate exactly 3 bullets per project
- ALWAYS generate exactly 1 description per certification
- Base content on user's actual experience but align with JD keywords and requirements
- Professional summary should immediately signal the target role and value proposition
"""
    def _build_enhanced_system_prompt(self) -> str:
        """Build comprehensive system prompt for FAANG-level content generation."""
        return """You are an expert resume writer specializing in FAANG (Meta, Apple, Amazon, Netflix, Google) and top-tier tech company resumes. You have helped 1000+ candidates get interviews at these companies.

## CRITICAL REQUIREMENTS:

### 1. ACTION VERBS (100% compliance required)
- **EVERY** bullet point MUST start with a powerful action verb
- Use verbs like: Architected, Engineered, Spearheaded, Optimized, Scaled, Led, Designed, Implemented
- **NEVER** use weak phrases: "worked on", "helped with", "was responsible for", "assisted with"

### 2. QUANTIFICATION (70%+ of bullets required)
- Include specific metrics: percentages, dollar amounts, time saved, scale, user counts
- Examples:
  * "Reduced API latency by 45% (from 200ms to 110ms)"
  * "Scaled system to handle 5M+ daily active users"
  * "Cut infrastructure costs by $180K annually through optimization"
  * "Improved deployment speed by 3x (from 2 hours to 40 minutes)"

### 3. STAR METHOD (Situation-Task-Action-Result)
Structure bullets as: [Action Verb] + [What] + [How/Technologies] + [Quantified Impact]

### 4. KEYWORD OPTIMIZATION
- Seamlessly integrate job description keywords into bullets (15-20% keyword density)
- Use exact terminology from job posting
- Include related technologies (e.g., if they want React, mention Next.js, TypeScript)
- Natural integration - NO keyword stuffing

### 5. TECHNICAL DEPTH
- Show architecture-level thinking, not just implementation
- Demonstrate impact on business metrics
- Highlight scale, performance, reliability
- Include specific technologies and versions where relevant

### 6. PROFESSIONAL SUMMARY
Format: "[X] years [Title] specialized in [domain] | Expert in [tech stack] | Track record of [quantified achievements] | [Value proposition]"

Example: "8 years Senior Software Engineer specialized in distributed systems and cloud infrastructure | Expert in Python, Go, Kubernetes, AWS | Built platforms serving 50M+ users with 99.99% uptime | Passionate about scaling backend systems and mentoring engineering teams"

## OUTPUT FORMAT:

Return ONLY valid JSON with this exact structure:

```json
{
    "professional_summary": "2-3 sentence summary with keywords and metrics",
    "skills": {
        "Programming Languages": ["Python", "Java", "Go"],
        "Frameworks & Libraries": ["Django", "Spring Boot", "React"],
        "Cloud & Infrastructure": ["AWS", "Docker", "Kubernetes", "Terraform"],
        "Databases": ["PostgreSQL", "MongoDB", "Redis"],
        "Tools & Practices": ["Git", "CI/CD", "Agile", "TDD"]
    },
    "experience": [
        {
            "title": "Senior Software Engineer",
            "company": "Tech Corp",
            "location": "San Francisco, CA",
            "duration": "Jan 2021 - Present",
            "bullets": [
                "",
                "",
                ""
            ]
        }
    ],
    "education": [
        {
            "degree": "Bachelor of Science in Computer Science",
            "school": "Stanford University",
            "location": "Stanford, CA",
            "graduation_year": "2020",
            "gpa": "3.8/4.0",
            "relevant_coursework": "Distributed Systems, Algorithms, Machine Learning"
        }
    ],
    "projects": [
        {
            "name": "Open Source Contribution - Django REST Framework",
            "technologies": ["Python", "Django", "REST APIs"],
            "description": "",
            "link": "github.com/username/project"
        }
    ],
    "matched_keywords": ["Python", "Kubernetes", "microservices", "AWS"],
    "missing_keywords": ["Terraform", "GraphQL"],
    "metadata": {
        "total_bullets": 12,
        "quantified_bullets": 9,
        "quantification_rate": 0.75,
        "action_verbs_used": ["Architected", "Optimized", "Led"],
        "keyword_density": 0.18,
        "weak_phrases_found": []
    }
}
```

## VALIDATION CHECKLIST:
Before returning, verify:
- [ ] 100% of experience bullets start with strong action verbs
- [ ] 70%+ of bullets contain quantified metrics (numbers, %, $, time, scale)
- [ ] All critical keywords from job description are included
- [ ] No weak phrases like "worked on", "helped with", "responsible for"
- [ ] Technical depth matches job seniority level
- [ ] Professional summary includes keywords and metrics
- [ ] Skills section matches job requirements exactly
- [ ] All JSON is valid and properly formatted

## REMEMBER:
- Quality over quantity - 3-5 strong bullets per role is better than 7 weak ones
- Every word should demonstrate value and impact
- Think like a hiring manager at FAANG companies
- Show, don't tell - use metrics to prove claims
"""
    
    def generate(
        self,
        job_description: str,
        personal_info: Dict[str, Any],
        feedback: str = None,
        sections_to_regenerate: list = None,
        cached_content: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate FAANG-optimized resume content.
        
        Args:
            job_description: Raw job description text
            personal_info: User's personal information (skills, experience, education)
            feedback: Optional feedback from previous iteration
            sections_to_regenerate: FIX-3 - List of sections to regenerate (for selective mode)
            cached_content: FIX-3 - Previously generated content to reuse for non-failed sections
            
        Returns:
            Structured resume content with quality metadata
        """
        logger.info("=== Content Generator Agent: Starting ===")
        
        # FIX-3: Handle selective regeneration mode
        if sections_to_regenerate:
            logger.info(f"Selective regeneration mode: regenerating sections {sections_to_regenerate}\")")
            # For now, regenerate all sections. In future, can optimize to regenerate only specified sections
        
        # Parse job description with enhanced extraction
        job_context = self._extract_job_requirements(job_description)
        logger.info(f"Extracted {len(job_context['critical_keywords'])} critical keywords")
        logger.info(f"Identified {len(job_context['technical_skills'])} technical skills")
        
        # Build the prompt
        if feedback:
            user_prompt = self._build_prompt_with_feedback(
                job_description,
                personal_info,
                job_context,
                feedback
            )
            logger.info("Using feedback from previous iteration")
        else:
            user_prompt = self._build_initial_prompt(
                job_description,
                personal_info,
                job_context
            )
            logger.info("Creating initial resume content")
        
        # Generate content via Groq API
        try:
            full_prompt = self.system_prompt + "\n\n" + user_prompt
            response_text = groq_generate(
                full_prompt, 
                max_tokens=4096, 
                temperature=0.7,  # Higher to avoid repetitive outputs
                model=GROQ_CONTENT_GENERATOR_MODEL
            )
            logger.info("Received response from Groq API")
            
            # Parse and validate JSON from main prompt
            is_valid, resume_content = validate_json_output(response_text)
            
            if not is_valid:
                logger.error(f"Failed to parse JSON output: {resume_content}")
                return {
                    "success": False,
                    "error": "Invalid JSON output from LLM",
                    "raw_output": response_text
                }

            # CRITICAL: Call master bullet generator - this is the PRIMARY content source
            bullet_payload = self._generate_master_bullets(job_description, personal_info, job_context)
            if bullet_payload:
                resume_content["_llm_bullets"] = True
                resume_content["professional_summary"] = bullet_payload.get("professional_summary", "")
                resume_content["experience_bullets"] = bullet_payload.get("experience_bullets", [])
                resume_content["project_bullets"] = bullet_payload.get("project_bullets", {})
                resume_content["certification_descriptions"] = bullet_payload.get("certification_descriptions", {})
                
                # Validate that content was actually generated
                if not resume_content["professional_summary"]:
                    logger.error("CRITICAL: Master prompt returned EMPTY professional summary!")
                    # Attempt targeted re-prompt to generate professional summary
                    summary_text = self._generate_professional_summary(job_description, personal_info, job_context)
                    if summary_text and summary_text.strip():
                        resume_content["professional_summary"] = summary_text.strip()
                        logger.info("Filled professional summary via targeted re-prompt")
                    else:
                        logger.error("Re-prompt failed to produce a professional summary")
                if not resume_content["experience_bullets"]:
                    logger.error("CRITICAL: Master prompt returned EMPTY experience bullets!")
                if not resume_content["project_bullets"]:
                    logger.warning("Master prompt returned EMPTY project bullets")
                if not resume_content["certification_descriptions"]:
                    logger.warning("Master prompt returned EMPTY certification descriptions")
                    
                logger.info(f"Master content generated - Summary: {len(resume_content['professional_summary'])} chars, Experience: {len(resume_content['experience_bullets'])} bullets, Projects: {len(resume_content['project_bullets'])} entries")
            else:
                logger.error("CRITICAL: Master bullet generation FAILED completely - no payload returned!")
                # This should never happen in production

            # Post-processing: Validate and enhance content (inject personal info early)
            resume_content["personal_info"] = personal_info
            enhanced_content = self._post_process_content(
                resume_content,
                job_context,
                personal_info
            )
            
            enhanced_content["source_job_keywords"] = job_context["critical_keywords"]
            enhanced_content["success"] = True
            
            # Quality report
            quality_report = self._generate_quality_report(enhanced_content, job_context)
            enhanced_content["quality_report"] = quality_report
            
            logger.info(f"[OK] Content generated successfully")
            logger.info(f"  - Quantification rate: {quality_report['quantification_rate']:.1%}")
            logger.info(f"  - Action verb compliance: {quality_report['action_verb_compliance']:.1%}")
            logger.info(f"  - Keyword coverage: {quality_report['keyword_coverage']:.1%}")
            
            if quality_report['warnings']:
                logger.warning(f"Quality warnings: {', '.join(quality_report['warnings'])}")
            
            return enhanced_content
            
        except Exception as e:
            logger.error(f"Content Generator error: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }

    def _generate_professional_summary(
        self,
        job_description: str,
        personal_info: Dict[str, Any],
        job_context: Dict[str, Any]
    ) -> str:
        """Generate a 2-3 sentence professional summary aligned to the JD.

        Uses a focused prompt to avoid empty outputs and ensure role relevance,
        metrics, and keyword alignment. Returns plain text.
        """
        try:
            must_have = ", ".join(job_context.get("must_have_skills", [])[:8])
            keywords_list = [kw if isinstance(kw, str) else kw[0] for kw in job_context.get("critical_keywords", [])]
            keywords_str = ", ".join(keywords_list[:12])
            years = len(personal_info.get("experience", []))
            current_role = personal_info.get("experience", [{}])[0].get("title", "") if personal_info.get("experience") else ""
            name = personal_info.get("name", "")
            edu_short = personal_info.get("education", [])
            edu_str = json.dumps(edu_short[:1]) if edu_short else "[]"

            prompt = f"""
You are a senior technical resume writer for data roles (Analyst/Scientist/Engineer).
Write a professional summary of 2-3 sentences tailored to the target job.

Strict requirements:
- Mention years of experience (~{years} roles) and current role ('{current_role}') if relevant.
- Integrate JD-aligned keywords naturally: {keywords_str}
- Include at least one quantified achievement (%, $, time, scale, users).
- Convey domain impact and value proposition specific to the JD.
- Avoid generic fluff and templated phrasing.

Context:
- Candidate: {name}
- Must-Have Skills: {must_have}
- Education: {edu_str}
- Target JD (excerpt):\n{job_description[:800]}

Return ONLY the summary text (no JSON, no preamble).
"""
            response = groq_generate(prompt, max_tokens=256, temperature=0.3, model=GROQ_CONTENT_GENERATOR_MODEL)
            # Clean up whitespace and ensure 2-3 sentences by truncation if overly long
            summary = (response or "").strip()
            # Basic sanity: enforce max ~3 sentences
            sentences = re.split(r"(?<=[.!?])\s+", summary)
            summary = " ".join(sentences[:3]).strip()
            return summary
        except Exception as exc:
            logger.warning(f"Professional summary generation failed: {exc}")
            return ""
    
    def _extract_job_requirements(self, job_description: str) -> Dict[str, Any]:
        """Enhanced job description parsing with keyword importance ranking."""
        # Use existing tools
        base_context = parse_job_description(job_description)
        technical_skills = extract_technical_skills(job_description)
        soft_skills = extract_soft_skills(job_description)
        
        # Extract keywords with importance scoring
        keywords_with_scores = self._rank_keywords_by_importance(
            job_description,
            technical_skills
        )
        
        # Identify must-have vs nice-to-have
        must_have = [kw for kw, score in keywords_with_scores if score >= 8]
        nice_to_have = [kw for kw, score in keywords_with_scores if 5 <= score < 8]
        
        return {
            "critical_keywords": keywords_with_scores,
            "must_have_skills": must_have,
            "nice_to_have_skills": nice_to_have,
            "technical_skills": technical_skills,
            "soft_skills": soft_skills,
            "all_keywords": base_context.get("keywords", [])
        }
    
    def _rank_keywords_by_importance(
        self, 
        job_description: str, 
        technical_skills: List[str]
    ) -> List[Tuple[str, int]]:
        """
        Rank keywords by importance (1-10 scale).
        Higher score = more critical for ATS.
        """
        keywords_with_scores = []
        jd_lower = job_description.lower()
        
        for skill in technical_skills:
            skill_lower = skill.lower()
            
            # Count mentions
            mentions = jd_lower.count(skill_lower)
            
            # Check if in requirements section (higher importance)
            in_requirements = bool(re.search(
                rf'(?:require|must have|essential).*{re.escape(skill_lower)}',
                jd_lower,
                re.IGNORECASE
            ))
            
            # Check if in qualifications section
            in_qualifications = bool(re.search(
                rf'(?:qualification|experience with).*{re.escape(skill_lower)}',
                jd_lower,
                re.IGNORECASE
            ))
            
            # Calculate importance score (1-10)
            score = min(10, 5 + mentions * 2)  # Base 5, +2 per mention
            if in_requirements:
                score = min(10, score + 3)
            if in_qualifications:
                score = min(10, score + 1)
            
            keywords_with_scores.append((skill, score))
        
        # Sort by importance
        keywords_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        return keywords_with_scores[:30]  # Top 30 keywords
    
    def _build_initial_prompt(
        self,
        job_description: str,
        personal_info: Dict[str, Any],
        job_context: Dict[str, Any]
    ) -> str:
        """Build initial prompt with enhanced context."""
        must_have = ", ".join(job_context["must_have_skills"][:10])
        nice_to_have = ", ".join(job_context["nice_to_have_skills"][:5])
        
        prompt = f"""
CREATE A FAANG-QUALITY RESUME

## JOB DESCRIPTION:
{job_description}

## CRITICAL KEYWORDS (Must include naturally):
**Must-Have**: {must_have}
**Nice-to-Have**: {nice_to_have}

## APPLICANT'S BACKGROUND:
{json.dumps(personal_info, indent=2)}

## YOUR TASK:
Generate a resume that will score 90+ on ATS and impress FAANG recruiters.

**Requirements**:
1. **Professional Summary**: 2-3 lines with years of experience, key technologies, and quantified achievements
2. **Skills Section**: Organize by category (Programming Languages, Frameworks, Cloud, Databases, Tools)
   - Match job requirements EXACTLY
   - Prioritize must-have skills first
3. **Experience Section**: For each role, create 3-5 bullet points that:
   - Start with powerful action verbs (Architected, Engineered, Optimized, Scaled, Led)
   - Include quantified results (%, $, time, scale, users)
   - Follow STAR format: Action + Technology + Impact
   - Naturally incorporate keywords from job description
   - Show technical depth and business impact
4. **Education**: Degree, school, year, GPA if >3.5
5. **Projects** (optional): Personal projects with impact metrics

**Quality Targets**:
- 100% of bullets start with strong action verbs
- 70%+ of bullets have quantified metrics
- 90%+ keyword coverage from must-have list
- No weak phrases ("worked on", "helped with", "responsible for")

Return ONLY the JSON structure specified in the system prompt.
"""
        return prompt
    
    def _build_prompt_with_feedback(
        self,
        job_description: str,
        personal_info: Dict[str, Any],
        job_context: Dict[str, Any],
        feedback: str
    ) -> str:
        """Build refinement prompt incorporating feedback."""
        prompt = f"""
IMPROVE THE RESUME BASED ON FEEDBACK

## FEEDBACK TO ADDRESS:
{feedback}

## JOB DESCRIPTION:
{job_description}

## CRITICAL KEYWORDS STILL NEEDED:
{", ".join(job_context["must_have_skills"][:10])}

## APPLICANT'S BACKGROUND:
{json.dumps(personal_info, indent=2)}

## YOUR TASK:
Regenerate the resume addressing ALL feedback points while:
1. **Maintaining** all strong elements from previous version
2. **Adding** missing keywords naturally into experience bullets
3. **Improving** bullet points with weak action verbs or missing metrics
4. **Enhancing** technical depth where needed
5. **Keeping** the same JSON structure

**Focus Areas**:
- If keywords are missing: Weave them into 2-3 experience bullets naturally
- If quantification is low: Add specific metrics (%, time, scale, cost savings)
- If action verbs are weak: Replace with powerful alternatives
- If ATS score is low: Increase keyword density to 15-20%

Return ONLY the improved JSON structure.
"""
        return prompt
    
    def _post_process_content(
        self, 
        content: Dict[str, Any],
        job_context: Dict[str, Any],
        personal_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Post-process generated content to ensure quality.
        Validates and fixes common issues.
        """
        # Ensure basic structure exists, but never generate fallback bullets
        if not content.get("experience"):
            # Only add structure without bullets - bullets must come from LLM
            content["experience"] = self._backfill_experience(personal_info, job_context)
        if not content.get("education"):
            content["education"] = personal_info.get("education", [])
        if not content.get("skills"):
            content["skills"] = personal_info.get("skills", {})

        # Override bullets with master prompt payload when available
        if content.get("experience_bullets") and content.get("experience"):
            bullets = content["experience_bullets"]
            for exp in content["experience"]:
                exp["bullets"] = bullets
        
        # Handle new project_bullets structure (dict with project_0, project_1, etc.)
        if content.get("project_bullets"):
            projects = content.get("projects") or personal_info.get("projects", [])
            if projects:
                project_bullets_dict = content["project_bullets"]
                if isinstance(project_bullets_dict, dict):
                    # New format: {"project_0": [3 bullets], "project_1": [3 bullets]}
                    for idx, proj in enumerate(projects):
                        proj_key = f"project_{idx}"
                        if proj_key in project_bullets_dict:
                            proj["bullets"] = project_bullets_dict[proj_key]
                        else:
                            # Fallback if key missing: leave empty so downstream steps can generate or skip
                            proj["bullets"] = []
                else:
                    # Old format: simple list - distribute evenly
                    per_proj = max(1, len(project_bullets_dict) // len(projects))
                    for idx, proj in enumerate(projects):
                        start = idx * per_proj
                        proj["bullets"] = project_bullets_dict[start:start+per_proj] or project_bullets_dict
                content["projects"] = projects
        
        # Handle certification descriptions (dict with cert_0, cert_1, etc.)
        if content.get("certification_descriptions"):
            certs = personal_info.get("awards_and_certifications", [])
            cert_desc_dict = content["certification_descriptions"]
            if isinstance(cert_desc_dict, dict):
                for idx, cert in enumerate(certs):
                    cert_key = f"cert_{idx}"
                    if cert_key in cert_desc_dict:
                        cert["description"] = cert_desc_dict[cert_key]
                content["certifications_with_descriptions"] = certs

        # Only fix action verbs - no metric enrichment (LLM handles everything)
        if "experience" in content:
            for exp in content["experience"]:
                if "bullets" in exp and exp["bullets"]:
                    # Only fix weak action verbs, don't add content
                    enriched_bullets = []
                    for bullet in exp["bullets"]:
                        if bullet and bullet.strip():  # Only process non-empty bullets
                            fixed = self._fix_bullet_action_verb(bullet)
                            enriched_bullets.append(fixed)
                    exp["bullets"] = enriched_bullets

        # Enforce cross-section uniqueness (experience/projects/certifications)
        # (LLM already instructed; keep guard active)
        self._apply_uniqueness_guards(content, job_context)
        
        # Ensure metadata exists
        if "metadata" not in content:
            content["metadata"] = self._calculate_metadata(content, job_context)
        
        return content
    
    def _fix_bullet_action_verb(self, bullet: str) -> str:
        """Ensure bullet starts with a strong action verb."""
        # Check if starts with strong verb
        first_word = bullet.split()[0].rstrip('.,;:')
        
        if first_word in self.all_strong_verbs:
            return bullet  # Already good
        
        # Check for weak phrases
        bullet_lower = bullet.lower()
        for weak_phrase in self.WEAK_VERBS:
            if bullet_lower.startswith(weak_phrase):
                # Replace with appropriate strong verb
                replacement = self._suggest_strong_verb(bullet)
                logger.warning(f"Fixed weak verb: '{weak_phrase}' -> '{replacement}'")
                return bullet.replace(weak_phrase, replacement, 1).strip()
        
        return bullet
    
    def _suggest_strong_verb(self, bullet: str) -> str:
        """Suggest appropriate strong verb based on bullet content."""
        bullet_lower = bullet.lower()
        
        # Pattern matching for appropriate verb
        if any(word in bullet_lower for word in ["build", "create", "develop"]):
            return "Engineered"
        elif any(word in bullet_lower for word in ["improve", "optimize", "enhance"]):
            return "Optimized"
        elif any(word in bullet_lower for word in ["lead", "manage", "coordinate"]):
            return "Led"
        elif any(word in bullet_lower for word in ["design", "architect"]):
            return "Architected"
        elif any(word in bullet_lower for word in ["scale", "grow", "expand"]):
            return "Scaled"
        else:
            return "Implemented"  # Safe default

    def _backfill_experience(
        self,
        personal_info: Dict[str, Any],
        job_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Return experience structure without bullets - LLM must generate all content dynamically."""
        # No fallback bullets - force dynamic generation from master bullet prompt
        fallback_experience = []
        
        for role in personal_info.get("experience", []):
            fallback_experience.append({
                "title": role.get("title", ""),
                "company": role.get("company", ""),
                "location": role.get("location", ""),
                "duration": role.get("duration", ""),
                "bullets": []  # Empty - must be populated by LLM
            })

        return fallback_experience

    def _apply_uniqueness_guards(
        self,
        content: Dict[str, Any],
        job_context: Dict[str, Any]
    ) -> None:
        """Enforce unique verb+object+metric and 4-gram separation across bullets."""
        bullet_lists: List[List[str]] = []

        # Collect experience bullets
        for exp in content.get("experience", []):
            if isinstance(exp, dict) and isinstance(exp.get("bullets"), list):
                bullet_lists.append(exp["bullets"])

        # Collect project bullet-like fields if present
        for proj in content.get("projects", []):
            if isinstance(proj, dict):
                if isinstance(proj.get("bullets"), list):
                    bullet_lists.append(proj["bullets"])
                elif isinstance(proj.get("description"), list):
                    bullet_lists.append(proj["description"])

        # Collect certification bullet-like fields if present
        for cert in content.get("awards_and_certifications", []):
            if isinstance(cert, dict) and isinstance(cert.get("bullets"), list):
                bullet_lists.append(cert["bullets"])

        if not bullet_lists:
            return

        used_ngrams = set()
        used_trios = set()

        for bullets in bullet_lists:
            for i, bullet in enumerate(bullets):
                rewritten = self._enforce_bullet_uniqueness(
                    bullet,
                    used_ngrams,
                    used_trios,
                    0,
                    0,
                    job_context
                )
                bullets[i] = rewritten

    def _enforce_bullet_uniqueness(
        self,
        bullet: str,
        used_ngrams: set,
        used_trios: set,
        outcome_idx: int,
        tool_idx: int,
        job_context: Dict[str, Any]
    ) -> str:
        """Rewrite bullet if it overlaps via 4-grams or verb-object pair with prior bullets."""
        tokens = re.findall(r"\b\w+\b", bullet.lower())
        ngrams = {" ".join(tokens[i:i+4]) for i in range(len(tokens) - 3)} if len(tokens) >= 4 else set()

        verb = tokens[0] if tokens else ""
        obj = " ".join(tokens[1:4]) if len(tokens) >= 2 else ""
        trio = f"{verb}|{obj}"

        overlap = bool(ngrams & used_ngrams) or (trio in used_trios)

        if overlap:
            bullet = self._rewrite_with_rotations(
                bullet,
                outcome_idx,
                tool_idx,
                job_context
            )
            # Recompute to update signatures after rewrite
            tokens = re.findall(r"\b\w+\b", bullet.lower())
            ngrams = {" ".join(tokens[i:i+4]) for i in range(len(tokens) - 3)} if len(tokens) >= 4 else set()
            verb = tokens[0] if tokens else ""
            obj = " ".join(tokens[1:4]) if len(tokens) >= 2 else ""
            trio = f"{verb}|{obj}"

        used_ngrams.update(ngrams)
        used_trios.add(trio)
        return bullet

    def _rewrite_with_rotations(
        self,
        bullet: str,
        outcome_idx: int,
        tool_idx: int,
        job_context: Dict[str, Any]
    ) -> str:
        """Apply outcome/tool rotation and metric/keyword injection to break similarity."""
        # No longer used; LLM provides variation
        return bullet
    
    def _calculate_metadata(
        self, 
        content: Dict[str, Any],
        job_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate content quality metrics."""
        total_bullets = 0
        quantified_bullets = 0
        action_verbs_used = []
        weak_phrases_found = []
        
        # Pattern for detecting quantified metrics
        metric_pattern = r'\d+[%$KMB]?|\d+[x×]|\d+[-–]\d+%?'
        
        if "experience" in content:
            for exp in content["experience"]:
                for bullet in exp.get("bullets", []):
                    total_bullets += 1
                    
                    # Check for metrics
                    if re.search(metric_pattern, bullet):
                        quantified_bullets += 1
                    
                    # Extract action verb
                    first_word = bullet.split()[0].rstrip('.,;:')
                    if first_word in self.all_strong_verbs:
                        action_verbs_used.append(first_word)
                    
                    # Check for weak phrases
                    bullet_lower = bullet.lower()
                    for weak in self.WEAK_VERBS:
                        if weak in bullet_lower:
                            weak_phrases_found.append(weak)
        
        # Calculate rates
        quantification_rate = quantified_bullets / total_bullets if total_bullets > 0 else 0
        action_verb_compliance = len(action_verbs_used) / total_bullets if total_bullets > 0 else 0
        
        # Keyword coverage
        resume_text = json.dumps(content).lower()
        matched_keywords = sum(
            1 for kw, score in job_context["critical_keywords"]
            if kw.lower() in resume_text
        )
        keyword_coverage = matched_keywords / len(job_context["critical_keywords"]) if job_context["critical_keywords"] else 0
        
        return {
            "total_bullets": total_bullets,
            "quantified_bullets": quantified_bullets,
            "quantification_rate": round(quantification_rate, 2),
            "action_verbs_used": list(set(action_verbs_used)),
            "action_verb_compliance": round(action_verb_compliance, 2),
            "weak_phrases_found": list(set(weak_phrases_found)),
            "keyword_coverage": round(keyword_coverage, 2),
            "matched_keywords_count": matched_keywords
        }

    def _generate_master_bullets(
        self,
        job_description: str,
        personal_info: Dict[str, Any],
        job_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Call the master prompt to get experience/project/certification bullets via LLM."""
        try:
            target_keywords = [kw if isinstance(kw, str) else kw[0] for kw in job_context.get("critical_keywords", [])]
            user_resume_data = {
                "experience": personal_info.get("experience", []),
                "projects": personal_info.get("projects", []),
                "awards_and_certifications": personal_info.get("awards_and_certifications", [])
            }
            personal_info_summary = {
                "name": personal_info.get("name", ""),
                "years_of_experience": len(personal_info.get("experience", [])),
                "education": personal_info.get("education", []),
                "current_role": personal_info.get("experience", [{}])[0].get("title", "") if personal_info.get("experience") else ""
            }
            project_names = [p.get("name", f"project_{idx}") for idx, p in enumerate(user_resume_data.get("projects", []))]
            prompt = self.master_bullet_prompt.format(
                personal_info=json.dumps(personal_info_summary, indent=2),
                raw_experience=json.dumps(user_resume_data, indent=2),
                target_jd=job_description,
                target_keywords=json.dumps(target_keywords),
                project_names=json.dumps(project_names)
            )
            response_text = groq_generate(prompt, max_tokens=2048, temperature=0.7, model=GROQ_CONTENT_GENERATOR_MODEL)
            is_valid, payload = validate_json_output(response_text)
            if not is_valid:
                logger.warning("Master bullet prompt returned invalid JSON; skipping overrides")
                logger.warning(response_text)
                return {}
            
            # Handle old format (simple list) for backward compatibility
            if isinstance(payload, list):
                return {
                    "experience_bullets": payload,
                    "project_bullets": {},
                    "certification_descriptions": {}
                }
            
            # New format with structured project_bullets and cert descriptions
            result = {
                "experience_bullets": payload.get("experience_bullets", []),
                "project_bullets": payload.get("project_bullets", {}),
                "certification_descriptions": payload.get("certification_descriptions", {})
            }
            return result
        except Exception as exc:
            logger.warning(f"Master bullet generation failed: {exc}")
            return {}
    
    def _generate_quality_report(
        self,
        content: Dict[str, Any],
        job_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive quality assessment."""
        metadata = content.get("metadata", {})
        
        warnings = []
        recommendations = []
        
        # Check quantification rate
        quant_rate = metadata.get("quantification_rate", 0)
        if quant_rate < 0.7:
            warnings.append(f"Low quantification rate: {quant_rate:.1%} (need 70%+)")
            recommendations.append("Add specific metrics to experience bullets (%, $, time, scale)")
        
        # Check action verb compliance
        verb_compliance = metadata.get("action_verb_compliance", 0)
        if verb_compliance < 1.0:
            warnings.append(f"Weak action verbs detected: {verb_compliance:.1%} compliance")
            recommendations.append("Replace weak phrases with strong action verbs")
        
        # Check keyword coverage
        keyword_coverage = metadata.get("keyword_coverage", 0)
        if keyword_coverage < 0.9:
            warnings.append(f"Low keyword coverage: {keyword_coverage:.1%} (need 90%+)")
            recommendations.append("Integrate more keywords from job description naturally")
        
        # Check for weak phrases
        weak_phrases = metadata.get("weak_phrases_found", [])
        if weak_phrases:
            warnings.append(f"Weak phrases found: {', '.join(weak_phrases)}")
        
        return {
            "quantification_rate": quant_rate,
            "action_verb_compliance": verb_compliance,
            "keyword_coverage": keyword_coverage,
            "warnings": warnings,
            "recommendations": recommendations,
            "overall_quality": "excellent" if not warnings else "needs_improvement"
        }


__all__ = ["ResumeContentGeneratorAgent"]