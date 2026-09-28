"""
backend/app/services/ood_policy.py

Out-Of-Domain (OOD) / Abstention Policy Engine (Phase 25 Implementation).

Responsibilities:
  - Encapsulates non-destructive classification abstention policy logic.
  - Evaluates ML model confidence against frozen Phase 24 operating points.
  - Returns structured OOD decision metrics without altering classifier predictions.
  - Guarantees semantic distinction: Abstention means "Needs Manual Review", NOT candidate rejection.

Security & Integrity:
  - Pure deterministic policy evaluation without runtime model retraining.
  - Resume text/PII is never logged or exposed.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

from app.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class OODPolicy:
    """Configurable OOD policy settings derived from Phase 24 validation evidence."""
    confidence_threshold: float = 0.85
    entropy_threshold: Optional[float] = None
    margin_threshold: Optional[float] = None
    policy_version: str = "v1.0-phase24-op4"
    enabled: bool = True


@dataclass
class OODDecision:
    """Structured result of OOD policy evaluation."""
    status: str             # "accepted" | "review"
    ood_status: str         # "in_domain_like" | "possible_out_of_domain"
    review_required: bool   # False | True
    policy_version: str     # e.g. "v1.0-phase24-op4"
    reason: str             # "confidence_above_configured_threshold" | "confidence_below_configured_threshold" | ...
    confidence_threshold: float


def get_active_ood_policy() -> OODPolicy:
    """Retrieve active OOD policy configuration from application settings."""
    settings = get_settings()
    return OODPolicy(
        confidence_threshold=settings.ood_confidence_threshold,
        policy_version=settings.ood_policy_version,
        enabled=settings.ood_enabled,
    )


def evaluate_ood_policy(
    predicted_class: Optional[str],
    confidence: Optional[float],
    policy: Optional[OODPolicy] = None,
    all_probabilities: Optional[Dict[str, float]] = None,
) -> OODDecision:
    """
    Evaluate ML prediction outputs against configured OOD policy constraints.

    Args:
        predicted_class: Classifier output string or None.
        confidence: Top predicted class probability float or None.
        policy: Custom OODPolicy instance, or None to use system settings.
        all_probabilities: Optional dictionary of all class probabilities.

    Returns:
        Structured OODDecision object.
    """
    if policy is None:
        policy = get_active_ood_policy()

    if not policy.enabled:
        return OODDecision(
            status="accepted",
            ood_status="in_domain_like",
            review_required=False,
            policy_version=policy.policy_version,
            reason="ood_policy_disabled",
            confidence_threshold=policy.confidence_threshold,
        )

    if predicted_class is None or confidence is None:
        return OODDecision(
            status="review",
            ood_status="possible_out_of_domain",
            review_required=True,
            policy_version=policy.policy_version,
            reason="input_empty_or_model_unavailable",
            confidence_threshold=policy.confidence_threshold,
        )

    # Core auditable threshold comparison
    if confidence >= policy.confidence_threshold:
        return OODDecision(
            status="accepted",
            ood_status="in_domain_like",
            review_required=False,
            policy_version=policy.policy_version,
            reason="confidence_above_configured_threshold",
            confidence_threshold=policy.confidence_threshold,
        )
    else:
        return OODDecision(
            status="review",
            ood_status="possible_out_of_domain",
            review_required=True,
            policy_version=policy.policy_version,
            reason="confidence_below_configured_threshold",
            confidence_threshold=policy.confidence_threshold,
        )
