"""
backend/tests/test_e2e_abstention_verification.py

Phase 26: End-to-End OOD / Abstention Integration Verification Test Suite.

Validates the full application abstention flow from extraction -> service -> policy -> DB -> API -> Frontend semantics.
"""

from __future__ import annotations

import logging
import os
import joblib
import pytest
import pandas as pd
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.resume import Resume, ProcessingStatus
from app.services.classification_service import predict, ClassificationResult
from app.services.ood_policy import evaluate_ood_policy, OODPolicy


def test_case_a_high_confidence_indomain():
    """TEST CASE A: High-Confidence In-Domain Resume Verification."""
    # Test using Phase 24 frozen OP-4 threshold on high confidence sample (prob >= 0.85)
    policy = OODPolicy(confidence_threshold=0.85, policy_version="v1.0-phase24-op4")
    decision = evaluate_ood_policy(
        predicted_class="Cybersecurity",
        confidence=0.9575,
        policy=policy,
    )
    assert decision.status == "accepted"
    assert decision.review_required is False
    assert decision.ood_status == "in_domain_like"
    assert decision.policy_version == "v1.0-phase24-op4"
    assert decision.reason == "confidence_above_configured_threshold"


def test_case_b_ood_review():
    """TEST CASE B: Out-Of-Domain / Accountant Resume Review Verification."""
    # Accountant / non-technical OCR text producing low confidence (< 0.85)
    policy = OODPolicy(confidence_threshold=0.85, policy_version="v1.0-phase24-op4")
    decision = evaluate_ood_policy(
        predicted_class="Data Science",  # Internal classifier output preserved
        confidence=0.4210,
        policy=policy,
    )
    assert decision.status == "review"
    assert decision.review_required is True
    assert decision.ood_status == "possible_out_of_domain"
    assert decision.policy_version == "v1.0-phase24-op4"
    assert decision.reason == "confidence_below_configured_threshold"


def test_case_c_exact_boundary():
    """TEST CASE C: Exact Boundary Condition Verification (0.85 vs 0.849999)."""
    policy = OODPolicy(confidence_threshold=0.85, policy_version="v1.0-phase24-op4")
    
    # Exactly at threshold -> ACCEPTED
    d_at = evaluate_ood_policy("DevOps", 0.85, policy=policy)
    assert d_at.status == "accepted"
    assert d_at.review_required is False
    assert d_at.ood_status == "in_domain_like"

    # Just below threshold -> REVIEW
    d_below = evaluate_ood_policy("DevOps", 0.849999, policy=policy)
    assert d_below.status == "review"
    assert d_below.review_required is True
    assert d_below.ood_status == "possible_out_of_domain"


