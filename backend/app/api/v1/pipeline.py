"""
backend/app/api/v1/pipeline.py

Candidate Journey Pipeline endpoints — Kanban-style hiring pipeline management.

GET  /api/v1/pipeline/{job_id}           — Get all pipeline entries for a job (Kanban board data)
POST /api/v1/pipeline/{job_id}/add       — Add a candidate to the pipeline
PATCH /api/v1/pipeline/{entry_id}/move   — Move a candidate to a new stage
GET  /api/v1/pipeline/{job_id}/history   — Get transition history for a job
GET  /api/v1/pipeline/stats/{job_id}     — Pipeline stage counts and velocity metrics
"""

from __future__ import annotations

import datetime
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.dependencies import HRUser, AnyAuthUser
from app.database import get_db
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.pipeline import PipelineEntry, PipelineHistory, PipelineStage
from app.models.screening import ScreeningResult
from app.services.email_service import send_candidate_stage_update

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/pipeline", tags=["Pipeline"])


# ---------------------------------------------------------------------------
# Request / Response Schemas
# ---------------------------------------------------------------------------

class AddToPipelineRequest(BaseModel):
    candidate_id: int
    stage: str = PipelineStage.APPLIED
    notes: str | None = None


class MoveStageRequest(BaseModel):
    to_stage: str
    notes: str | None = None


class PipelineEntryRead(BaseModel):
    id: int
    public_id: str
    candidate_id: int
    candidate_name: str | None = None
    candidate_email: str | None = None
    job_id: int
    stage: str
    notes: str | None = None
    entered_at: datetime.datetime
    stage_changed_at: datetime.datetime
    relevance_score: float | None = None
    predicted_domain: str | None = None

    model_config = {"from_attributes": True}


class PipelineHistoryRead(BaseModel):
    id: int
    candidate_id: int
    candidate_name: str | None = None
    job_id: int
    from_stage: str
    to_stage: str
    notes: str | None = None
    transitioned_at: datetime.datetime

    model_config = {"from_attributes": True}


class PipelineStatsResponse(BaseModel):
    job_id: int
    job_title: str
    total_candidates: int
    stage_counts: dict[str, int]
    avg_time_in_stage_hours: dict[str, float]
    conversion_rates: dict[str, float]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/{job_id}", response_model=list[PipelineEntryRead])
