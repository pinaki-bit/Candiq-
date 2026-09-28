"""
backend/app/schemas/ats.py

Phase 14: ATS Adapter Architecture Schemas.
Pydantic schemas for Greenhouse, Lever, Workday, and Mock ATS provider integrations.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ATSProviderEnum(str, Enum):
    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    WORKDAY = "workday"
    MOCK = "mock"


class ATSCredentials(BaseModel):
    api_key: Optional[str] = Field(None, description="API Key or Personal Access Token")
    api_url: Optional[str] = Field(None, description="Base ATS API URL endpoint")
    client_id: Optional[str] = Field(None, description="OAuth2 Client ID")
    client_secret: Optional[str] = Field(None, description="OAuth2 Client Secret")
    tenant_id: Optional[str] = Field(None, description="Enterprise Tenant ID (e.g. Workday)")
    environment: str = Field("sandbox", description="Environment: sandbox or production")


class ATSCandidateExportRequest(BaseModel):
    resume_id: int = Field(..., description="ID of candidate resume to export")
    job_id: Optional[int] = Field(None, description="Target local job ID to attach application")
    provider: ATSProviderEnum = Field(ATSProviderEnum.MOCK, description="Target ATS Provider")
    credentials: Optional[ATSCredentials] = None
    notes: Optional[str] = Field(None, description="Screening notes or match summary")


class ATSCandidateExportResponse(BaseModel):
    success: bool
    provider: str
    ats_candidate_id: str
    ats_application_id: Optional[str] = None
    message: str
    timestamp: str
    data: Optional[Dict[str, Any]] = None


class ATSJobSyncRequest(BaseModel):
    provider: ATSProviderEnum = Field(ATSProviderEnum.MOCK, description="Target ATS Provider")
    credentials: Optional[ATSCredentials] = None
    auto_create_local: bool = Field(True, description="Automatically save synced jobs to local DB")


class ATSJobSyncResponse(BaseModel):
    success: bool
    provider: str
    synced_jobs_count: int
    jobs: List[Dict[str, Any]] = []
    message: str


class ATSConnectionTestRequest(BaseModel):
    provider: ATSProviderEnum = Field(..., description="ATS Provider to test")
    credentials: Optional[ATSCredentials] = None


class ATSConnectionTestResponse(BaseModel):
    success: bool
    provider: str
    status: str
    latency_ms: float
    message: str