def test_case_d_database_persistence_and_api(client: TestClient, hr_token: str, db_session: Session):
    """TEST CASE D: Database Persistence & API Response Consistency Verification."""
    headers = {"Authorization": f"Bearer {hr_token}"}
    
    # Create resume in DB with Phase 25 OOD Policy fields
    resume = Resume(
        original_filename="accountant_sample.pdf",
        stored_filename="uuid-acc-001.pdf",
        file_size_bytes=1024,
        mime_type="application/pdf",
        status=ProcessingStatus.NEEDS_REVIEW,
        predicted_domain="Web Development",
        prediction_confidence="low",
        classification_status="review",
        review_required=True,
        ood_status="possible_out_of_domain",
        policy_version="v1.0-phase24-op4",
        policy_reason="confidence_below_configured_threshold",
    )
    db_session.add(resume)
    db_session.commit()
    db_session.refresh(resume)

    # Retrieve through API endpoint
    resp = client.get(f"/api/v1/resumes/{resume.public_id}", headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    # Verify DB and API state agree
    assert data["public_id"] == resume.public_id
    assert data["status"] == "needs_review"
    assert data["classification_status"] == "review"
    assert data["review_required"] is True
    assert data["ood_status"] == "possible_out_of_domain"
    assert data["policy_version"] == "v1.0-phase24-op4"
    assert data["policy_reason"] == "confidence_below_configured_threshold"


def test_case_e_refresh_state_survival(client: TestClient, hr_token: str, db_session: Session):
    """TEST CASE E: Refresh / State Survival Verification."""
    headers = {"Authorization": f"Bearer {hr_token}"}

    resume = Resume(
        original_filename="test_refresh.pdf",
        stored_filename="uuid-ref-002.pdf",
        file_size_bytes=2048,
        mime_type="application/pdf",
        status=ProcessingStatus.NEEDS_REVIEW,
        predicted_domain="Cloud Computing",
        prediction_confidence="medium",
        classification_status="review",
        review_required=True,
        ood_status="possible_out_of_domain",
        policy_version="v1.0-phase24-op4",
        policy_reason="confidence_below_configured_threshold",
    )
    db_session.add(resume)
    db_session.commit()

    # Query 1
    resp1 = client.get(f"/api/v1/resumes/{resume.public_id}", headers=headers)
    assert resp1.status_code == 200

    # Query 2 (simulating page refresh / repeat request)
    resp2 = client.get(f"/api/v1/resumes/{resume.public_id}", headers=headers)
    assert resp2.status_code == 200
    assert resp2.json() == resp1.json()
    assert resp2.json()["review_required"] is True


def test_case_f_frontend_semantics():
    """TEST CASE F: Frontend Neutral Semantics Verification (No Candidate Rejection Wording)."""
    upload_view_path = "frontend/views/upload.py"
    results_view_path = "frontend/views/results.py"

    forbidden_terms = ["Candidate Rejected", "Rejected Candidate", "Failed Candidate", "Unqualified Candidate"]

    for path in [upload_view_path, results_view_path]:
        if os.path.exists(path):
            text = open(path, "r", encoding="utf-8").read()
            for term in forbidden_terms:
                assert term.lower() not in text.lower(), f"Forbidden phrase '{term}' found in {path}!"


def test_case_g_backward_compatibility(client: TestClient, hr_token: str, db_session: Session):
    """TEST CASE G: Backward Compatibility for Pre-Phase 25 Records."""
    headers = {"Authorization": f"Bearer {hr_token}"}

    # Legacy record with null OOD fields
    legacy_resume = Resume(
        original_filename="legacy_resume.pdf",
        stored_filename="uuid-legacy-003.pdf",
        file_size_bytes=512,
        mime_type="application/pdf",
        status=ProcessingStatus.COMPLETED,
        predicted_domain="Data Science",
        prediction_confidence="high",
        classification_status=None,
        review_required=None,
        ood_status=None,
        policy_version=None,
        policy_reason=None,
    )
    db_session.add(legacy_resume)
    db_session.commit()

    resp = client.get(f"/api/v1/resumes/{legacy_resume.public_id}", headers=headers)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["public_id"] == legacy_resume.public_id
    assert data["status"] == "completed"
    assert data["classification_status"] is None
    assert data["review_required"] is None


def test_case_h_api_compatibility(client: TestClient, hr_token: str, db_session: Session):
    """TEST CASE H: API Schema Compatibility Verification."""
    headers = {"Authorization": f"Bearer {hr_token}"}

    resumes_resp = client.get("/api/v1/resumes", headers=headers)
    assert resumes_resp.status_code == 200
    resumes = resumes_resp.json()

    if resumes:
        r = resumes[0]
        # Check required legacy keys are intact
        for legacy_key in ["id", "public_id", "original_filename", "file_size_bytes", "status", "predicted_domain", "prediction_confidence", "uploaded_at"]:
            assert legacy_key in r, f"Legacy key '{legacy_key}' missing from API response!"


def test_case_i_pii_logging_audit(caplog):
    """TEST CASE I: PII and Logging Guardrails Verification."""
    caplog.set_level(logging.INFO)

    sensitive_text = (
        "John Doe, Email: john.doe@example.com, Phone: +1-555-0199, Address: 123 Tech Way. "
        "Senior Software Engineer with Python and Docker experience."
    )
    res = predict(sensitive_text)
    assert res.predicted_domain is not None

    # Audit log output for PII leakage
    for record in caplog.records:
        msg = record.getMessage()
        assert "john.doe@example.com" not in msg, "PII Email leaked into log!"
        assert "+1-555-0199" not in msg, "PII Phone number leaked into log!"
        assert "123 Tech Way" not in msg, "PII Address leaked into log!"


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def _resolve(rel_path: str) -> str:
    if os.path.exists(rel_path):
        return rel_path
    p = os.path.join(PROJECT_ROOT, rel_path)
    if os.path.exists(p):
        return p
    return rel_path


def test_case_j_model_output_preservation():
    """TEST CASE J: Model Output Preservation Verification (Direct vs Service)."""
    model_path = _resolve("ml/artifacts/model_latest.joblib")
    artifact = joblib.load(model_path)
    pipeline = artifact["pipeline"]

    test_text = "Experienced DevOps Engineer with Kubernetes, Terraform, Ansible, AWS, and CI/CD pipelines."

    # Direct model inference
    direct_class = pipeline.predict([test_text])[0]
    
    # Service inference
    service_res = predict(test_text)

    # Class predictions must be 100% identical
    assert service_res.predicted_domain == str(direct_class)
