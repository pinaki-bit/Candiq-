"""
backend/tests/test_hybrid_ranking.py

Unit tests for the 6-Signal Hybrid Candidate Ranking Engine.
Verifies configurable weights, signal contributions, and non-overriding strict requirement rules.
"""

from __future__ import annotations

import pytest
from app.services.matching_service import compute_hybrid_match


class TestHybridCandidateRanking:
    def test_hybrid_match_returns_6_signal_breakdown(self):
        req = [("Python", 1.0), ("FastAPI", 1.0)]
        pref = [("Docker", 1.0)]
        skills = ["Python", "FastAPI"]
        res_text = "Experienced Senior Python Software Engineer building REST APIs with FastAPI and PostgreSQL."
        job_text = "Looking for a Senior Python Backend Developer with FastAPI experience."

        result = compute_hybrid_match(
            required_skills=req,
            preferred_skills=pref,
            candidate_skills=skills,
            resume_text=res_text,
            job_description=job_text,
            predicted_domain="Web Development",
            job_domain="Web Development",
            confidence="high",
        )

        assert result.required_coverage == 100.0
        assert result.combined_match > 0.0
        assert "signal_scores" in result.score_breakdown
        signals = result.score_breakdown["signal_scores"]
        assert "required_coverage" in signals
        assert "preferred_coverage" in signals
        assert "semantic_similarity" in signals
        assert "lexical_similarity" in signals
        assert "experience_depth" in signals
        assert "domain_alignment" in signals
        assert signals["domain_alignment"] == 100.0

    def test_semantic_similarity_never_hides_missing_required_skills(self):
        req = [("Python", 1.0), ("Kubernetes", 1.0)]
        pref = []
        skills = ["Python"]
        res_text = "Python developer with container experience using Docker."
        job_text = "Python developer with Kubernetes orchestration skills."

        result = compute_hybrid_match(
            required_skills=req,
            preferred_skills=pref,
            candidate_skills=skills,
            resume_text=res_text,
            job_description=job_text,
        )

        # Kubernetes must be explicitly in missing_required
        assert "Kubernetes" in result.missing_required
        assert result.required_coverage == 50.0

    def test_custom_weights_configuration(self):
        req = [("Python", 1.0)]
        pref = []
        skills = ["Python"]

        custom_weights = {
            "req": 0.50,
            "pref": 0.10,
            "sem": 0.20,
            "lex": 0.10,
            "exp": 0.05,
            "dom": 0.05,
        }

        result = compute_hybrid_match(
            required_skills=req,
            preferred_skills=pref,
            candidate_skills=skills,
            weights=custom_weights,
        )

        assert result.score_breakdown["signal_weights"]["req"] == 0.50
