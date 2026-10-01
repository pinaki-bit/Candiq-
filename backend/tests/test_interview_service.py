"""
backend/tests/test_interview_service.py

Unit test suite for Phase 8: Interview Intelligence Engine.
"""

import pytest
from app.services.interview_service import InterviewKitResult, generate_interview_kit


def test_generate_interview_kit_structure():
    result = generate_interview_kit(
        job_title="Senior Python Developer",
        candidate_skills=["Python", "FastAPI", "PostgreSQL"],
        missing_skills=["Kubernetes", "Redis"],
    )
    
    assert isinstance(result, InterviewKitResult)
    assert len(result.questions) == 5
    
    categories = [q.category for q in result.questions]
    assert "Technical" in categories or "Technical Fundamentals" in categories
    assert len(categories) == 5


def test_generate_interview_kit_question_details():
    result = generate_interview_kit(
        job_title="Data Scientist",
        candidate_skills=["Python", "PyTorch"],
        missing_skills=["MLOps"],
    )
    
    for q in result.questions:
        assert q.question != ""
        assert q.why_this_question != ""
        assert len(q.expected_key_points) > 0
        assert q.difficulty in ("Easy", "Medium", "Hard")


def test_api_create_interview_kit_endpoint(client, hr_token):
    headers = {"Authorization": f"Bearer {hr_token}"}
    payload = {
        "job_title": "Backend Architect",
        "candidate_skills": ["Go", "gRPC", "Docker"],
        "missing_skills": ["Kafka"],
    }
    
    response = client.post("/api/v1/screening/interview-kit", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["job_title"] == "Backend Architect"
    assert len(data["questions"]) == 5
    assert "why_this_question" in data["questions"][0]
    assert "expected_key_points" in data["questions"][0]
