"""
backend/app/services/matching_service.py

Transparent skill-match formula.

Formula (configurable weights):
  required_coverage   = Σ(weight of matched required skills)
                        ─────────────────────────────────── × 100
                        Σ(weight of all required skills)

  preferred_coverage  = Σ(weight of matched preferred skills)
                        ──────────────────────────────────────── × 100
                        Σ(weight of all preferred skills)

  combined_match      = (req_weight × required_coverage)
                      + (pref_weight × preferred_coverage)
                        ──────────────────────────────────
                        (req_weight + pref_weight)

  → Result is always in [0, 100]. Weights are normalized.

Edge cases:
  - No required skills: required_coverage = 100.0 (vacuously satisfied).
  - No preferred skills: preferred_coverage = 0.0 and pref_weight treated as 0.
  - No skills at all: return "insufficient requirements" warning.
  - Division by zero: impossible given above rules.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

DEFAULT_REQUIRED_WEIGHT = 0.70   # 70% of combined score from required skills
DEFAULT_PREFERRED_WEIGHT = 0.30  # 30% from preferred skills


@dataclass
class MatchResult:
    required_coverage: float        # 0.0–100.0
    preferred_coverage: float       # 0.0–100.0
    combined_match: float           # 0.0–100.0
    matched_required: list[str]
    missing_required: list[str]
    matched_preferred: list[str]
    matched_evidence: dict[str, str] # Maps skill name to evidence snippet
    score_breakdown: dict           # explainability
    warning: str | None


def compute_match(
    required_skills: list[tuple[str, float]],    # [(skill_name, weight), ...]
    preferred_skills: list[tuple[str, float]],   # [(skill_name, weight), ...]
    candidate_skills: list,                      # list of SkillMatch objects
    required_weight: float = DEFAULT_REQUIRED_WEIGHT,
    preferred_weight: float = DEFAULT_PREFERRED_WEIGHT,
) -> MatchResult:
    """
    Compute skill-match scores between a job's requirements and a candidate's skills.

    Args:
        required_skills:  List of (canonical_skill_name, weight) for required skills.
        preferred_skills: List of (canonical_skill_name, weight) for preferred skills.
        candidate_skills: List of SkillMatch objects extracted from the candidate's resume.
        required_weight:  Relative weight of required coverage in the combined score.
        preferred_weight: Relative weight of preferred coverage in the combined score.

    Returns:
        MatchResult with full transparency breakdown.
    """
    # Normalize skill names for comparison and extract evidence
    candidate_skills_dict = {}
    for s in candidate_skills:
        if isinstance(s, str):
            candidate_skills_dict[s.lower()] = ""
        elif hasattr(s, "canonical_name"):
            candidate_skills_dict[s.canonical_name.lower()] = getattr(s, "evidence_snippet", "")
        elif isinstance(s, dict):
            name = s.get("canonical_name") or s.get("matched_text") or ""
            candidate_skills_dict[name.lower()] = s.get("evidence_snippet", "")
    candidate_lower = set(candidate_skills_dict.keys())

    # --- Guard: no skills at all ---
    if not required_skills and not preferred_skills:
        return MatchResult(
            required_coverage=0.0,
            preferred_coverage=0.0,
            combined_match=0.0,
            matched_required=[],
            missing_required=[],
            matched_preferred=[],
            matched_evidence={},
            score_breakdown={},
            warning="Insufficient job requirements for skill-match scoring.",
        )

    # --- Required skills ---
    matched_req: list[str] = []
    missing_req: list[str] = []
    matched_evidence: dict[str, str] = {}
    total_req_weight = 0.0
    matched_req_weight = 0.0

    for skill, weight in required_skills:
        total_req_weight += weight
        skill_lower = skill.lower()
        if skill_lower in candidate_lower:
            matched_req.append(skill)
            matched_req_weight += weight
            matched_evidence[skill] = candidate_skills_dict[skill_lower]
        else:
            missing_req.append(skill)

    if total_req_weight > 0:
        required_coverage = (matched_req_weight / total_req_weight) * 100.0
    else:
        # No required skills → vacuously satisfied
        required_coverage = 100.0

    # --- Preferred skills ---
    matched_pref: list[str] = []
    total_pref_weight = 0.0
    matched_pref_weight = 0.0

    for skill, weight in preferred_skills:
        total_pref_weight += weight
        skill_lower = skill.lower()
        if skill_lower in candidate_lower:
            matched_pref.append(skill)
            matched_pref_weight += weight
            matched_evidence[skill] = candidate_skills_dict[skill_lower]

    if total_pref_weight > 0:
        preferred_coverage = (matched_pref_weight / total_pref_weight) * 100.0
    else:
        preferred_coverage = 0.0
        preferred_weight = 0.0   # treat as absent

    # --- Combined score ---
    total_weight = required_weight + preferred_weight
    if total_weight == 0:
        combined_match = 0.0
    else:
        combined_match = (
            (required_weight * required_coverage)
            + (preferred_weight * preferred_coverage)
        ) / total_weight

    # Clamp to [0, 100] (should be guaranteed by formula, but defensive)
    combined_match = max(0.0, min(100.0, combined_match))

    # --- Explainability breakdown ---
    breakdown = {
        "formula": (
            "combined_match = "
            "(req_weight × required_coverage + pref_weight × preferred_coverage) "
            "/ (req_weight + pref_weight)"
        ),
        "required_coverage_pct": round(required_coverage, 2),
        "preferred_coverage_pct": round(preferred_coverage, 2),
        "required_weight_used": round(required_weight, 3),
        "preferred_weight_used": round(preferred_weight, 3),
        "matched_required_count": len(matched_req),
        "total_required_count": len(required_skills),
        "matched_preferred_count": len(matched_pref),
        "total_preferred_count": len(preferred_skills),
        "label": "skill_match_percentage (not a probability of job success)",
    }

    return MatchResult(
        required_coverage=round(required_coverage, 2),
        preferred_coverage=round(preferred_coverage, 2),
        combined_match=round(combined_match, 2),
        matched_required=matched_req,
        missing_required=missing_req,
        matched_preferred=matched_pref,
        matched_evidence=matched_evidence,
        score_breakdown=breakdown,
        warning=None,
    )


def calculate_lexical_similarity(text1: str, text2: str) -> float:
    """Calculate Jaccard lexical token overlap similarity (0.0 to 1.0)."""
    if not text1 or not text2:
        return 0.0
    t1_tokens = set(text1.lower().split())
    t2_tokens = set(text2.lower().split())
    if not t2_tokens or not t1_tokens:
        return 0.0
    intersection = t1_tokens.intersection(t2_tokens)
    union = t1_tokens.union(t2_tokens)
    return len(intersection) / len(union) if union else 0.0


def compute_hybrid_match(
    required_skills: list[tuple[str, float]],
    preferred_skills: list[tuple[str, float]],
    candidate_skills: list,
    resume_text: str = "",
    job_description: str = "",
    predicted_domain: str | None = None,
    job_domain: str | None = None,
    confidence: str | None = None,
    weights: dict | None = None,
) -> MatchResult:
    """
    6-Signal Hybrid Candidate Ranking Engine.

    Weights (Default):
      - Required Skill Coverage (35%)
      - Preferred Skill Coverage (15%)
      - Semantic Similarity (25% via EmbeddingService)
      - Lexical Similarity (10%)
      - Experience / Depth Relevance (10%)
      - Domain Classification Alignment (5%)

    Strict Constraint:
      - Semantic similarity or domain bonus NEVER satisfies or hides missing required skills.
    """
    from app.services.embedding_service import get_embedding_service

    default_weights = {
        "req": 0.35,
        "pref": 0.15,
        "sem": 0.25,
        "lex": 0.10,
        "exp": 0.10,
        "dom": 0.05,
    }
    w = {**default_weights, **(weights or {})}

    # Base lexical skill match
    base_match = compute_match(
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        candidate_skills=candidate_skills,
        required_weight=w["req"],
        preferred_weight=w["pref"],
    )

    s_req = base_match.required_coverage
    s_pref = base_match.preferred_coverage

    # Semantic similarity signal
    s_sem = 0.0
    if resume_text and job_description:
        embedder = get_embedding_service()
        v_res = embedder.embed_document(resume_text)
        v_job = embedder.embed_document(job_description)
        s_sem = round(embedder.similarity(v_res, v_job) * 100.0, 2)
    else:
        s_sem = base_match.combined_match

    # Lexical similarity signal (Jaccard token overlap)
    s_lex = 0.0
    if resume_text and job_description:
        res_tokens = set(resume_text.lower().split())
        job_tokens = set(job_description.lower().split())
        if job_tokens:
            intersection = res_tokens.intersection(job_tokens)
            union = res_tokens.union(job_tokens)
            s_lex = round((len(intersection) / len(union)) * 100.0, 2) if union else 0.0
    else:
        s_lex = s_req

    # Experience / Depth relevance signal
    s_exp = min(100.0, round((len(candidate_skills) * 8.0) + (len(resume_text) / 50.0), 2))

    # Domain bonus signal
    s_dom = 0.0
    if predicted_domain and job_domain and predicted_domain.lower() == job_domain.lower():
        s_dom = 100.0 if (confidence or "").lower() == "high" else 50.0

    # Composite 6-signal weighted score
    total_w = sum(w.values())
    composite = (
        (w["req"] * s_req)
        + (w["pref"] * s_pref)
        + (w["sem"] * s_sem)
        + (w["lex"] * s_lex)
        + (w["exp"] * s_exp)
        + (w["dom"] * s_dom)
    ) / total_w if total_w > 0 else 0.0

    composite = max(0.0, min(100.0, round(composite, 2)))

    hybrid_breakdown = {
        **base_match.score_breakdown,
        "hybrid_formula": "Composite = Σ(weight_i × signal_i) / Σ(weight_i)",
        "signal_scores": {
            "required_coverage": s_req,
            "preferred_coverage": s_pref,
            "semantic_similarity": s_sem,
            "lexical_similarity": s_lex,
            "experience_depth": s_exp,
            "domain_alignment": s_dom,
        },
        "signal_weights": w,
        "composite_score": composite,
    }

    return MatchResult(
        required_coverage=base_match.required_coverage,
        preferred_coverage=base_match.preferred_coverage,
        combined_match=composite,
        matched_required=base_match.matched_required,
        missing_required=base_match.missing_required,
        matched_preferred=base_match.matched_preferred,
        matched_evidence=base_match.matched_evidence,
        score_breakdown=hybrid_breakdown,
        warning=base_match.warning,
    )


def extract_job_skills(
    requirements: list,  # list of JobRequirement ORM objects
) -> tuple[list[tuple[str, float]], list[tuple[str, float]]]:
    """
    Split job requirements into required and preferred lists.

    Returns:
        (required_skills, preferred_skills) — each is [(name, weight), ...]
    """
    required = [(r.skill_name, r.weight) for r in requirements if r.is_required]
    preferred = [(r.skill_name, r.weight) for r in requirements if not r.is_required]
    return required, preferred

