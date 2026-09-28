"""
backend/tests/test_browser_extension.py

Unit test suite for Phase 15: Browser Extension Architecture & API Endpoints.
"""

import pytest


def test_api_extension_status(client):
    response = client.get("/api/v1/extension/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"
    assert "linkedin" in data["supported_platforms"]


def test_api_extension_ingest_candidate(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {
        "name": "Sarah Connor",
        "current_title": "Senior Data Scientist",
        "company": "Cyberdyne Systems",
        "profile_url": "https://linkedin.com/in/sarah-connor-ds",
        "source_platform": "linkedin",
        "summary": "Experienced Data Scientist specializing in Machine Learning, Python, and Predictive Modeling.",
        "skills": ["Python", "Machine Learning", "Scikit-Learn", "FastAPI"],
        "notes": "Sourced via Chrome Extension for Senior Data Scientist requisition",
    }

    response = client.post("/api/v1/extension/ingest", json=payload, headers=headers)
    assert response.status_code == 200
    res_data = response.json()

    assert res_data["success"] is True
    assert res_data["candidate_id"] > 0
    assert res_data["resume_id"] > 0
    assert res_data["predicted_domain"] is not None
    assert "sarah connor" in res_data["message"].lower()


def test_api_extension_ingest_unauthenticated(client):
    payload = {
        "name": "John Doe",
        "source_platform": "indeed",
    }
    response = client.post("/api/v1/extension/ingest", json=payload)
    assert response.status_code == 401


def test_api_extension_ingest_empty_name(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {
        "name": "   ",
        "source_platform": "linkedin",
    }
    response = client.post("/api/v1/extension/ingest", json=payload, headers=headers)
    assert response.status_code == 422
