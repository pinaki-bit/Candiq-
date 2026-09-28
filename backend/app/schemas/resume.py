"""
backend/app/schemas/resume.py

Pydantic v2 schemas for Resume upload and processing results.
"""

from __future__ import annotations

import datetime

from pydantic import BaseModel, Field


class ResumeRead(BaseModel):
    id: int
    public_id: str
    candidate_id: int | None
    original_filename: str
    file_size_bytes: int
    page_count: int | None
    status: str
    error_message: str | None
    text_char_count: int | None
    predicted_domain: str | None
    prediction_confidence: str | None
    classification_status: str | None = None
    review_required: bool | None = None
    ood_status: str | None = None
    policy_version: str | None = None
    policy_reason: str | None = None
    uploaded_at: datetime.datetime
    processed_at: datetime.datetime | None

    # extracted_text is intentionally EXCLUDED from API responses
    model_config = {"from_attributes": True}


class ResumeUploadResponse(BaseModel):
    """Returned immediately after a successful upload (before processing)."""
    public_id: str
    status: str
    message: str


class ExtractedSkillRead(BaseModel):
    id: int
    canonical_name: str
    matched_text: str
    domain: str | None
    category: str | None
    evidence_snippet: str | None
    extraction_method: str
    frequency: int

    model_config = {"from_attributes": True}


class ResumeDetailRead(ResumeRead):
    """Full resume detail including extracted skills."""
    extracted_skills: list[ExtractedSkillRead] = []


class BulletRewriteRequest(BaseModel):
    bullet: str = Field(..., min_length=5, description="The original resume bullet point text.")
    mode: str = Field(default="STAR", description="Optimization mode: STAR | TECHNICAL | ATS")
    target_job_title: str | None = Field(default=None, description="Optional target job title")
    target_skills: list[str] | None = Field(default=None, description="Optional target required skills")


class BulletRewriteResponse(BaseModel):
    original_bullet: str
    optimized_bullet: str
    mode: str
    key_changes: list[str]
    action_verb_used: str
    placeholders_needed: list[str]
    tokens_used: int
    estimated_cost_usd: float
    guardrail_warnings: list[str] = []


class CoverLetterRequest(BaseModel):
    job_title: str = Field(..., min_length=2, description="Target job position title")
    company_name: str = Field(..., min_length=2, description="Target hiring company name")
    candidate_name: str | None = Field(default="Candidate", description="Candidate name")
    candidate_skills: list[str] | None = Field(default=None, description="Key skills to highlight")
    candidate_text: str | None = Field(default=None, description="Resume text summary or context")
    job_description: str | None = Field(default=None, description="Job description text")
    tone: str = Field(default="PROFESSIONAL", description="Tone: PROFESSIONAL | ENTHUSIASTIC | EXECUTIVE")


class CoverLetterResponse(BaseModel):
    salutation: str
    opening_hook: str
    core_value_proposition: str
    company_alignment_paragraph: str
    closing_call_to_action: str
    full_cover_letter: str
    tone_used: str
    tokens_used: int
    estimated_cost_usd: float
    guardrail_warnings: list[str] = []


class LiveResumeAnalysisRequest(BaseModel):
    resume_markdown: str = Field(..., min_length=1, description="Raw resume text or markdown")
    job_description: str | None = Field(default=None, description="Optional target job description")
    target_skills: list[str] | None = Field(default=None, description="Optional list of target skills")


class LiveResumeAnalysisResponse(BaseModel):
    char_count: int
    word_count: int
    estimated_pages: int
    ats_score: float
    extracted_skills: list[str]
    matched_skills: list[str]
    missing_skills: list[str]
    live_match_score: float
    ats_warnings: list[str] = []
    suggestions: list[str] = []


class ATSCheckRequest(BaseModel):
    resume_text: str = Field(..., min_length=10, description="Resume text to analyze for ATS compliance")


class ATSCheckResponse(BaseModel):
    overall_score: float
    structure_score: float
    readability_score: float
    contact_score: float
    density_score: float
    compliance_category: str
    detected_sections: list[str]
    missing_essential_sections: list[str]
    critical_issues: list[str] = []
    warnings: list[str] = []
    actionable_recommendations: list[str] = []
