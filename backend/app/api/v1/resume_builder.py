"""
backend/app/api/v1/resume_builder.py

Phase 35 — AI Resume Builder & Live ATS Optimization API Router.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import AnyAuthUser, get_current_tenant_id, get_current_user
from app.core.sanitizer import (
    format_untrusted_data_boundary,
    sanitize_prompt_input,
    verify_tenant_access,
)
from app.database import get_db
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.resume import Resume
from app.models.resume_builder import ResumeDraft, ResumeVersion
from app.schemas.resume_builder import (
    AIAssistRequest,
    MatchRequest,
    MatchResponse,
    ResumeDraftCreate,
    ResumeDraftResponse,
    ResumeDraftUpdate,
    ResumeVersionResponse,
    StructuredResumeContent,
)
from app.services.ai_service import get_ai_service
from app.services.audit_service import log_event
from app.services.bullet_rewriter import rewrite_bullet_point
from app.services.resume_builder_service import (
    compile_draft_to_text,
    compute_real_ats_match,
    generate_resume_pdf,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/resume-builder", tags=["AI Resume Builder"])


def _get_draft_or_404(
    db: Session, draft_id: str, current_user: AnyAuthUser, tenant_id: str
) -> ResumeDraft:
    """Helper to fetch a draft by ID/public_id and enforce tenant/user ownership security."""
    query = db.query(ResumeDraft)
    if draft_id.isdigit():
        draft = query.filter(ResumeDraft.id == int(draft_id)).first()
    else:
        draft = query.filter(ResumeDraft.public_id == draft_id).first()

    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume draft '{draft_id}' not found.",
        )

    # Security: Verify tenant isolation and owner access
    user_tenant = getattr(current_user, "tenant_id", "default_tenant")
    verify_tenant_access(user_tenant, draft.tenant_id)

    # Standard users can only access their own drafts unless they are admin/hr
    user_role = getattr(current_user, "role", "user")
    if user_role not in ("admin", "hr_manager", "recruiter") and draft.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have access to this resume draft.",
        )

    return draft


def _get_job_or_404(db: Session, job_id: str, tenant_id: str) -> Job:
    """Helper to fetch job and enforce tenant isolation."""
    query = db.query(Job)
    if job_id.isdigit():
        job = query.filter(Job.id == int(job_id)).first()
    else:
        job = query.filter(Job.public_id == job_id).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job '{job_id}' not found.",
        )

    job_tenant = getattr(job, "tenant_id", None)
    if job_tenant and job_tenant != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Target job belongs to another tenant.",
        )

    return job


def _format_draft_response(db: Session, draft: ResumeDraft) -> ResumeDraftResponse:
    content_dict = draft.get_content_dict()
    raw_md = compile_draft_to_text(content_dict)

    target_job_pub_id = None
    if draft.target_job_id:
        j = db.query(Job).filter(Job.id == draft.target_job_id).first()
        if j:
            target_job_pub_id = j.public_id

    try:
        struct_obj = StructuredResumeContent(**content_dict)
    except Exception:
        struct_obj = StructuredResumeContent()

    return ResumeDraftResponse(
        id=draft.public_id,
        title=draft.title,
        target_job_id=target_job_pub_id,
        candidate_id=str(draft.candidate_id) if draft.candidate_id else None,
        original_resume_id=str(draft.original_resume_id) if draft.original_resume_id else None,
        structured_content=struct_obj,
        raw_markdown=raw_md,
        created_at=draft.created_at,
        updated_at=draft.updated_at,
        versions_count=len(draft.versions),
    )


# ── 1. Create Resume Draft ────────────────────────────────────────────────

@router.post("", response_model=ResumeDraftResponse, status_code=status.HTTP_201_CREATED)
def create_resume_draft(
    payload: ResumeDraftCreate,
    current_user: AnyAuthUser,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
) -> ResumeDraftResponse:
    """
    Creates a new editable structured resume draft workspace.
    """
    user_tenant = getattr(current_user, "tenant_id", tenant_id or "default_tenant")

    target_job_db_id = None
    if payload.target_job_id:
        job = _get_job_or_404(db, payload.target_job_id, user_tenant)
        target_job_db_id = job.id

    content_dict = (
        payload.structured_content.model_dump()
        if payload.structured_content
        else StructuredResumeContent().model_dump()
    )

    draft = ResumeDraft(
        user_id=current_user.id,
        tenant_id=user_tenant,
        title=payload.title or "Untitled Resume Draft",
        target_job_id=target_job_db_id,
        structured_content_json=json.dumps(content_dict, default=str),
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)

    # Initial Version 1
    version = ResumeVersion(
        draft_id=draft.id,
        version_number=1,
        label="Initial Draft",
        structured_content_json=draft.structured_content_json,
    )
    db.add(version)
    db.commit()

    log_event(
        db=db,
        actor_id=current_user.id,
        actor_email=current_user.email,
        event_type="resume_builder.create",
        summary=f"Created resume draft '{draft.public_id}'",
        resource_type="resume_draft",
        resource_id=draft.public_id,
        outcome="success",
    )

    return _format_draft_response(db, draft)


# ── 2. List Resume Drafts ─────────────────────────────────────────────────

@router.get("", response_model=List[ResumeDraftResponse])
def list_resume_drafts(
    current_user: AnyAuthUser,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
) -> List[ResumeDraftResponse]:
    """
    Lists all active resume drafts owned by the current user.
    """
    user_tenant = getattr(current_user, "tenant_id", tenant_id or "default_tenant")
    drafts = (
        db.query(ResumeDraft)
        .filter(ResumeDraft.user_id == current_user.id, ResumeDraft.tenant_id == user_tenant)
        .order_by(ResumeDraft.updated_at.desc())
        .all()
    )
    return [_format_draft_response(db, d) for d in drafts]


# ── 3. Get Resume Draft ───────────────────────────────────────────────────

@router.get("/{draft_id}", response_model=ResumeDraftResponse)
def get_resume_draft(
    draft_id: str,
    current_user: AnyAuthUser,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
) -> ResumeDraftResponse:
    """
    Retrieves a specific resume draft workspace by ID.
    """
    draft = _get_draft_or_404(db, draft_id, current_user, tenant_id)
    return _format_draft_response(db, draft)


# ── 4. Patch / Save Draft ─────────────────────────────────────────────────

@router.patch("/{draft_id}", response_model=ResumeDraftResponse)
def update_resume_draft(
    draft_id: str,
    payload: ResumeDraftUpdate,
    current_user: AnyAuthUser,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
) -> ResumeDraftResponse:
    """
    Updates resume draft content, title, or target job selection (Autosave / Draft Save).
    """
    draft = _get_draft_or_404(db, draft_id, current_user, tenant_id)

    if payload.title is not None:
        draft.title = payload.title

    if payload.target_job_id is not None:
        if payload.target_job_id == "":
            draft.target_job_id = None
        else:
            job = _get_job_or_404(db, payload.target_job_id, draft.tenant_id)
            draft.target_job_id = job.id

    if payload.structured_content is not None:
        content_dict = payload.structured_content.model_dump()
        draft.set_content_dict(content_dict)
        draft.raw_markdown = compile_draft_to_text(content_dict)

    db.commit()
    db.refresh(draft)

    log_event(
        db=db,
        actor_id=current_user.id,
        actor_email=current_user.email,
        event_type="resume_builder.update",
        summary=f"Updated resume draft '{draft.public_id}'",
        resource_type="resume_draft",
        resource_id=draft.public_id,
        outcome="success",
    )

    return _format_draft_response(db, draft)


# ── 5. Real-Time ATS Job Match & Before/After Comparison ─────────────────

@router.post("/{draft_id}/match", response_model=MatchResponse)
def calculate_resume_match(
    draft_id: str,
    current_user: AnyAuthUser,
    payload: Optional[MatchRequest] = None,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
) -> MatchResponse:
    """
    Calculates real 6-signal hybrid ATS match score against target job using existing matching engine.
    Supports optional Before/After comparison against a previous version.
    """
    draft = _get_draft_or_404(db, draft_id, current_user, tenant_id)

    job_id_str = payload.job_id if (payload and payload.job_id) else (str(draft.target_job_id) if draft.target_job_id else None)
    if not job_id_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No target job selected for match calculation. Please select a job.",
        )

    job = _get_job_or_404(db, job_id_str, draft.tenant_id)

    content_dict = (
        payload.structured_content.model_dump()
        if (payload and payload.structured_content)
        else draft.get_content_dict()
    )

    prev_score = None
    if payload and payload.compare_version_id:
        v = (
            db.query(ResumeVersion)
            .filter(ResumeVersion.draft_id == draft.id)
            .filter(
                (ResumeVersion.public_id == payload.compare_version_id)
                | (ResumeVersion.id == (int(payload.compare_version_id) if payload.compare_version_id.isdigit() else 0))
            )
            .first()
        )
        if v:
            try:
                v_content = json.loads(v.structured_content_json)
                v_match = compute_real_ats_match(v_content, job)
                prev_score = v_match["match_score"]
            except Exception as err:
                logger.warning(f"Failed to calculate previous version score: {err}")

    res = compute_real_ats_match(content_dict, job, previous_score=prev_score)

    return MatchResponse(
        match_score=res["match_score"],
        required_coverage=res["required_coverage"],
        preferred_coverage=res["preferred_coverage"],
        semantic_similarity=res["semantic_similarity"],
        lexical_similarity=res["lexical_similarity"],
        experience_depth=res["experience_depth"],
        domain_alignment=res["domain_alignment"],
        matched_skills=res["matched_skills"],
        missing_required_skills=res["missing_required_skills"],
        missing_preferred_skills=res["missing_preferred_skills"],
        score_breakdown=res["score_breakdown"],
        suggestions=res["suggestions"],
        before_score=res["before_score"],
        after_score=res["after_score"],
        score_delta=res["score_delta"],
    )


# ── 6. Save Resume Version Snapshot ──────────────────────────────────────

@router.post("/{draft_id}/versions", response_model=ResumeVersionResponse, status_code=status.HTTP_201_CREATED)
def create_resume_version(
    draft_id: str,
    current_user: AnyAuthUser,
    label: Optional[str] = Query(None, description="Optional custom version label"),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
) -> ResumeVersionResponse:
    """
    Creates a new immutable snapshot version of the current draft.
    """
    draft = _get_draft_or_404(db, draft_id, current_user, tenant_id)

    existing_count = db.query(ResumeVersion).filter(ResumeVersion.draft_id == draft.id).count()
    next_ver = existing_count + 1

    version = ResumeVersion(
        draft_id=draft.id,
        version_number=next_ver,
        label=label or f"Version {next_ver}",
        structured_content_json=draft.structured_content_json,
    )
    db.add(version)
    db.commit()
    db.refresh(version)

    log_event(
        db=db,
        actor_id=current_user.id,
        actor_email=current_user.email,
        event_type="resume_builder.version_save",
        summary=f"Saved version {version.version_number} for draft '{draft.public_id}'",
        resource_type="resume_draft",
        resource_id=draft.public_id,
        outcome="success",
    )

    try:
        s_obj = StructuredResumeContent(**json.loads(version.structured_content_json))
    except Exception:
        s_obj = StructuredResumeContent()

    return ResumeVersionResponse(
        id=version.public_id,
        version_number=version.version_number,
        label=version.label,
        structured_content=s_obj,
        created_at=version.created_at,
    )


# ── 7. List Resume Versions ───────────────────────────────────────────────

@router.get("/{draft_id}/versions", response_model=List[ResumeVersionResponse])
def list_resume_versions(
    draft_id: str,
    current_user: AnyAuthUser,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
) -> List[ResumeVersionResponse]:
    """
    Lists all saved snapshot versions for a resume draft.
    """
    draft = _get_draft_or_404(db, draft_id, current_user, tenant_id)

    versions = (
        db.query(ResumeVersion)
        .filter(ResumeVersion.draft_id == draft.id)
        .order_by(ResumeVersion.version_number.desc())
        .all()
    )

    result = []
    for v in versions:
        try:
            s_obj = StructuredResumeContent(**json.loads(v.structured_content_json))
        except Exception:
            s_obj = StructuredResumeContent()
        result.append(
            ResumeVersionResponse(
                id=v.public_id,
                version_number=v.version_number,
                label=v.label,
                structured_content=s_obj,
                created_at=v.created_at,
            )
        )

    return result


# ── 8. Restore Resume Version ─────────────────────────────────────────────

@router.post("/{draft_id}/restore/{version_id}", response_model=ResumeDraftResponse)
def restore_resume_version(
    draft_id: str,
    version_id: str,
    current_user: AnyAuthUser,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
) -> ResumeDraftResponse:
    """
    Restores a previous snapshot version into the active draft without destroying history.
    """
    draft = _get_draft_or_404(db, draft_id, current_user, tenant_id)

    query = db.query(ResumeVersion).filter(ResumeVersion.draft_id == draft.id)
    if version_id.isdigit():
        version = query.filter(ResumeVersion.id == int(version_id)).first()
    else:
        version = query.filter(ResumeVersion.public_id == version_id).first()

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version '{version_id}' not found for this draft.",
        )

    draft.structured_content_json = version.structured_content_json
    draft.raw_markdown = compile_draft_to_text(draft.get_content_dict())
    db.commit()
    db.refresh(draft)

    log_event(
        db=db,
        actor_id=current_user.id,
        actor_email=current_user.email,
        event_type="resume_builder.version_restore",
        summary=f"Restored version {version.version_number} into draft '{draft.public_id}'",
        resource_type="resume_draft",
        resource_id=draft.public_id,
        outcome="success",
    )

    return _format_draft_response(db, draft)


# ── 9. Export PDF Endpoint ────────────────────────────────────────────────

@router.get("/{draft_id}/export-pdf")
@router.post("/{draft_id}/export-pdf")
def export_resume_pdf(
    draft_id: str,
    current_user: AnyAuthUser,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
) -> Response:
    """
    Generates and downloads a clean, ATS-compliant PDF document of the saved resume draft.
    """
    draft = _get_draft_or_404(db, draft_id, current_user, tenant_id)
    content_dict = draft.get_content_dict()

    pdf_bytes = generate_resume_pdf(content_dict)

    log_event(
        db=db,
        actor_id=current_user.id,
        actor_email=current_user.email,
        event_type="resume_builder.export_pdf",
        summary=f"Exported PDF for draft '{draft.public_id}'",
        resource_type="resume_draft",
        resource_id=draft.public_id,
        outcome="success",
    )

    filename = f"{draft.title.replace(' ', '_')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── 10. AI Resume Assistant Endpoint ──────────────────────────────────────

@router.post("/{draft_id}/ai-assist")
def ai_resume_builder_assistant(
    draft_id: str,
    payload: AIAssistRequest,
    current_user: AnyAuthUser,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
) -> dict:
    """
    Provides AI suggestions (Professional Summary, Bullet Improvement, Project, Skill, Review)
    grounded strictly in draft context and target job requirements.
    """
    draft = _get_draft_or_404(db, draft_id, current_user, tenant_id)
    content_dict = draft.get_content_dict()

    job = None
    if payload.target_job_id or draft.target_job_id:
        j_id = payload.target_job_id or str(draft.target_job_id)
        job = _get_job_or_404(db, j_id, draft.tenant_id)

    ai_service = get_ai_service()

    job_title = job.title if job else "Target Position"
    job_desc = job.description if (job and job.description) else ""

    sanitized_context = sanitize_prompt_input(payload.context_text or "", max_length=2000)
    job_boundary = format_untrusted_data_boundary(job_desc, label="JOB_DESCRIPTION", max_length=1500)
    draft_boundary = format_untrusted_data_boundary(
        compile_draft_to_text(content_dict), label="DRAFT_RESUME", max_length=2000
    )

    sys_prompt = (
        "You are an AI resume optimization assistant.\n"
        "STRICT FACTUAL RULE: Only reference skills, experience, and background present in the draft.\n"
        "Do NOT invent unsupplied companies, metrics, certifications, or technologies."
    )

    if payload.assist_type == "summary":
        prompt = (
            f"Generate a professional summary for a candidate targeting role '{job_title}'.\n\n"
            f"{job_boundary}\n\n"
            f"{draft_boundary}\n\n"
            f"Context snippet: {sanitized_context}\n"
            f"Return JSON with 'summary' string."
        )
        res = ai_service.generate_json(
            prompt, schema_description='{"summary": "string"}', system_prompt=sys_prompt
        )
        res["label"] = "AI Generated — Verify Before Use"
        return res

    elif payload.assist_type == "bullet":
        rewrite_res = rewrite_bullet_point(
            bullet=sanitized_context or "Led engineering team on backend services.",
            target_job_title=job_title,
        )
        return {
            "original_bullet": rewrite_res.original_bullet,
            "optimized_bullet": rewrite_res.optimized_bullet,
            "key_changes": rewrite_res.key_changes,
            "placeholders_needed": rewrite_res.placeholders_needed,
            "label": "AI Generated — Verify Before Use",
        }

    elif payload.assist_type == "keywords":
        req_skills = [r.skill_name for r in (job.requirements if job else []) if r.is_required]
        pref_skills = [r.skill_name for r in (job.requirements if job else []) if not r.is_required]
        return {
            "suggested_required_keywords": req_skills,
            "suggested_preferred_keywords": pref_skills,
            "recommendation": "Incorporate these canonical keywords into your Skills or Experience bullets.",
            "label": "AI Generated — Verify Before Use",
        }

    else:
        # Default review / general assist
        prompt = (
            f"Review this resume draft for alignment with job '{job_title}'.\n\n"
            f"{job_boundary}\n\n"
            f"{draft_boundary}\n\n"
            f"Return JSON with 'strengths': ['string'], 'improvement_tips': ['string']."
        )
        res = ai_service.generate_json(
            prompt,
            schema_description='{"strengths": ["string"], "improvement_tips": ["string"]}',
            system_prompt=sys_prompt,
        )
        res["label"] = "AI Generated — Verify Before Use"
        return res
