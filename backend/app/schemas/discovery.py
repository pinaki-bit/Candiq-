"""
backend/app/schemas/discovery.py

Phase 36 — Pydantic Schemas for Advanced Candidate Discovery, Semantic Search & Hiring Intelligence.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ParsedQueryFilters(BaseModel):
    extracted_skills: List[str] = Field(default_factory=list)
    extracted_domain: Optional[str] = None
    min_semantic_similarity: Optional[float] = None
    min_required_coverage: Optional[float] = None


class DiscoveryCandidateResult(BaseModel):
    candidate_id: str
    public_id: str
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    domain: Optional[str] = None
    prediction_confidence: Optional[str] = None
    existing_screening_score: Optional[float] = None
    discovery_relevance_score: float
    semantic_similarity: float
    required_coverage: Optional[float] = None
    preferred_coverage: Optional[float] = None
    matched_skills: List[str] = Field(default_factory=list)
    missing_required_skills: List[str] = Field(default_factory=list)
    missing_preferred_skills: List[str] = Field(default_factory=list)
    ood_status: Optional[str] = "in_domain_like"
    review_status: Optional[str] = "pending"
    snippet: str = ""
    explanation: str = ""


class DiscoverySearchResponse(BaseModel):
    query: str
    parsed_filters: ParsedQueryFilters
    total_count: int
    page: int
    page_size: int
    results: List[DiscoveryCandidateResult] = Field(default_factory=list)


class JobCandidateDiscoveryResult(BaseModel):
    candidate_id: str
    public_id: str
    full_name: str
    email: Optional[str] = None
    domain: Optional[str] = None
    screening_score: float
    discovery_relevance_score: float
    required_coverage: float
    preferred_coverage: float
    semantic_similarity: float
    matched_skills: List[str] = Field(default_factory=list)
    missing_required_skills: List[str] = Field(default_factory=list)
    missing_preferred_skills: List[str] = Field(default_factory=list)
    ood_status: Optional[str] = "in_domain_like"
    review_status: str = "pending"


class JobCandidateDiscoveryResponse(BaseModel):
    job_id: str
    job_title: str
    total_count: int
    page: int
    page_size: int
    results: List[JobCandidateDiscoveryResult] = Field(default_factory=list)


class SimilarCandidateItem(BaseModel):
    candidate_id: str
    public_id: str
    full_name: str
    domain: Optional[str] = None
    semantic_similarity: float
    shared_skills: List[str] = Field(default_factory=list)
    label: str = "Semantically similar — not automatically equivalent."


class SimilarCandidateResponse(BaseModel):
    target_candidate_id: str
    label: str = "Semantically similar — not automatically equivalent."
    similar_candidates: List[SimilarCandidateItem] = Field(default_factory=list)


class SimilarJobItem(BaseModel):
    job_id: str
    public_id: str
    title: str
    department: Optional[str] = None
    domain: Optional[str] = None
    semantic_similarity: float
    shared_skills: List[str] = Field(default_factory=list)


class SimilarJobResponse(BaseModel):
    target_job_id: str
    target_job_title: str
    similar_jobs: List[SimilarJobItem] = Field(default_factory=list)


class CandidateCompareRequest(BaseModel):
    candidate_ids: List[str]
    job_id: Optional[str] = None


class CandidateCompareItem(BaseModel):
    candidate_id: str
    full_name: str
    email: Optional[str] = None
    domain: Optional[str] = None
    screening_score: Optional[float] = None
    required_coverage: Optional[float] = None
    preferred_coverage: Optional[float] = None
    semantic_similarity: Optional[float] = None
    matched_skills: List[str] = Field(default_factory=list)
    missing_required_skills: List[str] = Field(default_factory=list)
    missing_preferred_skills: List[str] = Field(default_factory=list)
    ood_status: Optional[str] = None
    review_status: Optional[str] = None


class CandidateCompareResponse(BaseModel):
    target_job_id: Optional[str] = None
    comparison_matrix: List[CandidateCompareItem] = Field(default_factory=list)
