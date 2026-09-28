"""
backend/tests/test_model_v2_regression.py

Phase 21O: Model Regression & Production Compatibility Test Suite.
Validates candidate model_v2.joblib against schema, edge cases, and inference requirements.
"""

import hashlib
import os
import joblib
import pytest

from app.services.classification_service import ClassificationResult, predict


MODEL_V2_PATH = "ml/artifacts/model_v2.joblib"


def test_model_v2_file_and_hash_integrity():
    """Verify that model_v2.joblib exists and hash matches sidecar file."""
    assert os.path.exists(MODEL_V2_PATH), "model_v2.joblib artifact missing!"
    
    file_bytes = open(MODEL_V2_PATH, "rb").read()
    file_hash = hashlib.sha256(file_bytes).hexdigest()
    
    sidecar_path = f"{MODEL_V2_PATH}.sha256"
    assert os.path.exists(sidecar_path), "model_v2.joblib.sha256 sidecar file missing!"
    
    expected_hash = open(sidecar_path, "r", encoding="utf-8").read().strip().split()[0]
    assert file_hash == expected_hash, f"Hash mismatch! Got {file_hash} vs expected {expected_hash}"


def test_model_v2_classes_available():
    """Verify that all 5 target production domains exist in model_v2."""
    artifact = joblib.load(MODEL_V2_PATH)
    classes = list(artifact["classes"])
    
    expected_classes = [
        "Cloud Computing",
        "Cybersecurity",
        "Data Science",
        "DevOps",
        "Web Development",
    ]
    assert sorted(classes) == sorted(expected_classes), f"Class mismatch: {classes}"


def test_model_v2_inference_schema_compatibility():
    """Test candidate model inference against standard ClassificationResult schema."""
    artifact = joblib.load(MODEL_V2_PATH)
    pipeline = artifact["pipeline"]
    
    sample_text = "Senior Data Scientist specializing in PyTorch, TensorFlow, Scikit-learn, and NLP models."
    pred_label = pipeline.predict([sample_text])[0]
    
    assert pred_label in artifact["classes"]
    assert hasattr(pipeline, "predict_proba")
    
    probs = pipeline.predict_proba([sample_text])[0]
    assert len(probs) == 5
    assert sum(probs) == pytest.approx(1.0, abs=1e-3)


def test_inference_edge_case_empty_text():
    """Verify graceful handling of empty string."""
    res = predict("")
    assert isinstance(res, ClassificationResult)
    assert res.predicted_domain is None
    assert res.is_uncertain is True


def test_inference_edge_case_short_text():
    """Verify handling of extremely short text input."""
    res = predict("python")
    assert isinstance(res, ClassificationResult)
    assert res.predicted_domain is not None or res.is_uncertain is True


def test_inference_edge_case_long_text():
    """Verify handling of very long resume text (10,000+ characters)."""
    long_text = "Senior Software Architect with Python, Docker, Kubernetes experience. " * 300
    res = predict(long_text)
    assert isinstance(res, ClassificationResult)
    assert res.predicted_domain in [
        "Cloud Computing", "Cybersecurity", "Data Science", "DevOps", "Web Development"
    ]


def test_inference_edge_case_unicode_text():
    """Verify handling of Unicode ligatures, special characters, and math symbols."""
    unicode_text = "Experiênce: Devôps Enginëer — 💻 Kubernetes, Docker, Python & PyTorch \u2013 CI/CD."
    res = predict(unicode_text)
    assert isinstance(res, ClassificationResult)
    assert res.predicted_domain is not None
