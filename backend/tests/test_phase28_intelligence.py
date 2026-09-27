"""
backend/tests/test_phase28_intelligence.py

Phase 28 — Resume Intelligence Core: Skill Extraction, Normalization, Evidence,
Matching Formula, Mandatory Skill Behavior, and Explanation Audit Tests.
"""

import pytest
from app.services.skill_service import match_skills, SkillMatch
from app.services.matching_service import compute_match, compute_hybrid_match
from app.services.embedding_service import LocalEmbeddingProvider, get_embedding_service


def test_skill_extraction_exact_and_case_insensitive():
    """Verify exact and case-insensitive skill extraction."""
    text = "Proficient in FastAPI, FASTAPI, and fastapi."
    matches = match_skills(text)
    assert len(matches) == 1
    assert matches[0].canonical_name == "FastAPI"
    assert matches[0].frequency == 3


def test_skill_extraction_alias_normalization():
    """Verify that skill aliases map to canonical skill names."""
    test_cases = [
        ("Experience with ReactJS and React.js", "React"),
        ("Built APIs using Node, Node.js, and Express.js", "Node.js"),
        ("Database experience in Postgres and PostgreSQL", "PostgreSQL"),
        ("Deployed services on AWS and Amazon Web Services", "AWS"),
        ("Scikit-learn and sklearn for machine learning", "scikit-learn"),
    ]
    for text, expected_canonical in test_cases:
        matches = match_skills(text)
        canonical_names = [m.canonical_name for m in matches]
        assert expected_canonical in canonical_names


def test_skill_extraction_multi_word():
    """Verify multi-word skill extraction."""
    text = "Knowledge of Natural Language Processing and Deep Learning."
    matches = match_skills(text)
    names = {m.canonical_name for m in matches}
    assert "Natural Language Processing" in names
    assert "Deep Learning" in names


def test_skill_extraction_empty_and_no_skills():
    """Verify graceful handling of empty or no-skill text."""
    assert match_skills("") == []
    assert match_skills("   ") == []
    assert match_skills("Hello world! Nothing relevant here.") == []


def test_skill_extraction_evidence_snippet():
    """Verify that extracted skills include safe evidence snippets."""
    text = "Developed enterprise microservices using Python and FastAPI on AWS."
    matches = match_skills(text)
    for m in matches:
        assert isinstance(m.evidence_snippet, str)
        assert len(m.evidence_snippet) > 0
        assert len(m.evidence_snippet) <= 200


def test_matching_formula_required_and_preferred():
    """Verify 70/30 skill matching formula calculation."""
    required = [("Python", 1.0), ("FastAPI", 1.0)]
    preferred = [("Docker", 1.0)]
    
    # Candidate has Python and Docker (1/2 required = 50%, 1/1 preferred = 100%)
    candidate_skills = [
        SkillMatch("Python", "Python", "Web", "backend", "snippet Python"),
        SkillMatch("Docker", "Docker", "DevOps", "containers", "snippet Docker"),
    ]
    
    res = compute_match(required, preferred, candidate_skills)
    assert res.required_coverage == 50.0
    assert res.preferred_coverage == 100.0
    # Combined score = 0.70 * 50.0 + 0.30 * 100.0 = 35.0 + 30.0 = 65.0
    assert res.combined_match == 65.0
    assert "Python" in res.matched_required
    assert "FastAPI" in res.missing_required
    assert "Docker" in res.matched_preferred
    assert res.matched_evidence["Python"] == "snippet Python"
    assert res.matched_evidence["Docker"] == "snippet Docker"


def test_mandatory_skill_behavior_cases():
    """Audit mandatory skill behavior across 4 test scenarios."""
    req = [("Python", 1.0), ("FastAPI", 1.0), ("PostgreSQL", 1.0)]
    pref = [("Docker", 1.0), ("AWS", 1.0)]

    # Case A: All mandatory skills present
    case_a = [
        SkillMatch("Python", "Python", "Web", "b", "snip"),
        SkillMatch("FastAPI", "FastAPI", "Web", "b", "snip"),
        SkillMatch("PostgreSQL", "PostgreSQL", "Web", "db", "snip"),
        SkillMatch("Docker", "Docker", "DevOps", "c", "snip"),
        SkillMatch("AWS", "AWS", "Cloud", "a", "snip"),
    ]
    res_a = compute_match(req, pref, case_a)
    assert res_a.required_coverage == 100.0
    assert res_a.preferred_coverage == 100.0
    assert res_a.combined_match == 100.0
    assert res_a.missing_required == []

    # Case B: One mandatory skill missing (2/3 req = 66.67%, 2/2 pref = 100%)
    case_b = [
        SkillMatch("Python", "Python", "Web", "b", "snip"),
        SkillMatch("FastAPI", "FastAPI", "Web", "b", "snip"),
        SkillMatch("Docker", "Docker", "DevOps", "c", "snip"),
        SkillMatch("AWS", "AWS", "Cloud", "a", "snip"),
    ]
    res_b = compute_match(req, pref, case_b)
    assert res_b.required_coverage == 66.67
    assert res_b.preferred_coverage == 100.0
    assert res_b.combined_match == 76.67
    assert res_b.missing_required == ["PostgreSQL"]

    # Case C: Multiple mandatory skills missing (1/3 req = 33.33%, 1/2 pref = 50%)
    case_c = [
        SkillMatch("Python", "Python", "Web", "b", "snip"),
        SkillMatch("Docker", "Docker", "DevOps", "c", "snip"),
    ]
    res_c = compute_match(req, pref, case_c)
    assert res_c.required_coverage == 33.33
    assert res_c.preferred_coverage == 50.0
    assert res_c.combined_match == 38.33
    assert set(res_c.missing_required) == {"FastAPI", "PostgreSQL"}

    # Case D: Zero mandatory skills present (0/3 req = 0.0%, 2/2 pref = 100%)
    case_d = [
        SkillMatch("Docker", "Docker", "DevOps", "c", "snip"),
        SkillMatch("AWS", "AWS", "Cloud", "a", "snip"),
    ]
    res_d = compute_match(req, pref, case_d)
    assert res_d.required_coverage == 0.0
    assert res_d.preferred_coverage == 100.0
    assert res_d.combined_match == 30.0  # Demonstrates design limitation where pref score yields 30%
    assert set(res_d.missing_required) == {"Python", "FastAPI", "PostgreSQL"}


def test_embedding_service_hash_projection_audit():
    """Verify that local embedding provider operates via deterministic hash projection."""
    provider = LocalEmbeddingProvider(dim=128)
    vec1 = provider.embed_text("Python FastAPI backend")
    vec2 = provider.embed_text("Python FastAPI backend")
    vec3 = provider.embed_text("Unrelated legal audit text")

    assert len(vec1) == 128
    assert vec1 == vec2  # Deterministic hash projection
    assert vec1 != vec3
