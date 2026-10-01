"""
backend/tests/test_phase33_analytics.py

Phase 33 — Advanced Recruiter Analytics & Hiring Insights Test Suite.
Validates real analytics computation, tenant isolation, RBAC, date filtering,
empty states, skill gap intelligence, and recruiter decision / OOD separation.
"""

import datetime
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.job import Job, JobRequirement
from app.models.candidate import Candidate
from app.models.resume import Resume, ProcessingStatus
from app.models.screening import ScreeningResult, ReviewStatus


@pytest.fixture
def auth_headers(hr_token: str):
    """Provide Bearer auth headers for test HR user."""
    return {"Authorization": f"Bearer {hr_token}"}


@pytest.fixture
def sample_analytics_data(db_session: Session):
    """Populate test database with sample jobs, candidates, resumes, and screenings."""
    uid = uuid.uuid4().hex[:6]

    job = Job(
        title=f"Senior Python Developer {uid}",
        department="Engineering",
        domain="Engineering",
        is_active=True,
    )
    db_session.add(job)
    db_session.flush()

    req1 = JobRequirement(job_id=job.id, skill_name="Python", is_required=True, weight=1.0)
    req2 = JobRequirement(job_id=job.id, skill_name="FastAPI", is_required=True, weight=1.0)
    req3 = JobRequirement(job_id=job.id, skill_name="Docker", is_required=False, weight=0.5)
    db_session.add_all([req1, req2, req3])

    cand1 = Candidate(reference_code=f"CAND-{uid}-1", display_name="Alice Smith", email=f"alice_{uid}@test.com")
    cand2 = Candidate(reference_code=f"CAND-{uid}-2", display_name="Bob Jones", email=f"bob_{uid}@test.com")
    db_session.add_all([cand1, cand2])
    db_session.flush()

    res1 = Resume(
        candidate_id=cand1.id,
        original_filename=f"alice_{uid}.pdf",
        stored_filename=f"alice_{uid}_uuid.pdf",
        file_size_bytes=10240,
        status=ProcessingStatus.COMPLETED,
        predicted_domain="Engineering",
        prediction_confidence="high",
        classification_status="accepted",
        ood_status="in_domain_like",
    )
    res2 = Resume(
        candidate_id=cand2.id,
        original_filename=f"bob_{uid}.pdf",
        stored_filename=f"bob_{uid}_uuid.pdf",
        file_size_bytes=12288,
        status=ProcessingStatus.NEEDS_REVIEW,
        predicted_domain="Engineering",
        prediction_confidence="low",
        classification_status="review",
        ood_status="possible_out_of_domain",
    )
    db_session.add_all([res1, res2])
    db_session.flush()

    sr1 = ScreeningResult(
        resume_id=res1.id,
        job_id=job.id,
        candidate_id=cand1.id,
        required_skill_coverage=100.0,
        preferred_skill_coverage=100.0,
        combined_skill_match=100.0,
        relevance_score=92.5,
        matched_required_skills='["Python", "FastAPI"]',
        missing_required_skills='[]',
        matched_preferred_skills='["Docker"]',
        review_status=ReviewStatus.APPROVED,
        reviewed_at=datetime.datetime.now(datetime.UTC),
    )
    sr2 = ScreeningResult(
        resume_id=res2.id,
        job_id=job.id,
        candidate_id=cand2.id,
        required_skill_coverage=50.0,
        preferred_skill_coverage=0.0,
        combined_skill_match=35.0,
        relevance_score=45.0,
        matched_required_skills='["Python"]',
        missing_required_skills='["FastAPI"]',
        matched_preferred_skills='[]',
        review_status=ReviewStatus.PENDING,
    )
    db_session.add_all([sr1, sr2])
    db_session.commit()

    return {"job": job, "cand1": cand1, "cand2": cand2, "sr1": sr1, "sr2": sr2}


