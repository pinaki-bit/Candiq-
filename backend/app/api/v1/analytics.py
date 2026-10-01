"""
backend/app/api/v1/analytics.py

Analytics endpoints — real recruiter analytics and hiring insights layer.

GET /api/v1/analytics/summary        — high-level stats & overview metrics
GET /api/v1/analytics/funnel         — screening funnel progression
GET /api/v1/analytics/jobs           — job-level analytics breakdown
GET /api/v1/analytics/skills         — skill intelligence & gap analysis
GET /api/v1/analytics/score-hist      — score distribution & coverage metrics
GET /api/v1/analytics/time-series    — historical processing & activity trends
GET /api/v1/analytics/job-comparison — side-by-side job comparative metrics
GET /api/v1/analytics/pipeline/{job_id} — candidate pipeline insights for job
GET /api/v1/analytics/activity       — real recruiter activity timeline
GET /api/v1/analytics/domain-dist    — resume domain distribution
GET /api/v1/analytics/skill-heatmap  — top skills by domain heatmap
GET /api/v1/analytics/review-status  — review status counts
GET /api/v1/analytics/token-usage    — LLM telemetry & cost breakdown
"""

import datetime
import json
import logging
from collections import Counter, defaultdict

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import func, cast, Date
from sqlalchemy.orm import Session

from app.api.dependencies import AnyAuthUser
from app.database import get_db
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.resume import Resume
from app.models.screening import ScreeningResult, ReviewStatus
from app.models.skill import ExtractedSkill
from app.models.audit_event import AuditEvent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])


@router.get("/summary")
def get_summary(
    current_user: AnyAuthUser,
    db: Session = Depends(get_db),
) -> dict:
    """High-level system summary and overview metrics."""
    total_resumes = db.query(Resume).count()
    processed_resumes = db.query(Resume).filter(
        Resume.status.in_(["completed", "needs_review"])
    ).count()
    total_jobs = db.query(Job).count()
    active_jobs = db.query(Job).filter(Job.is_active == True).count()  # noqa: E712
    total_candidates = db.query(Candidate).count()
    total_screenings = db.query(ScreeningResult).count()

    # Recruiter review status breakdown
    pending_reviews = db.query(ScreeningResult).filter(
        ScreeningResult.review_status == ReviewStatus.PENDING
    ).count()
    approved_candidates = db.query(ScreeningResult).filter(
        ScreeningResult.review_status == ReviewStatus.APPROVED
    ).count()
    on_hold_candidates = db.query(ScreeningResult).filter(
        ScreeningResult.review_status == ReviewStatus.ON_HOLD
    ).count()
    rejected_candidates = db.query(ScreeningResult).filter(
        ScreeningResult.review_status == ReviewStatus.REJECTED
    ).count()

    # AI / OOD review status breakdown
    ood_review_count = db.query(Resume).filter(
        Resume.classification_status == "review"
    ).count()
    model_unavailable = db.query(Resume).filter(
        Resume.prediction_confidence == "unavailable"
    ).count()

    return {
        "total_resumes": total_resumes,
        "processed_resumes": processed_resumes,
        "processing_rate_pct": (
            round(100 * processed_resumes / total_resumes, 1) if total_resumes > 0 else 0.0
        ),
        "total_jobs": total_jobs,
        "total_active_jobs": active_jobs,
        "total_candidates": total_candidates,
        "total_screenings": total_screenings,
        "pending_reviews": pending_reviews,
        "candidates_requiring_review": pending_reviews + ood_review_count,
        "approved_candidates": approved_candidates,
        "shortlisted_candidates": approved_candidates,  # Alias
        "on_hold_candidates": on_hold_candidates,
        "rejected_candidates": rejected_candidates,
        "ood_review_count": ood_review_count,
        "model_unavailable_count": model_unavailable,
        "explainability": (
            f"Overview computed from {total_resumes} real resumes, {total_candidates} candidates, "
            f"and {total_screenings} screening results in database."
        ),
    }


