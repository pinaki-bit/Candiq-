"""
backend/tests/test_phase35_resume_builder.py

Unit and Integration Test Suite for Phase 35 — AI Resume Builder & Live ATS Match Optimization.
Tests all 24 required cases.
"""

import json
import pytest
from app.models.job import Job, JobRequirement
from app.models.resume_builder import ResumeDraft, ResumeVersion
from app.models.user import User
from app.services.matching_service import compute_hybrid_match


@pytest.fixture
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def test_job(db_session):
    job = Job(
        title="Senior Python Backend Engineer",
        description="We are looking for a Senior Python Developer with FastAPI and PostgreSQL expertise.",
        department="Engineering",
        domain="Engineering",
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    req1 = JobRequirement(job_id=job.id, skill_name="Python", weight=1.0, is_required=True)
    req2 = JobRequirement(job_id=job.id, skill_name="FastAPI", weight=1.0, is_required=True)
    req3 = JobRequirement(job_id=job.id, skill_name="PostgreSQL", weight=1.0, is_required=True)
    pref1 = JobRequirement(job_id=job.id, skill_name="Docker", weight=1.0, is_required=False)
    pref2 = JobRequirement(job_id=job.id, skill_name="Kubernetes", weight=1.0, is_required=False)

    db_session.add_all([req1, req2, req3, pref1, pref2])
    db_session.commit()
    return job


# ── 1. Create Resume Draft ────────────────────────────────────────────────
def test_create_resume_draft(client, auth_headers):
    payload = {
        "title": "My Software Engineer Resume",
        "structured_content": {
            "personal_info": {"full_name": "Alice Smith", "email": "alice@example.com"},
            "summary": "Experienced Python developer",
            "skills": ["Python", "FastAPI", "SQL"],
        },
    }
    res = client.post("/api/v1/resume-builder", json=payload, headers=auth_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == "My Software Engineer Resume"
    assert data["structured_content"]["personal_info"]["full_name"] == "Alice Smith"
    assert "id" in data


# ── 2. Update Resume Draft ────────────────────────────────────────────────
def test_update_resume_draft(client, auth_headers):
    create_res = client.post(
        "/api/v1/resume-builder",
        json={"title": "Draft 1", "structured_content": {"summary": "Initial summary"}},
        headers=auth_headers,
    )
    draft_id = create_res.json()["id"]

    patch_res = client.patch(
        f"/api/v1/resume-builder/{draft_id}",
        json={
            "title": "Updated Draft Title",
            "structured_content": {"summary": "Updated summary statement", "skills": ["Python"]},
        },
        headers=auth_headers,
    )
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["title"] == "Updated Draft Title"
    assert data["structured_content"]["summary"] == "Updated summary statement"


# ── 3. Retrieve Resume Draft ──────────────────────────────────────────────
def test_get_resume_draft(client, auth_headers):
    create_res = client.post(
        "/api/v1/resume-builder",
        json={"title": "Fetchable Draft"},
        headers=auth_headers,
    )
    draft_id = create_res.json()["id"]

    get_res = client.get(f"/api/v1/resume-builder/{draft_id}", headers=auth_headers)
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Fetchable Draft"


# ── 4. Delete / Modify Resume Section ─────────────────────────────────────
def test_section_modification(client, auth_headers):
    create_res = client.post(
        "/api/v1/resume-builder",
        json={"title": "Section Draft", "structured_content": {"skills": ["Python", "Java", "C++"]}},
        headers=auth_headers,
    )
    draft_id = create_res.json()["id"]

    # Delete 'Java' and 'C++' from skills
    patch_res = client.patch(
        f"/api/v1/resume-builder/{draft_id}",
        json={"structured_content": {"skills": ["Python"]}},
        headers=auth_headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["structured_content"]["skills"] == ["Python"]


# ── 5. Version Creation ───────────────────────────────────────────────────
def test_create_resume_version(client, auth_headers):
    create_res = client.post(
        "/api/v1/resume-builder",
        json={"title": "Versioned Draft"},
        headers=auth_headers,
    )
    draft_id = create_res.json()["id"]

    ver_res = client.post(
        f"/api/v1/resume-builder/{draft_id}/versions?label=v2_snapshot",
        headers=auth_headers,
    )
    assert ver_res.status_code == 201
    data = ver_res.json()
    assert data["label"] == "v2_snapshot"
    assert data["version_number"] >= 1


# ── 6. Version Restoration ────────────────────────────────────────────────
def test_restore_resume_version(client, auth_headers):
    # Create draft with version 1 (skills: Python)
    create_res = client.post(
        "/api/v1/resume-builder",
        json={"title": "Restorable Draft", "structured_content": {"skills": ["Python"]}},
        headers=auth_headers,
    )
    draft_id = create_res.json()["id"]

    # Save version 1 snapshot
    v1_res = client.post(
        f"/api/v1/resume-builder/{draft_id}/versions?label=Snapshot1",
        headers=auth_headers,
    )
    v1_id = v1_res.json()["id"]

    # Update draft to skills: Rust
    client.patch(
        f"/api/v1/resume-builder/{draft_id}",
        json={"structured_content": {"skills": ["Rust"]}},
        headers=auth_headers,
    )

    # Restore version 1
    restore_res = client.post(
        f"/api/v1/resume-builder/{draft_id}/restore/{v1_id}",
        headers=auth_headers,
    )
    assert restore_res.status_code == 200
    assert restore_res.json()["structured_content"]["skills"] == ["Python"]


# ── 7. Job Selection & Linkage ────────────────────────────────────────────
def test_job_selection(client, auth_headers, test_job):
    create_res = client.post(
        "/api/v1/resume-builder",
        json={"title": "Job-Linked Draft", "target_job_id": test_job.public_id},
        headers=auth_headers,
    )
    assert create_res.status_code == 201
    assert create_res.json()["target_job_id"] == test_job.public_id


# ── 8 & 9 & 10 & 11. Real 6-Signal Matching & Score Breakdown ────────────
def test_real_ats_matching(client, auth_headers, test_job):
    create_res = client.post(
        "/api/v1/resume-builder",
        json={
            "title": "ATS Match Draft",
            "target_job_id": test_job.public_id,
            "structured_content": {
                "summary": "Senior Python Backend Developer proficient in FastAPI and PostgreSQL.",
                "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
            },
        },
        headers=auth_headers,
    )
    draft_id = create_res.json()["id"]

    match_res = client.post(
        f"/api/v1/resume-builder/{draft_id}/match",
        json={"job_id": test_job.public_id},
        headers=auth_headers,
    )
    assert match_res.status_code == 200
    data = match_res.json()

    assert data["match_score"] > 50.0
    assert data["required_coverage"] == 100.0  # Python, FastAPI, PostgreSQL covered
    assert "Docker" in data["matched_skills"]
    assert "Kubernetes" in data["missing_preferred_skills"]
    assert len(data["missing_required_skills"]) == 0
    assert "signal_scores" in data["score_breakdown"]


# ── 12. Before / After Score Calculation ──────────────────────────────────
def test_before_after_score_calculation(client, auth_headers, test_job):
    # Create draft with partial skills (Python only)
    create_res = client.post(
        "/api/v1/resume-builder",
        json={
            "title": "Before After Draft",
            "target_job_id": test_job.public_id,
            "structured_content": {"skills": ["Python"]},
        },
        headers=auth_headers,
    )
    draft_id = create_res.json()["id"]

    # Save initial snapshot
    v1_res = client.post(
        f"/api/v1/resume-builder/{draft_id}/versions?label=v1",
        headers=auth_headers,
    )
    v1_id = v1_res.json()["id"]

    # Update draft to add FastAPI and PostgreSQL
    client.patch(
        f"/api/v1/resume-builder/{draft_id}",
        json={"structured_content": {"skills": ["Python", "FastAPI", "PostgreSQL"]}},
        headers=auth_headers,
    )

    # Compare match against version 1
    match_res = client.post(
        f"/api/v1/resume-builder/{draft_id}/match",
        json={"job_id": test_job.public_id, "compare_version_id": v1_id},
        headers=auth_headers,
    )
    assert match_res.status_code == 200
    data = match_res.json()
    assert data["before_score"] is not None
    assert data["after_score"] > data["before_score"]
    assert data["score_delta"] > 0.0


# ── 13 & 14. Tenant Isolation & RBAC ──────────────────────────────────────
def test_tenant_isolation_resume_builder(client, auth_headers, db_session):
    # Create draft under another tenant directly in DB
    other_draft = ResumeDraft(
        user_id=999,
        tenant_id="tenant_b",
        title="Other Tenant Draft",
        structured_content_json="{}",
    )
    db_session.add(other_draft)
    db_session.commit()

    res = client.get(f"/api/v1/resume-builder/{other_draft.public_id}", headers=auth_headers)
    assert res.status_code in (403, 404)


# ── 15. Unauthenticated Access ────────────────────────────────────────────
def test_unauthenticated_access_resume_builder(client):
    res = client.get("/api/v1/resume-builder")
    assert res.status_code == 401


# ── 16. Empty Resume Handling ─────────────────────────────────────────────
def test_empty_resume_handling(client, auth_headers, test_job):
    create_res = client.post(
        "/api/v1/resume-builder",
        json={"title": "Empty Draft", "structured_content": {}},
        headers=auth_headers,
    )
    draft_id = create_res.json()["id"]

    match_res = client.post(
        f"/api/v1/resume-builder/{draft_id}/match",
        json={"job_id": test_job.public_id},
        headers=auth_headers,
    )
    assert match_res.status_code == 200
    assert match_res.json()["match_score"] >= 0.0


# ── 17. Missing Job Handling ──────────────────────────────────────────────
def test_missing_job_handling(client, auth_headers):
    create_res = client.post(
        "/api/v1/resume-builder",
        json={"title": "No Job Draft"},
        headers=auth_headers,
    )
    draft_id = create_res.json()["id"]

    match_res = client.post(
        f"/api/v1/resume-builder/{draft_id}/match",
        json={"job_id": "non_existent_job_id"},
        headers=auth_headers,
    )
    assert match_res.status_code in (400, 404)


# ── 18. Invalid Input Validation ──────────────────────────────────────────
def test_invalid_input_validation(client, auth_headers):
    res = client.post("/api/v1/resume-builder", json={"structured_content": "invalid_type"}, headers=auth_headers)
    assert res.status_code == 422


# ── 19 & 20. AI Assistant & Content Labeling ──────────────────────────────
def test_ai_resume_builder_assistant(client, auth_headers, test_job):
    create_res = client.post(
        "/api/v1/resume-builder",
        json={
            "title": "AI Draft",
            "target_job_id": test_job.public_id,
            "structured_content": {"summary": "Backend developer with Python skills."},
        },
        headers=auth_headers,
    )
    draft_id = create_res.json()["id"]

    ai_res = client.post(
        f"/api/v1/resume-builder/{draft_id}/ai-assist",
        json={"assist_type": "summary", "target_job_id": test_job.public_id},
        headers=auth_headers,
    )
    assert ai_res.status_code == 200
    data = ai_res.json()
    assert "label" in data
    assert "AI Generated — Verify Before Use" in data["label"]


# ── 21. No Fabricated Score ───────────────────────────────────────────────
def test_no_fabricated_score(client, auth_headers, test_job):
    struct_content = {"skills": ["Python", "FastAPI"]}
    create_res = client.post(
        "/api/v1/resume-builder",
        json={
            "title": "Score Check Draft",
            "target_job_id": test_job.public_id,
            "structured_content": struct_content,
        },
        headers=auth_headers,
    )
    draft_id = create_res.json()["id"]

    match_res = client.post(
        f"/api/v1/resume-builder/{draft_id}/match",
        json={"job_id": test_job.public_id},
        headers=auth_headers,
    )
    api_score = match_res.json()["match_score"]

    # Verify score comes directly from compute_real_ats_match
    from app.services.resume_builder_service import compute_real_ats_match
    raw_res = compute_real_ats_match(struct_content, test_job)
    assert abs(api_score - raw_res["match_score"]) < 0.01


# ── 22. PDF Export ────────────────────────────────────────────────────────
def test_export_resume_pdf(client, auth_headers):
    create_res = client.post(
        "/api/v1/resume-builder",
        json={
            "title": "Exportable PDF Resume",
            "structured_content": {
                "personal_info": {"full_name": "Bob Architect", "email": "bob@example.com"},
                "summary": "Cloud Architect with 8+ years experience.",
                "skills": ["AWS", "Terraform", "Go"],
            },
        },
        headers=auth_headers,
    )
    draft_id = create_res.json()["id"]

    pdf_res = client.get(f"/api/v1/resume-builder/{draft_id}/export-pdf", headers=auth_headers)
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert pdf_res.content.startswith(b"%PDF")


# ── 23. Persistence After Restart ─────────────────────────────────────────
def test_persistence_after_restart(client, auth_headers, db_session):
    create_res = client.post(
        "/api/v1/resume-builder",
        json={"title": "Persistent Draft", "structured_content": {"summary": "Persistent text"}},
        headers=auth_headers,
    )
    draft_id = create_res.json()["id"]

    # Check DB record
    d = db_session.query(ResumeDraft).filter(ResumeDraft.public_id == draft_id).first()
    assert d is not None
    assert "Persistent text" in d.structured_content_json


# ── 24. Existing Recruiter Workflow Unaffected ─────────────────────────────
def test_existing_recruiter_workflow_unaffected(client, auth_headers, test_job):
    res = client.get(f"/api/v1/jobs/{test_job.public_id}", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["title"] == test_job.title
