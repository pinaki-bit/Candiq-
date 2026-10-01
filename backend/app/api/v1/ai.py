"""
backend/app/api/v1/ai.py

Phase 34 — LLM Intelligence Layer API Router.

Endpoints:
  POST /api/v1/ai/candidates/{candidate_id}/explanation        — AI Candidate Explanation
  POST /api/v1/ai/candidates/{candidate_id}/interview-questions — Interview Question Generator
  POST /api/v1/ai/candidates/{candidate_id}/cover-letter       — Tailored Cover Letter Generator
  POST /api/v1/ai/resumes/{resume_id}/rewrite-bullets          — Resume Bullet Point Improvement
"""

import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import AnyAuthUser, get_current_tenant_id
from app.core.sanitizer import (
    format_untrusted_data_boundary,
    sanitize_prompt_input,
    verify_tenant_access,
)
from app.database import get_db
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.resume import Resume
from app.models.screening import ScreeningResult
from app.services.ai_service import get_ai_service
from app.services.audit_service import log_event
from app.services.bullet_rewriter import rewrite_bullet_point
from app.services.cover_letter_service import generate_cover_letter
from app.services.interview_service import generate_interview_kit

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ai", tags=["AI Intelligence Layer"])


# ── Schemas for AI Requests ───────────────────────────────────────────────

class CoverLetterRequest(BaseModel):
    company_name: Optional[str] = "Target Company"
    tone: Optional[str] = "PROFESSIONAL"


class BulletRewriteRequest(BaseModel):
    bullet: str = Field(..., min_length=5, max_length=2000, description="Resume bullet text to improve")
    mode: Optional[str] = Field("STAR", description="Rewrite mode: STAR, TECHNICAL, or ATS")
    target_job_title: Optional[str] = None
    target_skills: Optional[List[str]] = None


# ── Helper resolution functions ──────────────────────────────────────────

def _get_candidate_by_id_or_public_id(db: Session, candidate_id: str) -> Candidate:
    """Fetch candidate by public_id or integer ID."""
    cand = db.query(Candidate).filter(Candidate.public_id == candidate_id).first()
    if not cand and candidate_id.isdigit():
        cand = db.query(Candidate).filter(Candidate.id == int(candidate_id)).first()
    if not cand:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found.")
    return cand


def _get_resume_by_id_or_public_id(db: Session, resume_id: str) -> Resume:
    """Fetch resume by public_id or integer ID."""
    res = db.query(Resume).filter(Resume.public_id == resume_id).first()
    if not res and resume_id.isdigit():
        res = db.query(Resume).filter(Resume.id == int(resume_id)).first()
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found.")
    return res


# ── 1. AI Candidate Explanation Endpoint ──────────────────────────────────

