"""
backend/app/api/v1/compare.py

Candidate Comparison endpoints — side-by-side analysis of multiple candidates for a job.

POST /api/v1/compare/{job_id}  — Compare 2-4 candidates against a job
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.dependencies import AnyAuthUser
from app.database import get_db
from app.models.candidate import Candidate
from app.models.job import Job, JobRequirement
from app.models.resume import Resume
from app.models.screening import ScreeningResult
from app.models.skill import ExtractedSkill

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/compare", tags=["Compare"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------

class CompareRequest(BaseModel):
    candidate_ids: list[int] = Field(..., min_length=2, max_length=6)


class CandidateSkillProfile(BaseModel):
    skill_name: str
    domain: str | None = None
    category: str | None = None
    frequency: int = 1


class CandidateCompareProfile(BaseModel):
    candidate_id: int
    candidate_name: str | None = None
    candidate_email: str | None = None

    # Screening scores
    relevance_score: float | None = None
    required_coverage: float | None = None
    preferred_coverage: float | None = None
    combined_match: float | None = None

    # Classification
    predicted_domain: str | None = None
    prediction_confidence: str | None = None

    # Skill lists
    skills: list[CandidateSkillProfile] = []
    matched_required: list[str] = []
    missing_required: list[str] = []
    matched_preferred: list[str] = []

    # Score breakdown (6-signal)
    score_breakdown: dict | None = None

    # Resume metadata
    resume_filename: str | None = None
    resume_text_length: int | None = None


class SkillOverlap(BaseModel):
    """Skills shared between all candidates vs unique to each."""
    shared_skills: list[str]  # Skills every candidate has
    per_candidate: dict[str, list[str]]  # candidate_id -> unique skills


class RadarDimension(BaseModel):
    dimension: str
    values: dict[str, float]  # candidate_id -> score (0-100)


class CompareResponse(BaseModel):
    job_id: int
    job_title: str
    candidates: list[CandidateCompareProfile]
    skill_overlap: SkillOverlap
    radar_chart: list[RadarDimension]
    ranking: list[dict]  # sorted by relevance_score desc
    ai_summary: str | None = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/{job_id}", response_model=CompareResponse)
def compare_candidates(
    job_id: int,
    payload: CompareRequest,
    current_user: AnyAuthUser,
    db: Session = Depends(get_db),
) -> dict:
    """
    Compare 2-6 candidates side-by-side for a given job.
    Returns enriched profiles, skill overlap analysis, radar chart data, and ranking.
    """
    # Validate job
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    candidates_data: list[dict] = []
    all_skills_per_candidate: dict[int, set[str]] = {}

    for cid in payload.candidate_ids:
        candidate = db.query(Candidate).filter(Candidate.id == cid).first()
        if not candidate:
            raise HTTPException(status_code=404, detail=f"Candidate {cid} not found.")

        # Get best screening result for this candidate-job pair
        screening = (
            db.query(ScreeningResult)
            .filter(
                ScreeningResult.candidate_id == cid,
                ScreeningResult.job_id == job_id,
            )
            .order_by(ScreeningResult.relevance_score.desc().nulls_last())
            .first()
        )

        # Get resume and skills
        resume = (
            db.query(Resume)
            .filter(Resume.candidate_id == cid)
            .order_by(Resume.uploaded_at.desc())
            .first()
        )

        skills: list[dict] = []
        skill_names: set[str] = set()
        if resume:
            extracted = (
                db.query(ExtractedSkill)
                .filter(ExtractedSkill.resume_id == resume.id)
                .all()
            )
            for s in extracted:
                skills.append({
                    "skill_name": s.canonical_name,
                    "domain": s.domain,
                    "category": s.category,
                    "frequency": s.frequency,
                })
                skill_names.add(s.canonical_name.lower())

        all_skills_per_candidate[cid] = skill_names

        # Parse screening JSON fields
        matched_required: list[str] = []
        missing_required: list[str] = []
        matched_preferred: list[str] = []
        score_breakdown: dict | None = None

        if screening:
            try:
                matched_required = json.loads(screening.matched_required_skills or "[]")
            except (json.JSONDecodeError, TypeError):
                pass
            try:
                missing_required = json.loads(screening.missing_required_skills or "[]")
            except (json.JSONDecodeError, TypeError):
                pass
            try:
                matched_preferred = json.loads(screening.matched_preferred_skills or "[]")
            except (json.JSONDecodeError, TypeError):
                pass
            try:
                score_breakdown = json.loads(screening.score_breakdown or "{}")
            except (json.JSONDecodeError, TypeError):
                pass

        profile = {
            "candidate_id": cid,
            "candidate_name": candidate.display_name,
            "candidate_email": candidate.email,
            "relevance_score": screening.relevance_score if screening else None,
            "required_coverage": screening.required_skill_coverage if screening else None,
            "preferred_coverage": screening.preferred_skill_coverage if screening else None,
            "combined_match": screening.combined_skill_match if screening else None,
            "predicted_domain": screening.predicted_domain if screening else (resume.predicted_domain if resume else None),
            "prediction_confidence": screening.prediction_confidence if screening else (resume.prediction_confidence if resume else None),
            "skills": skills,
            "matched_required": matched_required,
            "missing_required": missing_required,
            "matched_preferred": matched_preferred,
            "score_breakdown": score_breakdown,
            "resume_filename": resume.original_filename if resume else None,
            "resume_text_length": resume.text_char_count if resume else None,
        }
        candidates_data.append(profile)

    # --- Skill Overlap Analysis ---
    if all_skills_per_candidate:
        all_sets = list(all_skills_per_candidate.values())
        shared = set.intersection(*all_sets) if all_sets else set()

        per_candidate_unique: dict[str, list[str]] = {}
        for cid, skills_set in all_skills_per_candidate.items():
            others = set()
            for other_cid, other_set in all_skills_per_candidate.items():
                if other_cid != cid:
                    others.update(other_set)
            unique = skills_set - others
            per_candidate_unique[str(cid)] = sorted(unique)

        skill_overlap = {
            "shared_skills": sorted(shared),
            "per_candidate": per_candidate_unique,
        }
    else:
        skill_overlap = {"shared_skills": [], "per_candidate": {}}

    # --- Radar Chart Data ---
    dimensions = [
        "Required Coverage",
        "Preferred Coverage",
        "Combined Match",
        "Relevance Score",
        "Skill Count",
        "Resume Depth",
    ]
    radar_chart = []
    for dim in dimensions:
        values: dict[str, float] = {}
        for cd in candidates_data:
            cid_str = str(cd["candidate_id"])
            if dim == "Required Coverage":
                values[cid_str] = cd.get("required_coverage") or 0
            elif dim == "Preferred Coverage":
                values[cid_str] = cd.get("preferred_coverage") or 0
            elif dim == "Combined Match":
                values[cid_str] = cd.get("combined_match") or 0
            elif dim == "Relevance Score":
                values[cid_str] = cd.get("relevance_score") or 0
            elif dim == "Skill Count":
                # Normalize to 0-100 (cap at 30 skills = 100)
                count = len(cd.get("skills", []))
                values[cid_str] = min(100, (count / 30) * 100)
            elif dim == "Resume Depth":
                # Normalize text length to 0-100 (cap at 5000 chars = 100)
                length = cd.get("resume_text_length") or 0
                values[cid_str] = min(100, (length / 5000) * 100)
        radar_chart.append({"dimension": dim, "values": values})

    # --- Ranking ---
    ranking = sorted(
        [
            {
                "candidate_id": cd["candidate_id"],
                "candidate_name": cd["candidate_name"],
                "relevance_score": cd.get("relevance_score") or 0,
                "rank": 0,
            }
            for cd in candidates_data
        ],
        key=lambda x: x["relevance_score"],
        reverse=True,
    )
    for i, r in enumerate(ranking):
        r["rank"] = i + 1

    # --- AI Summary (static for now, can be replaced with LLM call) ---
    ai_summary = _generate_comparison_summary(candidates_data, job)

    return {
        "job_id": job_id,
        "job_title": job.title,
        "candidates": candidates_data,
        "skill_overlap": skill_overlap,
        "radar_chart": radar_chart,
        "ranking": ranking,
        "ai_summary": ai_summary,
    }


def _generate_comparison_summary(candidates: list[dict], job: Job) -> str:
    """Generate a deterministic comparison summary without LLM dependency."""
    if len(candidates) < 2:
        return "Need at least 2 candidates to compare."

    sorted_c = sorted(candidates, key=lambda x: x.get("relevance_score") or 0, reverse=True)
    top = sorted_c[0]
    runner = sorted_c[1]

    top_name = top.get("candidate_name") or f"Candidate #{top['candidate_id']}"
    runner_name = runner.get("candidate_name") or f"Candidate #{runner['candidate_id']}"

    lines = [
        f"**Top Candidate: {top_name}** — ",
    ]

    top_score = top.get("relevance_score")
    runner_score = runner.get("relevance_score")

    if top_score and runner_score:
        diff = round(top_score - runner_score, 1)
        lines[0] += f"leads by {diff} points ({round(top_score, 1)}% vs {round(runner_score, 1)}%)."
    else:
        lines[0] += "has the strongest profile for this position."

    # Skill advantages
    top_skills = {s["skill_name"].lower() for s in top.get("skills", [])}
    runner_skills = {s["skill_name"].lower() for s in runner.get("skills", [])}
    top_unique = top_skills - runner_skills
    runner_unique = runner_skills - top_skills

    if top_unique:
        lines.append(f"\n{top_name} brings unique skills: {', '.join(sorted(list(top_unique)[:5]))}.")
    if runner_unique:
        lines.append(f"\n{runner_name} offers: {', '.join(sorted(list(runner_unique)[:5]))}.")

    # Missing skills warning
    top_missing = top.get("missing_required", [])
    if top_missing:
        lines.append(f"\n⚠️ Even the top candidate is missing: {', '.join(top_missing[:4])}.")

    return " ".join(lines)
