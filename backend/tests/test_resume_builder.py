"""
backend/tests/test_resume_builder.py

Unit test suite for Phase 9: Candidate Live Resume Builder & Match Simulator.
"""

import pytest
from app.services.resume_builder_service import LiveResumeAnalysisResult, analyze_live_resume


def test_analyze_live_resume_basic_metrics():
    text = (
        "JOHN DOE\nemail: john@example.com | phone: (555) 019-2834\n\n"
        "WORK EXPERIENCE\n"
        "Software Engineer at Acme Corp. Developed REST APIs using Python, FastAPI, and PostgreSQL.\n"
        "Managed Docker container deployments and CI/CD pipelines.\n\n"
        "TECHNICAL SKILLS\n"
        "Python, FastAPI, PostgreSQL, Docker, Git, AWS, REST APIs.\n\n"
        "EDUCATION\n"
        "B.S. Computer Science\n"
    )
    result = analyze_live_resume(text)
    
    assert isinstance(result, LiveResumeAnalysisResult)
    assert result.char_count > 0
    assert result.word_count > 20
    assert result.ats_score > 70.0
    assert "Python" in result.extracted_skills or "FastAPI" in result.extracted_skills


def test_analyze_live_resume_target_match():
    text = (
        "ALICE SMITH\nalice@example.com | 555-123-4567\n\n"
        "WORK EXPERIENCE\n"
        "Senior Backend Developer. Built scalable services in Python, PyTorch, and SQL.\n\n"
        "SKILLS\n"
        "Python, SQL, PyTorch, Git, Docker.\n"
    )
    target_skills = ["Python", "PyTorch", "Kubernetes"]
    result = analyze_live_resume(text, target_skills=target_skills)
    
    assert len(result.matched_skills) >= 1
    assert "Kubernetes" in result.missing_skills
    assert result.live_match_score > 0.0


def test_api_live_resume_analysis_endpoint(client, hr_token):
    headers = {"Authorization": f"Bearer {hr_token}"}
    payload = {
        "resume_markdown": "DEVELOPER RESUME\ntest@example.com | 555-999-8888\n\nWORK EXPERIENCE\nBuilt web applications using React and Node.js.\n\nSKILLS\nReact, Node.js, JavaScript, HTML, CSS.",
        "target_skills": ["React", "TypeScript", "Node.js"],
    }
    
    response = client.post("/api/v1/resumes/live-analysis", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "ats_score" in data
    assert "live_match_score" in data
    assert "extracted_skills" in data
    assert "missing_skills" in data
