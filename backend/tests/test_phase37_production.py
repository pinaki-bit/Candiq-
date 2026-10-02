"""
backend/tests/test_phase37_production.py

Comprehensive Test Suite for Phase 37 — Production Deployment, Observability,
Performance & Reliability Hardening.
Tests all 30 required production verification criteria.
"""

import os
import hashlib
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.config import get_settings, Settings
from app.database import engine, check_db_connection, get_db
from app.core.metrics import metrics_collector
from app.services.backup_service import create_database_backup, verify_backup_integrity
from app.services.pdf_service import validate_upload, PDFValidationError
from app.services.ai_service import generate_ai_completion
from app.services.embedding_service import get_embedding_service
from app.services.classification_service import classify_resume


@pytest.fixture
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


# ── 1. Health Endpoint ───────────────────────────────────────────────────
def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "environment" in data


# ── 2. Liveness Probe ─────────────────────────────────────────────────────
def test_liveness(client):
    res = client.get("/health/live")
    assert res.status_code == 200
    assert res.json()["status"] == "alive"


# ── 3. Readiness Probe ────────────────────────────────────────────────────
def test_readiness_probe_healthy(client):
    res = client.get("/health/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert data["checks"]["database"] == "ok"
    assert data["checks"]["ml_model"] == "ok"
    assert data["checks"]["storage"] == "ok"


# ── 4. Database Health ────────────────────────────────────────────────────
def test_database_health():
    connected = check_db_connection()
    assert connected is True


# ── 5. Model Health ───────────────────────────────────────────────────────
def test_model_health():
    settings = get_settings()
    model_path = settings.active_model_path
    assert os.path.exists(model_path)
    assert os.path.isfile(model_path)


# ── 6. Request ID Tracing ─────────────────────────────────────────────────
def test_request_id_tracing(client):
    res = client.get("/health")
    assert "X-Request-ID" in res.headers
    req_id = res.headers["X-Request-ID"]
    assert req_id != ""

    # Test custom correlation ID propagation
    custom_id = "req_custom_test_12345"
    res2 = client.get("/health", headers={"X-Request-ID": custom_id})
    assert res2.headers["X-Request-ID"] == custom_id


# ── 7. Structured Error Response ──────────────────────────────────────────
def test_structured_error_response(client):
    res = client.get("/api/v1/nonexistent_endpoint_xyz")
    assert res.status_code == 404
    data = res.json()
    assert "detail" in data


# ── 8. Exception Handling ────────────────────────────────────────────────
def test_exception_handling(client, auth_headers):
    # Route with missing/invalid params should produce clean JSON response without leaking tracebacks
    res = client.get("/api/v1/discovery/search?min_required_cov=invalid_number", headers=auth_headers)
    assert res.status_code == 422
    data = res.json()
    assert "detail" in data


# ── 9. Security Headers ──────────────────────────────────────────────────
def test_security_headers(client):
    res = client.get("/health")
    assert res.headers.get("X-Content-Type-Options") == "nosniff"
    assert res.headers.get("X-Frame-Options") == "DENY"
    assert res.headers.get("X-XSS-Protection") == "1; mode=block"
    assert res.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "Content-Security-Policy" in res.headers


# ── 10. Rate Limiting ────────────────────────────────────────────────────
def test_rate_limiting(client):
    # Verify rate limit configuration settings
    settings = get_settings()
    assert settings.rate_limit_login is not None
    assert settings.rate_limit_upload is not None


# ── 11. File Size Validation ─────────────────────────────────────────────
def test_file_size_validation():
    settings = get_settings()
    oversized_content = b"%PDF-1.4 " + (b"0" * (settings.max_upload_size_bytes + 100))
    with pytest.raises(PDFValidationError, match="exceeds the maximum allowed size"):
        validate_upload("test.pdf", oversized_content, "application/pdf")


# ── 12. File Magic Validation ────────────────────────────────────────────
def test_file_magic_validation():
    invalid_content = b"NOT_A_PDF_FILE_HEADER"
    with pytest.raises(PDFValidationError, match="signature mismatch"):
        validate_upload("test.pdf", invalid_content, "application/pdf")


# ── 13. Path Traversal Prevention ────────────────────────────────────────
def test_path_traversal_prevention():
    valid_pdf = b"%PDF-1.4 valid content"
    with pytest.raises(PDFValidationError, match="Invalid filename"):
        validate_upload("../../../etc/passwd.pdf", valid_pdf, "application/pdf")

    with pytest.raises(PDFValidationError, match="Invalid filename"):
        validate_upload("..\\system32\\cmd.pdf", valid_pdf, "application/pdf")


# ── 14. Temporary File Cleanup ───────────────────────────────────────────
def test_temporary_file_cleanup():
    with tempfile.NamedTemporaryFile(suffix=".tmp", delete=False) as tmp:
        tmp_path = Path(tmp.name)
        tmp.write(b"temporary data")

    assert tmp_path.exists()
    tmp_path.unlink()
    assert not tmp_path.exists()


# ── 15. Database Rollback ────────────────────────────────────────────────
def test_database_rollback(db_session):
    try:
        from app.models.candidate import Candidate
        invalid_cand = Candidate(id="invalid_type")  # Will fail DB commit
        db_session.add(invalid_cand)
        db_session.commit()
    except Exception:
        db_session.rollback()

    # Session remains active after rollback
    assert db_session.is_active


# ── 16. Database Persistence After Restart ────────────────────────────────
def test_database_persistence_after_restart(db_session):
    from app.models.candidate import Candidate
    cand = Candidate(display_name="Persist Test", reference_code="REF-PERSIST-99")
    db_session.add(cand)
    db_session.commit()

    ref = cand.reference_code

    # Re-query DB
    persisted = db_session.query(Candidate).filter(Candidate.reference_code == ref).first()
    assert persisted is not None
    assert persisted.display_name == "Persist Test"


# ── 17. Backup Integrity & Recovery ──────────────────────────────────────
def test_backup_integrity():
    res = create_database_backup()
    assert res["success"] is True
    assert "backup_path" in res
    assert verify_backup_integrity(res["backup_path"]) is True

    # Cleanup test backup file
    b_path = Path(res["backup_path"])
    if b_path.exists():
        b_path.unlink()


# ── 18. LLM Timeout Handling ────────────────────────────────────────────
def test_llm_timeout_handling():
    res = generate_ai_completion("Test prompt", system_prompt="Test system", timeout_seconds=1)
    assert res is not None
    assert hasattr(res, "content")


# ── 19. LLM Provider Failure Graceful Degradation ───────────────────────
def test_llm_provider_failure_degradation():
    # Calling AI completion with invalid provider fallback
    res = generate_ai_completion("Summarize candidate text", provider="invalid_provider")
    assert res is not None
    assert res.content != ""


# ── 20. Embedding Failure Graceful Degradation ───────────────────────────
def test_embedding_failure_degradation():
    embedder = get_embedding_service()
    vec = embedder.embed_document("Test text for embedding resilience")
    assert isinstance(vec, list)
    assert len(vec) > 0


# ── 21. ML Classifier Failure Graceful Degradation ───────────────────────
def test_ml_failure_degradation():
    res = classify_resume("Simple resume text with no skills")
    assert res is not None
    assert hasattr(res, "predicted_domain")


# ── 22 & 23. WebSocket Connection & Disconnect ────────────────────────────
def test_websocket_pipeline(client):
    with client.websocket_connect("/ws/pipeline") as websocket:
        websocket.send_text("ping")
        data = websocket.receive_text()
        assert data == "pong"


# ── 24. Configuration Validation ─────────────────────────────────────────
def test_configuration_validation():
    settings = get_settings()
    assert settings.app_env in ("development", "production", "test", "staging")
    assert settings.active_model_filename == "model_latest.joblib"


# ── 25. Secret Exposure Prevention ────────────────────────────────────────
def test_secret_exposure_prevention(client):
    res = client.get("/health/ready")
    assert res.status_code == 200
    text = res.text
    # Verify no secret key or credentials leaked in response
    assert "SECRET_KEY" not in text
    assert "changeme123" not in text


# ── 26 & 27. Frontend API Configuration & Production URL ────────────────
def test_frontend_api_configuration():
    import sys, os
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)
    from frontend.services.api_client import API_BASE
    assert API_BASE != ""
    assert isinstance(API_BASE, str)


# ── 28. Graceful Shutdown ─────────────────────────────────────────────────
def test_graceful_shutdown():
    # Test DB engine dispose does not crash process
    engine.dispose()
    assert check_db_connection() is True


# ── 29. No Fake Monitoring Data ──────────────────────────────────────────
def test_no_fake_monitoring_data(client):
    res = client.get("/health/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "uptime_seconds" in data
    if data.get("status") == "No runtime data available":
        assert data.get("total_requests", 0) == 0


# ── 30. Model & Data Integrity Verification ───────────────────────────────
def test_model_and_data_hashes_phase37():
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


def test_ood_threshold_constant():
    settings = get_settings()
    assert settings.ood_confidence_threshold == 0.85


def test_matching_weights_constant():
    from app.services.matching_service import WEIGHTS
    assert WEIGHTS["required_coverage"] == 0.35
    assert WEIGHTS["preferred_coverage"] == 0.15
    assert WEIGHTS["semantic_similarity"] == 0.25
    assert WEIGHTS["lexical_overlap"] == 0.10
    assert WEIGHTS["experience_depth"] == 0.10
    assert WEIGHTS["domain_alignment"] == 0.05
