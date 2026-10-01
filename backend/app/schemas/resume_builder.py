"""
backend/app/schemas/resume_builder.py

Phase 35 — Pydantic Schemas for AI Resume Builder & Live ATS Optimization.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PersonalInfo(BaseModel):
    full_name: Optional[str] = ""
    email: Optional[str] = ""
    phone: Optional[str] = ""
    location: Optional[str] = ""
    linkedin: Optional[str] = ""
    github: Optional[str] = ""
    website: Optional[str] = ""


class ExperienceItem(BaseModel):
    title: Optional[str] = ""
    company: Optional[str] = ""
    location: Optional[str] = ""
    start_date: Optional[str] = ""
    end_date: Optional[str] = ""
    is_current: Optional[bool] = False
    bullets: List[str] = Field(default_factory=list)


class EducationItem(BaseModel):
    institution: Optional[str] = ""
    degree: Optional[str] = ""
    field_of_study: Optional[str] = ""
    start_date: Optional[str] = ""
    end_date: Optional[str] = ""
    gpa: Optional[str] = ""


class ProjectItem(BaseModel):
    name: Optional[str] = ""
    description: Optional[str] = ""
    technologies: List[str] = Field(default_factory=list)
    link: Optional[str] = ""


class CertificationItem(BaseModel):
    name: Optional[str] = ""
    issuer: Optional[str] = ""
    date: Optional[str] = ""
    url: Optional[str] = ""


class AchievementItem(BaseModel):
    title: Optional[str] = ""
    description: Optional[str] = ""
    date: Optional[str] = ""


class StructuredResumeContent(BaseModel):
    personal_info: Optional[PersonalInfo] = Field(default_factory=PersonalInfo)
    summary: Optional[str] = ""
    skills: List[str] = Field(default_factory=list)
    experience: List[ExperienceItem] = Field(default_factory=list)
    education: List[EducationItem] = Field(default_factory=list)
    projects: List[ProjectItem] = Field(default_factory=list)
    certifications: List[CertificationItem] = Field(default_factory=list)
    achievements: List[AchievementItem] = Field(default_factory=list)
    section_order: List[str] = Field(
        default_factory=lambda: [
            "personal_info", "summary", "skills", "experience",
            "education", "projects", "certifications", "achievements"
        ]
    )


class ResumeDraftCreate(BaseModel):
    title: Optional[str] = "Untitled Resume Draft"
    target_job_id: Optional[str] = None
    candidate_id: Optional[str] = None
    original_resume_id: Optional[str] = None
    structured_content: Optional[StructuredResumeContent] = None


class ResumeDraftUpdate(BaseModel):
    title: Optional[str] = None
    target_job_id: Optional[str] = None
    structured_content: Optional[StructuredResumeContent] = None


class ResumeDraftResponse(BaseModel):
    id: str
    title: str
    target_job_id: Optional[str] = None
    candidate_id: Optional[str] = None
    original_resume_id: Optional[str] = None
    structured_content: StructuredResumeContent
    raw_markdown: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    versions_count: int = 0


class ResumeVersionResponse(BaseModel):
    id: str
    version_number: int
    label: str
    structured_content: StructuredResumeContent
    created_at: datetime.datetime


class MatchRequest(BaseModel):
    job_id: Optional[str] = None
    structured_content: Optional[StructuredResumeContent] = None
    compare_version_id: Optional[str] = None


class MatchResponse(BaseModel):
    match_score: float
    required_coverage: float
    preferred_coverage: float
    semantic_similarity: float
    lexical_similarity: float
    experience_depth: float
    domain_alignment: float
    matched_skills: List[str]
    missing_required_skills: List[str]
    missing_preferred_skills: List[str]
    score_breakdown: Dict[str, Any]
    suggestions: List[str]
    before_score: Optional[float] = None
    after_score: Optional[float] = None
    score_delta: Optional[float] = None


class AIAssistRequest(BaseModel):
    assist_type: str = Field(
        ..., description="summary | bullet | project | skill | keywords | review"
    )
    context_text: Optional[str] = ""
    target_job_id: Optional[str] = None
