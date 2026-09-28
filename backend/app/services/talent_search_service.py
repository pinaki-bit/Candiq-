"""
backend/app/services/talent_search_service.py

Talent Semantic Search Engine.
Natural language candidate search pipeline (Query → Embed → Hybrid Filter & Rank).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.resume import Resume, ProcessingStatus
from app.services.embedding_service import get_embedding_service
from app.services.skill_service import match_skills

logger = logging.getLogger(__name__)


@dataclass
class TalentCandidateResult:
    resume_id: int
    public_id: str
    original_filename: str
    predicted_domain: Optional[str]
    prediction_confidence: Optional[str]
    hybrid_score: float
    semantic_similarity: float
    matched_skills: List[str]
    snippet: str


@dataclass
class TalentSearchResult:
    query: str
    total_candidates_searched: int
    results_count: int
    results: List[TalentCandidateResult] = field(default_factory=list)


def search_talent_pool(
    db: Session,
    query: str,
    domain_filter: Optional[str] = None,
    min_confidence: Optional[str] = None,
    required_skills: Optional[List[str]] = None,
    limit: int = 10,
) -> TalentSearchResult:
    """
    Search talent pool using hybrid semantic vector similarity and NLP skill matching.
    """
    cleaned_query = query.strip()
    if not cleaned_query:
        return TalentSearchResult(query=query, total_candidates_searched=0, results_count=0, results=[])

    # 1. Fetch active processed resumes
    q = db.query(Resume).filter(
        Resume.status.in_([ProcessingStatus.COMPLETED, ProcessingStatus.NEEDS_REVIEW]),
        Resume.extracted_text.isnot(None),
    )

    if domain_filter:
        q = q.filter(Resume.predicted_domain.ilike(f"%{domain_filter}%"))
    if min_confidence:
        q = q.filter(Resume.prediction_confidence.ilike(f"%{min_confidence}%"))

    resumes = q.all()
    total_searched = len(resumes)

    if not resumes:
        return TalentSearchResult(query=query, total_candidates_searched=0, results_count=0, results=[])

    # 2. Extract skills from natural language query
    query_extracted = match_skills(cleaned_query)
    query_skill_set = {s.canonical_name.lower() for s in query_extracted}
    if required_skills:
        query_skill_set.update(s.lower() for s in required_skills)

    # 3. Vector embedding of search query
    embedder = get_embedding_service()
    query_vector = embedder.embed_document(cleaned_query)

    ranked_candidates: List[TalentCandidateResult] = []

    for res in resumes:
        text = res.extracted_text or ""
        # Vector semantic similarity (0.0 to 1.0)
        res_vector = embedder.embed_document(text[:1500])
        sem_sim = round(embedder.similarity(query_vector, res_vector) * 100.0, 2)

        # NLP skill overlap
        if res.extracted_skills:
            res_skills = [s.canonical_name for s in res.extracted_skills]
        else:
            res_skills = [s.canonical_name for s in match_skills(text)]
        res_skills_set = {s.lower() for s in res_skills}
        
        matched_set = query_skill_set.intersection(res_skills_set)
        if query_skill_set:
            skill_score = (len(matched_set) / len(query_skill_set)) * 100.0
        else:
            skill_score = 50.0

        # Confidence bonus
        conf_bonus = 0.0
        if (res.prediction_confidence or "").lower() == "high":
            conf_bonus = 100.0
        elif (res.prediction_confidence or "").lower() == "medium":
            conf_bonus = 50.0

        # Hybrid Talent Rank Score: 55% Semantic Vector + 35% Skill Overlap + 10% Confidence
        hybrid_score = round(0.55 * sem_sim + 0.35 * skill_score + 0.10 * conf_bonus, 1)
        hybrid_score = max(0.0, min(100.0, hybrid_score))

        matched_names = sorted([s for s in res_skills if s.lower() in matched_set])

        # Extract relevant snippet from candidate text
        snippet_lines = [line.strip() for line in text.split("\n") if line.strip()]
        snippet = snippet_lines[0] if snippet_lines else "No text excerpt."
        for line in snippet_lines:
            if any(term in line.lower() for term in cleaned_query.lower().split()):
                snippet = line[:160]
                break

        ranked_candidates.append(
            TalentCandidateResult(
                resume_id=res.id,
                public_id=res.public_id,
                original_filename=res.original_filename,
                predicted_domain=res.predicted_domain,
                prediction_confidence=res.prediction_confidence,
                hybrid_score=hybrid_score,
                semantic_similarity=sem_sim,
                matched_skills=matched_names,
                snippet=snippet,
            )
        )

    # Sort descending by hybrid score
    ranked_candidates.sort(key=lambda c: c.hybrid_score, reverse=True)
    top_results = ranked_candidates[:limit]

    return TalentSearchResult(
        query=cleaned_query,
        total_candidates_searched=total_searched,
        results_count=len(top_results),
        results=top_results,
    )
