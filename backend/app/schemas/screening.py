"""
backend/app/schemas/screening.py

Pydantic v2 schemas for ScreeningResult.
"""

from __future__ import annotations

import datetime
import json
from typing import Any

from pydantic import BaseModel, Field, model_validator


class ScreeningResultRead(BaseModel):
    id: int
    public_id: str
    resume_id: int
    job_id: int
    candidate_id: int | None

    required_skill_coverage: float | None
    preferred_skill_coverage: float | None
    combined_skill_match: float | None

    matched_required_skills: list[str]
    missing_required_skills: list[str]
    matched_preferred_skills: list[str]

    predicted_domain: str | None
    prediction_confidence: str | None
    relevance_score: float | None
    score_breakdown: dict[str, Any] | None

    review_status: str
    review_notes: str | None
    screened_at: datetime.datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def parse_json_fields(cls, data: Any) -> Any:
        """Parse JSON string fields into Python objects."""
        if hasattr(data, "__dict__"):
            # ORM object
            obj = data
            for field in (
                "matched_required_skills",
                "missing_required_skills",
                "matched_preferred_skills",
            ):
                val = getattr(obj, field, None)
                if isinstance(val, str):
                    try:
                        setattr(obj, field, json.loads(val))
                    except (json.JSONDecodeError, ValueError):
                        setattr(obj, field, [])
                elif val is None:
                    setattr(obj, field, [])

            breakdown = getattr(obj, "score_breakdown", None)
            if isinstance(breakdown, str):
                try:
                    obj.score_breakdown = json.loads(breakdown)
                except Exception:
                    obj.score_breakdown = None
        return data


class ReviewUpdate(BaseModel):
    review_status: str
    review_notes: str | None = None


class InterviewQuestionSchema(BaseModel):
    question_id: int
    category: str
    question: str
    why_this_question: str
    expected_key_points: list[str]
    difficulty: str


class InterviewKitRequest(BaseModel):
    job_title: str | None = "Software Engineer"
    candidate_skills: list[str] | None = None
    missing_skills: list[str] | None = None
    resume_text: str | None = None
    job_description: str | None = None


class InterviewKitResponse(BaseModel):
    job_title: str
    questions: list[InterviewQuestionSchema]
    tokens_used: int
    estimated_cost_usd: float
    guardrail_warnings: list[str] = []


class TalentSearchRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Natural language search query")
    domain_filter: str | None = Field(default=None, description="Optional domain filter")
    min_confidence: str | None = Field(default=None, description="Optional min confidence: low|medium|high")
    required_skills: list[str] | None = Field(default=None, description="Optional list of required skills")
    limit: int = Field(default=10, ge=1, le=50, description="Max results to return")


class TalentCandidateResultSchema(BaseModel):
    resume_id: int
    public_id: str
    original_filename: str
    predicted_domain: str | None
    prediction_confidence: str | None
    hybrid_score: float
    semantic_similarity: float
    matched_skills: list[str]
    snippet: str


class TalentSearchResponse(BaseModel):
    query: str
    total_candidates_searched: int
    results_count: int
    results: list[TalentCandidateResultSchema]
