"""Content Validator Agent (Agent 2).

Refines resume content produced by Agent 1 to enforce strict word-count
constraints without introducing new information. Outputs are LaTeX-ready and
structure-preserving so Agent 3 (LaTeX Generator) can consume them directly.
"""
import copy
import json
import re
from typing import Any, Dict, List, Optional

from config.settings import GROQ_CONTENT_GENERATOR_MODEL
from tools.groq_client import groq_generate
from utils.logger import logger
from utils.validators import validate_json_output


class ContentValidatorAgent:
    """Agent 2: Enforce length precision and polish content without adding facts."""

    SUMMARY_RANGE = (40, 50)
    EXPERIENCE_RANGE = (18, 20)
    PROJECT_RANGE = (16, 18)
    CERT_RANGE = (13, 15)

    def __init__(self) -> None:
        self.system_prompt = self._build_system_prompt()

    def validate(self, resume_content: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and constrain resume content for strict word-count ranges."""
        base_content = copy.deepcopy(resume_content or {})

        try:
            llm_payload = self._call_validator_llm(base_content)
        except Exception as exc:  # Defensive: never halt pipeline on validator failure
            logger.error(f"Content Validator error: {exc}")
            return {
                "success": False,
                "error": str(exc),
            }

        merged = self._merge_with_original(base_content, llm_payload)
        enforced = self._enforce_local_constraints(merged)

        return {
            "success": True,
            "validated_content": enforced,
        }

    # ---------------------------------------------------------------------
    # LLM interaction
    # ---------------------------------------------------------------------
    def _call_validator_llm(self, resume_content: Dict[str, Any]) -> Dict[str, Any]:
        """Call LLM to refine content with complete sentences meeting word-count targets."""
        prompt = self._build_user_prompt(resume_content)

        response_text = groq_generate(
            prompt,
            max_tokens=3072,  # Increased for better sentence completion
            temperature=0.3,  # Slight creativity for better phrasing while staying factual
            model=GROQ_CONTENT_GENERATOR_MODEL,
        )

        is_valid, payload = validate_json_output(response_text)
        if not is_valid or not isinstance(payload, dict):
            logger.warning("Content Validator returned invalid JSON; using original content")
            return resume_content

        # Validate that LLM maintained complete sentences (basic check)
        self._validate_sentence_completeness(payload)

        return payload

    def _validate_sentence_completeness(self, content: Dict[str, Any]) -> None:
        """Log warnings if content appears to have incomplete sentences."""
        def check_completeness(text: str, context: str) -> None:
            if not text or not text.strip():
                return
            
            # Check for obvious fragments (ends with 'and', 'or', 'using', etc.)
            text = text.strip()
            fragment_indicators = [
                'and', 'or', 'using', 'with', 'for', 'to', 'by', 'in', 'at',
                'the', 'a', 'an', 'of', 'that', 'which'
            ]
            last_word = text.split()[-1].rstrip('.,!?').lower()
            if last_word in fragment_indicators:
                logger.warning(f"Possible incomplete sentence in {context}: '{text}'")
        
        # Check summary
        if isinstance(content.get("professional_summary"), str):
            check_completeness(content["professional_summary"], "professional_summary")
        
        # Check experience bullets
        for idx, exp in enumerate(content.get("experience", []) or []):
            if isinstance(exp, dict) and isinstance(exp.get("bullets"), list):
                for bullet_idx, bullet in enumerate(exp.get("bullets", [])):
                    check_completeness(bullet, f"experience[{idx}].bullets[{bullet_idx}]")
        
        # Check project bullets
        for idx, proj in enumerate(content.get("projects", []) or []):
            if isinstance(proj, dict) and isinstance(proj.get("bullets"), list):
                for bullet_idx, bullet in enumerate(proj.get("bullets", [])):
                    check_completeness(bullet, f"projects[{idx}].bullets[{bullet_idx}]")

    def _build_system_prompt(self) -> str:
        return (
            "You are Content Validator (Agent 2), an expert technical writer. Your role is to "
            "refine resume content to meet exact word-count constraints while maintaining "
            "COMPLETE, MEANINGFUL sentences. Never break sentences mid-way or create fragments. "
            "\n\nCRITICAL RULES:\n"
            "- Every output must be a complete, grammatically correct sentence\n"
            "- Preserve all factual information, metrics, and technical terms\n"
            "- Tighten wording by removing filler words, not by truncating sentences\n"
            "- Use strong, concise language (e.g., 'Built scalable API' not 'Worked on building API')\n"
            "- If content is slightly over limit, compress wording while keeping meaning\n"
            "- If content is slightly under limit, keep it as-is (DON'T pad with filler)\n"
            "- Maintain professional resume tone and action-verb structure\n"
            "- Output valid JSON with the same structure as input"
        )

    def _build_user_prompt(self, resume_content: Dict[str, Any]) -> str:
        payload = self._extract_relevant_sections(resume_content)

        constraints = (
            "WORD-COUNT TARGET RANGES (must be COMPLETE sentences):\n"
            "- Professional Summary: 40-50 words (2-3 complete sentences)\n"
            "- Experience bullets: 18-20 words each (ONE complete sentence per bullet)\n"
            "- Project bullets: 16-18 words each (ONE complete sentence per bullet)\n"
            "- Certification descriptions: 13-15 words each (ONE complete sentence)\n"
            "\n"
            "HOW TO COMPRESS TEXT:\n"
            "✓ Remove filler: 'was responsible for' → 'Led'\n"
            "✓ Use strong verbs: 'worked on building' → 'Built'\n"
            "✓ Remove redundancy: 'various different' → 'various'\n"
            "✓ Consolidate phrases: 'in order to' → 'to'\n"
            "✗ NEVER break sentences mid-way\n"
            "✗ NEVER create fragments like 'Built system using Python and'\n"
            "✗ NEVER pad with filler words to meet minimum\n"
            "\n"
            "If a bullet is 17 words (target 18-20), keep it as-is. Quality > exact count.\n"
            "If a bullet is 23 words (target 18-20), compress by removing weak words.\n"
            "\n"
            "PRESERVE:\n"
            "- All metrics, percentages, and numbers\n"
            "- All technical tools, frameworks, and technologies\n"
            "- All company names, dates, and titles\n"
            "- Same bullet count and section structure\n"
        )

        return (
            f"{self.system_prompt}\n\n"
            f"{constraints}\n\n"
            "Return ONLY valid JSON with the SAME structure. Every text field must contain "
            "COMPLETE, MEANINGFUL sentences.\n"
            "\nJSON INPUT:\n"
            f"{json.dumps(payload, indent=2)}"
        )

    # ---------------------------------------------------------------------
    # Merging and constraint enforcement
    # ---------------------------------------------------------------------
    def _merge_with_original(
        self,
        base: Dict[str, Any],
        candidate: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Merge validated text back into the original structure safely."""
        merged = copy.deepcopy(base)

        if isinstance(candidate.get("professional_summary"), str):
            merged["professional_summary"] = candidate["professional_summary"]

        if isinstance(candidate.get("experience"), list) and isinstance(base.get("experience"), list):
            merged["experience"] = self._merge_sections(
                base.get("experience", []),
                candidate.get("experience", []),
                bullets_key="bullets",
            )

        if isinstance(candidate.get("projects"), list) and isinstance(base.get("projects"), list):
            merged["projects"] = self._merge_sections(
                base.get("projects", []),
                candidate.get("projects", []),
                bullets_key="bullets",
            )

        candidate_certs = candidate.get("certifications_with_descriptions") or candidate.get("awards_and_certifications")
        base_certs = base.get("certifications_with_descriptions") or base.get("awards_and_certifications")
        if isinstance(candidate_certs, list) and isinstance(base_certs, list):
            merged_certs = self._merge_sections(
                base_certs,
                candidate_certs,
                bullets_key="description",
            )
            # Preserve both keys for downstream compatibility
            if "certifications_with_descriptions" in base:
                merged["certifications_with_descriptions"] = merged_certs
            if "awards_and_certifications" in base:
                merged["awards_and_certifications"] = merged_certs

        return merged

    def _merge_sections(
        self,
        base_items: List[Dict[str, Any]],
        candidate_items: List[Dict[str, Any]],
        bullets_key: str,
    ) -> List[Dict[str, Any]]:
        merged_items: List[Dict[str, Any]] = []
        for idx, base_item in enumerate(base_items):
            merged_item = copy.deepcopy(base_item)
            candidate_item = candidate_items[idx] if idx < len(candidate_items) else {}

            if isinstance(candidate_item, dict):
                candidate_bullets = candidate_item.get(bullets_key)
                if isinstance(candidate_bullets, list):
                    # Preserve bullet count by aligning to base length
                    base_bullets = base_item.get(bullets_key, []) if isinstance(base_item.get(bullets_key), list) else []
                    merged_item[bullets_key] = self._align_bullet_count(candidate_bullets, base_bullets)
                elif isinstance(candidate_bullets, str) and bullets_key == "description":
                    merged_item[bullets_key] = candidate_bullets
            merged_items.append(merged_item)
        return merged_items

    def _align_bullet_count(self, candidate_bullets: List[str], base_bullets: List[str]) -> List[str]:
        if not base_bullets:
            return candidate_bullets

        # Match base bullet count; trim extras, keep order
        aligned = candidate_bullets[: len(base_bullets)]
        if len(aligned) < len(base_bullets):
            # If candidate has fewer bullets, pad with originals to maintain structure
            aligned.extend(base_bullets[len(aligned) :])
        return aligned

    def _enforce_local_constraints(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Final guardrail to guarantee word-count compliance while preserving meaning."""
        enforced = copy.deepcopy(content)

        if isinstance(enforced.get("professional_summary"), str):
            original = enforced["professional_summary"]
            coerced = self._coerce_text(original, *self.SUMMARY_RANGE)
            enforced["professional_summary"] = coerced
            if original != coerced:
                logger.info(f"Summary constrained: {len(original.split())} → {len(coerced.split())} words")

        for exp_idx, exp in enumerate(enforced.get("experience", []) or []):
            if isinstance(exp, dict) and isinstance(exp.get("bullets"), list):
                new_bullets = []
                for bullet_idx, bullet in enumerate(exp.get("bullets", [])):
                    original_wc = len(bullet.split())
                    coerced = self._coerce_text(bullet, *self.EXPERIENCE_RANGE)
                    new_wc = len(coerced.split())
                    new_bullets.append(coerced)
                    if original_wc != new_wc:
                        logger.debug(f"Experience[{exp_idx}].bullet[{bullet_idx}]: {original_wc} → {new_wc} words")
                exp["bullets"] = new_bullets

        for proj_idx, proj in enumerate(enforced.get("projects", []) or []):
            if isinstance(proj, dict) and isinstance(proj.get("bullets"), list):
                new_bullets = []
                for bullet_idx, bullet in enumerate(proj.get("bullets", [])):
                    original_wc = len(bullet.split())
                    coerced = self._coerce_text(bullet, *self.PROJECT_RANGE)
                    new_wc = len(coerced.split())
                    new_bullets.append(coerced)
                    if original_wc != new_wc:
                        logger.debug(f"Project[{proj_idx}].bullet[{bullet_idx}]: {original_wc} → {new_wc} words")
                proj["bullets"] = new_bullets

        cert_list = enforced.get("certifications_with_descriptions") or enforced.get("awards_and_certifications")
        if isinstance(cert_list, list):
            for cert_idx, cert in enumerate(cert_list):
                if isinstance(cert, dict) and isinstance(cert.get("description"), str):
                    original = cert["description"]
                    original_wc = len(original.split())
                    coerced = self._coerce_text(original, *self.CERT_RANGE)
                    new_wc = len(coerced.split())
                    cert["description"] = coerced
                    if original_wc != new_wc:
                        logger.debug(f"Certification[{cert_idx}]: {original_wc} → {new_wc} words")

        return enforced

    # ---------------------------------------------------------------------
    # Utilities
    # ---------------------------------------------------------------------
    def _extract_relevant_sections(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Slim payload for LLM: include only text fields that need constraint checks."""
        slim: Dict[str, Any] = {
            "professional_summary": content.get("professional_summary", ""),
            "experience": [],
            "projects": [],
            "certifications_with_descriptions": [],
        }

        for exp in content.get("experience", []) or []:
            if isinstance(exp, dict):
                slim_exp = {
                    "title": exp.get("title"),
                    "company": exp.get("company"),
                    "duration": exp.get("duration"),
                    "bullets": exp.get("bullets", []),
                }
                slim["experience"].append(slim_exp)

        for proj in content.get("projects", []) or []:
            if isinstance(proj, dict):
                slim_proj = {
                    "name": proj.get("name"),
                    "bullets": proj.get("bullets", proj.get("description", [])),
                }
                slim["projects"].append(slim_proj)

        certs = content.get("certifications_with_descriptions") or content.get("awards_and_certifications") or []
        for cert in certs:
            if isinstance(cert, dict):
                slim_cert = {
                    "name": cert.get("name"),
                    "description": cert.get("description", ""),
                }
                slim["certifications_with_descriptions"].append(slim_cert)

        return slim

    def _coerce_text(self, text: Optional[str], min_words: int, max_words: int) -> str:
        """Enforce word-count constraints while preserving complete sentences."""
        if not text or not text.strip():
            return ""

        text = text.strip()
        tokens = re.findall(r"\b\w+[\w'-]*\b", text)
        word_count = len(tokens)

        # If within acceptable range (allow ±2 word tolerance), keep as-is
        tolerance = 2
        if min_words - tolerance <= word_count <= max_words + tolerance:
            return text

        # If text exceeds maximum, try to truncate at sentence boundary
        if word_count > max_words:
            return self._truncate_at_sentence(text, max_words)

        # If text is below minimum, keep as-is (LLM should have handled this)
        # DON'T pad with nonsense - incomplete is better than meaningless
        return text

    def _truncate_at_sentence(self, text: str, max_words: int) -> str:
        """Truncate text at nearest sentence boundary before max_words."""
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        result = []
        word_count = 0
        
        for sentence in sentences:
            sentence_words = len(re.findall(r"\b\w+[\w'-]*\b", sentence))
            
            # If adding this sentence keeps us under limit, add it
            if word_count + sentence_words <= max_words:
                result.append(sentence)
                word_count += sentence_words
            else:
                # We've hit the limit - stop here to preserve complete sentences
                break
        
        # If result is empty (first sentence itself exceeds max), do smart truncation
        if not result and sentences:
            first_sentence = sentences[0]
            tokens = re.findall(r"\b\w+[\w'-]*\b", first_sentence)
            
            # Try to keep subject-verb-object structure intact
            if len(tokens) > max_words:
                # Keep first max_words but try to end at a natural point
                truncated_tokens = tokens[:max_words]
                # Check if we can back up to a comma or conjunction for cleaner break
                truncated_text = " ".join(truncated_tokens)
                
                # If we broke mid-phrase, try to find last complete clause
                if ',' in truncated_text:
                    parts = truncated_text.rsplit(',', 1)
                    # Use a simple threshold (10 words minimum for clause)
                    if len(re.findall(r"\b\w+[\w'-]*\b", parts[0])) >= 10:
                        return parts[0].strip()
                
                return truncated_text
        
        return " ".join(result).strip()


__all__ = ["ContentValidatorAgent"]
