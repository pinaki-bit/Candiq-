"""
backend/app/services/discovery_service.py

Phase 36 — Advanced Candidate Discovery, Semantic Search & Hiring Intelligence Service.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.models.job import Job
from app.models.resume import ProcessingStatus, Resume
from app.models.screening import ScreeningResult
from app.schemas.discovery import (
    CandidateCompareItem,
    CandidateCompareResponse,
    DiscoveryCandidateResult,
    DiscoverySearchResponse,
    JobCandidateDiscoveryResult,
    JobCandidateDiscoveryResponse,
    ParsedQueryFilters,
    SimilarCandidateItem,
    SimilarCandidateResponse,
    SimilarJobItem,
    SimilarJobResponse,
)
from app.services.embedding_service import get_embedding_service
from app.services.matching_service import (
    calculate_lexical_similarity,
    compute_hybrid_match,
    extract_job_skills,
)
from app.services.skill_service import match_skills

logger = logging.getLogger(__name__)


def search_candidates(
    db: Session,
    query: str,
    tenant_id: str,
    domain_filter: Optional[str] = None,
    min_required_cov: Optional[float] = None,
    min_preferred_cov: Optional[float] = None,
    min_semantic_sim: Optional[float] = None,
    ood_status_filter: Optional[str] = None,
    review_status_filter: Optional[str] = None,
    required_skills_filter: Optional[List[str]] = None,
    job_id_filter: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
) -> DiscoverySearchResponse:
    """
    Semantic vector search + NLP skill filtering across active candidates and resumes.
    """
    cleaned_query = (query or "").strip()

    # 1. NLP skill extraction from query
    query_extracted_skills = [s.canonical_name for s in match_skills(cleaned_query)] if cleaned_query else []

    parsed_filters = ParsedQueryFilters(
        extracted_skills=query_extracted_skills,
        extracted_domain=domain_filter,
        min_semantic_similarity=min_semantic_sim,
        min_required_coverage=min_required_cov,
    )

    # 2. Fetch candidates in tenant
    cand_query = db.query(Candidate)
    if hasattr(Candidate, "tenant_id"):
        cand_query = cand_query.filter(Candidate.tenant_id == tenant_id)

    candidates = cand_query.all()
    if not candidates:
        return DiscoverySearchResponse(
            query=cleaned_query,
            parsed_filters=parsed_filters,
            total_count=0,
            page=page,
            page_size=page_size,
            results=[],
        )

    # If job_id_filter is provided, fetch target job
    job = None
    if job_id_filter:
        if job_id_filter.isdigit():
            job = db.query(Job).filter(Job.id == int(job_id_filter)).first()
        else:
            job = db.query(Job).filter(Job.public_id == job_id_filter).first()

    # 3. Vector embedding of search query
    embedder = get_embedding_service()
    query_vector = embedder.embed_document(cleaned_query) if cleaned_query else []

    results_list: List[DiscoveryCandidateResult] = []

    for cand in candidates:
        # Latest completed or needs_review resume
        resume = (
            db.query(Resume)
            .filter(
                Resume.candidate_id == cand.id,
                Resume.status.in_([ProcessingStatus.COMPLETED, ProcessingStatus.NEEDS_REVIEW]),
            )
            .order_by(Resume.uploaded_at.desc())
            .first()
        )
        if not resume or not resume.extracted_text:
            continue

        # Review status filter
        if review_status_filter and cand.review_status != review_status_filter:
            continue

        # OOD status filter
        res_ood = resume.ood_status or "in_domain_like"
        if ood_status_filter and res_ood != ood_status_filter:
            continue

        # Domain filter
        cand_domain = getattr(cand, "domain", None) or (resume.predicted_domain if resume else None)
        if domain_filter and cand_domain:
            if domain_filter.lower() not in cand_domain.lower():
                continue

        text = resume.extracted_text or ""
        cand_skills = [s.canonical_name for s in (resume.extracted_skills or [])]
        if not cand_skills:
            cand_skills = [s.canonical_name for s in match_skills(text)]

        cand_skills_lower = {s.lower() for s in cand_skills}

        # Vector semantic similarity
        if query_vector:
            res_vec = embedder.embed_document(text[:2000])
            sem_sim = round(embedder.similarity(query_vector, res_vec) * 100.0, 2)
        else:
            sem_sim = 50.0

        if min_semantic_sim is not None and sem_sim < min_semantic_sim:
            continue

        # Check job screening result if job context exists
        sr = None
        req_cov = None
        pref_cov = None
        matched_req = []
        missing_req = []
        missing_pref = []

        if job:
            sr = (
                db.query(ScreeningResult)
                .filter(ScreeningResult.candidate_id == cand.id, ScreeningResult.job_id == job.id)
                .first()
            )
            req_skills, pref_skills = extract_job_skills(job.requirements)
            match_res = compute_hybrid_match(
                required_skills=req_skills,
                preferred_skills=pref_skills,
                candidate_skills=resume.extracted_skills or [],
                resume_text=text,
                job_description=job.description or "",
            )
            req_cov = match_res.required_coverage
            pref_cov = match_res.preferred_coverage
            matched_req = match_res.matched_required
            missing_req = match_res.missing_required
            all_pref_names = [p[0] for p in pref_skills]
            missing_pref = [p for p in all_pref_names if p not in match_res.matched_preferred]

            if min_required_cov is not None and req_cov < min_required_cov:
                continue
            if min_preferred_cov is not None and pref_cov < min_preferred_cov:
                continue
        else:
            # Query skill match
            query_skills_set = {s.lower() for s in (query_extracted_skills + (required_skills_filter or []))}
            if query_skills_set:
                matched_set = query_skills_set.intersection(cand_skills_lower)
                missing_set = query_skills_set - matched_set
                req_cov = round((len(matched_set) / len(query_skills_set)) * 100.0, 2)
                matched_req = sorted([s for s in cand_skills if s.lower() in matched_set])
                missing_req = sorted(list(missing_set))
            else:
                req_cov = 50.0
                matched_req = cand_skills[:5]

        # Explicit Discovery Relevance Formula:
        # Discovery Relevance = 0.50 * Semantic Similarity + 0.35 * Required Coverage + 0.15 * Domain Alignment
        conf_bonus = 100.0 if (resume.prediction_confidence or "").lower() == "high" else 50.0
        discovery_score = round(0.50 * sem_sim + 0.35 * (req_cov or 50.0) + 0.15 * conf_bonus, 2)
        discovery_score = max(0.0, min(100.0, discovery_score))

        # Snippet extraction
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        snippet = lines[0] if lines else "Candidate resume"
        if cleaned_query:
            for l in lines:
                if any(w in l.lower() for w in cleaned_query.lower().split()):
                    snippet = l[:160]
                    break

        explanation = (
            f"Matched {len(matched_req)} skill(s) ({', '.join(matched_req[:3])}). "
            f"Semantic vector similarity is {sem_sim}% with query context."
        )

        results_list.append(
            DiscoveryCandidateResult(
                candidate_id=cand.public_id,
                public_id=cand.public_id,
                full_name=getattr(cand, "full_name", None) or getattr(cand, "display_name", None) or getattr(cand, "reference_code", None) or "Candidate",
                email=getattr(cand, "email", None),
                phone=getattr(cand, "phone", None),
                domain=cand_domain,
                prediction_confidence=resume.prediction_confidence if resume else None,
                existing_screening_score=sr.relevance_score if sr else None,
                discovery_relevance_score=discovery_score,
                semantic_similarity=sem_sim,
                required_coverage=req_cov,
                preferred_coverage=pref_cov,
                matched_skills=matched_req,
                missing_required_skills=missing_req,
                missing_preferred_skills=missing_pref,
                ood_status=res_ood,
                review_status=getattr(cand, "review_status", None) or "pending",
                snippet=snippet,
                explanation=explanation,
            )
        )

    # Sort descending by discovery relevance score
    results_list.sort(key=lambda x: x.discovery_relevance_score, reverse=True)

    # Paginate
    total_count = len(results_list)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_results = results_list[start_idx:end_idx]

    return DiscoverySearchResponse(
        query=cleaned_query,
        parsed_filters=parsed_filters,
        total_count=total_count,
        page=page,
        page_size=page_size,
        results=paginated_results,
    )


def get_job_candidates_discovery(
    db: Session,
    job: Job,
    tenant_id: str,
    page: int = 1,
    page_size: int = 10,
    sort_by: str = "screening_score",
    order: str = "desc",
) -> JobCandidateDiscoveryResponse:
    """
    Retrieves candidates matched against a specific job with discovery relevance metrics.
    """
    embedder = get_embedding_service()
    job_vector = embedder.embed_document(job.description or "")

    # Fetch screening results for job
    srs = db.query(ScreeningResult).filter(ScreeningResult.job_id == job.id).all()

    req_skills, pref_skills = extract_job_skills(job.requirements)
    all_pref_names = [p[0] for p in pref_skills]

    results: List[JobCandidateDiscoveryResult] = []

    for sr in srs:
        cand = db.query(Candidate).filter(Candidate.id == sr.candidate_id).first()
        if not cand:
            continue

        user_tenant = getattr(cand, "tenant_id", "default_tenant")
        if user_tenant != tenant_id and tenant_id != "default_tenant":
            continue

        resume = (
            db.query(Resume)
            .filter(
                Resume.candidate_id == cand.id,
                Resume.status.in_([ProcessingStatus.COMPLETED, ProcessingStatus.NEEDS_REVIEW]),
            )
            .order_by(Resume.uploaded_at.desc())
            .first()
        )
        text = resume.extracted_text if (resume and resume.extracted_text) else ""

        # Calculate semantic similarity
        sem_sim = 50.0
        if text and job_vector:
            res_vec = embedder.embed_document(text[:2000])
            sem_sim = round(embedder.similarity(job_vector, res_vec) * 100.0, 2)

        matched_req = json.loads(sr.matched_required_skills or "[]")
        missing_req = json.loads(sr.missing_required_skills or "[]")
        matched_pref = json.loads(sr.matched_preferred_skills or "[]")
        missing_pref = [p for p in all_pref_names if p not in matched_pref]

        req_cov = getattr(sr, "required_skill_coverage", getattr(sr, "required_coverage", 0.0)) or 0.0
        pref_cov = getattr(sr, "preferred_skill_coverage", getattr(sr, "preferred_coverage", 0.0)) or 0.0

        # Discovery relevance score for job-specific view
        disc_score = round(0.40 * sem_sim + 0.35 * req_cov + 0.25 * sr.relevance_score, 2)

        results.append(
            JobCandidateDiscoveryResult(
                candidate_id=cand.public_id,
                public_id=cand.public_id,
                full_name=getattr(cand, "full_name", None) or getattr(cand, "display_name", None) or getattr(cand, "reference_code", None) or "Candidate",
                email=getattr(cand, "email", None),
                domain=getattr(cand, "domain", None) or (resume.predicted_domain if resume else None),
                screening_score=sr.relevance_score,
                discovery_relevance_score=disc_score,
                required_coverage=req_cov,
                preferred_coverage=pref_cov,
                semantic_similarity=sem_sim,
                matched_skills=matched_req + matched_pref,
                missing_required_skills=missing_req,
                missing_preferred_skills=missing_pref,
                ood_status=resume.ood_status if resume else "in_domain_like",
                review_status=getattr(cand, "review_status", None) or getattr(sr, "review_status", "pending"),
            )
        )

    # Sorting
    reverse_flag = order.lower() == "desc"
    if sort_by == "semantic_similarity":
        results.sort(key=lambda x: x.semantic_similarity, reverse=reverse_flag)
    elif sort_by == "required_coverage":
        results.sort(key=lambda x: x.required_coverage, reverse=reverse_flag)
    elif sort_by == "discovery_relevance":
        results.sort(key=lambda x: x.discovery_relevance_score, reverse=reverse_flag)
    else:
        results.sort(key=lambda x: x.screening_score, reverse=reverse_flag)

    total_count = len(results)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_results = results[start_idx:end_idx]

    return JobCandidateDiscoveryResponse(
        job_id=job.public_id,
        job_title=job.title,
        total_count=total_count,
        page=page,
        page_size=page_size,
        results=paginated_results,
    )


def find_similar_candidates(
    db: Session,
    candidate_id: str,
    tenant_id: str,
    limit: int = 5,
) -> SimilarCandidateResponse:
    """
    Finds candidates semantically similar to target candidate using production MiniLM embeddings.
    """
    # Fetch target candidate
    query = db.query(Candidate)
    if candidate_id.isdigit():
        target_cand = query.filter(Candidate.id == int(candidate_id)).first()
    else:
        target_cand = query.filter(Candidate.public_id == candidate_id).first()

    if not target_cand:
        raise ValueError(f"Candidate '{candidate_id}' not found.")

    target_resume = (
        db.query(Resume)
        .filter(
            Resume.candidate_id == target_cand.id,
            Resume.status.in_([ProcessingStatus.COMPLETED, ProcessingStatus.NEEDS_REVIEW]),
        )
        .order_by(Resume.uploaded_at.desc())
        .first()
    )

    if not target_resume or not target_resume.extracted_text:
        return SimilarCandidateResponse(
            target_candidate_id=target_cand.public_id,
            similar_candidates=[],
        )

    target_text = target_resume.extracted_text
    target_skills = {s.canonical_name.lower() for s in (target_resume.extracted_skills or [])}

    embedder = get_embedding_service()
    target_vector = embedder.embed_document(target_text[:2000])

    other_cands = db.query(Candidate).filter(Candidate.id != target_cand.id).all()

    similar_list: List[SimilarCandidateItem] = []

    for other in other_cands:
        other_resume = (
            db.query(Resume)
            .filter(
                Resume.candidate_id == other.id,
                Resume.status.in_([ProcessingStatus.COMPLETED, ProcessingStatus.NEEDS_REVIEW]),
            )
            .order_by(Resume.uploaded_at.desc())
            .first()
        )
        if not other_resume or not other_resume.extracted_text:
            continue

        other_text = other_resume.extracted_text
        other_vector = embedder.embed_document(other_text[:2000])
        sem_sim = round(embedder.similarity(target_vector, other_vector) * 100.0, 2)

        other_skills = [s.canonical_name for s in (other_resume.extracted_skills or [])]
        shared = [s for s in other_skills if s.lower() in target_skills]

        similar_list.append(
            SimilarCandidateItem(
                candidate_id=other.public_id,
                public_id=other.public_id,
                full_name=getattr(other, "full_name", None) or getattr(other, "display_name", None) or getattr(other, "reference_code", None) or "Candidate",
                domain=getattr(other, "domain", None) or (other_resume.predicted_domain if other_resume else None),
                semantic_similarity=sem_sim,
                shared_skills=shared,
                label="Semantically similar — not automatically equivalent.",
            )
        )

    similar_list.sort(key=lambda x: x.semantic_similarity, reverse=True)
    top_similar = similar_list[:limit]

    return SimilarCandidateResponse(
        target_candidate_id=target_cand.public_id,
        label="Semantically similar — not automatically equivalent.",
        similar_candidates=top_similar,
    )


def find_similar_jobs(
    db: Session,
    job_id: str,
    tenant_id: str,
    limit: int = 5,
) -> SimilarJobResponse:
    """
    Finds jobs semantically similar to target job using production MiniLM embeddings.
    """
    query = db.query(Job)
    if job_id.isdigit():
        target_job = query.filter(Job.id == int(job_id)).first()
    else:
        target_job = query.filter(Job.public_id == job_id).first()

    if not target_job:
        raise ValueError(f"Job '{job_id}' not found.")

    embedder = get_embedding_service()
    target_vector = embedder.embed_document(target_job.description or "")
    target_skills = {r.skill_name.lower() for r in target_job.requirements}

    other_jobs = db.query(Job).filter(Job.id != target_job.id, Job.is_active == True).all()

    similar_list: List[SimilarJobItem] = []

    for other in other_jobs:
        job_tenant = getattr(other, "tenant_id", None)
        if job_tenant and job_tenant != tenant_id and tenant_id != "default_tenant":
            continue

        other_vector = embedder.embed_document(other.description or "")
        sem_sim = round(embedder.similarity(target_vector, other_vector) * 100.0, 2)

        other_skills = [r.skill_name for r in other.requirements]
        shared = [s for s in other_skills if s.lower() in target_skills]

        similar_list.append(
            SimilarJobItem(
                job_id=other.public_id,
                public_id=other.public_id,
                title=other.title,
                department=other.department,
                domain=other.domain,
                semantic_similarity=sem_sim,
                shared_skills=shared,
            )
        )

    similar_list.sort(key=lambda x: x.semantic_similarity, reverse=True)
    top_jobs = similar_list[:limit]

    return SimilarJobResponse(
        target_job_id=target_job.public_id,
        target_job_title=target_job.title,
        similar_jobs=top_jobs,
    )


def compare_candidates(
    db: Session,
    candidate_ids: List[str],
    job_id: Optional[str] = None,
    tenant_id: str = "default_tenant",
) -> CandidateCompareResponse:
    """
    Generates side-by-side factual comparison matrix for specified candidate IDs.
    """
    job = None
    if job_id:
        if job_id.isdigit():
            job = db.query(Job).filter(Job.id == int(job_id)).first()
        else:
            job = db.query(Job).filter(Job.public_id == job_id).first()

    embedder = get_embedding_service()
    job_vector = embedder.embed_document(job.description or "") if job else []

    comparison_list: List[CandidateCompareItem] = []

    for c_id in candidate_ids:
        query = db.query(Candidate)
        if c_id.isdigit():
            cand = query.filter(Candidate.id == int(c_id)).first()
        else:
            cand = query.filter(Candidate.public_id == c_id).first()

        if not cand:
            continue

        resume = (
            db.query(Resume)
            .filter(
                Resume.candidate_id == cand.id,
                Resume.status.in_([ProcessingStatus.COMPLETED, ProcessingStatus.NEEDS_REVIEW]),
            )
            .order_by(Resume.uploaded_at.desc())
            .first()
        )
        text = resume.extracted_text if (resume and resume.extracted_text) else ""

        sr = None
        sem_sim = None
        req_cov = None
        pref_cov = None
        matched_req = []
        missing_req = []
        missing_pref = []

        if job:
            sr = (
                db.query(ScreeningResult)
                .filter(ScreeningResult.candidate_id == cand.id, ScreeningResult.job_id == job.id)
                .first()
            )
            req_skills, pref_skills = extract_job_skills(job.requirements)
            match_res = compute_hybrid_match(
                required_skills=req_skills,
                preferred_skills=pref_skills,
                candidate_skills=resume.extracted_skills if resume else [],
                resume_text=text,
                job_description=job.description or "",
            )
            req_cov = match_res.required_coverage
            pref_cov = match_res.preferred_coverage
            matched_req = match_res.matched_required
            missing_req = match_res.missing_required
            all_pref_names = [p[0] for p in pref_skills]
            missing_pref = [p for p in all_pref_names if p not in match_res.matched_preferred]

            if job_vector and text:
                res_vec = embedder.embed_document(text[:2000])
                sem_sim = round(embedder.similarity(job_vector, res_vec) * 100.0, 2)
        else:
            cand_skills = [s.canonical_name for s in (resume.extracted_skills if resume else [])]
            matched_req = cand_skills

        comparison_list.append(
            CandidateCompareItem(
                candidate_id=cand.public_id,
                full_name=getattr(cand, "full_name", None) or getattr(cand, "display_name", None) or getattr(cand, "reference_code", None) or "Candidate",
                email=getattr(cand, "email", None),
                domain=getattr(cand, "domain", None) or (resume.predicted_domain if resume else None),
                screening_score=sr.relevance_score if sr else None,
                required_coverage=req_cov,
                preferred_coverage=pref_cov,
                semantic_similarity=sem_sim,
                matched_skills=matched_req,
                missing_required_skills=missing_req,
                missing_preferred_skills=missing_pref,
                ood_status=resume.ood_status if resume else "in_domain_like",
                review_status=getattr(cand, "review_status", None) or (sr.review_status if sr else "pending"),
            )
        )

    return CandidateCompareResponse(
        target_job_id=job.public_id if job else None,
        comparison_matrix=comparison_list,
    )
