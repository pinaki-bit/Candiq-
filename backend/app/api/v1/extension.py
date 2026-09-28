"""
backend/app/api/v1/extension.py

Phase 15: Chrome Browser Extension API Endpoints.
Handles candidate profile ingestion scraped directly from LinkedIn, Indeed, GitHub, etc.
"""

from __future__ import annotations

import datetime
import uuid
import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.candidate import Candidate
from app.models.resume import Resume, ProcessingStatus
from app.models.skill import ExtractedSkill
from app.schemas.extension import (
    ExtensionIngestRequest,
    ExtensionIngestResponse,
    ExtensionStatusResponse,
)
from app.services.classification_service import predict as predict_domain

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/extension", tags=["Browser Extension"])


@router.get("/status", response_model=ExtensionStatusResponse)
def get_extension_status():
    """Returns browser extension health and compatibility status."""
    return ExtensionStatusResponse(
        status="ok",
        version="1.0.0",
        supported_platforms=["linkedin", "indeed", "github", "custom"],
    )


@router.post("/ingest", response_model=ExtensionIngestResponse)
def ingest_candidate_from_extension(
    request: ExtensionIngestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ingests candidate profile scraped from browser extension."""
    if not request.name.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Candidate name cannot be empty",
        )

    # Step 1: Create Candidate
    candidate = Candidate(
        display_name=request.name,
        notes=f"Source: {request.source_platform.upper()} | Profile: {request.profile_url or 'N/A'}\n{request.notes or ''}".strip(),
    )
    db.add(candidate)
    db.flush()

    # Step 2: Build synthetic profile text for classification
    profile_text = (
        f"Candidate: {request.name}\n"
        f"Title: {request.current_title or 'N/A'}\n"
        f"Company: {request.company or 'N/A'}\n"
        f"Source: {request.source_platform}\n"
        f"Summary: {request.summary or 'N/A'}\n"
        f"Skills: {', '.join(request.skills)}"
    )

    # Step 3: Run Domain Classification
    classification_result = predict_domain(profile_text)
    predicted_domain = classification_result.predicted_domain or "Software Engineering"
    confidence = classification_result.top_probability if classification_result.top_probability is not None else 0.85

    # Step 4: Create Resume record
    stored_name = f"ext_{uuid.uuid4().hex[:12]}.txt"
    resume = Resume(
        candidate_id=candidate.id,
        original_filename=f"{request.name.lower().replace(' ', '_')}_{request.source_platform}.txt",
        stored_filename=stored_name,
        file_size_bytes=len(profile_text.encode("utf-8")),
        mime_type="text/plain",
        status=ProcessingStatus.COMPLETED,
        extracted_text=profile_text,
        text_char_count=len(profile_text),
        predicted_domain=predicted_domain,
        prediction_confidence="high" if confidence > 0.8 else "medium",
        uploaded_by=current_user.id,
        processed_at=datetime.datetime.now(datetime.timezone.utc),
    )
    db.add(resume)
    db.flush()

    # Step 5: Save Extracted Skills
    for skill_name in request.skills:
        s = skill_name.strip()
        if s:
            extracted_skill = ExtractedSkill(
                resume_id=resume.id,
                canonical_name=s.lower(),
                matched_text=s,
                extraction_method="extension_scraper",
            )
            db.add(extracted_skill)

    db.commit()

    logger.info(f"Ingested candidate '{request.name}' (ID: {candidate.id}) via extension from {request.source_platform}.")

    return ExtensionIngestResponse(
        success=True,
        candidate_id=candidate.id,
        resume_id=resume.id,
        predicted_domain=predicted_domain,
        confidence=confidence,
        message=f"Candidate '{request.name}' successfully ingested into {predicted_domain} talent pool.",
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    )
