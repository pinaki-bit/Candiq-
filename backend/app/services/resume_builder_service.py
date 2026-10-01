"""
backend/app/services/resume_builder_service.py

Live Candidate Resume Builder & Real-Time Match Simulator.
Phase 35 — REAL 6-Signal ATS/Job Match Optimization Engine & PDF Exporter.
"""

from __future__ import annotations

import io
import json
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer

from app.models.job import Job
from app.services.matching_service import (
    calculate_lexical_similarity,
    compute_hybrid_match,
    extract_job_skills,
)
from app.services.skill_service import match_skills

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


def compile_draft_to_text(structured_content: Dict[str, Any]) -> str:
    """
    Compiles structured resume JSON sections into a continuous plain text / markdown string
    for NLP extraction and 6-signal hybrid matching.
    """
    if not isinstance(structured_content, dict):
        return ""

    lines: List[str] = []

    # Personal Info
    pinfo = structured_content.get("personal_info", {})
    if isinstance(pinfo, dict):
        full_name = pinfo.get("full_name", "").strip()
        if full_name:
            lines.append(f"# {full_name}")
        contacts = [
            str(pinfo.get(k, "")).strip()
            for k in ["email", "phone", "location", "linkedin", "github", "website"]
            if pinfo.get(k)
        ]
        if contacts:
            lines.append(" | ".join(contacts))
        lines.append("")

    # Summary
    summary = structured_content.get("summary", "")
    if summary:
        lines.append("## PROFESSIONAL SUMMARY")
        lines.append(str(summary).strip())
        lines.append("")

    # Skills
    skills = structured_content.get("skills", [])
    if skills:
        lines.append("## TECHNICAL SKILLS")
        if isinstance(skills, list):
            lines.append(", ".join([str(s) for s in skills if s]))
        else:
            lines.append(str(skills))
        lines.append("")

    # Experience
    exp_list = structured_content.get("experience", [])
    if exp_list and isinstance(exp_list, list):
        lines.append("## WORK EXPERIENCE")
        for exp in exp_list:
            if not isinstance(exp, dict):
                continue
            title = exp.get("title", "")
            company = exp.get("company", "")
            loc = exp.get("location", "")
            s_date = exp.get("start_date", "")
            e_date = "Present" if exp.get("is_current") else exp.get("end_date", "")
            dates = f"({s_date} - {e_date})" if s_date or e_date else ""
            lines.append(f"### {title} at {company} {loc} {dates}".strip())
            bullets = exp.get("bullets", [])
            if isinstance(bullets, list):
                for b in bullets:
                    if b:
                        lines.append(f"- {b}")
            lines.append("")

    # Education
    edu_list = structured_content.get("education", [])
    if edu_list and isinstance(edu_list, list):
        lines.append("## EDUCATION")
        for edu in edu_list:
            if not isinstance(edu, dict):
                continue
            inst = edu.get("institution", "")
            deg = edu.get("degree", "")
            field_name = edu.get("field_of_study", "")
            s_date = edu.get("start_date", "")
            e_date = edu.get("end_date", "")
            dates = f"({s_date} - {e_date})" if s_date or e_date else ""
            lines.append(f"- {deg} in {field_name}, {inst} {dates}".strip())
        lines.append("")

    # Projects
    proj_list = structured_content.get("projects", [])
    if proj_list and isinstance(proj_list, list):
        lines.append("## PROJECTS")
        for proj in proj_list:
            if not isinstance(proj, dict):
                continue
            name = proj.get("name", "")
            desc = proj.get("description", "")
            techs = proj.get("technologies", [])
            tech_str = f" (Technologies: {', '.join(techs)})" if techs else ""
            lines.append(f"- {name}: {desc}{tech_str}".strip())
        lines.append("")

    # Certifications
    certs = structured_content.get("certifications", [])
    if certs and isinstance(certs, list):
        lines.append("## CERTIFICATIONS")
        for c in certs:
            if isinstance(c, dict):
                lines.append(f"- {c.get('name', '')} ({c.get('issuer', '')}, {c.get('date', '')})".strip())
        lines.append("")

    # Achievements
    achievements = structured_content.get("achievements", [])
    if achievements and isinstance(achievements, list):
        lines.append("## ACHIEVEMENTS")
        for a in achievements:
            if isinstance(a, dict):
                lines.append(f"- {a.get('title', '')}: {a.get('description', '')}".strip())
        lines.append("")

    return "\n".join(lines).strip()


