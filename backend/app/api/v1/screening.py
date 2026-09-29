"""
backend/app/api/v1/screening.py

Screening endpoints — match resumes to jobs and manage human review.

POST /api/v1/screening/{job_id}/match/{resume_id}
    - Runs skill-match formula between a job and a processed resume
    - Creates or updates a ScreeningResult record
    - Returns full match breakdown

GET  /api/v1/screening/{job_id}/results
    - Returns ranked candidate list for a job

PATCH /api/v1/screening/results/{result_id}/review
    - HR/admin: update review status (approved, rejected, on_hold)

GET  /api/v1/screening/results/{result_id}
    - Get a single ScreeningResult
"""


import datetime
import json
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import AnyAuthUser, HRUser
from app.database import get_db
from app.models.job import Job
from app.models.resume import Resume, ProcessingStatus
from app.models.screening import ScreeningResult, ReviewStatus
from app.schemas.screening import (
    BulkReviewUpdate,
    InterviewKitRequest,
    InterviewKitResponse,
    InterviewQuestionSchema,
    ReviewUpdate,
    ScreeningResultRead,
    TalentCandidateResultSchema,
    TalentSearchRequest,
    TalentSearchResponse,
)
from app.services import audit_service, matching_service, ranking_service
from app.services.interview_service import generate_interview_kit
from app.services.talent_search_service import search_talent_pool
from app.config import get_settings
from app.rate_limiter import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/screening", tags=["Screening"])


def _get_job_or_404(db: Session, job_id: str) -> Job:
    job = db.query(Job).filter(Job.public_id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    return job


def _get_resume_or_404(db: Session, resume_id: str) -> Resume:
    resume = db.query(Resume).filter(Resume.public_id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found.")
    return resume


@router.post(
    "/{job_id}/match/{resume_id}",
    response_model=ScreeningResultRead,
    status_code=status.HTTP_201_CREATED,
    summary="Match a resume to a job",
)
def match_resume_to_job(
    job_id: str,
    resume_id: str,
    request: Request,
    current_user: HRUser,
    db: Session = Depends(get_db),
) -> ScreeningResult:
    """
    Compute skill-match between a job and a processed resume.

    The candidate is NEVER automatically accepted or rejected.
    This endpoint produces a score + breakdown for human review.
    Screening results are always in 'pending' review state initially.
    """
    job = _get_job_or_404(db, job_id)
    resume = _get_resume_or_404(db, resume_id)

    # Guard: resume must be processed
    if resume.status not in (ProcessingStatus.COMPLETED, ProcessingStatus.NEEDS_REVIEW):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Resume status is '{resume.status}'. "
                "Only 'completed' or 'needs_review' resumes can be matched."
            ),
        )

    # Extract candidate skills
    candidate_skills = resume.extracted_skills

    # Extract job requirements
    required_skills, preferred_skills = matching_service.extract_job_skills(job.requirements)

    # Compute match
    match = matching_service.compute_match(
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        candidate_skills=candidate_skills,
    )

    # Compute composite relevance score
    # Weights: 70% skill match, 30% domain alignment bonus
    domain_bonus = 0.0
    if (
        resume.predicted_domain
        and job.domain
        and resume.predicted_domain.lower() == job.domain.lower()
        and resume.prediction_confidence in ("high", "medium")
    ):
        domain_bonus = 10.0 if resume.prediction_confidence == "high" else 5.0

    # Cap at 100
    relevance_score = min(100.0, round(match.combined_match + domain_bonus, 2))

    score_breakdown = {
        **match.score_breakdown,
        "domain_bonus": domain_bonus,
        "domain_bonus_reason": (
            "Job domain matches resume predicted domain with "
            f"'{resume.prediction_confidence}' confidence"
            if domain_bonus > 0
            else "No domain alignment bonus applied"
        ),
        "final_relevance_score": relevance_score,
        "missing_required_skills": match.missing_required,
        "matched_evidence_snippets": match.matched_evidence,
        "ethical_note": (
            "Score is based exclusively on technical skills and domain alignment. "
            "Protected characteristics are not used."
        ),
    }

    # Check for existing result and update if present
    existing = db.query(ScreeningResult).filter(
        ScreeningResult.resume_id == resume.id,
        ScreeningResult.job_id == job.id,
    ).first()

    if existing:
        result = existing
    else:
        result = ScreeningResult(
            resume_id=resume.id,
            job_id=job.id,
            candidate_id=resume.candidate_id,
        )
        db.add(result)
        db.flush()

    # Update all fields
    result.required_skill_coverage = match.required_coverage
    result.preferred_skill_coverage = match.preferred_coverage
    result.combined_skill_match = match.combined_match
    result.matched_required_skills = json.dumps(match.matched_required)
    result.missing_required_skills = json.dumps(match.missing_required)
    result.matched_preferred_skills = json.dumps(match.matched_preferred)
    result.predicted_domain = resume.predicted_domain
    result.prediction_confidence = resume.prediction_confidence
    result.relevance_score = relevance_score
    result.score_breakdown = json.dumps(score_breakdown)
    result.scoring_weights = json.dumps({
        "skill_match_weight": 0.90,
        "domain_alignment_bonus_max": 10.0,
    })
    result.screened_at = datetime.datetime.now(datetime.timezone.utc)

    db.commit()
    db.refresh(result)

    audit_service.log_event(
        db,
        event_type="screening.match",
        summary=f"Resume matched to job '{job.title}'",
        actor_id=current_user.id,
        actor_email=current_user.email,
        resource_type="screening_result",
        resource_id=result.public_id,
        detail={
            "job_id": job.public_id,
            "resume_id": resume.public_id,
            "relevance_score": relevance_score,
        },
        ip_address=request.client.host if request.client else None,
    )

    return result