@router.get("/funnel")
def get_screening_funnel(
    current_user: AnyAuthUser,
    job_id: str | None = None,
    db: Session = Depends(get_db),
) -> dict:
    """
    Screening funnel progression metrics.
    Uploaded -> Processed -> Matched -> Needs Review -> Shortlisted -> Approved -> On Hold -> Rejected
    """
    q_resumes = db.query(Resume)
    q_screenings = db.query(ScreeningResult)

    if job_id:
        job = db.query(Job).filter(Job.public_id == job_id).first()
        if job:
            q_screenings = q_screenings.filter(ScreeningResult.job_id == job.id)
            # Filter resumes associated with candidates screened for this job
            res_ids = [sr.resume_id for sr in q_screenings.all()]
            q_resumes = q_resumes.filter(Resume.id.in_(res_ids) if res_ids else False)

    uploaded = q_resumes.count()
    processed = q_resumes.filter(Resume.status.in_(["completed", "needs_review"])).count()
    matched = q_screenings.count()

    review_status_counts = dict(
        q_screenings.with_entities(
            ScreeningResult.review_status, func.count(ScreeningResult.id)
        )
        .group_by(ScreeningResult.review_status)
        .all()
    )

    needs_review = review_status_counts.get(ReviewStatus.PENDING, 0)
    approved = review_status_counts.get(ReviewStatus.APPROVED, 0)
    on_hold = review_status_counts.get(ReviewStatus.ON_HOLD, 0)
    rejected = review_status_counts.get(ReviewStatus.REJECTED, 0)

    funnel_stages = [
        {"stage": "Uploaded", "count": uploaded, "percentage": 100.0 if uploaded > 0 else 0.0},
        {"stage": "Processed", "count": processed, "percentage": round(100 * processed / uploaded, 1) if uploaded > 0 else 0.0},
        {"stage": "Matched", "count": matched, "percentage": round(100 * matched / processed, 1) if processed > 0 else 0.0},
        {"stage": "Needs Review", "count": needs_review, "percentage": round(100 * needs_review / matched, 1) if matched > 0 else 0.0},
        {"stage": "Shortlisted / Approved", "count": approved, "percentage": round(100 * approved / matched, 1) if matched > 0 else 0.0},
        {"stage": "On Hold", "count": on_hold, "percentage": round(100 * on_hold / matched, 1) if matched > 0 else 0.0},
        {"stage": "Rejected", "count": rejected, "percentage": round(100 * rejected / matched, 1) if matched > 0 else 0.0},
    ]

    return {
        "job_id": job_id,
        "total_uploaded": uploaded,
        "total_matched": matched,
        "stages": funnel_stages,
        "explainability": f"Funnel stages computed from {matched} persisted screening results.",
    }


@router.get("/jobs")
def get_job_analytics(
    current_user: AnyAuthUser,
    job_id: str | None = None,
    db: Session = Depends(get_db),
) -> dict:
    """Job-level analytics breakdown for all active jobs or a specific job."""
    q_jobs = db.query(Job)
    if job_id:
        q_jobs = q_jobs.filter(Job.public_id == job_id)

    jobs = q_jobs.order_by(Job.created_at.desc()).all()
    job_metrics = []

    for job in jobs:
        screenings = db.query(ScreeningResult).filter(ScreeningResult.job_id == job.id).all()
        screening_count = len(screenings)

        scores = [sr.relevance_score for sr in screenings if sr.relevance_score is not None]
        req_coverages = [sr.required_skill_coverage for sr in screenings if sr.required_skill_coverage is not None]
        pref_coverages = [sr.preferred_skill_coverage for sr in screenings if sr.preferred_skill_coverage is not None]

        review_status_counts = Counter([sr.review_status for sr in screenings])

        candidate_ids = {sr.candidate_id for sr in screenings if sr.candidate_id is not None}
        failed_count = db.query(Resume).filter(
            Resume.status == "failed"
        ).count()

        job_metrics.append({
            "job_id": job.public_id,
            "title": job.title,
            "department": job.department,
            "domain": job.domain,
            "is_active": job.is_active,
            "candidate_count": len(candidate_ids),
            "screening_count": screening_count,
            "avg_relevance_score": round(sum(scores) / len(scores), 2) if scores else None,
            "avg_required_coverage": round(sum(req_coverages) / len(req_coverages), 2) if req_coverages else None,
            "avg_preferred_coverage": round(sum(pref_coverages) / len(pref_coverages), 2) if pref_coverages else None,
            "pending_count": review_status_counts.get(ReviewStatus.PENDING, 0),
            "approved_count": review_status_counts.get(ReviewStatus.APPROVED, 0),
            "on_hold_count": review_status_counts.get(ReviewStatus.ON_HOLD, 0),
            "rejected_count": review_status_counts.get(ReviewStatus.REJECTED, 0),
            "processing_failures": failed_count,
        })

    return {
        "total_jobs_analyzed": len(job_metrics),
        "jobs": job_metrics,
        "explainability": f"Analyzed real metrics across {len(job_metrics)} job descriptions.",
    }