@router.post("/candidates/{candidate_id}/explanation")
def generate_candidate_explanation(
    candidate_id: str,
    current_user: AnyAuthUser,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
) -> dict:
    """
    Generates an AI Candidate Explanation grounded strictly in real candidate resume text,
    extracted skills, and deterministic screening result breakdown.
    """
    cand = _get_candidate_by_id_or_public_id(db, candidate_id)

    # Tenant access isolation check
    user_tenant = getattr(current_user, "tenant_id", "default_tenant")
    verify_tenant_access(user_tenant, tenant_id)

    # Fetch latest screening result and resume
    sr = (
        db.query(ScreeningResult)
        .filter(ScreeningResult.candidate_id == cand.id)
        .order_by(ScreeningResult.screened_at.desc())
        .first()
    )

    resume = (
        db.query(Resume)
        .filter(Resume.candidate_id == cand.id)
        .order_by(Resume.uploaded_at.desc())
        .first()
    )

    job = db.query(Job).filter(Job.id == sr.job_id).first() if sr else None

    resume_text = resume.extracted_text if (resume and resume.extracted_text) else "N/A"
    job_title = job.title if job else "Target Position"
    job_desc = job.description if (job and job.description) else "N/A"

    matched_skills = json.loads(sr.matched_required_skills or "[]") if sr else []
    missing_skills = json.loads(sr.missing_required_skills or "[]") if sr else []
    score_breakdown = sr.score_breakdown if (sr and sr.score_breakdown) else "{}"

    # Prompt injection protection & boundary wrapping
    resume_boundary = format_untrusted_data_boundary(resume_text, label="CANDIDATE_RESUME", max_length=3000)
    job_boundary = format_untrusted_data_boundary(job_desc, label="JOB_DESCRIPTION", max_length=2000)

    ai_service = get_ai_service()

    system_prompt = (
        "You are an AI hiring intelligence analyst. Generate a factual candidate match explanation.\n"
        "FACTUAL RULE: Only reference facts present in candidate data or job description. "
        "Do NOT invent unsupplied skills, degrees, or qualifications."
    )

    prompt = (
        f"Target Job Title: {job_title}\n"
        f"Deterministic Screening Score: {sr.relevance_score if sr else 'N/A'}%\n"
        f"Matched Skills: {', '.join(matched_skills)}\n"
        f"Missing Skills: {', '.join(missing_skills)}\n"
        f"Score Breakdown: {score_breakdown}\n\n"
        f"{job_boundary}\n\n"
        f"{resume_boundary}\n\n"
        f"Generate JSON output containing summary, matching_reasons, missing_requirements, "
        f"strengths, concerns, evidence, and explanation."
    )

    schema_desc = (
        '{\n'
        '  "summary": "string",\n'
        '  "matching_reasons": ["string"],\n'
        '  "missing_requirements": ["string"],\n'
        '  "strengths": ["string"],\n'
        '  "concerns": ["string"],\n'
        '  "evidence": ["string"],\n'
        '  "explanation": "string"\n'
        '}'
    )

    explanation_data = ai_service.generate_json(prompt, schema_description=schema_desc, system_prompt=system_prompt)

    # Attach deterministic screening values to guarantee zero fabrication
    explanation_data["candidate_id"] = cand.public_id
    explanation_data["deterministic_screening_score"] = sr.relevance_score if sr else None
    explanation_data["ood_status"] = resume.ood_status if resume else None
    explanation_data["label"] = "AI Generated — Verify Before Use"

    # Audit event logging
    log_event(
        db=db,
        actor_id=current_user.id,
        actor_email=current_user.email,
        event_type="ai.candidate_explanation",
        summary=f"Generated AI explanation for candidate {cand.public_id}",
        resource_type="candidate",
        resource_id=cand.public_id,
        outcome="success",
    )

    return explanation_data


# ── 2. AI Interview Question Generator Endpoint ───────────────────────────

@router.post("/candidates/{candidate_id}/interview-questions")
def generate_candidate_interview_questions(
    candidate_id: str,
    current_user: AnyAuthUser,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
) -> dict:
    """
    Generates role-specific 5-category interview questions based on candidate background and skill gaps.
    """
    cand = _get_candidate_by_id_or_public_id(db, candidate_id)

    user_tenant = getattr(current_user, "tenant_id", "default_tenant")
    verify_tenant_access(user_tenant, tenant_id)

    sr = (
        db.query(ScreeningResult)
        .filter(ScreeningResult.candidate_id == cand.id)
        .order_by(ScreeningResult.screened_at.desc())
        .first()
    )
    resume = (
        db.query(Resume)
        .filter(Resume.candidate_id == cand.id)
        .order_by(Resume.uploaded_at.desc())
        .first()
    )
    job = db.query(Job).filter(Job.id == sr.job_id).first() if sr else None

    job_title = job.title if job else "Software Engineer"
    candidate_skills = json.loads(sr.matched_required_skills or "[]") if sr else []
    missing_skills = json.loads(sr.missing_required_skills or "[]") if sr else []
    resume_text = resume.extracted_text if (resume and resume.extracted_text) else ""

    kit_result = generate_interview_kit(
        job_title=job_title,
        candidate_skills=candidate_skills,
        missing_skills=missing_skills,
        resume_text=sanitize_prompt_input(resume_text, max_length=2000),
        job_description=sanitize_prompt_input(job.description if job else "", max_length=2000),
    )

    questions_list = [
        {
            "question_id": q.question_id,
            "category": q.category,
            "question": q.question,
            "why_this_question": q.why_this_question,
            "expected_key_points": q.expected_key_points,
            "difficulty": q.difficulty,
        }
        for q in kit_result.questions
    ]

    log_event(
        db=db,
        actor_id=current_user.id,
        actor_email=current_user.email,
        event_type="ai.interview_questions",
        summary=f"Generated AI interview questions for candidate {cand.public_id}",
        resource_type="candidate",
        resource_id=cand.public_id,
        outcome="success",
    )

    return {
        "candidate_id": cand.public_id,
        "job_title": kit_result.job_title,
        "questions": questions_list,
        "label": "AI Generated — Verify Before Use",
        "_metadata": {
            "tokens_used": kit_result.tokens_used,
            "estimated_cost_usd": kit_result.estimated_cost_usd,
            "guardrail_warnings": kit_result.guardrail_warnings,
        }
    }


# ── 3. AI Cover Letter Generator Endpoint ─────────────────────────────────

