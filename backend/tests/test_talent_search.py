"""
backend/tests/test_talent_search.py

Unit test suite for Phase 11: Talent Semantic Search Engine.
"""

import pytest
from app.models.resume import Resume, ProcessingStatus
from app.services.talent_search_service import TalentSearchResult, search_talent_pool


def test_search_talent_pool_with_seeded_resumes(db_session):
    # Seed processed resumes
    res1 = Resume(
        original_filename="python_dev.pdf",
        stored_filename="uuid1.pdf",
        file_size_bytes=1024,
        mime_type="application/pdf",
        status=ProcessingStatus.COMPLETED,
        extracted_text="Senior Python developer experienced in FastAPI, PostgreSQL, Docker, and Kubernetes microservices.",
        predicted_domain="Software Engineering",
        prediction_confidence="high",
        uploaded_by=1,
    )
    res2 = Resume(
        original_filename="data_scientist.pdf",
        stored_filename="uuid2.pdf",
        file_size_bytes=1024,
        mime_type="application/pdf",
        status=ProcessingStatus.COMPLETED,
        extracted_text="Data Scientist specializing in PyTorch, NLP, Machine Learning, and Scikit-Learn data pipelines.",
        predicted_domain="Data Science",
        prediction_confidence="high",
        uploaded_by=1,
    )
    db_session.add(res1)
    db_session.add(res2)
    db_session.commit()

    # Query 1: Backend Developer
    result = search_talent_pool(db_session, query="Looking for a Python backend engineer with FastAPI and Docker")
    assert isinstance(result, TalentSearchResult)
    assert result.total_candidates_searched >= 2
    assert result.results_count > 0
    assert result.results[0].original_filename in ("python_dev.pdf", "alice_resume.pdf")
    assert result.results[0].hybrid_score > 50.0

    # Query 2: Data Scientist
    result_ds = search_talent_pool(db_session, query="Machine learning specialist with PyTorch and NLP experience")
    assert result_ds.results_count > 0
    assert result_ds.results[0].original_filename in ("data_scientist.pdf", "bob_resume.pdf")


def test_search_talent_pool_domain_filtering(db_session):
    result = search_talent_pool(db_session, query="Python", domain_filter="Data Science")
    assert result.total_candidates_searched >= 1
    for c in result.results:
        assert "data science" in c.predicted_domain.lower()


def test_api_talent_search_endpoint(client, hr_token):
    headers = {"Authorization": f"Bearer {hr_token}"}
    payload = {
        "query": "Senior Software Architect with Kubernetes experience",
        "limit": 5,
    }
    
    response = client.post("/api/v1/screening/talent-search", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "query" in data
    assert "total_candidates_searched" in data
    assert "results" in data