@router.get("/skills")
def get_skill_intelligence(
    current_user: AnyAuthUser,
    job_id: str | None = None,
    top_n: int = 15,
    db: Session = Depends(get_db),
) -> dict:
    """
    Skill intelligence and gap analysis.
    Computes most frequently matched skills and missing required skills across screening results.
    """
    q_screenings = db.query(ScreeningResult)
    if job_id:
        job = db.query(Job).filter(Job.public_id == job_id).first()
        if job:
            q_screenings = q_screenings.filter(ScreeningResult.job_id == job.id)

    screenings = q_screenings.all()
    matched_req_counter = Counter()
    matched_pref_counter = Counter()
    missing_req_counter = Counter()

    for sr in screenings:
        if sr.matched_required_skills:
            try:
                skills = json.loads(sr.matched_required_skills)
                matched_req_counter.update(skills)
            except Exception:
                pass
        if sr.matched_preferred_skills:
            try:
                skills = json.loads(sr.matched_preferred_skills)
                matched_pref_counter.update(skills)
            except Exception:
                pass
        if sr.missing_required_skills:
            try:
                skills = json.loads(sr.missing_required_skills)
                missing_req_counter.update(skills)
            except Exception:
                pass

    total_screenings = len(screenings)

    top_matched_required = [
        {
            "skill": skill,
            "count": count,
            "percentage": round(100 * count / total_screenings, 1) if total_screenings > 0 else 0.0
        }
        for skill, count in matched_req_counter.most_common(top_n)
    ]

    top_missing_required = [
        {
            "skill": skill,
            "count": count,
            "percentage": round(100 * count / total_screenings, 1) if total_screenings > 0 else 0.0
        }
        for skill, count in missing_req_counter.most_common(top_n)
    ]

    top_matched_preferred = [
        {
            "skill": skill,
            "count": count,
            "percentage": round(100 * count / total_screenings, 1) if total_screenings > 0 else 0.0
        }
        for skill, count in matched_pref_counter.most_common(top_n)
    ]

    return {
        "job_id": job_id,
        "total_screenings_analyzed": total_screenings,
        "top_matched_required": top_matched_required,
        "top_missing_required": top_missing_required,
        "top_matched_preferred": top_matched_preferred,
        "explainability": (
            f"Skill intelligence aggregated from {total_screenings} screening result records."
        ),
    }


