"""
backend/tests/test_phase30_matching.py

Phase 30 — Matching Policy & Ranking Validation Unit Tests.
Tests edge cases, explainability, ranking stability, and scoring behavior.
"""

import pytest
from app.services.matching_service import compute_match, compute_hybrid_match, MatchResult
from app.services.skill_service import SkillMatch


class TestPhase30MatchingValidation:
    def test_edge_case_empty_skills_and_text(self):
        """Verify graceful handling when no skills or text are provided."""
        res = compute_match(required_skills=[], preferred_skills=[], candidate_skills=[])
        assert res.required_coverage == 0.0
        assert res.preferred_coverage == 0.0
        assert res.combined_match == 0.0
        assert res.warning is not None

    def test_edge_case_no_required_skills(self):
        """Vacuously satisfies required coverage if job lists only preferred skills."""
        pref = [("Docker", 1.0)]
        skills = [SkillMatch("Docker", "Docker", "DevOps", "containers", "Docker experience")]
        res = compute_match(required_skills=[], preferred_skills=pref, candidate_skills=skills)
        assert res.required_coverage == 100.0
        assert res.preferred_coverage == 100.0
        assert res.combined_match == 100.0

    def test_edge_case_no_preferred_skills(self):
        """Required coverage only if job has no preferred skills."""
        req = [("Python", 1.0)]
        skills = [SkillMatch("Python", "Python", "Web", "b", "Python experience")]
        res = compute_match(required_skills=req, preferred_skills=[], candidate_skills=skills)
        assert res.required_coverage == 100.0
        assert res.preferred_coverage == 0.0
        assert res.combined_match == 100.0

    def test_explainability_and_evidence_snippets(self):
        """Verify score breakdown dict and matched evidence snippets."""
        req = [("Python", 1.0), ("FastAPI", 1.0)]
        pref = [("AWS", 1.0)]
        skills = [
            SkillMatch("Python", "Python", "Web", "b", "Developed Python API"),
        ]
        res = compute_match(req, pref, skills)
        assert res.matched_required == ["Python"]
        assert res.missing_required == ["FastAPI"]
        assert res.matched_evidence["Python"] == "Developed Python API"
        assert "required_coverage_pct" in res.score_breakdown
        assert res.score_breakdown["required_coverage_pct"] == 50.0

    def test_ranking_stability_under_punctuation_and_casing(self):
        """Verify score stability across casing and minor punctuation differences."""
        req = [("Python", 1.0), ("FastAPI", 1.0)]
        pref = [("Docker", 1.0)]

        s1 = [
            SkillMatch("Python", "python", "Web", "b", "python context"),
            SkillMatch("FastAPI", "FASTAPI", "Web", "b", "FASTAPI context"),
        ]
        s2 = [
            SkillMatch("Python", "Python", "Web", "b", "Python context"),
            SkillMatch("FastAPI", "FastAPI", "Web", "b", "FastAPI context"),
        ]

        r1 = compute_match(req, pref, s1)
        r2 = compute_match(req, pref, s2)
        assert r1.combined_match == r2.combined_match
        assert r1.required_coverage == r2.required_coverage

    def test_zero_required_skills_current_behavior(self):
        """Document current behavior for 0% required coverage with 100% preferred match."""
        req = [("Python", 1.0), ("FastAPI", 1.0)]
        pref = [("Docker", 1.0)]
        skills = [SkillMatch("Docker", "Docker", "DevOps", "containers", "Docker experience")]

        res = compute_match(req, pref, skills)
        assert res.required_coverage == 0.0
        assert res.preferred_coverage == 100.0
        assert res.combined_match == 30.0  # Current 30% baseline from preferred match
