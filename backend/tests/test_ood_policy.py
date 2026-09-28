"""
backend/tests/test_ood_policy.py

Unit and integration tests for Phase 25 OOD / Abstention Policy Engine.

Verifies:
  A. High-confidence in-domain resume → ACCEPT
  B. Below-threshold resume → REVIEW
  C. Exactly-at-threshold behavior (confidence == threshold)
  D. Empty / unsupported input handling
  E. Existing API response field backward compatibility
  F. Policy configuration loading from Settings
  G. Policy version included in response
  H. Original predicted class retained when abstaining
"""

from __future__ import annotations

import pytest
from app.config import get_settings
from app.services.classification_service import predict, ClassificationResult
from app.services.ood_policy import (
    OODDecision,
    OODPolicy,
    evaluate_ood_policy,
    get_active_ood_policy,
)


def test_ood_policy_config_loading():
    """Verify policy configuration loads default settings derived from Phase 24."""
    policy = get_active_ood_policy()
    assert policy.enabled is True
    assert policy.confidence_threshold == 0.85
    assert policy.policy_version == "v1.0-phase24-op4"


def test_high_confidence_in_domain_accept():
    """Test Case A: High-confidence prediction above threshold is ACCEPTED."""
    policy = OODPolicy(confidence_threshold=0.85, policy_version="v1.0-test")
    decision = evaluate_ood_policy(
        predicted_class="Data Science",
        confidence=0.92,
        policy=policy,
    )
    assert decision.status == "accepted"
    assert decision.ood_status == "in_domain_like"
    assert decision.review_required is False
    assert decision.policy_version == "v1.0-test"
    assert decision.reason == "confidence_above_configured_threshold"


def test_below_threshold_abstain_review():
    """Test Case B: Prediction below threshold returns REVIEW / ABSTAIN."""
    policy = OODPolicy(confidence_threshold=0.85, policy_version="v1.0-test")
    decision = evaluate_ood_policy(
        predicted_class="Web Development",
        confidence=0.74,
        policy=policy,
    )
    assert decision.status == "review"
    assert decision.ood_status == "possible_out_of_domain"
    assert decision.review_required is True
    assert decision.policy_version == "v1.0-test"
    assert decision.reason == "confidence_below_configured_threshold"


def test_exactly_at_threshold_behavior():
    """Test Case C: Prediction EXACTLY at threshold is ACCEPTED."""
    policy = OODPolicy(confidence_threshold=0.85, policy_version="v1.0-test")
    decision = evaluate_ood_policy(
        predicted_class="DevOps",
        confidence=0.85,
        policy=policy,
    )
    assert decision.status == "accepted"
    assert decision.ood_status == "in_domain_like"
    assert decision.review_required is False
    assert decision.reason == "confidence_above_configured_threshold"


def test_empty_input_preserves_error_behavior():
    """Test Case D: Empty or None input returns safe review decision."""
    policy = OODPolicy(confidence_threshold=0.85, policy_version="v1.0-test")
    decision = evaluate_ood_policy(
        predicted_class=None,
        confidence=None,
        policy=policy,
    )
    assert decision.status == "review"
    assert decision.ood_status == "possible_out_of_domain"
    assert decision.review_required is True
    assert decision.reason == "input_empty_or_model_unavailable"


def test_original_predicted_class_retained_when_abstaining():
    """Test Case H: Original predicted class is retained even when abstaining."""
    result = predict("General project manager resume with accountant administrative details.")
    # Regardless of whether confidence is high or low, predicted_domain must be populated if classifier produced output
    if result.predicted_domain is not None:
        assert isinstance(result.predicted_domain, str)
        assert len(result.predicted_domain) > 0

    if result.status == "review":
        assert result.review_required is True
        # Ensure predicted domain wasn't wiped out to None just because of review status
        assert result.predicted_domain is not None


def test_api_response_backward_compatibility():
    """Test Case E & G: Predict returns ClassificationResult with backward compatible + new OOD fields."""
    text = (
        "Senior Data Scientist with experience in Python, Machine Learning, TensorFlow, PyTorch, "
        "Scikit-learn, SQL, Docker, and Cloud Computing AWS."
    )
    result = predict(text)

    # Legacy fields
    assert hasattr(result, "predicted_domain")
    assert hasattr(result, "confidence_label")
    assert hasattr(result, "top_probability")
    assert hasattr(result, "all_probabilities")
    assert hasattr(result, "model_version")
    assert hasattr(result, "is_uncertain")
    assert hasattr(result, "warning")

    # New Phase 25 OOD Policy fields
    assert hasattr(result, "status")
    assert hasattr(result, "ood_status")
    assert hasattr(result, "review_required")
    assert hasattr(result, "policy_version")
    assert hasattr(result, "reason")

    assert result.status in ("accepted", "review")
    assert result.ood_status in ("in_domain_like", "possible_out_of_domain")
    assert isinstance(result.review_required, bool)
    assert result.policy_version == "v1.0-phase24-op4"


def test_disabled_ood_policy_accepts_all():
    """Test that disabling the OOD policy bypasses threshold checks."""
    policy = OODPolicy(confidence_threshold=0.99, enabled=False, policy_version="v1.0-disabled")
    decision = evaluate_ood_policy(
        predicted_class="Cybersecurity",
        confidence=0.50,
        policy=policy,
    )
    assert decision.status == "accepted"
    assert decision.ood_status == "in_domain_like"
    assert decision.review_required is False
    assert decision.reason == "ood_policy_disabled"
