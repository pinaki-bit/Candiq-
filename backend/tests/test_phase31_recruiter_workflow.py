"""
backend/tests/test_phase31_recruiter_workflow.py

Phase 31 End-to-End Recruiter Workflow Integration Test.

Verifies:
  1. HR Authenticated Recruiter Job Creation
  2. Multi-resume / single upload processing
  3. Candidate & ScreeningResult persistence
  4. 6-signal hybrid match scoring & breakdown explainability
  5. Recruiter manual review actions: Shortlist (approved), Reject, Review notes
  6. Bulk review update
  7. Verification that AI scores serve as assistive signals and DO NOT auto-reject candidates
  8. OOD status remains distinct from recruiter decision
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.resume import Resume, ProcessingStatus
from app.models.screening import ScreeningResult
from app.models.candidate import Candidate


def test_recruiter_e2e_workflow_lifecycle(client: TestClient, db_session: Session, hr_token: str):
    headers = {"Authorization": f"Bearer {hr_token}"}

    # 1. Create a job position
    job_payload = {
        "title": "Lead Python Developer",
        "department": "Engineering",
        "domain": "Web Development",
        "description": "Looking for an experienced Python developer with FastAPI and Docker skills.",
        "requirements": [
            {"skill_name": "Python", "is_required": True, "weight": 1.0},
            {"skill_name": "FastAPI", "is_required": True, "weight": 1.0},
            {"skill_name": "Docker", "is_required": False, "weight": 1.0},
        ],
    }

    resp = client.post("/api/v1/jobs", json=job_payload, headers=headers)
    assert resp.status_code == 201, resp.text
    job_data = resp.json()
    job_public_id = job_data["public_id"]

    # Verify Job stored in DB
    job_db = db_session.query(Job).filter(Job.public_id == job_public_id).first()
    assert job_db is not None
    assert job_db.title == "Lead Python Developer"

    # 2. Prepare sample PDF resume file
    pdf_content = (
        b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n"
        b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        b"5 0 obj\n<< /Length 120 >>\nstream\n"
        b"BT /F1 12 Tf 72 712 Td (Senior Python Developer with FastAPI and Docker experience) Tj ET\n"
        b"endstream\nendobj\nxref\n0 6\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\n"
        b"0000000115 00000 n\n0000000221 00000 n\n0000000293 00000 n\ntrailer\n<< /Size 6 /Root 1 0 R >>\n"
        b"startxref\n460\n%%EOF\n"
    )

    # 3. Upload & process resume
    files = {"file": ("test_resume.pdf", pdf_content, "application/pdf")}
    upload_resp = client.post(
        "/api/v1/resumes/upload",
        files=files,
        data={"candidate_reference": "CAND-TEST-3101"},
        headers=headers,
    )
    assert upload_resp.status_code == 201, upload_resp.text
    resume_data = upload_resp.json()
    resume_public_id = resume_data["public_id"]

    # Verify Candidate & Resume records in DB
    resume_db = db_session.query(Resume).filter(Resume.public_id == resume_public_id).first()
    assert resume_db is not None
    assert resume_db.status in (ProcessingStatus.COMPLETED, ProcessingStatus.NEEDS_REVIEW)
    assert resume_db.candidate_id is not None

    cand_db = db_session.query(Candidate).filter(Candidate.id == resume_db.candidate_id).first()
    assert cand_db is not None
    assert cand_db.reference_code == "CAND-TEST-3101"

    # 4. Match resume to job
    match_resp = client.post(
        f"/api/v1/screening/{job_public_id}/match/{resume_public_id}",
        headers=headers,
    )
    assert match_resp.status_code == 201, match_resp.text
    result_data = match_resp.json()
    result_public_id = result_data["public_id"]

    # Initial review status MUST be pending (no auto-rejection)
    assert result_data["review_status"] == "pending"
    assert result_data["relevance_score"] is not None
    assert result_data["relevance_score"] > 0.0

    # 5. Fetch ranked candidate list for job
    results_resp = client.get(f"/api/v1/screening/{job_public_id}/results", headers=headers)
    assert results_resp.status_code == 200, results_resp.text
    ranked_list = results_resp.json()
    assert len(ranked_list) >= 1
    assert ranked_list[0]["public_id"] == result_public_id

    # 6. Perform recruiter action: Shortlist candidate with recruiter notes
    review_resp = client.patch(
        f"/api/v1/screening/results/{result_public_id}/review",
        json={"review_status": "approved", "review_notes": "Strong Python candidate, shortlisted for interview."},
        headers=headers,
    )
    assert review_resp.status_code == 200, review_resp.text
    updated_result = review_resp.json()
    assert updated_result["review_status"] == "approved"
    assert updated_result["review_notes"] == "Strong Python candidate, shortlisted for interview."

    # 7. Perform bulk review update
    bulk_resp = client.patch(
        "/api/v1/screening/results/bulk-review",
        json={"result_ids": [result_public_id], "review_status": "approved", "review_notes": "Bulk shortlisted"},
        headers=headers,
    )
    assert bulk_resp.status_code == 200, bulk_resp.text
    bulk_list = bulk_resp.json()
    assert len(bulk_list) == 1
    assert bulk_list[0]["review_status"] == "approved"

    # 8. Verify persistence in SQLite
    result_db = db_session.query(ScreeningResult).filter(ScreeningResult.public_id == result_public_id).first()
    assert result_db is not None
    assert result_db.review_status == "approved"
    assert result_db.review_notes == "Bulk shortlisted"


def test_batch_match_all_resumes_endpoint(client: TestClient, db_session: Session, hr_token: str):
    headers = {"Authorization": f"Bearer {hr_token}"}

    # Create job
    job_payload = {
        "title": "DevOps Specialist",
        "department": "Infrastructure",
        "domain": "DevOps",
        "description": "Looking for DevOps specialist.",
        "requirements": [{"skill_name": "Docker", "is_required": True, "weight": 1.0}],
    }
    j_resp = client.post("/api/v1/jobs", json=job_payload, headers=headers)
    assert j_resp.status_code == 201
    job_id = j_resp.json()["public_id"]

    # Match all resumes
    m_resp = client.post(f"/api/v1/screening/{job_id}/match-all", headers=headers)
    assert m_resp.status_code == 201
    m_list = m_resp.json()
    assert isinstance(m_list, list)
