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
        """Parse JSON string fields into Python objects without mutating live ORM state."""
        if hasattr(data, "__dict__"):
            # Create a shallow dict copy so we don't mutate live SQLAlchemy ORM model state
            d = {
                "id": getattr(data, "id", None),
                "public_id": getattr(data, "public_id", None),
                "resume_id": getattr(data, "resume_id", None),
                "job_id": getattr(data, "job_id", None),
                "candidate_id": getattr(data, "candidate_id", None),
                "required_skill_coverage": getattr(data, "required_skill_coverage", None),
                "preferred_skill_coverage": getattr(data, "preferred_skill_coverage", None),
                "combined_skill_match": getattr(data, "combined_skill_match", None),
                "predicted_domain": getattr(data, "predicted_domain", None),
                "prediction_confidence": getattr(data, "prediction_confidence", None),
                "relevance_score": getattr(data, "relevance_score", None),
                "review_status": getattr(data, "review_status", None),
                "review_notes": getattr(data, "review_notes", None),
                "screened_at": getattr(data, "screened_at", None),
            }
            for field in (
                "matched_required_skills",
                "missing_required_skills",
                "matched_preferred_skills",
            ):
                val = getattr(data, field, None)
                if isinstance(val, str):
                    try:
                        d[field] = json.loads(val)
                    except (json.JSONDecodeError, ValueError):
                        d[field] = []
                elif isinstance(val, list):
                    d[field] = val
                else:
                    d[field] = []

            breakdown = getattr(data, "score_breakdown", None)
            if isinstance(breakdown, str):
                try:
                    d["score_breakdown"] = json.loads(breakdown)
                except Exception:
                    d["score_breakdown"] = None
            elif isinstance(breakdown, dict):
                d["score_breakdown"] = breakdown
            else:
                d["score_breakdown"] = None

            return d
        return data


class ReviewUpdate(BaseModel):
    review_status: str
    review_notes: str | None = None


class BulkReviewUpdate(BaseModel):
    result_ids: list[str]
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
