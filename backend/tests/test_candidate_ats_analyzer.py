import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
import os
import tempfile

def test_candidate_analyze_endpoint_requires_auth(client: TestClient):
    response = client.post("/api/v1/resumes/candidate-analyze")
    assert response.status_code == 401

def test_candidate_analyze_invalid_file(client: TestClient, hr_token: str):
    headers = {"Authorization": f"Bearer {hr_token}"}
    files = {"file": ("test.txt", b"hello world", "text/plain")}
    response = client.post("/api/v1/resumes/candidate-analyze", files=files, headers=headers)
    assert response.status_code == 400
    assert "File type '.txt' is not allowed" in response.json()["detail"]

def test_candidate_analyze_success(client: TestClient, hr_token: str, monkeypatch):
    headers = {"Authorization": f"Bearer {hr_token}"}
    from app.services import pdf_service
    from app.services.pdf_service import ExtractionResult
    
    def mock_extract(path):
        return ExtractionResult(True, "JOHN DOE\n\njohn.doe@example.com\n\nPROFESSIONAL SUMMARY\nExperienced Python developer.\n\nWORK EXPERIENCE\nBuilt a scalable API using FastAPI which increased throughput by 50%.\n\nTECHNICAL SKILLS\nPython, FastAPI, SQL, Docker", 200, 1, None)
    
    monkeypatch.setattr(pdf_service, "extract_text_from_path", mock_extract)
    monkeypatch.setattr(pdf_service, "validate_upload", lambda n, c, t: None)

    files = {"file": ("test.pdf", b"%PDF-1.4...", "application/pdf")}
    data = {"job_description": "We need a Python developer who knows FastAPI and Docker."}
    
    response = client.post("/api/v1/resumes/candidate-analyze", files=files, data=data, headers=headers)
    assert response.status_code == 200
    
    result = response.json()
    assert "ats_score" in result
    assert "score_breakdown" in result
    
    # Assert Skills
    assert "Python" in result["detected_skills"]
    assert "FastAPI" in result["detected_skills"]
    
    # Assert Sections
    assert result["sections"]["WORK EXPERIENCE"]["detected"] is True
    assert result["sections"]["EDUCATION"]["detected"] is False
    
    # Assert Job Alignment
    assert result["job_alignment"]["job_provided"] is True
    assert result["job_alignment"]["relevance_score"] > 0
