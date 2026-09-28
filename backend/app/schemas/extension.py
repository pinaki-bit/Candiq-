"""
backend/app/schemas/extension.py

Phase 15: Browser Extension Architecture Schemas.
Pydantic schemas for candidate ingestion and extension API status.
"""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class ExtensionIngestRequest(BaseModel):
    name: str = Field(..., description="Full name of candidate scraped from profile")
    current_title: Optional[str] = Field(None, description="Current job title or headline")
    company: Optional[str] = Field(None, description="Current company or organization")
    profile_url: Optional[str] = Field(None, description="Original URL of candidate profile (LinkedIn/Indeed/GitHub)")
    source_platform: str = Field("linkedin", description="Source platform: linkedin, indeed, github, etc.")
    summary: Optional[str] = Field(None, description="Candidate bio, about section, or experience summary")
    skills: List[str] = Field(default_factory=list, description="Extracted skills list")
    job_id: Optional[int] = Field(None, description="Target job ID to screen against")
    notes: Optional[str] = Field(None, description="Sourcing notes from recruiter")


class ExtensionIngestResponse(BaseModel):
    success: bool
    candidate_id: int
    resume_id: int
    predicted_domain: str
    confidence: float
    message: str
    timestamp: str


class ExtensionStatusResponse(BaseModel):
    status: str
    version: str
    supported_platforms: List[str]