def get_pipeline(
    job_id: int,
    current_user: AnyAuthUser,
    db: Session = Depends(get_db),
) -> list[dict]:
    """Get all pipeline entries for a job, enriched with candidate info and screening scores."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    entries = (
        db.query(PipelineEntry)
        .filter(PipelineEntry.job_id == job_id)
        .order_by(PipelineEntry.stage_changed_at.desc())
        .all()
    )

    results = []
    for entry in entries:
        candidate = db.query(Candidate).filter(Candidate.id == entry.candidate_id).first()

        # Get best screening score for this candidate-job pair
        screening = (
            db.query(ScreeningResult)
            .filter(
                ScreeningResult.candidate_id == entry.candidate_id,
                ScreeningResult.job_id == job_id,
            )
            .order_by(ScreeningResult.relevance_score.desc().nulls_last())
            .first()
        )

        results.append({
            "id": entry.id,
            "public_id": entry.public_id,
            "candidate_id": entry.candidate_id,
            "candidate_name": candidate.display_name if candidate else None,
            "candidate_email": candidate.email if candidate else None,
            "job_id": entry.job_id,
            "stage": entry.stage,
            "notes": entry.notes,
            "entered_at": entry.entered_at,
            "stage_changed_at": entry.stage_changed_at,
            "relevance_score": screening.relevance_score if screening else None,
            "predicted_domain": screening.predicted_domain if screening else None,
        })

    return results


@router.post("/{job_id}/add", response_model=PipelineEntryRead, status_code=201)
def add_to_pipeline(
    job_id: int,
    payload: AddToPipelineRequest,
    current_user: HRUser,
    db: Session = Depends(get_db),
) -> dict:
    """Add a candidate to the hiring pipeline for a specific job."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    candidate = db.query(Candidate).filter(Candidate.id == payload.candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found.")

    if payload.stage not in PipelineStage.ALL:
        raise HTTPException(status_code=422, detail=f"Invalid stage: {payload.stage}")

    # Check if candidate is already in pipeline for this job
    existing = (
        db.query(PipelineEntry)
        .filter(
            PipelineEntry.candidate_id == payload.candidate_id,
            PipelineEntry.job_id == job_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail="Candidate is already in the pipeline for this job.",
        )

    entry = PipelineEntry(
        candidate_id=payload.candidate_id,
        job_id=job_id,
        stage=payload.stage,
        moved_by=current_user.id,
        notes=payload.notes,
    )
    db.add(entry)
    db.flush()

    # Record initial history
    history = PipelineHistory(
        pipeline_entry_id=entry.id,
        candidate_id=payload.candidate_id,
        job_id=job_id,
        from_stage="(new)",
        to_stage=payload.stage,
        moved_by=current_user.id,
        notes=payload.notes,
    )
    db.add(history)
    db.commit()
    db.refresh(entry)

    screening = (
        db.query(ScreeningResult)
        .filter(
            ScreeningResult.candidate_id == payload.candidate_id,
            ScreeningResult.job_id == job_id,
        )
        .order_by(ScreeningResult.relevance_score.desc().nulls_last())
        .first()
    )

    return {
        "id": entry.id,
        "public_id": entry.public_id,
        "candidate_id": entry.candidate_id,
        "candidate_name": candidate.display_name,
        "candidate_email": candidate.email,
        "job_id": entry.job_id,
        "stage": entry.stage,
        "notes": entry.notes,
        "entered_at": entry.entered_at,
        "stage_changed_at": entry.stage_changed_at,
        "relevance_score": screening.relevance_score if screening else None,
        "predicted_domain": screening.predicted_domain if screening else None,
    }


@router.patch("/{entry_id}/move", response_model=PipelineEntryRead)
def move_stage(
    entry_id: int,
    payload: MoveStageRequest,
    current_user: HRUser,
    db: Session = Depends(get_db),
) -> dict:
    """Move a candidate to a new pipeline stage with state machine validation."""
    entry = db.query(PipelineEntry).filter(PipelineEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Pipeline entry not found.")

    if payload.to_stage not in PipelineStage.ALL:
        raise HTTPException(status_code=422, detail=f"Invalid stage: {payload.to_stage}")

    if not PipelineStage.is_valid_transition(entry.stage, payload.to_stage):
        raise HTTPException(
            status_code=422,
            detail=(
                f"Invalid transition: {entry.stage!r} → {payload.to_stage!r}. "
                f"Allowed: {PipelineStage.TRANSITIONS.get(entry.stage, set())}"
            ),
        )

    old_stage = entry.stage
    entry.stage = payload.to_stage
    entry.moved_by = current_user.id
    entry.stage_changed_at = func.now()
    if payload.notes:
        entry.notes = payload.notes

    # Record transition history
    history = PipelineHistory(
        pipeline_entry_id=entry.id,
        candidate_id=entry.candidate_id,
        job_id=entry.job_id,
        from_stage=old_stage,
        to_stage=payload.to_stage,
        moved_by=current_user.id,
        notes=payload.notes,
    )
    db.add(history)
    db.commit()
    db.refresh(entry)

    candidate = db.query(Candidate).filter(Candidate.id == entry.candidate_id).first()
    job = db.query(Job).filter(Job.id == entry.job_id).first()
    screening = (
        db.query(ScreeningResult)
        .filter(
            ScreeningResult.candidate_id == entry.candidate_id,
            ScreeningResult.job_id == entry.job_id,
        )
        .order_by(ScreeningResult.relevance_score.desc().nulls_last())
        .first()
    )

    logger.info(
        "Pipeline move: candidate=%d job=%d %s → %s by user=%d",
        entry.candidate_id, entry.job_id, old_stage, payload.to_stage, current_user.id,
    )
    
    # Send automated email to the candidate
    if candidate and candidate.email and job:
        send_candidate_stage_update(
            candidate_email=candidate.email,
            candidate_name=candidate.display_name or "Candidate",
            job_title=job.title,
            stage=payload.to_stage,
            custom_notes=payload.notes
        )

    return {
        "id": entry.id,
        "public_id": entry.public_id,
        "candidate_id": entry.candidate_id,
        "candidate_name": candidate.display_name if candidate else None,
        "candidate_email": candidate.email if candidate else None,
        "job_id": entry.job_id,
        "stage": entry.stage,
        "notes": entry.notes,
        "entered_at": entry.entered_at,
        "stage_changed_at": entry.stage_changed_at,
        "relevance_score": screening.relevance_score if screening else None,
        "predicted_domain": screening.predicted_domain if screening else None,
    }


@router.get("/{job_id}/history", response_model=list[PipelineHistoryRead])
def get_pipeline_history(
    job_id: int,
    current_user: AnyAuthUser,
    db: Session = Depends(get_db),
    limit: int = 50,
) -> list[dict]:
    """Get the full stage transition history for a job pipeline."""
    history = (
        db.query(PipelineHistory)
        .filter(PipelineHistory.job_id == job_id)
        .order_by(PipelineHistory.transitioned_at.desc())
        .limit(limit)
        .all()
    )

    results = []
    for h in history:
        candidate = db.query(Candidate).filter(Candidate.id == h.candidate_id).first()
        results.append({
            "id": h.id,
            "candidate_id": h.candidate_id,
            "candidate_name": candidate.display_name if candidate else None,
            "job_id": h.job_id,
            "from_stage": h.from_stage,
            "to_stage": h.to_stage,
            "notes": h.notes,
            "transitioned_at": h.transitioned_at,
        })

    return results


@router.get("/stats/{job_id}", response_model=PipelineStatsResponse)
def get_pipeline_stats(
    job_id: int,
    current_user: AnyAuthUser,
    db: Session = Depends(get_db),
) -> dict:
    """Pipeline velocity metrics: stage counts, average time-in-stage, conversion rates."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    entries = (
        db.query(PipelineEntry)
        .filter(PipelineEntry.job_id == job_id)
        .all()
    )

    # Stage counts
    stage_counts: dict[str, int] = {s: 0 for s in PipelineStage.ALL}
    for entry in entries:
        stage_counts[entry.stage] = stage_counts.get(entry.stage, 0) + 1

    total = len(entries)

    # Conversion rates (what % moved past each stage)
    conversion_rates: dict[str, float] = {}
    if total > 0:
        for i, stage in enumerate(PipelineStage.ORDERED):
            past_this = sum(
                1 for e in entries
                if PipelineStage.stage_order(e.stage) > i
                or e.stage == PipelineStage.HIRED
            )
            conversion_rates[stage] = round((past_this / total) * 100, 1)

    # Average time in current stage (hours)
    avg_time: dict[str, float] = {}
    now = datetime.datetime.now(datetime.timezone.utc)
    for stage in PipelineStage.ALL:
        stage_entries = [e for e in entries if e.stage == stage]
        if stage_entries:
            total_hours = sum(
                (now - (e.stage_changed_at.replace(tzinfo=datetime.timezone.utc) if e.stage_changed_at.tzinfo is None else e.stage_changed_at)).total_seconds() / 3600
                for e in stage_entries
            )
            avg_time[stage] = round(total_hours / len(stage_entries), 1)

    return {
        "job_id": job_id,
        "job_title": job.title,
        "total_candidates": total,
        "stage_counts": stage_counts,
        "avg_time_in_stage_hours": avg_time,
        "conversion_rates": conversion_rates,
    }
