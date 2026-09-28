"""
backend/app/services/resume_builder_service.py

Live Candidate Resume Builder & Real-Time Match Simulator.
Computes real-time ATS readability formatting scores, word counts, skill extractions, and job alignment match scores.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional

from app.services.skill_service import match_skills
from app.services.matching_service import calculate_lexical_similarity

logger = logging.getLogger(__name__)

STANDARD_SECTION_HEADERS = [
    "WORK EXPERIENCE", "EXPERIENCE", "EMPLOYMENT",
    "EDUCATION", "ACADEMIC BACKGROUND",
    "SKILLS", "TECHNICAL SKILLS", "COMPETENCIES",
    "PROJECTS", "PERSONAL PROJECTS",
    "SUMMARY", "PROFESSIONAL SUMMARY", "OBJECTIVE",
]


@dataclass
class LiveResumeAnalysisResult:
    char_count: int
    word_count: int
    estimated_pages: int
    ats_score: float
    extracted_skills: List[str]
    matched_skills: List[str]
    missing_skills: List[str]
    live_match_score: float
    ats_warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


def analyze_live_resume(
    resume_markdown: str,
    job_description: Optional[str] = None,
    target_skills: Optional[List[str]] = None,
) -> LiveResumeAnalysisResult:
    """
    Perform instantaneous, debounced ATS and match analysis on raw resume text/markdown.
    """
    cleaned_text = resume_markdown.strip()
    char_count = len(cleaned_text)
    words = cleaned_text.split()
    word_count = len(words)
    estimated_pages = max(1, (word_count // 450) + (1 if word_count % 450 > 50 else 0))

    warnings: List[str] = []
    suggestions: List[str] = []
    ats_deductions = 0.0

    # 1. ATS Header Check
    upper_text = cleaned_text.upper()
    found_headers = [h for h in STANDARD_SECTION_HEADERS if h in upper_text]
    if len(found_headers) < 2:
        warnings.append("Missing standard capital section headers (e.g., WORK EXPERIENCE, EDUCATION, SKILLS).")
        ats_deductions += 20.0
        suggestions.append("Add uppercase headers like WORK EXPERIENCE and TECHNICAL SKILLS.")

    # 2. Text Length Check
    if word_count < 150:
        warnings.append("Resume content is sparse (< 150 words). Low feature density may lower ATS ranking.")
        ats_deductions += 25.0
        suggestions.append("Expand work experience bullets to reach 300+ words.")
    elif word_count > 1000:
        warnings.append("Resume is lengthy (> 1000 words). Consider condensing to 1-2 pages.")
        ats_deductions += 10.0

    # 3. Contact Info Markers
    email_found = bool(re.search(r"[\w\.-]+@[\w\.-]+\.\w+", cleaned_text))
    phone_found = bool(re.search(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", cleaned_text))
    if not email_found:
        warnings.append("No valid email address detected in text.")
        ats_deductions += 15.0
    if not phone_found:
        warnings.append("No standard phone number format detected.")
        ats_deductions += 10.0

    # 4. Skill Extraction via NLP
    extracted = match_skills(cleaned_text)
    extracted_skill_names = sorted(list({s.canonical_name for s in extracted}))

    if len(extracted_skill_names) < 5:
        warnings.append(f"Only {len(extracted_skill_names)} canonical skills extracted. Target at least 8-12.")
        ats_deductions += 15.0
        suggestions.append("Add a dedicated TECHNICAL SKILLS section listing frameworks and tools.")

    # Compute ATS Score
    ats_score = max(0.0, min(100.0, round(100.0 - ats_deductions, 1)))

    # 5. Job Match Calculation
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    live_match_score = 0.0

    if target_skills:
        req_set = {s.strip().lower() for s in target_skills}
        ext_set = {s.lower() for s in extracted_skill_names}
        matched_set = req_set.intersection(ext_set)
        missing_set = req_set - ext_set

        matched_skills = sorted([s for s in target_skills if s.strip().lower() in matched_set])
        missing_skills = sorted([s for s in target_skills if s.strip().lower() in missing_set])

        if req_set:
            skill_cov = len(matched_set) / len(req_set)
        else:
            skill_cov = 1.0

        lex_sim = calculate_lexical_similarity(cleaned_text, job_description or " ".join(target_skills))
        live_match_score = round((0.7 * skill_cov + 0.3 * lex_sim) * 100.0, 1)

        if missing_skills:
            suggestions.append(f"Incorporate missing target skills: {', '.join(missing_skills[:5])}.")
    elif job_description:
        job_extracted = match_skills(job_description)
        job_skill_names = {s.canonical_name for s in job_extracted}
        if job_skill_names:
            ext_set = {s.lower() for s in extracted_skill_names}
            matched_set = {s for s in job_skill_names if s.lower() in ext_set}
            missing_set = job_skill_names - matched_set

            matched_skills = sorted(list(matched_set))
            missing_skills = sorted(list(missing_set))
            skill_cov = len(matched_set) / len(job_skill_names)
            lex_sim = calculate_lexical_similarity(cleaned_text, job_description)
            live_match_score = round((0.7 * skill_cov + 0.3 * lex_sim) * 100.0, 1)

    return LiveResumeAnalysisResult(
        char_count=char_count,
        word_count=word_count,
        estimated_pages=estimated_pages,
        ats_score=ats_score,
        extracted_skills=extracted_skill_names,
        matched_skills=matched_skills,
        missing_skills=missing_skills,
        live_match_score=live_match_score,
        ats_warnings=warnings,
        suggestions=suggestions,
    )
