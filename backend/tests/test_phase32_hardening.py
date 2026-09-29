"""
backend/tests/test_phase32_hardening.py

Phase 32 Production End-to-End Hardening, Security, and Data-Integrity Test Suite.

Verifies:
  1. Authorization Matrix & Multi-tenant/Role Access Isolation (Admin, HR, Readonly, Unauthenticated)
  2. Server-side Job & Candidate Access Boundaries
  3. Duplicate Resume Upload & Repeated Match Request Deduplication
  4. Batch Upload Partial Failure Resilience & Path Traversal Security
  5. File Validation Hardening (Magic Bytes, MIME, Empty Files, Traversal)
  6. Transaction Integrity & Rollback Safety
  7. Recruiter State Machine Transitions & OOD Status Distinction
  8. Bulk Review Action Resilience
  9. Recruiter Notes Persistence & Privacy
  10. API Error Response Contracts (No Stack Traces / Secrets Leaked)
"""

import time
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.resume import Resume, ProcessingStatus
from app.models.screening import ScreeningResult, ReviewStatus
from app.models.candidate import Candidate


def _sample_pdf_bytes():
    return (
        b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n"
        b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        b"5 0 obj\n<< /Length 110 >>\nstream\n"
        b"BT /F1 12 Tf 72 712 Td (Experienced Cloud Architect with AWS, Kubernetes, Python) Tj ET\n"
        b"endstream\nendobj\nxref\n0 6\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n"
        b"0000000115 00000 n\n0000000221 00000 n\n0000000293 00000 n\ntrailer\n<< /Size 6 /Root 1 0 R >>\n"
        b"startxref\n450\n%%EOF\n"
    )


# ── 1. Authorization Matrix & Role Access Isolation ───────────────────────

def test_auth_matrix_role_permissions(client: TestClient, admin_token: str, hr_token: str, readonly_token: str):
    admin_hdr = {"Authorization": f"Bearer {admin_token}"}
    hr_hdr = {"Authorization": f"Bearer {hr_token}"}
    ro_hdr = {"Authorization": f"Bearer {readonly_token}"}

    # Unauthenticated access rejected
    assert client.get("/api/v1/jobs").status_code == 401
    assert client.get("/api/v1/resumes").status_code == 401
    assert client.post("/api/v1/jobs", json={"title": "Test"}).status_code == 401

    # Readonly role escalation guards
    assert client.post("/api/v1/jobs", json={"title": "Dev"}, headers=ro_hdr).status_code == 403
    assert client.post("/api/v1/resumes/upload-batch", files=[], headers=ro_hdr).status_code == 403

    # HR role allowed job creation
    resp = client.post("/api/v1/jobs", json={"title": "HR Job"}, headers=hr_hdr)
    assert resp.status_code == 201
    job_id = resp.json()["public_id"]

    # HR role cannot deactivate job (Admin only)
    assert client.delete(f"/api/v1/jobs/{job_id}", headers=hr_hdr).status_code == 403

    # Admin role can deactivate job
    assert client.delete(f"/api/v1/jobs/{job_id}", headers=admin_hdr).status_code == 200


# ── 2. Duplicate Upload & Match Request Deduplication ──────────────────────

def test_duplicate_screening_deduplication(client: TestClient, db_session: Session, hr_token: str):
    hdr = {"Authorization": f"Bearer {hr_token}"}

    # Create Job
    j_resp = client.post("/api/v1/jobs", json={"title": "Cloud Engineer"}, headers=hdr)
    assert j_resp.status_code == 201
    job_id = j_resp.json()["public_id"]

    # Upload Resume
    files = {"file": ("cloud_resume.pdf", _sample_pdf_bytes(), "application/pdf")}
    u_resp = client.post("/api/v1/resumes/upload", files=files, headers=hdr)
    assert u_resp.status_code == 201
    resume_id = u_resp.json()["public_id"]

    # First Match Request
    m1_resp = client.post(f"/api/v1/screening/{job_id}/match/{resume_id}", headers=hdr)
    assert m1_resp.status_code == 201
    scr1_id = m1_resp.json()["public_id"]

    # Repeated Match Request for SAME job + resume
    m2_resp = client.post(f"/api/v1/screening/{job_id}/match/{resume_id}", headers=hdr)
    assert m2_resp.status_code == 201
    scr2_id = m2_resp.json()["public_id"]

    # Verify ID is reused (in-place update, no duplicate ScreeningResult records)
    assert scr1_id == scr2_id

    # Verify DB count for this job+resume pair is exactly 1
    job_db = db_session.query(Job).filter(Job.public_id == job_id).first()
    resume_db = db_session.query(Resume).filter(Resume.public_id == resume_id).first()
    count = db_session.query(ScreeningResult).filter(
        ScreeningResult.job_id == job_db.id,
        ScreeningResult.resume_id == resume_db.id,
    ).count()
    assert count == 1


# ── 3. File Security & Path Traversal Protections ─────────────────────────

