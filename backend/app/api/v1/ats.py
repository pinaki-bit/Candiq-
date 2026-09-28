"""
backend/app/api/v1/ats.py

Phase 14: ATS Integration API Endpoints.
Provides REST endpoints for enterprise ATS connectivity, job syncing, and candidate exporting.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.resume import Resume
from app.models.job import Job
from app.schemas.ats import (
    ATSProviderEnum,
    ATSCandidateExportRequest,
    ATSCandidateExportResponse,
    ATSJobSyncRequest,
    ATSJobSyncResponse,
    ATSConnectionTestRequest,
    ATSConnectionTestResponse,
)
from app.services.ats_adapters import ATSFactory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ats", tags=["ATS Integration"])


@router.get("/providers", response_model=List[str])
def get_supported_ats_providers(current_user: User = Depends(get_current_user)):
    """Returns list of supported Applicant Tracking System (ATS) providers."""
    return [p.value for p in ATSProviderEnum]


@router.post("/test-connection", response_model=ATSConnectionTestResponse)
def test_ats_connection(
    request: ATSConnectionTestRequest,
    current_user: User = Depends(get_current_user),
):
    """Tests connectivity and credentials for a given ATS provider."""
    adapter = ATSFactory.get_adapter(provider=request.provider, credentials=request.credentials)
    return adapter.test_connection()


@router.post("/sync-jobs", response_model=ATSJobSyncResponse)
def sync_jobs_from_ats(
    request: ATSJobSyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Harvests open job requisitions from target ATS adapter."""
    adapter = ATSFactory.get_adapter(provider=request.provider, credentials=request.credentials)
    sync_result = adapter.sync_jobs()

    if request.auto_create_local and sync_result.success:
        created_count = 0
        for job_dict in sync_result.jobs:
            existing = db.query(Job).filter(Job.title == job_dict["title"]).first()
            if not existing:
                new_job = Job(
                    title=job_dict["title"],
                    department=job_dict.get("department", "General"),
                    description=f"Harvested from {request.provider.value.title()} ATS ({job_dict.get('ats_job_id')}). Requirements: {job_dict.get('requirements', '')}",
                    is_active=True,
                )
                db.add(new_job)
                created_count += 1
        if created_count > 0:
            db.commit()
            sync_result.message += f" (Auto-saved {created_count} new job(s) to local DB)"

    return sync_result


@router.post("/export", response_model=ATSCandidateExportResponse)
def export_candidate_to_ats(
    request: ATSCandidateExportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Exports candidate resume and screening telemetry to target ATS provider."""
    resume = db.query(Resume).filter(Resume.id == request.resume_id).first()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume with ID {request.resume_id} not found",
        )

    job_dict = None
    if request.job_id:
        job = db.query(Job).filter(Job.id == request.job_id).first()
        if job:
            job_dict = {
                "id": job.id,
                "title": job.title,
                "department": job.department,
            }

    resume_data = {
        "id": resume.id,
        "filename": resume.original_filename,
        "candidate_id": resume.candidate_id,
        "predicted_domain": resume.predicted_domain,
        "experience_years": getattr(resume, "experience_years", 0),
        "parsed_skills": getattr(resume, "parsed_skills", []),
    }

    adapter = ATSFactory.get_adapter(provider=request.provider, credentials=request.credentials)
    export_result = adapter.export_candidate(
        resume_data=resume_data,
        job_data=job_dict,
        notes=request.notes,
    )

    return export_result