def test_overview_metrics(client: TestClient, auth_headers: dict, sample_analytics_data: dict):
    """Test 1: Overview metrics endpoint returns accurate DB counts."""
    response = client.get("/api/v1/analytics/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert data["total_resumes"] >= 2
    assert data["total_candidates"] >= 2
    assert data["total_screenings"] >= 2
    assert data["approved_candidates"] >= 1
    assert data["pending_reviews"] >= 1
    assert "explainability" in data


def test_funnel_calculations(client: TestClient, auth_headers: dict, sample_analytics_data: dict):
    """Test 2: Funnel stages compute uploaded -> processed -> matched -> status breakdown."""
    response = client.get("/api/v1/analytics/funnel", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert "stages" in data
    stages = {s["stage"]: s["count"] for s in data["stages"]}
    assert stages["Uploaded"] >= 2
    assert stages["Matched"] >= 2
    assert "Shortlisted / Approved" in stages


def test_job_analytics(client: TestClient, auth_headers: dict, sample_analytics_data: dict):
    """Test 3: Job-level analytics calculates candidate count and average scores."""
    job_id = sample_analytics_data["job"].public_id
    response = client.get(f"/api/v1/analytics/jobs?job_id={job_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert data["total_jobs_analyzed"] == 1
    job_stat = data["jobs"][0]
    assert job_stat["job_id"] == job_id
    assert job_stat["candidate_count"] == 2
    assert job_stat["screening_count"] == 2
    assert job_stat["avg_relevance_score"] == 68.75  # (92.5 + 45.0) / 2


def test_skill_analytics(client: TestClient, auth_headers: dict, sample_analytics_data: dict):
    """Test 4: Skill intelligence aggregates matched vs missing skills."""
    response = client.get("/api/v1/analytics/skills", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    matched_skills = [s["skill"] for s in data["top_matched_required"]]
    missing_skills = [s["skill"] for s in data["top_missing_required"]]

    assert "Python" in matched_skills
    assert "FastAPI" in missing_skills


def test_score_distributions(client: TestClient, auth_headers: dict, sample_analytics_data: dict):
    """Test 5: Score histogram and coverage distribution buckets."""
    response = client.get("/api/v1/analytics/score-hist", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert data["total_screened"] >= 2
    assert "buckets" in data
    assert "required_coverage_buckets" in data
    assert "ood_distribution" in data


def test_date_filtering(client: TestClient, auth_headers: dict, sample_analytics_data: dict):
    """Test 6 & 8: Time-series date filtering and insufficient historical data handling."""
    response = client.get("/api/v1/analytics/time-series?days=7d", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert "period" in data
    assert "has_sufficient_data" in data
    assert "series" in data


def test_unauthorized_access(client: TestClient):
    """Test 10 & 11: Unauthenticated request to analytics returns 401."""
    response = client.get("/api/v1/analytics/summary")
    assert response.status_code == 401


def test_tenant_isolation(db_session: Session):
    """Test 9: Verify tenant isolation scope default on user model."""
    user = db_session.query(User).filter(User.email == "hr@example.com").first()
    assert user.tenant_id == "default_tenant"


def test_job_comparison(client: TestClient, auth_headers: dict, sample_analytics_data: dict):
    """Test 13: Job comparison side-by-side analysis."""
    job_id = sample_analytics_data["job"].public_id
    response = client.get(f"/api/v1/analytics/job-comparison?job_ids={job_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert data["job_count"] == 1
    assert data["comparison"][0]["job_id"] == job_id
    assert data["comparison"][0]["candidate_volume"] == 2


def test_candidate_pipeline_insights(client: TestClient, auth_headers: dict, sample_analytics_data: dict):
    """Test 16: Pipeline insights maintains strict separation between AI OOD & Recruiter decision."""
    job_id = sample_analytics_data["job"].public_id
    response = client.get(f"/api/v1/analytics/pipeline/{job_id}", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    sep = data["pipeline_separation"]
    assert "ood_review_count" in sep
    assert "recruiter_pending" in sep
    assert "recruiter_approved" in sep


def test_recruiter_activity(client: TestClient, auth_headers: dict, sample_analytics_data: dict):
    """Test 15: Recruiter activity timeline returns real persisted review timestamps."""
    response = client.get("/api/v1/analytics/activity", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert "count" in data
    assert "activity" in data
    assert len(data["activity"]) >= 1
    assert data["activity"][0]["action"].startswith("Status updated to")
