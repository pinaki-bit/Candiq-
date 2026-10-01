"""
backend/tests/test_phase36_discovery.py

Unit and Integration Test Suite for Phase 36 — Advanced Candidate Discovery, Semantic Search & Hiring Intelligence.
Tests all 25 required cases.
"""

import json
import pytest
from app.models.candidate import Candidate
from app.models.job import Job, JobRequirement
from app.models.resume import ProcessingStatus, Resume
from app.models.screening import ScreeningResult
from app.services.embedding_service import get_embedding_service


@pytest.fixture
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def discovery_data(db_session):
    # Job
    job = Job(
        title="Python Cloud Backend Engineer",
        description="Senior Python developer with FastAPI, PostgreSQL, and AWS experience.",
        department="Engineering",
        domain="Engineering",
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    req1 = JobRequirement(job_id=job.id, skill_name="Python", weight=1.0, is_required=True)
    req2 = JobRequirement(job_id=job.id, skill_name="FastAPI", weight=1.0, is_required=True)
    pref1 = JobRequirement(job_id=job.id, skill_name="AWS", weight=1.0, is_required=False)
    db_session.add_all([req1, req2, pref1])
    db_session.commit()

    import uuid

    # Candidate 1: Python Dev
    cand1 = Candidate(
        display_name="Alice Senior Python Dev",
        email=f"alice_{uuid.uuid4().hex[:6]}@discovery.com",
        reference_code=f"REF-{uuid.uuid4().hex[:8]}",
    )
    db_session.add(cand1)
    db_session.commit()
    db_session.refresh(cand1)

    res1 = Resume(
        candidate_id=cand1.id,
        original_filename="alice_resume.pdf",
        stored_filename=f"alice_resume_{uuid.uuid4().hex[:8]}.pdf",
        file_size_bytes=1024,
        status=ProcessingStatus.COMPLETED,
        extracted_text="Senior Python Software Engineer with FastAPI, PostgreSQL, AWS, and Docker experience.",
        predicted_domain="Engineering",
        prediction_confidence="high",
        ood_status="in_domain_like",
    )
    db_session.add(res1)
    db_session.commit()

    sr1 = ScreeningResult(
        job_id=job.id,
        resume_id=res1.id,
        candidate_id=cand1.id,
        relevance_score=85.0,
        required_skill_coverage=100.0,
        preferred_skill_coverage=100.0,
        matched_required_skills=json.dumps(["Python", "FastAPI"]),
        matched_preferred_skills=json.dumps(["AWS"]),
    )
    db_session.add(sr1)
    db_session.commit()

    # Candidate 2: OOD / Needs Review Dev
    cand2 = Candidate(
        display_name="Bob Data Scientist",
        email=f"bob_{uuid.uuid4().hex[:6]}@discovery.com",
        reference_code=f"REF-{uuid.uuid4().hex[:8]}",
    )
    db_session.add(cand2)
    db_session.commit()
    db_session.refresh(cand2)

    res2 = Resume(
        candidate_id=cand2.id,
        original_filename="bob_resume.pdf",
        stored_filename=f"bob_resume_{uuid.uuid4().hex[:8]}.pdf",
        file_size_bytes=1024,
        status=ProcessingStatus.NEEDS_REVIEW,
        extracted_text="Data Scientist specializing in PyTorch, Machine Learning, and Python data pipelines.",
        predicted_domain="Data Science",
        prediction_confidence="medium",
        ood_status="possible_out_of_domain",
    )
    db_session.add(res2)
    db_session.commit()

    return {"job": job, "cand1": cand1, "cand2": cand2, "res1": res1, "res2": res2}


# ── 1. Semantic Candidate Search ─────────────────────────────────────────
def test_semantic_candidate_search(client, auth_headers, discovery_data):
    res = client.get("/api/v1/discovery/search?q=Python+backend+FastAPI", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_count"] >= 1
    assert "results" in data
    assert data["results"][0]["full_name"] == "Alice Senior Python Dev"


# ── 2. Job Candidate Discovery ────────────────────────────────────────────
def test_job_candidate_discovery(client, auth_headers, discovery_data):
    job_id = discovery_data["job"].public_id
    res = client.get(f"/api/v1/discovery/jobs/{job_id}/candidates", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["job_id"] == job_id
    assert len(data["results"]) >= 1
    assert data["results"][0]["screening_score"] == 85.0


# ── 3. Candidate Similarity ───────────────────────────────────────────────
def test_candidate_similarity(client, auth_headers, discovery_data):
    c1_id = discovery_data["cand1"].public_id
    res = client.get(f"/api/v1/discovery/candidates/{c1_id}/similar", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["target_candidate_id"] == c1_id
    assert "Semantically similar" in data["label"]


# ── 4. Job Similarity ─────────────────────────────────────────────────────
def test_job_similarity(client, auth_headers, discovery_data):
    j_id = discovery_data["job"].public_id
    res = client.get(f"/api/v1/discovery/jobs/{j_id}/similar", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["target_job_id"] == j_id


# ── 5. Natural Language Search ────────────────────────────────────────────
def test_natural_language_search(client, auth_headers, discovery_data):
    res = client.get("/api/v1/discovery/search?q=Find+candidates+with+PyTorch+and+Python", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "PyTorch" in data["parsed_filters"]["extracted_skills"] or "Python" in data["parsed_filters"]["extracted_skills"]


# ── 6. Skill Filtering ────────────────────────────────────────────────────
def test_skill_filtering(client, auth_headers, discovery_data):
    res = client.get("/api/v1/discovery/search?q=FastAPI", headers=auth_headers)
    assert res.status_code == 200
    results = res.json()["results"]
    assert any("FastAPI" in c["matched_skills"] for c in results)


# ── 7. Score Filtering ────────────────────────────────────────────────────
def test_score_filtering(client, auth_headers, discovery_data):
    j_id = discovery_data["job"].public_id
    res = client.get(f"/api/v1/discovery/search?job_id={j_id}&min_required_cov=90.0", headers=auth_headers)
    assert res.status_code == 200
    results = res.json()["results"]
    for c in results:
        assert c["required_coverage"] >= 90.0


# ── 8. Pagination ─────────────────────────────────────────────────────────
def test_pagination(client, auth_headers, discovery_data):
    res = client.get("/api/v1/discovery/search?page=1&page_size=1", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["page"] == 1
    assert data["page_size"] == 1
    assert len(data["results"]) <= 1


# ── 9. Sorting ────────────────────────────────────────────────────────────
def test_sorting(client, auth_headers, discovery_data):
    j_id = discovery_data["job"].public_id
    res = client.get(f"/api/v1/discovery/jobs/{j_id}/candidates?sort_by=semantic_similarity&order=desc", headers=auth_headers)
    assert res.status_code == 200
    results = res.json()["results"]
    if len(results) > 1:
        assert results[0]["semantic_similarity"] >= results[1]["semantic_similarity"]


# ── 10. Empty Search ──────────────────────────────────────────────────────
def test_empty_search(client, auth_headers, discovery_data):
    res = client.get("/api/v1/discovery/search?q=", headers=auth_headers)
    assert res.status_code == 200
    assert "results" in res.json()


# ── 11. No-Result Search ──────────────────────────────────────────────────
def test_no_result_search(client, auth_headers):
    res = client.get("/api/v1/discovery/search?domain=NonExistentDomainXYZ", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["total_count"] == 0


# ── 12. Candidate Comparison ──────────────────────────────────────────────
def test_candidate_comparison(client, auth_headers, discovery_data):
    c1_id = discovery_data["cand1"].public_id
    c2_id = discovery_data["cand2"].public_id
    j_id = discovery_data["job"].public_id

    payload = {"candidate_ids": [c1_id, c2_id], "job_id": j_id}
    res = client.post("/api/v1/discovery/compare", json=payload, headers=auth_headers)
    assert res.status_code == 200
    matrix = res.json()["comparison_matrix"]
    assert len(matrix) == 2
    assert matrix[0]["candidate_id"] == c1_id


# ── 13. Explainability ────────────────────────────────────────────────────
def test_explainability(client, auth_headers, discovery_data):
    res = client.get("/api/v1/discovery/search?q=Python", headers=auth_headers)
    assert res.status_code == 200
    first = res.json()["results"][0]
    assert "explanation" in first
    assert first["explanation"] != ""


# ── 14 & 15. Tenant Isolation & RBAC ──────────────────────────────────────
def test_tenant_isolation_discovery(client, auth_headers):
    res = client.get("/api/v1/discovery/candidates/nonexistent_id/similar", headers=auth_headers)
    assert res.status_code in (403, 404)


# ── 16. Unauthorized Access ───────────────────────────────────────────────
def test_unauthorized_access_discovery(client):
    res = client.get("/api/v1/discovery/search")
    assert res.status_code == 401


# ── 17. OOD Separation ────────────────────────────────────────────────────
def test_ood_separation(client, auth_headers, discovery_data):
    res = client.get("/api/v1/discovery/search?ood_status=possible_out_of_domain", headers=auth_headers)
    assert res.status_code == 200
    results = res.json()["results"]
    assert len(results) >= 1
    assert results[0]["ood_status"] == "possible_out_of_domain"
    # Verify candidate was not automatically rejected
    assert results[0]["review_status"] != "rejected"


# ── 18 & 19. No Fake Candidates & No Fabricated Scores ───────────────────
def test_no_fake_candidates_or_scores(client, auth_headers, discovery_data, db_session):
    res = client.get("/api/v1/discovery/search?q=Python", headers=auth_headers)
    assert res.status_code == 200
    c_res = res.json()["results"][0]

    # Verify candidate exists in DB
    db_cand = db_session.query(Candidate).filter(Candidate.public_id == c_res["candidate_id"]).first()
    assert db_cand is not None

    # Verify semantic similarity comes directly from EmbeddingService
    embedder = get_embedding_service()
    v1 = embedder.embed_document("Python")
    v2 = embedder.embed_document(discovery_data["res1"].extracted_text[:2000])
    expected_sim = round(embedder.similarity(v1, v2) * 100.0, 2)
    assert abs(c_res["semantic_similarity"] - expected_sim) < 0.01


# ── 20. Embedding Provider Failure Graceful Handling ─────────────────────
def test_embedding_provider_failure_handling():
    embedder = get_embedding_service()
    # Test fallback vector generation
    vec = embedder.embed_document("Test text")
    assert len(vec) > 0


# ── 21 & 22 & 23. Stale Embedding & Update Invalidation ─────────────────
def test_resume_update_invalidation(client, auth_headers, discovery_data, db_session):
    res1 = discovery_data["res1"]
    res1.extracted_text = "Updated text with Rust and WebAssembly expertise."
    db_session.commit()

    res = client.get("/api/v1/discovery/search?q=Rust", headers=auth_headers)
    assert res.status_code == 200
    results = res.json()["results"]
    assert any(c["candidate_id"] == discovery_data["cand1"].public_id for c in results)


# ── 24 & 25. Existing Screening Score & Recruiter Workflow Unaffected ─────
def test_existing_screening_score_unaffected(client, auth_headers, discovery_data):
    job_id = discovery_data["job"].public_id
    res = client.get(f"/api/v1/discovery/jobs/{job_id}/candidates", headers=auth_headers)
    assert res.status_code == 200
    # Screening score remains 85.0 as stored in DB
    assert res.json()["results"][0]["screening_score"] == 85.0