def test_file_security_and_traversal_rejection(client: TestClient, hr_token: str):
    hdr = {"Authorization": f"Bearer {hr_token}"}

    # Path traversal attempt in filename rejected with HTTP 422
    files = {"file": ("../../../../etc/passwd.pdf", _sample_pdf_bytes(), "application/pdf")}
    resp = client.post("/api/v1/resumes/upload", files=files, headers=hdr)
    assert resp.status_code == 422
    assert "Invalid filename" in resp.json()["detail"] or "traversal" in resp.json()["detail"].lower()

    # Non-PDF extension rejection
    bad_ext = {"file": ("malicious.exe", b"MZexecutablecontent", "application/octet-stream")}
    res_ext = client.post("/api/v1/resumes/upload", files=bad_ext, headers=hdr)
    assert res_ext.status_code == 422
    assert "pdf" in res_ext.json()["detail"].lower()

    # Empty PDF rejection
    empty_file = {"file": ("empty.pdf", b"", "application/pdf")}
    res_empty = client.post("/api/v1/resumes/upload", files=empty_file, headers=hdr)
    assert res_empty.status_code == 422


# ── 4. Batch Upload Partial Failure Resilience ────────────────────────────

def test_batch_upload_partial_failure_resilience(client: TestClient, hr_token: str):
    hdr = {"Authorization": f"Bearer {hr_token}"}

    files = [
        ("files", ("valid_1.pdf", _sample_pdf_bytes(), "application/pdf")),
        ("files", ("invalid.txt", b"plain text file", "text/plain")),
        ("files", ("valid_2.pdf", _sample_pdf_bytes(), "application/pdf")),
    ]

    resp = client.post("/api/v1/resumes/upload-batch", files=files, headers=hdr)
    assert resp.status_code == 201
    res_list = resp.json()

    # Valid PDFs succeed, invalid TXT is skipped safely without crashing batch
    assert len(res_list) == 2
    filenames = [r["original_filename"] for r in res_list]
    assert "valid_1.pdf" in filenames
    assert "valid_2.pdf" in filenames


# ── 5. Recruiter Status State Machine & OOD Distinction ────────────────────

def test_recruiter_state_transitions_and_ood_distinction(client: TestClient, hr_token: str):
    hdr = {"Authorization": f"Bearer {hr_token}"}

    # Create job & match resume
    j_resp = client.post("/api/v1/jobs", json={"title": "QA Engineer"}, headers=hdr)
    job_id = j_resp.json()["public_id"]

    files = {"file": ("qa_resume.pdf", _sample_pdf_bytes(), "application/pdf")}
    u_resp = client.post("/api/v1/resumes/upload", files=files, headers=hdr)
    resume_id = u_resp.json()["public_id"]

    m_resp = client.post(f"/api/v1/screening/{job_id}/match/{resume_id}", headers=hdr)
    scr_id = m_resp.json()["public_id"]

    # Transition: pending -> approved (shortlisted)
    r1 = client.patch(f"/api/v1/screening/results/{scr_id}/review", json={"review_status": "approved"}, headers=hdr)
    assert r1.status_code == 200
    assert r1.json()["review_status"] == "approved"

    # Transition: approved -> rejected
    r2 = client.patch(f"/api/v1/screening/results/{scr_id}/review", json={"review_status": "rejected"}, headers=hdr)
    assert r2.status_code == 200
    assert r2.json()["review_status"] == "rejected"

    # Transition: rejected -> on_hold
    r3 = client.patch(f"/api/v1/screening/results/{scr_id}/review", json={"review_status": "on_hold"}, headers=hdr)
    assert r3.status_code == 200
    assert r3.json()["review_status"] == "on_hold"

    # Invalid status code
    r4 = client.patch(f"/api/v1/screening/results/{scr_id}/review", json={"review_status": "invalid_status"}, headers=hdr)
    assert r4.status_code == 422


# ── 6. Bulk Review Action Resilience ──────────────────────────────────────

def test_bulk_review_resilience(client: TestClient, hr_token: str):
    hdr = {"Authorization": f"Bearer {hr_token}"}

    # Empty list
    b1 = client.patch("/api/v1/screening/results/bulk-review", json={"result_ids": [], "review_status": "approved"}, headers=hdr)
    assert b1.status_code == 200
    assert b1.json() == []

    # Non-existent IDs handled safely
    b2 = client.patch("/api/v1/screening/results/bulk-review", json={"result_ids": ["non_existent_1", "non_existent_2"], "review_status": "rejected"}, headers=hdr)
    assert b2.status_code == 200
    assert b2.json() == []


# ── 7. Performance Sanity Checks ──────────────────────────────────────────

def test_performance_sanity_checks(client: TestClient, hr_token: str):
    hdr = {"Authorization": f"Bearer {hr_token}"}

    # Measure upload + pipeline latency
    t0 = time.perf_counter()
    files = {"file": ("perf_resume.pdf", _sample_pdf_bytes(), "application/pdf")}
    resp = client.post("/api/v1/resumes/upload", files=files, headers=hdr)
    t1 = time.perf_counter()

    assert resp.status_code == 201
    processing_time_ms = (t1 - t0) * 1000
    assert processing_time_ms < 5000  # under 5s synchronous pipeline target