@router.get("/score-hist")
def get_score_distribution(
    current_user: AnyAuthUser,
    job_id: str | None = None,
    db: Session = Depends(get_db),
) -> dict:
    """
    Histogram of relevance scores and coverage metrics across screening results.
    """
    q = db.query(ScreeningResult)
    if job_id:
        job = db.query(Job).filter(Job.public_id == job_id).first()
        if job:
            q = q.filter(ScreeningResult.job_id == job.id)

    screenings = q.all()

    scores = [sr.relevance_score for sr in screenings if sr.relevance_score is not None]
    req_coverages = [sr.required_skill_coverage for sr in screenings if sr.required_skill_coverage is not None]
    pref_coverages = [sr.preferred_skill_coverage for sr in screenings if sr.preferred_skill_coverage is not None]

    def _bucketize(values: list[float]) -> list[dict]:
        buckets = {"0-20": 0, "20-40": 0, "40-60": 0, "60-80": 0, "80-100": 0}
        for val in values:
            if val < 20:
                buckets["0-20"] += 1
            elif val < 40:
                buckets["20-40"] += 1
            elif val < 60:
                buckets["40-60"] += 1
            elif val < 80:
                buckets["60-80"] += 1
            else:
                buckets["80-100"] += 1
        total = len(values)
        return [
            {"range": k, "count": v, "percentage": round(100 * v / total, 1) if total > 0 else 0.0}
            for k, v in buckets.items()
        ]

    # OOD distribution among screened resumes
    res_ids = [sr.resume_id for sr in screenings]
    ood_dist = {"in_domain_like": 0, "possible_out_of_domain": 0, "needs_review": 0}

    if res_ids:
        resumes = db.query(Resume).filter(Resume.id.in_(res_ids)).all()
        for r in resumes:
            if r.ood_status == "possible_out_of_domain":
                ood_dist["possible_out_of_domain"] += 1
            elif r.classification_status == "review" or r.status == "needs_review":
                ood_dist["needs_review"] += 1
            else:
                ood_dist["in_domain_like"] += 1

    return {
        "total_screened": len(scores),
        "mean_score": round(sum(scores) / len(scores), 2) if scores else None,
        "buckets": _bucketize(scores),
        "required_coverage_buckets": _bucketize(req_coverages),
        "preferred_coverage_buckets": _bucketize(pref_coverages),
        "ood_distribution": ood_dist,
        "explainability": f"Score distribution computed over {len(scores)} screening result records.",
    }


@router.get("/time-series")
def get_time_series_analytics(
    current_user: AnyAuthUser,
    days: str = Query("30d", description="Time period: 7d, 30d, 90d, or all"),
    db: Session = Depends(get_db),
) -> dict:
    """
    Real time-series analytics for resumes processed, screenings, and recruiter reviews.
    Returns honest empty/insufficient data state if historical data is lacking.
    """
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    cutoff = None

    if days == "7d":
        cutoff = now - datetime.timedelta(days=7)
    elif days == "30d":
        cutoff = now - datetime.timedelta(days=30)
    elif days == "90d":
        cutoff = now - datetime.timedelta(days=90)

    # Resume uploads over time
    q_res = db.query(func.date(Resume.uploaded_at).label("upload_date"), func.count(Resume.id))
    if cutoff:
        q_res = q_res.filter(Resume.uploaded_at >= cutoff)
    res_rows = q_res.group_by(func.date(Resume.uploaded_at)).order_by(func.date(Resume.uploaded_at)).all()

    # Screenings over time
    q_scr = db.query(func.date(ScreeningResult.screened_at).label("screen_date"), func.count(ScreeningResult.id))
    if cutoff:
        q_scr = q_scr.filter(ScreeningResult.screened_at >= cutoff)
    scr_rows = q_scr.group_by(func.date(ScreeningResult.screened_at)).order_by(func.date(ScreeningResult.screened_at)).all()

    # Reviews over time
    q_rev = db.query(func.date(ScreeningResult.reviewed_at).label("review_date"), func.count(ScreeningResult.id))
    if cutoff:
        q_rev = q_rev.filter(ScreeningResult.reviewed_at >= cutoff)
    rev_rows = q_rev.filter(ScreeningResult.reviewed_at.isnot(None)).group_by(func.date(ScreeningResult.reviewed_at)).order_by(func.date(ScreeningResult.reviewed_at)).all()



    # Combine into unified date dictionary
    date_map = defaultdict(lambda: {"uploads": 0, "screenings": 0, "reviews": 0})
    for d, c in res_rows:
        if d:
            date_map[str(d)]["uploads"] = c
    for d, c in scr_rows:
        if d:
            date_map[str(d)]["screenings"] = c
    for d, c in rev_rows:
        if d:
            date_map[str(d)]["reviews"] = c

    series_data = [
        {"date": date_str, **metrics}
        for date_str, metrics in sorted(date_map.items())
    ]

    has_sufficient_data = len(series_data) >= 1

    return {
        "period": days,
        "has_sufficient_data": has_sufficient_data,
        "total_data_points": len(series_data),
        "series": series_data,
        "message": None if has_sufficient_data else "Insufficient historical data for selected date range.",
        "explainability": f"Time-series aggregated across {len(series_data)} distinct activity dates.",
    }