@router.post("/candidates/{candidate_id}/cover-letter")
def generate_candidate_cover_letter(
    candidate_id: str,
    payload: CoverLetterRequest,
    current_user: AnyAuthUser,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
) -> dict:
    """
    Generates a tailored cover letter draft using candidate background and target job requirements.
    """
    cand = _get_candidate_by_id_or_public_id(db, candidate_id)

    user_tenant = getattr(current_user, "tenant_id", "default_tenant")
    verify_tenant_access(user_tenant, tenant_id)

    sr = (
        db.query(ScreeningResult)
        .filter(ScreeningResult.candidate_id == cand.id)
        .order_by(ScreeningResult.screened_at.desc())
        .first()
    )
    resume = (
        db.query(Resume)
        .filter(Resume.candidate_id == cand.id)
        .order_by(Resume.uploaded_at.desc())
        .first()
    )
    job = db.query(Job).filter(Job.id == sr.job_id).first() if sr else None

    job_title = job.title if job else "Target Role"
    company_name = payload.company_name or "Target Company"
    cand_name = cand.display_name or "Candidate"
    skills = json.loads(sr.matched_required_skills or "[]") if sr else []
    resume_text = resume.extracted_text if (resume and resume.extracted_text) else ""

    cover_res = generate_cover_letter(
        job_title=job_title,
        company_name=company_name,
        candidate_name=cand_name,
        candidate_skills=skills,
        candidate_text=sanitize_prompt_input(resume_text, max_length=2000),
        job_description=sanitize_prompt_input(job.description if job else "", max_length=2000),
        tone=payload.tone or "PROFESSIONAL",
    )

    log_event(
        db=db,
        actor_id=current_user.id,
        actor_email=current_user.email,
        event_type="ai.cover_letter",
        summary=f"Generated AI cover letter draft for candidate {cand.public_id}",
        resource_type="candidate",
        resource_id=cand.public_id,
        outcome="success",
    )

    return {
        "candidate_id": cand.public_id,
        "salutation": cover_res.salutation,
        "opening_hook": cover_res.opening_hook,
        "core_value_proposition": cover_res.core_value_proposition,
        "company_alignment_paragraph": cover_res.company_alignment_paragraph,
        "closing_call_to_action": cover_res.closing_call_to_action,
        "full_cover_letter": cover_res.full_cover_letter,
        "tone_used": cover_res.tone_used,
        "label": "AI Generated Draft — Verify Before Use",
        "_metadata": {
            "tokens_used": cover_res.tokens_used,
            "estimated_cost_usd": cover_res.estimated_cost_usd,
            "guardrail_warnings": cover_res.guardrail_warnings,
        }
    }


# ── 4. AI Resume Bullet Point Improvement Endpoint ────────────────────────

@router.post("/resumes/{resume_id}/rewrite-bullets")
def rewrite_resume_bullet(
    resume_id: str,
    payload: BulletRewriteRequest,
    current_user: AnyAuthUser,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
) -> dict:
    """
    Improves a resume experience bullet point while preserving factual content and inserting metric placeholders.
    """
    res = _get_resume_by_id_or_public_id(db, resume_id)

    user_tenant = getattr(current_user, "tenant_id", "default_tenant")
    verify_tenant_access(user_tenant, tenant_id)

    sanitized_bullet = sanitize_prompt_input(payload.bullet, max_length=1500)

    rewrite_res = rewrite_bullet_point(
        bullet=sanitized_bullet,
        mode=payload.mode or "STAR",
        target_job_title=payload.target_job_title,
        target_skills=payload.target_skills,
    )

    log_event(
        db=db,
        actor_id=current_user.id,
        actor_email=current_user.email,
        event_type="ai.rewrite_bullets",
        summary=f"Rewrote bullet point for resume {res.public_id}",
        resource_type="resume",
        resource_id=res.public_id,
        outcome="success",
    )

    return {
        "resume_id": res.public_id,
        "original_bullet": rewrite_res.original_bullet,
        "optimized_bullet": rewrite_res.optimized_bullet,
        "mode": rewrite_res.mode,
        "key_changes": rewrite_res.key_changes,
        "action_verb_used": rewrite_res.action_verb_used,
        "placeholders_needed": rewrite_res.placeholders_needed,
        "label": "AI Generated — Verify Before Use",
        "_metadata": {
            "tokens_used": rewrite_res.tokens_used,
            "estimated_cost_usd": rewrite_res.estimated_cost_usd,
            "guardrail_warnings": rewrite_res.guardrail_warnings,
        }
    }
