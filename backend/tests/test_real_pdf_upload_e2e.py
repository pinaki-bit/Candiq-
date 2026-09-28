"""
backend/tests/test_real_pdf_upload_e2e.py

Phase 27: Real Resume Upload End-to-End Integration Test Suite.

Verifies:
  - Technical PDF upload end-to-end (extraction -> NLP -> ML -> OOD -> DB -> API).
  - Accountant OOD PDF upload end-to-end (NEEDS_REVIEW / review status).
  - Image-only scanned PDF upload fallback & graceful error handling.
  - API round-trip retrieval and schema consistency.
  - Error handling (non-PDF, magic mismatch, path traversal).
  - Security & authorization boundaries.
"""

from __future__ import annotations

import os
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.resume import Resume, ProcessingStatus


def test_real_technical_pdf_upload_e2e(client: TestClient, hr_token: str):
    """Verify real technical PDF upload workflow."""
    headers = {"Authorization": f"Bearer {hr_token}"}
    pdf_path = "ml/data/test_pdfs/technical_resume.pdf"
    assert os.path.exists(pdf_path), "Technical PDF test asset missing!"

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    resp = client.post(
        "/api/v1/resumes/upload",
        headers=headers,
        files={"file": ("technical_resume.pdf", pdf_bytes, "application/pdf")},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()

    assert data["public_id"] is not None
    assert data["original_filename"] == "technical_resume.pdf"
    assert data["text_char_count"] > 100
    assert data["predicted_domain"] is not None
    assert data["classification_status"] in ("accepted", "review")
    assert isinstance(data["review_required"], bool)
    assert data["policy_version"] == "v1.0-phase24-op4"
    assert len(data.get("extracted_skills", [])) > 0

    # API Round trip verification
    get_resp = client.get(f"/api/v1/resumes/{data['public_id']}", headers=headers)
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["public_id"] == data["public_id"]
    assert get_data["classification_status"] == data["classification_status"]


def test_real_accountant_ood_pdf_upload_e2e(client: TestClient, hr_token: str):
    """Verify real non-target Accountant OOD PDF upload workflow."""
    headers = {"Authorization": f"Bearer {hr_token}"}
    pdf_path = "ml/data/test_pdfs/accountant_ood_resume.pdf"
    assert os.path.exists(pdf_path), "Accountant OOD PDF test asset missing!"

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    resp = client.post(
        "/api/v1/resumes/upload",
        headers=headers,
        files={"file": ("accountant_ood_resume.pdf", pdf_bytes, "application/pdf")},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()

    assert data["public_id"] is not None
    assert data["text_char_count"] > 100
    assert data["status"] == "needs_review"
    assert data["classification_status"] == "review"
    assert data["review_required"] is True
    assert data["ood_status"] == "possible_out_of_domain"
    assert data["policy_version"] == "v1.0-phase24-op4"
    assert data["policy_reason"] == "confidence_below_configured_threshold"


def test_scanned_image_pdf_upload_handling(client: TestClient, hr_token: str):
    """Verify scanned image-only PDF handling."""
    headers = {"Authorization": f"Bearer {hr_token}"}
    pdf_path = "ml/data/test_pdfs/scanned_image_resume.pdf"
    assert os.path.exists(pdf_path), "Scanned PDF test asset missing!"

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    resp = client.post(
        "/api/v1/resumes/upload",
        headers=headers,
        files={"file": ("scanned_image_resume.pdf", pdf_bytes, "application/pdf")},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()

    assert data["status"] == "failed"
    assert data["error_message"] is not None
    assert "No text could be extracted" in data["error_message"] or "images" in data["error_message"]


def test_upload_error_cases(client: TestClient, hr_token: str):
    """Verify upload validation error cases."""
    headers = {"Authorization": f"Bearer {hr_token}"}

    # Non-PDF extension
    r_txt = client.post(
        "/api/v1/resumes/upload",
        headers=headers,
        files={"file": ("resume.txt", b"Hello text content", "text/plain")},
    )
    assert r_txt.status_code == 422
    assert "not allowed" in r_txt.json()["detail"]

    # Magic bytes mismatch
    r_magic = client.post(
        "/api/v1/resumes/upload",
        headers=headers,
        files={"file": ("fake.pdf", b"NOT_A_REAL_PDF", "application/pdf")},
    )
    assert r_magic.status_code == 422
    assert "signature mismatch" in r_magic.json()["detail"]

    # Path traversal attempt
    r_trav = client.post(
        "/api/v1/resumes/upload",
        headers=headers,
        files={"file": ("../../etc/passwd.pdf", b"%PDF-1.4 sample", "application/pdf")},
    )
    assert r_trav.status_code == 422
    assert "Invalid filename" in r_trav.json()["detail"]


def test_unauthorized_upload_rejected(client: TestClient):
    """Verify unauthenticated uploads are rejected."""
    resp = client.post(
        "/api/v1/resumes/upload",
        files={"file": ("test.pdf", b"%PDF-1.4 sample", "application/pdf")},
    )
    assert resp.status_code == 401
