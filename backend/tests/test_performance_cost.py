"""
backend/tests/test_performance_cost.py

Unit test suite for Phase 17: Performance Optimization & LLM Token Cost Control Tracking.
"""

import pytest
from app.services.cost_tracking_service import CostTracker, MODEL_PRICING


def test_cost_tracker_cost_calculation():
    tracker = CostTracker(monthly_budget_usd=100.0)
    tracker.clear()

    # gpt-4o-mini: 1000 prompt tokens ($0.00015) + 1000 completion tokens ($0.00060) = $0.00075
    cost = tracker.calculate_cost("gpt-4o-mini", 1000, 1000)
    assert cost == 0.00075


def test_cost_tracker_logging_and_summary():
    tracker = CostTracker(monthly_budget_usd=10.0)
    tracker.clear()

    tracker.log_usage("gpt-4o-mini", prompt_tokens=10000, completion_tokens=5000, endpoint="test_endpoint")
    tracker.log_usage("gemini-1.5-flash", prompt_tokens=20000, completion_tokens=10000, endpoint="test_endpoint")

    summary = tracker.get_summary()
    assert summary.total_requests == 2
    assert summary.total_tokens == 45000
    assert summary.total_cost_usd > 0
    assert "gpt-4o-mini" in summary.usage_by_model
    assert "gemini-1.5-flash" in summary.usage_by_model
    assert summary.budget_status == "HEALTHY"


def test_cost_tracker_budget_warning_status():
    tracker = CostTracker(monthly_budget_usd=0.001)  # Extremely low budget to trigger warning
    tracker.clear()

    # Log heavy usage
    tracker.log_usage("gpt-4o", prompt_tokens=100000, completion_tokens=50000)
    summary = tracker.get_summary()
    assert summary.budget_status in ["WARNING_BUDGET", "CRITICAL_BUDGET"]


def test_api_get_token_usage_endpoint(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/api/v1/analytics/token-usage", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_prompt_tokens" in data
    assert "total_completion_tokens" in data
    assert "total_cost_usd" in data
    assert "budget_status" in data
