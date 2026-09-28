"""
backend/app/services/ats_analyzer_service.py

Enterprise ATS Compatibility Analyzer & Parser Compliance Suite.
Evaluates resume text across 4 compliance dimensions:
  1. Document Structure & Headers (25%)
  2. Text Readability & Formatting (25%)
  3. Contact Information Compliance (25%)
  4. Keyword & Skill Density (25%)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import List, Optional

from app.services.skill_service import match_skills

logger = logging.getLogger(__name__)

ESSENTIAL_SECTIONS = {
    "WORK EXPERIENCE": ["WORK EXPERIENCE", "EXPERIENCE", "EMPLOYMENT HISTORY", "CAREER HISTORY"],
    "EDUCATION": ["EDUCATION", "ACADEMIC BACKGROUND", "QUALIFICATIONS"],
    "TECHNICAL SKILLS": ["TECHNICAL SKILLS", "SKILLS", "CORE COMPETENCIES", "TECHNOLOGIES"],
    "SUMMARY": ["PROFESSIONAL SUMMARY", "SUMMARY", "PROFILE", "OBJECTIVE"],
}

ACTION_VERBS = {
    "architected", "built", "spearheaded", "engineered", "developed", "orchestrated",
    "implemented", "designed", "optimized", "managed", "led", "created", "refactored",
    "scaled", "automated", "delivered", "deployed", "reduced", "increased", "accelerated",
}


@dataclass
class ATSAnalysisResult:
    overall_score: float
    structure_score: float
    readability_score: float
    contact_score: float
    density_score: float
    compliance_category: str
    detected_sections: List[str]
    missing_essential_sections: List[str]
    critical_issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    actionable_recommendations: List[str] = field(default_factory=list)


def analyze_ats_compatibility(resume_text: str) -> ATSAnalysisResult:
    """
    Run a comprehensive 4-dimension ATS compatibility scan on raw or extracted resume text.
    """
    text = resume_text.strip()
    upper_text = text.upper()
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    critical_issues: List[str] = []
    warnings: List[str] = []
    recommendations: List[str] = []

    # -------------------------------------------------------------------
    # Dimension 1: Document Structure & Headers (25 points max)
    # -------------------------------------------------------------------
    structure_score = 25.0
    detected_sections: List[str] = []
    missing_essential_sections: List[str] = []

    for std_name, aliases in ESSENTIAL_SECTIONS.items():
        found = False
        for alias in aliases:
            if alias in upper_text:
                found = True
                detected_sections.append(std_name)
                break
        if not found:
            missing_essential_sections.append(std_name)

    if missing_essential_sections:
        penalty = len(missing_essential_sections) * 6.0
        structure_score = max(0.0, structure_score - penalty)
        critical_issues.append(f"Missing essential section header(s): {', '.join(missing_essential_sections)}.")
        recommendations.append(f"Add explicit capitalized section headers for: {', '.join(missing_essential_sections)}.")

    # Check for all-caps section titles
    caps_headers = [line for line in lines if line.isupper() and len(line) < 40 and len(line) > 3]
    if len(caps_headers) < 2:
        structure_score = max(0.0, structure_score - 5.0)
        warnings.append("Low count of clear ALL-CAPS section headers. ATS parsers rely on clean section demarcations.")

    # -------------------------------------------------------------------
    # Dimension 2: Text Readability & Formatting (25 points max)
    # -------------------------------------------------------------------
    readability_score = 25.0

    # Non-ASCII / special noise characters check
    non_ascii_count = len(re.findall(r"[^\x00-\x7F]", text))
    if non_ascii_count > 30:
        readability_score -= 8.0
        warnings.append(f"Found {non_ascii_count} non-standard / special unicode characters. May cause font rendering noise.")
        recommendations.append("Replace custom symbol bullets (e.g. ❖, ➔) with standard bullet characters ('•' or '-').")

    # Character count / sparse check
    word_count = len(text.split())
    if word_count < 200:
        readability_score -= 12.0
        critical_issues.append("Resume content is sparse (< 200 words). High risk of automatic ATS rejection due to low content density.")
    elif word_count > 1200:
        readability_score -= 5.0
        warnings.append("Resume exceeds 1200 words. Recommended length is 450–800 words for optimal ATS parsing.")

    # -------------------------------------------------------------------
    # Dimension 3: Contact Information Compliance (25 points max)
    # -------------------------------------------------------------------
    contact_score = 25.0

    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    phone_match = re.search(r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
    linkedin_match = re.search(r"linkedin\.com/in/[\w\-]+", text, re.IGNORECASE)
    github_match = re.search(r"github\.com/[\w\-]+", text, re.IGNORECASE)

    if not email_match:
        contact_score -= 10.0
        critical_issues.append("No valid email address found in resume header.")
        recommendations.append("Include a clear email address at the top of your resume.")
    if not phone_match:
        contact_score -= 7.0
        warnings.append("No standard phone number format detected.")
        recommendations.append("Add a standard phone number (e.g., (555) 019-2834).")
    if not linkedin_match and not github_match:
        contact_score -= 4.0
        recommendations.append("Add a LinkedIn or GitHub profile URL to boost recruiter credibility.")

    # -------------------------------------------------------------------
    # Dimension 4: Keyword & Skill Density (25 points max)
    # -------------------------------------------------------------------
    density_score = 25.0

    extracted = match_skills(text)
    unique_skills = {s.canonical_name for s in extracted}
    
    if len(unique_skills) < 6:
        density_score -= 10.0
        warnings.append(f"Only {len(unique_skills)} technical skills identified. ATS systems filter out resumes with low skill keyword density.")
        recommendations.append("Add a dedicated TECHNICAL SKILLS section listing specific tools, languages, and frameworks.")
    elif len(unique_skills) >= 12:
        density_score = min(25.0, density_score + 2.0)

    # Action verb count
    words_lower = [w.lower().strip("•-*,.") for w in text.split()]
    verb_matches = [w for w in words_lower if w in ACTION_VERBS]
    if len(verb_matches) < 4:
        density_score -= 5.0
        recommendations.append("Begin work experience bullet points with strong action verbs (e.g., Architected, Spearheaded, Engineered).")

    # Quantified metric check
    metric_matches = re.findall(r"\b\d+%\b|\$\d+|\b\d+\s*(?:k|M|users|clients|ms|sec)\b", text, re.IGNORECASE)
    if len(metric_matches) < 2:
        density_score -= 5.0
        warnings.append("Few or no quantitative metrics found. Resumes with numbers and percentages score 40% higher in ATS screening.")
        recommendations.append("Quantify achievements with hard metrics (e.g., 'reduced API latency by 35%', 'handled 50k active users').")

    # Compute Overall Score
    overall_score = round(structure_score + readability_score + contact_score + density_score, 1)
    overall_score = max(0.0, min(100.0, overall_score))

    if overall_score >= 85.0:
        compliance_category = "EXCELLENT"
    elif overall_score >= 70.0:
        compliance_category = "GOOD"
    elif overall_score >= 50.0:
        compliance_category = "NEEDS_IMPROVEMENT"
    else:
        compliance_category = "CRITICAL"

    return ATSAnalysisResult(
        overall_score=overall_score,
        structure_score=round(structure_score, 1),
        readability_score=round(readability_score, 1),
        contact_score=round(contact_score, 1),
        density_score=round(density_score, 1),
        compliance_category=compliance_category,
        detected_sections=detected_sections,
        missing_essential_sections=missing_essential_sections,
        critical_issues=critical_issues,
        warnings=warnings,
        actionable_recommendations=recommendations,
    )
