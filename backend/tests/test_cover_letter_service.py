"""
backend/tests/test_cover_letter_service.py

Unit test suite for Phase 7: AI Cover Letter Generator Module.
"""

import pytest
from app.services.cover_letter_service import CoverLetterResult, generate_cover_letter


def test_generate_cover_letter_professional_tone():
    result = generate_cover_letter(
        job_title="Senior Python Developer",
        company_name="Acme Tech",
        candidate_name="Alex Johnson",
        candidate_skills=["Python", "FastAPI", "PostgreSQL", "Docker"],
        tone="PROFESSIONAL",
    )
    
    assert isinstance(result, CoverLetterResult)
    assert result.tone_used == "PROFESSIONAL"
    assert "Acme Tech" in result.full_cover_letter or "Acme Tech" in result.salutation
    assert result.opening_hook != ""
    assert result.core_value_proposition != ""


def test_generate_cover_letter_enthusiastic_tone():
    result = generate_cover_letter(
        job_title="ML Engineer",
        company_name="AI Innovations",
        candidate_name="Jane Doe",
        candidate_skills=["PyTorch", "NLP", "Scikit-Learn"],
        tone="ENTHUSIASTIC",
    )
    
    assert result.tone_used == "ENTHUSIASTIC"
    assert result.full_cover_letter != ""


def test_generate_cover_letter_executive_tone():
    result = generate_cover_letter(
        job_title="VP of Engineering",
        company_name="Enterprise Global",
        candidate_name="Robert Smith",
        candidate_skills=["System Architecture", "Team Leadership", "Cloud Infrastructure"],
        tone="EXECUTIVE",
    )
    
    assert result.tone_used == "EXECUTIVE"
    assert result.closing_call_to_action != ""


def test_api_generate_cover_letter_endpoint(client, hr_token):
    headers = {"Authorization": f"Bearer {hr_token}"}
    payload = {
        "job_title": "Full Stack Engineer",
        "company_name": "Tech Corp",
        "candidate_name": "Test Candidate",
        "candidate_skills": ["React", "TypeScript", "Node.js"],
        "tone": "PROFESSIONAL",
    }
    
    response = client.post("/api/v1/resumes/generate-cover-letter", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["tone_used"] == "PROFESSIONAL"
    assert "full_cover_letter" in data
    assert "salutation" in data
    assert "core_value_proposition" in data