def compute_real_ats_match(
    structured_content: Dict[str, Any],
    job: Job,
    previous_score: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Computes real 6-signal hybrid ATS match using the production matching pipeline:
      Required Coverage (35%), Preferred Coverage (15%), Semantic Similarity (25%),
      Lexical Token Overlap (10%), Experience Depth (10%), Domain Alignment (5%).
    """
    resume_text = compile_draft_to_text(structured_content)

    # 1. NLP Skill extraction
    extracted = match_skills(resume_text)

    # 2. Extract job skills
    required_skills, preferred_skills = extract_job_skills(job.requirements)

    # 3. Compute 6-signal hybrid match
    match = compute_hybrid_match(
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        candidate_skills=extracted,
        resume_text=resume_text,
        job_description=job.description or "",
        predicted_domain=None,
        job_domain=job.domain,
    )

    signals = match.score_breakdown.get("signal_scores", {})
    req_cov = signals.get("required_coverage", match.required_coverage)
    pref_cov = signals.get("preferred_coverage", match.preferred_coverage)
    sem_sim = signals.get("semantic_similarity", 0.0)
    lex_sim = signals.get("lexical_similarity", 0.0)
    exp_dep = signals.get("experience_depth", 0.0)
    dom_ali = signals.get("domain_alignment", 0.0)

    # Missing preferred skills calculation
    all_pref_names = [p[0] for p in preferred_skills]
    missing_pref = [p for p in all_pref_names if p not in match.matched_preferred]

    # Deterministic live feedback suggestions
    suggestions: List[str] = []

    req_count = len(required_skills)
    matched_req_count = len(match.matched_required)
    if req_count > 0:
        suggestions.append(f"Your resume currently covers {matched_req_count}/{req_count} required skills.")

    if match.missing_required:
        suggestions.append(f"{match.missing_required[0]} is missing from required skills.")
        if len(match.missing_required) > 1:
            suggestions.append(f"Adding evidence for {match.missing_required[1]} may improve required coverage.")
    else:
        suggestions.append("All required job skills are covered by your resume!")

    if match.matched_required:
        suggestions.append(f"{match.matched_required[0]} is already covered.")

    # Calculate score delta if previous score is supplied
    score_delta = None
    if previous_score is not None:
        score_delta = round(match.combined_match - previous_score, 2)

    return {
        "match_score": match.combined_match,
        "required_coverage": req_cov,
        "preferred_coverage": pref_cov,
        "semantic_similarity": sem_sim,
        "lexical_similarity": lex_sim,
        "experience_depth": exp_dep,
        "domain_alignment": dom_ali,
        "matched_skills": match.matched_required + match.matched_preferred,
        "missing_required_skills": match.missing_required,
        "missing_preferred_skills": missing_pref,
        "score_breakdown": match.score_breakdown,
        "suggestions": suggestions,
        "before_score": previous_score,
        "after_score": match.combined_match,
        "score_delta": score_delta,
    }


def generate_resume_pdf(structured_content: Dict[str, Any]) -> bytes:
    """
    Generates a clean, ATS-compliant PDF document from structured resume data.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0F172A"),
    )
    contact_style = ParagraphStyle(
        "ContactInfo",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#475569"),
    )
    section_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#1D4ED8"),
        spaceBefore=8,
        spaceAfter=3,
    )
    body_style = ParagraphStyle(
        "BodyCustom",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#1E293B"),
    )

    story = []

    # Personal Info
    pinfo = structured_content.get("personal_info", {})
    if isinstance(pinfo, dict) and pinfo.get("full_name"):
        story.append(Paragraph(pinfo["full_name"], title_style))
        contacts = [
            str(pinfo.get(k, "")).strip()
            for k in ["email", "phone", "location", "linkedin", "github", "website"]
            if pinfo.get(k)
        ]
        if contacts:
            story.append(Paragraph(" | ".join(contacts), contact_style))
        story.append(Spacer(1, 8))

    # Summary
    summary = structured_content.get("summary")
    if summary:
        story.append(Paragraph("PROFESSIONAL SUMMARY", section_style))
        story.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor("#CBD5E1"), spaceAfter=5))
        story.append(Paragraph(str(summary), body_style))
        story.append(Spacer(1, 8))

    # Technical Skills
    skills = structured_content.get("skills", [])
    if skills:
        story.append(Paragraph("TECHNICAL SKILLS", section_style))
        story.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor("#CBD5E1"), spaceAfter=5))
        skill_str = ", ".join(skills) if isinstance(skills, list) else str(skills)
        story.append(Paragraph(skill_str, body_style))
        story.append(Spacer(1, 8))

    # Work Experience
    experience = structured_content.get("experience", [])
    if experience and isinstance(experience, list):
        story.append(Paragraph("WORK EXPERIENCE", section_style))
        story.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor("#CBD5E1"), spaceAfter=5))
        for exp in experience:
            if not isinstance(exp, dict):
                continue
            title = exp.get("title", "")
            company = exp.get("company", "")
            s_date = exp.get("start_date", "")
            e_date = "Present" if exp.get("is_current") else exp.get("end_date", "")
            dates = f"({s_date} - {e_date})" if s_date or e_date else ""
            header_text = f"<b>{title}</b> — <i>{company}</i> {dates}".strip()
            story.append(Paragraph(header_text, body_style))
            bullets = exp.get("bullets", [])
            if isinstance(bullets, list):
                for b in bullets:
                    if b:
                        story.append(Paragraph(f"• {b}", body_style))
            story.append(Spacer(1, 5))

    # Education
    education = structured_content.get("education", [])
    if education and isinstance(education, list):
        story.append(Paragraph("EDUCATION", section_style))
        story.append(HRFlowable(width="100%", thickness=0.75, color=colors.HexColor("#CBD5E1"), spaceAfter=5))
        for edu in education:
            if not isinstance(edu, dict):
                continue
            deg = edu.get("degree", "")
            inst = edu.get("institution", "")
            s_date = edu.get("start_date", "")
            e_date = edu.get("end_date", "")
            dates = f"({s_date} - {e_date})" if s_date or e_date else ""
            story.append(Paragraph(f"<b>{deg}</b>, {inst} {dates}".strip(), body_style))
        story.append(Spacer(1, 5))

    doc.build(story)
    return buffer.getvalue()


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
