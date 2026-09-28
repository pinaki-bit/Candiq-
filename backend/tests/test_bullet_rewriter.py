"""
backend/tests/test_bullet_rewriter.py

Unit test suite for Phase 6: AI Resume Bullet Rewriting Module.
"""

import pytest
from app.services.bullet_rewriter import BulletRewriteResult, rewrite_bullet_point


def test_rewrite_bullet_star_mode():
    bullet = "Built a microservice for processing payment transactions."
    result = rewrite_bullet_point(bullet, mode="STAR")
    
    assert isinstance(result, BulletRewriteResult)
    assert result.mode == "STAR"
    assert result.optimized_bullet != ""
    assert result.action_verb_used != ""
    assert len(result.key_changes) > 0


def test_rewrite_bullet_technical_mode():
    bullet = "Managed database migrations and SQL query optimization."
    result = rewrite_bullet_point(bullet, mode="TECHNICAL", target_job_title="Senior Backend Engineer")
    
    assert result.mode == "TECHNICAL"
    assert result.optimized_bullet != ""
    assert len(result.key_changes) > 0


def test_rewrite_bullet_ats_mode():
    bullet = "Handled customer support tickets and user onboarding."
    result = rewrite_bullet_point(bullet, mode="ATS")
    
    assert result.mode == "ATS"
    assert result.optimized_bullet != ""


def test_rewrite_bullet_placeholder_metric_injection():
    # Bullet without quantitative metric should have placeholder requested
    bullet = "Improved website load times."
    result = rewrite_bullet_point(bullet, mode="STAR")
    
    assert len(result.placeholders_needed) > 0
    assert "metric" in result.placeholders_needed[0].lower() or "Metric Required" in result.optimized_bullet


def test_api_rewrite_bullet_endpoint(client, hr_token):
    headers = {"Authorization": f"Bearer {hr_token}"}
    payload = {
        "bullet": "Developed REST API endpoints using FastAPI and PostgreSQL.",
        "mode": "STAR",
        "target_job_title": "Python Developer",
    }
    
    response = client.post("/api/v1/resumes/rewrite-bullet", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "STAR"
    assert "optimized_bullet" in data
    assert "key_changes" in data
    assert "action_verb_used" in data