@router.get(
    "/{job_id}/results",
    summary="Get ranked candidates for a job",
)
def get_job_results(
    job_id: str,
    current_user: AnyAuthUser,
    review_status: str | None = None,
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    Return all candidates ranked by relevance score for a job.

    Access control:
      - Admin/HR: see all results.
      - Readonly: see only results for resumes they uploaded.
    """
    job = _get_job_or_404(db, job_id)
    ranked = ranking_service.rank_results_for_job(
        db, job.id, review_status_filter=review_status
    )

    from dataclasses import asdict
    results = [asdict(r) for r in ranked]

    # IDOR guard: readonly users only see their own results
    if current_user.role == "readonly":
        # Get resume IDs uploaded by this user
        own_resume_ids = {
            r.id for r in db.query(Resume.id).filter(
                Resume.uploaded_by == current_user.id
            ).all()
        }
        results = [r for r in results if r.get("resume_id") in own_resume_ids]

    return results


@router.get(
    "/results/{result_id}",
    response_model=ScreeningResultRead,
    summary="Get a single screening result",
)
def get_result(
    result_id: str,
    current_user: AnyAuthUser,
    db: Session = Depends(get_db),
) -> ScreeningResult:
    """
    Get a single screening result by public ID.

    Access control:
      - Admin/HR: see any result.
      - Readonly: see only results for resumes they uploaded.
    """
    result = db.query(ScreeningResult).filter(
        ScreeningResult.public_id == result_id
    ).first()
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Result not found.")

    # IDOR guard: readonly users can only see their own results
    if current_user.role == "readonly":
        resume = db.query(Resume).filter(Resume.id == result.resume_id).first()
        if not resume or resume.uploaded_by != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You can only view results for resumes you uploaded.",
            )

    return result


@router.patch(
    "/results/{result_id}/review",
    response_model=ScreeningResultRead,
    summary="Update human review status",
)
def update_review(
    result_id: str,
    payload: ReviewUpdate,
    request: Request,
    current_user: HRUser,
    db: Session = Depends(get_db),
) -> ScreeningResult:
    """
    Update the human review status of a screening result.

    Valid statuses: pending, approved, rejected, on_hold.

    Note: 'rejected' means the candidate was NOT selected for THIS job.
    It does NOT mean the candidate is blacklisted from future applications.
    """
    if payload.review_status not in ReviewStatus.ALL:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Invalid review status '{payload.review_status}'. "
                f"Valid values: {', '.join(sorted(ReviewStatus.ALL))}."
            ),
        )

    result = db.query(ScreeningResult).filter(
        ScreeningResult.public_id == result_id
    ).first()
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Result not found.")

    result.review_status = payload.review_status
    result.review_notes = payload.review_notes
    result.reviewed_by = current_user.id
    result.reviewed_at = datetime.datetime.now(datetime.timezone.utc)
    db.commit()
    db.refresh(result)

    audit_service.log_event(
        db,
        event_type="screening.review_update",
        summary=f"Review status set to '{payload.review_status}'",
        actor_id=current_user.id,
        actor_email=current_user.email,
        resource_type="screening_result",
        resource_id=result.public_id,
        ip_address=request.client.host if request.client else None,
    )

    return result


@router.patch(
    "/results/bulk-review",
    response_model=List[ScreeningResultRead],
    summary="Bulk update human review status for multiple candidates",
)
def bulk_update_reviews(
    payload: BulkReviewUpdate,
    request: Request,
    current_user: HRUser,
    db: Session = Depends(get_db),
) -> list[ScreeningResult]:
    """
    Bulk update review status for multiple candidates.
    Recruiter explicit action: Shortlist, Reject, Mark for Review.
    """
    if payload.review_status not in ReviewStatus.ALL:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid review status '{payload.review_status}'.",
        )

    results = db.query(ScreeningResult).filter(
        ScreeningResult.public_id.in_(payload.result_ids)
    ).all()

    now = datetime.datetime.now(datetime.timezone.utc)
    for res in results:
        res.review_status = payload.review_status
        if payload.review_notes:
            res.review_notes = payload.review_notes
        res.reviewed_by = current_user.id
        res.reviewed_at = now

    db.commit()
    for res in results:
        db.refresh(res)

    audit_service.log_event(
        db,
        event_type="screening.bulk_review_update",
        summary=f"Bulk review status set to '{payload.review_status}' for {len(results)} candidates",
        actor_id=current_user.id,
        actor_email=current_user.email,
        resource_type="screening_result",
        resource_id="bulk",
        ip_address=request.client.host if request.client else None,
    )

    return results


@router.post(
    "/{job_id}/match-all",
    response_model=List[ScreeningResultRead],
    status_code=status.HTTP_201_CREATED,
    summary="Match all available completed resumes to a job",
)
def match_all_resumes_to_job(
    job_id: str,
    request: Request,
    current_user: HRUser,
    db: Session = Depends(get_db),
) -> list[ScreeningResult]:
    """
    Run skill-matching pipeline between a job and all completed/needs_review resumes.
    """
    job = _get_job_or_404(db, job_id)
    resumes = db.query(Resume).filter(
        Resume.status.in_([ProcessingStatus.COMPLETED, ProcessingStatus.NEEDS_REVIEW])
    ).all()

    req_skills, pref_skills = matching_service.extract_job_skills(job.requirements)
    results: list[ScreeningResult] = []

    for resume in resumes:
        candidate_skills = resume.extracted_skills
        match = matching_service.compute_match(req_skills, pref_skills, candidate_skills)

        domain_bonus = 0.0
        if (
            resume.predicted_domain
            and job.domain
            and resume.predicted_domain.lower() == job.domain.lower()
            and resume.prediction_confidence in ("high", "medium")
        ):
            domain_bonus = 10.0 if resume.prediction_confidence == "high" else 5.0

        relevance_score = min(100.0, round(match.combined_match + domain_bonus, 2))

        score_breakdown = {
            **match.score_breakdown,
            "domain_bonus": domain_bonus,
            "final_relevance_score": relevance_score,
            "missing_required_skills": match.missing_required,
            "matched_evidence_snippets": match.matched_evidence,
        }

        existing = db.query(ScreeningResult).filter(
            ScreeningResult.resume_id == resume.id,
            ScreeningResult.job_id == job.id,
        ).first()

        if existing:
            result = existing
        else:
            result = ScreeningResult(
                resume_id=resume.id,
                job_id=job.id,
                candidate_id=resume.candidate_id,
            )
            db.add(result)
            db.flush()

        result.required_skill_coverage = match.required_coverage
        result.preferred_skill_coverage = match.preferred_coverage
        result.combined_skill_match = match.combined_match
        result.matched_required_skills = json.dumps(match.matched_required)
        result.missing_required_skills = json.dumps(match.missing_required)
        result.matched_preferred_skills = json.dumps(match.matched_preferred)
        result.predicted_domain = resume.predicted_domain
        result.prediction_confidence = resume.prediction_confidence
        result.relevance_score = relevance_score
        result.score_breakdown = json.dumps(score_breakdown)
        result.scoring_weights = json.dumps({
            "skill_match_weight": 0.90,
            "domain_alignment_bonus_max": 10.0,
        })
        result.screened_at = datetime.datetime.now(datetime.timezone.utc)
        results.append(result)

    db.commit()
    for r in results:
        db.refresh(r)

    return results


@router.post(
    "/interview-kit",
    response_model=InterviewKitResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate grounded 5-category technical interview questions",
)
@limiter.limit(get_settings().rate_limit_default)
def create_interview_kit(
    request: Request,
    payload: InterviewKitRequest,
    current_user: AnyAuthUser,
) -> InterviewKitResponse:
    """
    Generate a 5-category technical interview question kit grounded in candidate background and skill gaps.
    Categories:
      1. Technical Fundamentals
      2. Practical Implementation
      3. Project-Based Deep Dive
      4. Scenario-Based Problem Solving
      5. Verification / Claim Validation
    """
    result = generate_interview_kit(
        job_title=payload.job_title or "Software Engineer",
        candidate_skills=payload.candidate_skills,
        missing_skills=payload.missing_skills,
        resume_text=payload.resume_text,
        job_description=payload.job_description,
    )

    questions_schema = [
        InterviewQuestionSchema(
            question_id=q.question_id,
            category=q.category,
            question=q.question,
            why_this_question=q.why_this_question,
            expected_key_points=q.expected_key_points,
            difficulty=q.difficulty,
        )
        for q in result.questions
    ]

    return InterviewKitResponse(
        job_title=result.job_title,
        questions=questions_schema,
        tokens_used=result.tokens_used,
        estimated_cost_usd=result.estimated_cost_usd,
        guardrail_warnings=result.guardrail_warnings,
    )


@router.post(
    "/talent-search",
    response_model=TalentSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Natural language semantic talent search pipeline",
)
@limiter.limit(get_settings().rate_limit_default)
def search_candidates(
    request: Request,
    payload: TalentSearchRequest,
    current_user: AnyAuthUser,
    db: Session = Depends(get_db),
) -> TalentSearchResponse:
    """
    Search talent pool using hybrid semantic vector similarity, NLP skill matching, and confidence bonuses.
    Query → Embed → Hybrid Filter & Rank.
    """
    result = search_talent_pool(
        db=db,
        query=payload.query,
        domain_filter=payload.domain_filter,
        min_confidence=payload.min_confidence,
        required_skills=payload.required_skills,
        limit=payload.limit,
    )

    results_schema = [
        TalentCandidateResultSchema(
            resume_id=c.resume_id,
            public_id=c.public_id,
            original_filename=c.original_filename,
            predicted_domain=c.predicted_domain,
            prediction_confidence=c.prediction_confidence,
            hybrid_score=c.hybrid_score,
            semantic_similarity=c.semantic_similarity,
            matched_skills=c.matched_skills,
            snippet=c.snippet,
        )
        for c in result.results
    ]

    return TalentSearchResponse(
        query=result.query,
        total_candidates_searched=result.total_candidates_searched,
        results_count=result.results_count,
        results=results_schema,
    )
