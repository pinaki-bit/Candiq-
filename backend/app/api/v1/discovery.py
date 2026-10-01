"""
backend/app/api/v1/discovery.py

Phase 36 — Advanced Candidate Discovery, Semantic Search & Hiring Intelligence API Router.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
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
from app.schemas.discovery import (
    CandidateCompareRequest,
    CandidateCompareResponse,
    DiscoverySearchResponse,
    JobCandidateDiscoveryResponse,
    SimilarCandidateResponse,
    SimilarJobResponse,
)
from app.services.audit_service import log_event
from app.services.discovery_service import (
    compare_candidates as compare_candidates_service,
    find_similar_candidates as find_similar_candidates_service,
    find_similar_jobs as find_similar_jobs_service,
    get_job_candidates_discovery,
    search_candidates,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/discovery", tags=["Candidate Discovery & Hiring Intelligence"])


def _get_job_or_404(db: Session, job_id: str, tenant_id: str) -> Job:
    """Fetch job by ID/public_id and verify tenant access."""
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

    job_tenant = getattr(job, "tenant_id", "default_tenant")
    if job_tenant and job_tenant != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Job belongs to another tenant.",
        )

    return job


def _get_candidate_or_404(db: Session, candidate_id: str, tenant_id: str) -> Candidate:
    """Fetch candidate by ID/public_id and verify tenant access."""
    query = db.query(Candidate)
    if candidate_id.isdigit():
        cand = query.filter(Candidate.id == int(candidate_id)).first()
    else:
        cand = query.filter(Candidate.public_id == candidate_id).first()

    if not cand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate '{candidate_id}' not found.",
        )

    cand_tenant = getattr(cand, "tenant_id", "default_tenant")
    if cand_tenant != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Candidate belongs to another tenant.",
        )

    return cand


# ── 1. Semantic & Natural Language Candidate Search ───────────────────────

@router.get("/search", response_model=DiscoverySearchResponse)
def semantic_candidate_search(
    current_user: AnyAuthUser,
    q: Optional[str] = Query(None, description="Natural language search query"),
    domain: Optional[str] = Query(None, description="Filter by domain"),
    min_required_cov: Optional[float] = Query(None, description="Min required coverage (0-100)"),
    min_preferred_cov: Optional[float] = Query(None, description="Min preferred coverage (0-100)"),
    min_semantic_sim: Optional[float] = Query(None, description="Min semantic similarity (0-100)"),
    ood_status: Optional[str] = Query(None, description="Filter by OOD status"),
    review_status: Optional[str] = Query(None, description="Filter by recruiter review status"),
    job_id: Optional[str] = Query(None, description="Target job ID for candidate scoring context"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
) -> DiscoverySearchResponse:
    """
    Recruiter Candidate Search combining vector semantic similarity, NLP skill extractions,
    and structured recruiter filters.
    """
    user_tenant = getattr(current_user, "tenant_id", tenant_id or "default_tenant")
    verify_tenant_access(user_tenant, tenant_id)

    sanitized_q = sanitize_prompt_input(q or "", max_length=1000)

    results = search_candidates(
        db=db,
        query=sanitized_q,
        tenant_id=user_tenant,
        domain_filter=domain,
        min_required_cov=min_required_cov,
        min_preferred_cov=min_preferred_cov,
        min_semantic_sim=min_semantic_sim,
        ood_status_filter=ood_status,
        review_status_filter=review_status,
        job_id_filter=job_id,
        page=page,
        page_size=page_size,
    )

    log_event(
        db=db,
        actor_id=current_user.id,
        actor_email=current_user.email,
        event_type="discovery.search",
        summary=f"Ran semantic candidate search query '{sanitized_q[:40]}'",
        resource_type="discovery",
        outcome="success",
    )

    return results


# ── 2. Job -> Candidate Discovery ─────────────────────────────────────────

@router.get("/jobs/{job_id}/candidates", response_model=JobCandidateDiscoveryResponse)
def get_job_candidates_discovery_endpoint(
    job_id: str,
    current_user: AnyAuthUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort_by: str = Query("screening_score", description="screening_score | semantic_similarity | required_coverage | discovery_relevance"),
    order: str = Query("desc", description="asc | desc"),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
) -> JobCandidateDiscoveryResponse:
    """
    Retrieves all candidates matched against a specific job with discovery relevance metrics.
    """
    user_tenant = getattr(current_user, "tenant_id", tenant_id or "default_tenant")
    verify_tenant_access(user_tenant, tenant_id)

    job = _get_job_or_404(db, job_id, user_tenant)

    results = get_job_candidates_discovery(
        db=db,
        job=job,
        tenant_id=user_tenant,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        order=order,
    )

    log_event(
        db=db,
        actor_id=current_user.id,
        actor_email=current_user.email,
        event_type="discovery.job_candidates",
        summary=f"Retrieved candidate discovery for job '{job.public_id}'",
        resource_type="job",
        resource_id=job.public_id,
        outcome="success",
    )

    return results


# ── 3. Similar Candidates Endpoint ───────────────────────────────────────

@router.get("/candidates/{candidate_id}/similar", response_model=SimilarCandidateResponse)
def get_similar_candidates_endpoint(
    candidate_id: str,
    current_user: AnyAuthUser,
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
) -> SimilarCandidateResponse:
    """
    Finds semantically similar candidates using production MiniLM embeddings.
    """
    user_tenant = getattr(current_user, "tenant_id", tenant_id or "default_tenant")
    verify_tenant_access(user_tenant, tenant_id)

    # Verify candidate exists and belongs to tenant
    _get_candidate_or_404(db, candidate_id, user_tenant)

    try:
        res = find_similar_candidates_service(db, candidate_id, user_tenant, limit=limit)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))

    log_event(
        db=db,
        actor_id=current_user.id,
        actor_email=current_user.email,
        event_type="discovery.similar_candidates",
        summary=f"Ran similar candidate lookup for '{candidate_id}'",
        resource_type="candidate",
        resource_id=candidate_id,
        outcome="success",
    )

    return res


# ── 4. Similar Jobs Endpoint ──────────────────────────────────────────────

@router.get("/jobs/{job_id}/similar", response_model=SimilarJobResponse)
def get_similar_jobs_endpoint(
    job_id: str,
    current_user: AnyAuthUser,
    limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
) -> SimilarJobResponse:
    """
    Finds semantically similar jobs using production MiniLM embeddings.
    """
    user_tenant = getattr(current_user, "tenant_id", tenant_id or "default_tenant")
    verify_tenant_access(user_tenant, tenant_id)

    # Verify job exists and belongs to tenant
    _get_job_or_404(db, job_id, user_tenant)

    try:
        res = find_similar_jobs_service(db, job_id, user_tenant, limit=limit)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))

    log_event(
        db=db,
        actor_id=current_user.id,
        actor_email=current_user.email,
        event_type="discovery.similar_jobs",
        summary=f"Ran similar jobs lookup for '{job_id}'",
        resource_type="job",
        resource_id=job_id,
        outcome="success",
    )

    return res


# ── 5. Candidate Comparison Endpoint ─────────────────────────────────────

@router.post("/compare", response_model=CandidateCompareResponse)
def compare_candidates_endpoint(
    payload: CandidateCompareRequest,
    current_user: AnyAuthUser,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id),
) -> CandidateCompareResponse:
    """
    Generates side-by-side factual comparison matrix for specified candidate IDs.
    Does NOT produce subjective verdicts; provides objective metrics only.
    """
    user_tenant = getattr(current_user, "tenant_id", tenant_id or "default_tenant")
    verify_tenant_access(user_tenant, tenant_id)

    if not payload.candidate_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="candidate_ids list cannot be empty.",
        )

    res = compare_candidates_service(
        db=db,
        candidate_ids=payload.candidate_ids,
        job_id=payload.job_id,
        tenant_id=user_tenant,
    )

    log_event(
        db=db,
        actor_id=current_user.id,
        actor_email=current_user.email,
        event_type="discovery.compare",
        summary=f"Compared {len(payload.candidate_ids)} candidates",
        resource_type="candidate",
        outcome="success",
    )

    return res