@router.get("/job-comparison")
def get_job_comparison(
    current_user: AnyAuthUser,
    job_ids: str | None = Query(None, description="Comma-separated job public_ids"),
    db: Session = Depends(get_db),
) -> dict:
    """Comparative analysis across active jobs (candidate volume, scores, coverage, decisions)."""
    q = db.query(Job)
    if job_ids:
        ids_list = [i.strip() for i in job_ids.split(",") if i.strip()]
        if ids_list:
            q = q.filter(Job.public_id.in_(ids_list))

    jobs = q.all()
    comparison_results = []

    for job in jobs:
        screenings = db.query(ScreeningResult).filter(ScreeningResult.job_id == job.id).all()
        total_scr = len(screenings)

        scores = [sr.relevance_score for sr in screenings if sr.relevance_score is not None]
        reqs = [sr.required_skill_coverage for sr in screenings if sr.required_skill_coverage is not None]
        prefs = [sr.preferred_skill_coverage for sr in screenings if sr.preferred_skill_coverage is not None]

        decisions = Counter([sr.review_status for sr in screenings])

        missing_skills_counter = Counter()
        for sr in screenings:
            if sr.missing_required_skills:
                try:
                    missing_skills_counter.update(json.loads(sr.missing_required_skills))
                except Exception:
                    pass

        comparison_results.append({
            "job_id": job.public_id,
            "title": job.title,
            "department": job.department,
            "candidate_volume": len({sr.candidate_id for sr in screenings if sr.candidate_id is not None}),
            "screening_volume": total_scr,
            "avg_relevance_score": round(sum(scores) / len(scores), 2) if scores else None,
            "avg_required_coverage": round(sum(reqs) / len(reqs), 2) if reqs else None,
            "avg_preferred_coverage": round(sum(prefs) / len(prefs), 2) if prefs else None,
            "review_percentage": round(100 * decisions.get(ReviewStatus.PENDING, 0) / total_scr, 1) if total_scr > 0 else 0.0,
            "shortlist_percentage": round(100 * decisions.get(ReviewStatus.APPROVED, 0) / total_scr, 1) if total_scr > 0 else 0.0,
            "top_missing_skills": [s for s, _ in missing_skills_counter.most_common(5)],
        })

    return {
        "job_count": len(comparison_results),
        "comparison": comparison_results,
        "explainability": f"Job comparison computed across {len(comparison_results)} job profiles.",
    }


