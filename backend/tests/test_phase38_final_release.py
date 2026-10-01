"""
backend/tests/test_phase38_final_release.py

Final Release Validation Test Suite for Phase 38.
Verifies complete platform functionality, health, authentication, security,
matching, discovery, AI features, model hash integrity, and zero regression.
"""

import os
import hashlib
from pathlib import Path
import pytest

from app.config import get_settings
from app.database import check_db_connection
from app.services.matching_service import WEIGHTS, compute_match, extract_job_skills
from app.services.classification_service import classify_resume
from app.services.embedding_service import get_embedding_service
from app.services.ai_service import generate_ai_completion


@pytest.fixture
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


# ── 1. Application Startup & Health ───────────────────────────────────────
def test_app_startup_and_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "version" in data


# ── 2. Liveness & Readiness Probes ────────────────────────────────────────
def test_liveness_and_readiness_probes(client):
    live_res = client.get("/health/live")
    assert live_res.status_code == 200
    assert live_res.json()["status"] == "alive"

    ready_res = client.get("/health/ready")
    assert ready_res.status_code in (200, 503)
    ready_data = ready_res.json()
    assert "checks" in ready_data


# ── 3. Authentication & Login ─────────────────────────────────────────────
def test_authentication_flow(client):
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "testpass123"},
    )
    assert res.status_code == 200


# ── 4. RBAC & Unauthorized Access ─────────────────────────────────────────
def test_rbac_protection(client):
    res = client.get("/api/v1/admin/users")
    assert res.status_code == 401  # Unauthenticated request rejected


# ── 5. Multi-Tenant Data Isolation ────────────────────────────────────────
def test_multitenant_isolation(client, auth_headers):
    res = client.get("/api/v1/discovery/candidates/nonexistent_id/similar", headers=auth_headers)
    assert res.status_code in (403, 404)


# ── 6. Resume PDF Security Validation ─────────────────────────────────────
def test_pdf_validation():
    from app.services.pdf_service import validate_upload, PDFValidationError
    valid_pdf = b"%PDF-1.4 valid content header"
    validate_upload("resume.pdf", valid_pdf, "application/pdf")

    invalid_signature = b"INVALID_HEADER_DATA"
    with pytest.raises(PDFValidationError):
        validate_upload("resume.pdf", invalid_signature, "application/pdf")


# ── 7. ML Domain Classification ───────────────────────────────────────────
def test_ml_classification():
    text = "Senior Data Scientist proficient in Python, PyTorch, Machine Learning, pandas, and Scikit-Learn."
    res = classify_resume(text)
    assert res is not None
    assert res.predicted_domain in ("Data Science", "Web Development", "Cloud Computing", "DevOps", "Cybersecurity", "Unknown")


# ── 8. OOD Threshold Constant Integrity ───────────────────────────────────
def test_ood_threshold_constant():
    settings = get_settings()
    assert settings.ood_confidence_threshold == 0.85


# ── 9. Matching Algorithm Weights Integrity ──────────────────────────────
def test_matching_weights_constant():
    assert WEIGHTS["required_coverage"] == 0.35
    assert WEIGHTS["preferred_coverage"] == 0.15
    assert WEIGHTS["semantic_similarity"] == 0.25
    assert WEIGHTS["lexical_overlap"] == 0.10
    assert WEIGHTS["experience_depth"] == 0.10
    assert WEIGHTS["domain_alignment"] == 0.05


# ── 10. Semantic Vector Embedding Engine ──────────────────────────────────
def test_semantic_embedding_engine():
    embedder = get_embedding_service()
    vec1 = embedder.embed_document("Python FastAPI developer")
    vec2 = embedder.embed_document("Backend Python engineer")
    assert len(vec1) == 384
    sim = embedder.similarity(vec1, vec2)
    assert 0.0 <= sim <= 1.0


# ── 11. Candidate Discovery Search ────────────────────────────────────────
def test_candidate_discovery_search(client, auth_headers):
    res = client.get("/api/v1/discovery/search?q=Python", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "results" in data


# ── 12. Hiring Analytics Endpoints ────────────────────────────────────────
def test_analytics_endpoints(client, auth_headers):
    res = client.get("/api/v1/analytics/summary", headers=auth_headers)
    assert res.status_code == 200


# ── 13. AI Completion Abstraction ─────────────────────────────────────────
def test_ai_service_completion():
    res = generate_ai_completion("Help rewrite bullet point", system_prompt="Resume Assistant")
    assert res is not None
    assert res.content != ""


# ── 14. System Observability & Runtime Metrics ────────────────────────────
def test_system_metrics_endpoint(client):
    res = client.get("/health/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "uptime_seconds" in data


# ── 15. Security Headers ──────────────────────────────────────────────────
def test_security_headers_present(client):
    res = client.get("/health")
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"


# ── 16. Request ID Correlation ────────────────────────────────────────────
def test_request_id_correlation(client):
    res = client.get("/health")
    assert "X-Request-ID" in res.headers


# ── 17. Frontend API Configuration ────────────────────────────────────────
def test_frontend_api_config():
    from frontend.services.api_client import API_BASE
    assert API_BASE != ""


# ── 18. Model Artifact SHA-256 Hashes ─────────────────────────────────────
def test_model_artifact_hashes():
    root = Path(__file__).resolve().parent.parent.parent

    files_to_hash = {
        "model_latest.joblib": root / "ml" / "artifacts" / "model_latest.joblib",
        "model_v2.joblib": root / "ml" / "artifacts" / "model_v2.joblib",
        "train.csv": root / "ml" / "data" / "processed" / "train.csv",
        "val.csv": root / "ml" / "data" / "processed" / "val.csv",
        "test.csv": root / "ml" / "data" / "processed" / "test.csv",
    }

    expected_hashes = {
        "model_latest.joblib": "0bce6bf763cf39f0b87780e43945f1bbbd80aa85a65da84a28bdfe681b4b60fb",
        "model_v2.joblib": "6be329ae771bfebba5a86bf1130669bdc54aac786768581ebc21e124561e6df4",
        "train.csv": "24fd25a141efa2030394f46d48e206640dc24cba15d78e76ce92dd79e07fd0f0",
        "val.csv": "ceaa476cf720437f42256a7b01cf43d9bcfb9b6c5bd9d16f06ef91e64a161ff6",
        "test.csv": "10e456d0eed5a83c997b23ff0dac4cf95f8a234b3512835845d1fef410c331d4",
    }


    for name, path in files_to_hash.items():
        assert path.exists(), f"File {name} missing at {path}"
        computed = hashlib.sha256(path.read_bytes()).hexdigest().lower()
        assert computed == expected_hashes[name].lower(), f"Hash mismatch for {name}"
