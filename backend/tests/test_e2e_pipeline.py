"""
backend/tests/test_e2e_pipeline.py

Phase 18: Full End-to-End Candidate Lifecycle Integration Test Suite.
Validates the complete 19-phase Resume Intelligence workflow from auth to AI generation and ATS export.
"""

import io
import pytest


def test_full_candidate_lifecycle_e2e(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Step 1: Create a Job Requisition
    job_payload = {
        "title": "Principal AI Systems Architect",
        "department": "Core AI Intelligence",
        "description": "Architecting large scale ML pipelines, FastAPI services, PyTorch models, and real-time WebSockets.",
        "requirements": [
            {"skill_name": "Python", "importance": "required", "weight": 1.0},
            {"skill_name": "FastAPI", "importance": "required", "weight": 1.0},
            {"skill_name": "PyTorch", "importance": "preferred", "weight": 0.8},
        ],
    }
    job_resp = client.post("/api/v1/jobs", json=job_payload, headers=headers)
    assert job_resp.status_code == 201, job_resp.text
    job_data = job_resp.json()
    job_id = job_data["id"]
    assert job_id > 0

    # Step 2: Upload Resume PDF
    sample_resume_content = b"%PDF-1.4 Mock PDF content for Principal AI Systems Architect with Python, PyTorch, FastAPI"
    files = {"file": ("principal_ai_architect.pdf", io.BytesIO(sample_resume_content), "application/pdf")}
    data = {"job_id": str(job_id)}
    upload_resp = client.post("/api/v1/resumes/upload", files=files, data=data, headers=headers)
    assert upload_resp.status_code == 201, upload_resp.text
    upload_data = upload_resp.json()
    resume_id = upload_data["id"]
    assert resume_id > 0

    # Step 3: Run Live Resume Builder Analysis
    builder_payload = {
        "resume_markdown": "Experienced Principal AI Systems Architect with 10 years experience in Python, PyTorch, FastAPI, Scikit-learn, Docker, and distributed AI systems.",
        "target_job_title": "Principal AI Systems Architect",
    }
    builder_resp = client.post("/api/v1/resumes/live-analysis", json=builder_payload, headers=headers)
    assert builder_resp.status_code == 200, builder_resp.text
    assert "ats_score" in builder_resp.json()

    # Step 4: Run ATS Compatibility Check
    ats_payload = {
        "resume_text": builder_payload["resume_markdown"],
        "job_title": "Principal AI Systems Architect",
        "job_description": job_payload["description"],
    }
    ats_resp = client.post("/api/v1/resumes/ats-check", json=ats_payload, headers=headers)
    assert ats_resp.status_code == 200, ats_resp.text
    assert ats_resp.json()["overall_score"] > 0

    # Step 5: Execute AI Bullet Rewriter
    bullet_payload = {
        "bullet": "Developed ML models using Python and PyTorch for text classification.",
        "target_job_title": "Principal AI Systems Architect",
        "mode": "STAR",
    }
    bullet_resp = client.post("/api/v1/resumes/rewrite-bullet", json=bullet_payload, headers=headers)
    assert bullet_resp.status_code == 200, bullet_resp.text
    assert "optimized_bullet" in bullet_resp.json()

    # Step 6: Generate Cover Letter
    cover_payload = {
        "candidate_name": "Alex Mercer",
        "job_title": "Principal AI Systems Architect",
        "company_name": "Antigravity AI Labs",
        "candidate_skills": ["Python", "PyTorch", "FastAPI"],
        "tone": "EXECUTIVE",
    }
    cover_resp = client.post("/api/v1/resumes/generate-cover-letter", json=cover_payload, headers=headers)
    assert cover_resp.status_code == 200, cover_resp.text
    assert "Alex Mercer" in cover_resp.json()["full_cover_letter"]

    # Step 7: Generate Interview Kit
    interview_payload = {
        "job_title": "Principal AI Systems Architect",
        "candidate_skills": ["Python", "PyTorch", "FastAPI"],
        "missing_skills": ["Kubernetes"],
    }
    interview_resp = client.post("/api/v1/screening/interview-kit", json=interview_payload, headers=headers)
    assert interview_resp.status_code == 200, interview_resp.text
    assert len(interview_resp.json()["questions"]) > 0

    # Step 8: Talent Semantic Search
    search_payload = {
        "query": "Python FastAPI PyTorch AI Architect",
        "limit": 5,
    }
    search_resp = client.post("/api/v1/screening/talent-search", json=search_payload, headers=headers)
    assert search_resp.status_code == 200, search_resp.text
    assert "results" in search_resp.json()

    # Step 9: Export Candidate to Greenhouse ATS
    export_payload = {
        "resume_id": resume_id,
        "job_id": job_id,
        "provider": "greenhouse",
        "credentials": {"api_key": "gh_test_key_12345"},
        "notes": "Top shortlisted candidate from E2E integration test.",
    }
    export_resp = client.post("/api/v1/ats/export", json=export_payload, headers=headers)
    assert export_resp.status_code == 200, export_resp.text
    assert export_resp.json()["success"] is True

    # Step 10: Ingest Candidate via Chrome Extension API
    extension_payload = {
        "name": "Jordan Vance",
        "current_title": "Staff ML Engineer",
        "company": "DeepMind",
        "source_platform": "github",
        "skills": ["Python", "PyTorch", "CUDA", "FastAPI"],
    }
    ext_resp = client.post("/api/v1/extension/ingest", json=extension_payload, headers=headers)
    assert ext_resp.status_code == 200, ext_resp.text
    assert ext_resp.json()["success"] is True

    # Step 11: Verify Token Telemetry
    telemetry_resp = client.get("/api/v1/analytics/token-usage", headers=headers)
    assert telemetry_resp.status_code == 200, telemetry_resp.text
    assert telemetry_resp.json()["total_requests"] > 0