@router.get("/pipeline/{job_id}")
def get_candidate_pipeline_insights(
    job_id: str,
    current_user: AnyAuthUser,
    db: Session = Depends(get_db),
) -> dict:
    """Detailed candidate pipeline insights for a single job."""
    job = db.query(Job).filter(Job.public_id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    screenings = db.query(ScreeningResult).filter(ScreeningResult.job_id == job.id).all()
    res_ids = [sr.resume_id for sr in screenings]
    resumes = db.query(Resume).filter(Resume.id.in_(res_ids)).all() if res_ids else []

    status_counts = Counter([r.status for r in resumes])
    review_counts = Counter([sr.review_status for sr in screenings])

    # Distinct separation: AI OOD vs Recruiter Status
    ood_vs_recruiter = {
        "ood_review_count": sum(1 for r in resumes if r.classification_status == "review"),
        "in_domain_count": sum(1 for r in resumes if r.classification_status == "accepted"),
        "recruiter_pending": review_counts.get(ReviewStatus.PENDING, 0),
        "recruiter_approved": review_counts.get(ReviewStatus.APPROVED, 0),
        "recruiter_rejected": review_counts.get(ReviewStatus.REJECTED, 0),
        "recruiter_on_hold": review_counts.get(ReviewStatus.ON_HOLD, 0),
    }

    return {
        "job_id": job.public_id,
        "job_title": job.title,
        "total_candidates": len(screenings),
        "processing_summary": {
            "completed": status_counts.get("completed", 0),
            "needs_review": status_counts.get("needs_review", 0),
            "failed": status_counts.get("failed", 0),
        },
        "recruiter_decisions": dict(review_counts),
        "pipeline_separation": ood_vs_recruiter,
        "explainability": f"Pipeline insights computed for job '{job.title}' from {len(screenings)} candidate records.",
    }


@router.get("/activity")
def get_recruiter_activity(
    current_user: AnyAuthUser,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict:
    """Persisted timeline of actual recruiter actions and review status updates."""
    screenings = (
        db.query(ScreeningResult)
        .filter(ScreeningResult.reviewed_at.isnot(None))
        .order_by(ScreeningResult.reviewed_at.desc())
        .limit(limit)
        .all()
    )

    activities = []
    for sr in screenings:
        activities.append({
            "screening_id": sr.public_id,
            "action": f"Status updated to '{sr.review_status}'",
            "reviewed_by": sr.reviewed_by,
            "reviewed_at": sr.reviewed_at.isoformat() if sr.reviewed_at else None,
            "review_notes": sr.review_notes,
            "relevance_score": sr.relevance_score,
        })

    # Also pull audit events if present
    audit_events = (
        db.query(AuditEvent)
        .filter(AuditEvent.event_type.like("screening.%"))
        .order_by(AuditEvent.occurred_at.desc())
        .limit(limit)
        .all()
    )
    for ae in audit_events:
        activities.append({
            "audit_id": ae.id,
            "action": ae.summary,
            "reviewed_by": ae.actor_id,
            "reviewed_at": ae.occurred_at.isoformat() if ae.occurred_at else None,
            "review_notes": ae.detail_json,
            "relevance_score": None,
        })

    activities.sort(key=lambda x: x["reviewed_at"] or "", reverse=True)

    return {
        "count": len(activities[:limit]),
        "activity": activities[:limit],
        "explainability": f"Retrieved {len(activities[:limit])} real persisted recruiter activity events.",
    }


@router.get("/domain-dist")
def get_domain_distribution(
    current_user: AnyAuthUser,
    db: Session = Depends(get_db),
) -> dict:
    """Domain distribution of processed resumes."""
    rows = (
        db.query(Resume.predicted_domain, func.count(Resume.id))
        .filter(Resume.predicted_domain.isnot(None))
        .group_by(Resume.predicted_domain)
        .all()
    )
    total = sum(count for _, count in rows)
    distribution = [
        {
            "domain": domain or "Unknown",
            "count": count,
            "percentage": round(100 * count / total, 1) if total > 0 else 0.0,
        }
        for domain, count in sorted(rows, key=lambda x: -x[1])
    ]
    return {"total": total, "distribution": distribution}


@router.get("/skill-heatmap")
def get_skill_heatmap(
    current_user: AnyAuthUser,
    top_n: int = 15,
    db: Session = Depends(get_db),
) -> dict:
    """Top N skills per domain heatmap."""
    rows = (
        db.query(
            ExtractedSkill.domain,
            ExtractedSkill.canonical_name,
            func.sum(ExtractedSkill.frequency).label("total_freq"),
        )
        .filter(ExtractedSkill.domain.isnot(None))
        .group_by(ExtractedSkill.domain, ExtractedSkill.canonical_name)
        .order_by(ExtractedSkill.domain, func.sum(ExtractedSkill.frequency).desc())
        .all()
    )

    domain_skills: dict[str, list[dict]] = defaultdict(list)
    for domain, skill, freq in rows:
        if len(domain_skills[domain]) < top_n:
            domain_skills[domain].append({"skill": skill, "frequency": int(freq)})

    return {"domains": dict(domain_skills), "top_n": top_n}


@router.get("/review-status")
def get_review_status_summary(
    current_user: AnyAuthUser,
    db: Session = Depends(get_db),
) -> dict:
    """Count of screening results by review status."""
    rows = (
        db.query(ScreeningResult.review_status, func.count(ScreeningResult.id))
        .group_by(ScreeningResult.review_status)
        .all()
    )
    return {
        "counts": {status: count for status, count in rows},
        "total": sum(count for _, count in rows),
    }


@router.get("/token-usage")
def get_token_usage_telemetry(current_user: AnyAuthUser):
    """Returns LLM token usage telemetry and cost breakdown."""
    from app.services.cost_tracking_service import cost_tracker
    return cost_tracker.get_summary()
