"""
frontend/services/api_client.py

Typed HTTP client for the Resume Screening API.

All calls go through this module so that:
  - The base URL is configured in one place.
  - Auth tokens are injected from session state automatically.
  - Error responses are parsed uniformly.
  - No raw requests.* calls appear in page code.
"""

from __future__ import annotations

import os
from typing import Any

import requests
import streamlit as st

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")
_TIMEOUT = 30  # seconds


class APIError(Exception):
    """Raised when the API returns a non-2xx response."""
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"API error {status_code}: {detail}")


def _headers() -> dict[str, str]:
    """Return auth headers from Streamlit session state."""
    token = st.session_state.get("access_token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


# ---------------------------------------------------------------------------
# Health & System Observability
# ---------------------------------------------------------------------------

def get_health_status() -> dict[str, Any]:
    """Fetch base health liveness summary."""
    resp = requests.get(f"{API_BASE}/health", timeout=5)
    return _handle_response(resp)


def get_liveness_probe() -> dict[str, Any]:
    """Fetch Kubernetes liveness status."""
    resp = requests.get(f"{API_BASE}/health/live", timeout=5)
    return _handle_response(resp)


def get_readiness_probe() -> dict[str, Any]:
    """Fetch comprehensive readiness status."""
    resp = requests.get(f"{API_BASE}/health/ready", timeout=5)
    return _handle_response(resp)


def get_runtime_metrics() -> dict[str, Any]:
    """Fetch real-time aggregate performance measurements."""
    resp = requests.get(f"{API_BASE}/health/metrics", timeout=5)
    return _handle_response(resp)


def _handle_response(resp: requests.Response) -> Any:
    """Raise APIError on non-2xx; otherwise return parsed JSON."""
    if resp.status_code >= 400:
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        raise APIError(resp.status_code, detail)
    if resp.content:
        return resp.json()
    return {}


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

def login(email: str, password: str) -> dict:
    resp = requests.post(
        f"{API_BASE}/api/v1/auth/login",
        json={"email": email, "password": password},
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def get_me() -> dict:
    resp = requests.get(
        f"{API_BASE}/api/v1/auth/me",
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------

def list_jobs(active_only: bool = True) -> list[dict]:
    resp = requests.get(
        f"{API_BASE}/api/v1/jobs",
        params={"active_only": active_only},
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def create_job(payload: dict) -> dict:
    resp = requests.post(
        f"{API_BASE}/api/v1/jobs",
        json=payload,
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def get_job(job_id: str) -> dict:
    resp = requests.get(
        f"{API_BASE}/api/v1/jobs/{job_id}",
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def deactivate_job(job_id: str) -> dict:
    resp = requests.delete(
        f"{API_BASE}/api/v1/jobs/{job_id}",
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


# ---------------------------------------------------------------------------
# Resumes
# ---------------------------------------------------------------------------

def upload_resume(file_bytes: bytes, filename: str, candidate_ref: str | None = None) -> dict:
    files = {"file": (filename, file_bytes, "application/pdf")}
    data = {}
    if candidate_ref:
        data["candidate_reference"] = candidate_ref
    resp = requests.post(
        f"{API_BASE}/api/v1/resumes/upload",
        files=files,
        data=data,
        headers=_headers(),
        timeout=60,
    )
    return _handle_response(resp)


def upload_batch_resumes(file_list: list[tuple[str, bytes]], job_id: str | None = None) -> list[dict]:
    files = [("files", (filename, content, "application/pdf")) for filename, content in file_list]
    data = {}
    if job_id:
        data["job_id"] = job_id
    resp = requests.post(
        f"{API_BASE}/api/v1/resumes/upload-batch",
        files=files,
        data=data,
        headers=_headers(),
        timeout=120,
    )
    return _handle_response(resp)


def list_resumes(status_filter: str | None = None) -> list[dict]:
    params = {}
    if status_filter:
        params["status_filter"] = status_filter
    resp = requests.get(
        f"{API_BASE}/api/v1/resumes",
        params=params,
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def get_resume(resume_id: str) -> dict:
    resp = requests.get(
        f"{API_BASE}/api/v1/resumes/{resume_id}",
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


# ---------------------------------------------------------------------------
# Screening
# ---------------------------------------------------------------------------

def match_resume_to_job(job_id: str, resume_id: str) -> dict:
    resp = requests.post(
        f"{API_BASE}/api/v1/screening/{job_id}/match/{resume_id}",
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def match_all_resumes_to_job(job_id: str) -> list[dict]:
    resp = requests.post(
        f"{API_BASE}/api/v1/screening/{job_id}/match-all",
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def get_job_results(job_id: str, review_status: str | None = None) -> list[dict]:
    params = {}
    if review_status:
        params["review_status"] = review_status
    resp = requests.get(
        f"{API_BASE}/api/v1/screening/{job_id}/results",
        params=params,
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def update_review(result_id: str, review_status: str, notes: str | None = None) -> dict:
    resp = requests.patch(
        f"{API_BASE}/api/v1/screening/results/{result_id}/review",
        json={"review_status": review_status, "review_notes": notes},
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def bulk_update_reviews(result_ids: list[str], review_status: str, notes: str | None = None) -> list[dict]:
    resp = requests.patch(
        f"{API_BASE}/api/v1/screening/results/bulk-review",
        json={"result_ids": result_ids, "review_status": review_status, "review_notes": notes},
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

def get_summary() -> dict:
    resp = requests.get(
        f"{API_BASE}/api/v1/analytics/summary",
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def get_domain_distribution() -> dict:
    resp = requests.get(
        f"{API_BASE}/api/v1/analytics/domain-dist",
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def get_skill_heatmap(top_n: int = 15) -> dict:
    resp = requests.get(
        f"{API_BASE}/api/v1/analytics/skill-heatmap",
        params={"top_n": top_n},
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def get_score_distribution(job_id: str | None = None) -> dict:
    params = {}
    if job_id:
        params["job_id"] = job_id
    resp = requests.get(
        f"{API_BASE}/api/v1/analytics/score-hist",
        params=params,
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def get_analytics_funnel(job_id: str | None = None) -> dict:
    params = {}
    if job_id:
        params["job_id"] = job_id
    resp = requests.get(
        f"{API_BASE}/api/v1/analytics/funnel",
        params=params,
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def get_job_analytics(job_id: str | None = None) -> dict:
    params = {}
    if job_id:
        params["job_id"] = job_id
    resp = requests.get(
        f"{API_BASE}/api/v1/analytics/jobs",
        params=params,
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def get_skill_intelligence(job_id: str | None = None, top_n: int = 15) -> dict:
    params = {"top_n": top_n}
    if job_id:
        params["job_id"] = job_id
    resp = requests.get(
        f"{API_BASE}/api/v1/analytics/skills",
        params=params,
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def get_time_series_analytics(days: str = "30d") -> dict:
    resp = requests.get(
        f"{API_BASE}/api/v1/analytics/time-series",
        params={"days": days},
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def get_job_comparison(job_ids: str | None = None) -> dict:
    params = {}
    if job_ids:
        params["job_ids"] = job_ids
    resp = requests.get(
        f"{API_BASE}/api/v1/analytics/job-comparison",
        params=params,
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def get_candidate_pipeline_insights(job_id: str) -> dict:
    resp = requests.get(
        f"{API_BASE}/api/v1/analytics/pipeline/{job_id}",
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def get_recruiter_activity(limit: int = 20) -> dict:
    resp = requests.get(
        f"{API_BASE}/api/v1/analytics/activity",
        params={"limit": limit},
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


# ---------------------------------------------------------------------------
# AI Intelligence Layer
# ---------------------------------------------------------------------------

def get_ai_candidate_explanation(candidate_id: str) -> dict:
    resp = requests.post(
        f"{API_BASE}/api/v1/ai/candidates/{candidate_id}/explanation",
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def generate_ai_interview_questions(candidate_id: str) -> dict:
    resp = requests.post(
        f"{API_BASE}/api/v1/ai/candidates/{candidate_id}/interview-questions",
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def generate_ai_cover_letter(candidate_id: str, company_name: str = "Target Company", tone: str = "PROFESSIONAL") -> dict:
    resp = requests.post(
        f"{API_BASE}/api/v1/ai/candidates/{candidate_id}/cover-letter",
        json={"company_name": company_name, "tone": tone},
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def rewrite_ai_resume_bullet(
    resume_id: str,
    bullet: str,
    mode: str = "STAR",
    target_job_title: str | None = None,
    target_skills: list[str] | None = None,
) -> dict:
    payload = {
        "bullet": bullet,
        "mode": mode,
        "target_job_title": target_job_title,
        "target_skills": target_skills,
    }
    resp = requests.post(
        f"{API_BASE}/api/v1/ai/resumes/{resume_id}/rewrite-bullets",
        json=payload,
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)




# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------

def list_users() -> list[dict]:
    resp = requests.get(
        f"{API_BASE}/api/v1/admin/users",
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def create_user(payload: dict) -> dict:
    resp = requests.post(
        f"{API_BASE}/api/v1/admin/users",
        json=payload,
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def update_user(user_id: int, payload: dict) -> dict:
    resp = requests.patch(
        f"{API_BASE}/api/v1/admin/users/{user_id}",
        json=payload,
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def get_audit_logs(page: int = 1, event_type: str | None = None) -> dict:
    params = {"page": page}
    if event_type:
        params["event_type"] = event_type
    resp = requests.get(
        f"{API_BASE}/api/v1/admin/audit-logs",
        params=params,
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def list_model_versions() -> list[dict]:
    resp = requests.get(
        f"{API_BASE}/api/v1/admin/model-versions",
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def sync_model_versions() -> dict:
    resp = requests.post(
        f"{API_BASE}/api/v1/admin/model-versions/sync",
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def activate_model_version(version_id: int) -> dict:
    resp = requests.post(
        f"{API_BASE}/api/v1/admin/model-versions/{version_id}/activate",
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


# ---------------------------------------------------------------------------
# Auth extras
# ---------------------------------------------------------------------------

def logout() -> dict:
    resp = requests.post(
        f"{API_BASE}/api/v1/auth/logout",
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    try:
        return _handle_response(resp)
    except APIError:
        return {}  # Ignore errors on logout


def change_password(current_password: str, new_password: str) -> dict:
    resp = requests.post(
        f"{API_BASE}/api/v1/auth/change-password",
        json={"current_password": current_password, "new_password": new_password},
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


# ---------------------------------------------------------------------------
# Resume Builder (Phase 35)
# ---------------------------------------------------------------------------

def create_resume_draft(payload: dict) -> dict:
    resp = requests.post(
        f"{API_BASE}/api/v1/resume-builder",
        json=payload,
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def list_resume_drafts() -> list[dict]:
    resp = requests.get(
        f"{API_BASE}/api/v1/resume-builder",
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def get_resume_draft(draft_id: str) -> dict:
    resp = requests.get(
        f"{API_BASE}/api/v1/resume-builder/{draft_id}",
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def update_resume_draft(draft_id: str, payload: dict) -> dict:
    resp = requests.patch(
        f"{API_BASE}/api/v1/resume-builder/{draft_id}",
        json=payload,
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def calculate_resume_match(draft_id: str, payload: dict | None = None) -> dict:
    resp = requests.post(
        f"{API_BASE}/api/v1/resume-builder/{draft_id}/match",
        json=payload or {},
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def create_resume_version(draft_id: str, label: str | None = None) -> dict:
    params = {"label": label} if label else {}
    resp = requests.post(
        f"{API_BASE}/api/v1/resume-builder/{draft_id}/versions",
        params=params,
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def list_resume_versions(draft_id: str) -> list[dict]:
    resp = requests.get(
        f"{API_BASE}/api/v1/resume-builder/{draft_id}/versions",
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def restore_resume_version(draft_id: str, version_id: str) -> dict:
    resp = requests.post(
        f"{API_BASE}/api/v1/resume-builder/{draft_id}/restore/{version_id}",
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def ai_resume_builder_assist(draft_id: str, assist_type: str, context_text: str = "", target_job_id: str | None = None) -> dict:
    payload = {
        "assist_type": assist_type,
        "context_text": context_text,
        "target_job_id": target_job_id,
    }
    resp = requests.post(
        f"{API_BASE}/api/v1/resume-builder/{draft_id}/ai-assist",
        json=payload,
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


# ---------------------------------------------------------------------------
# Candidate Discovery & Hiring Intelligence (Phase 36)
# ---------------------------------------------------------------------------

def search_discovery_candidates(
    query: str | None = None,
    domain: str | None = None,
    min_required_cov: float | None = None,
    min_preferred_cov: float | None = None,
    min_semantic_sim: float | None = None,
    ood_status: str | None = None,
    review_status: str | None = None,
    job_id: str | None = None,
    page: int = 1,
    page_size: int = 10,
) -> dict:
    params = {"page": page, "page_size": page_size}
    if query:
        params["q"] = query
    if domain:
        params["domain"] = domain
    if min_required_cov is not None:
        params["min_required_cov"] = min_required_cov
    if min_preferred_cov is not None:
        params["min_preferred_cov"] = min_preferred_cov
    if min_semantic_sim is not None:
        params["min_semantic_sim"] = min_semantic_sim
    if ood_status:
        params["ood_status"] = ood_status
    if review_status:
        params["review_status"] = review_status
    if job_id:
        params["job_id"] = job_id

    resp = requests.get(
        f"{API_BASE}/api/v1/discovery/search",
        params=params,
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def get_job_discovery_candidates(job_id: str, page: int = 1, page_size: int = 10, sort_by: str = "screening_score", order: str = "desc") -> dict:
    params = {"page": page, "page_size": page_size, "sort_by": sort_by, "order": order}
    resp = requests.get(
        f"{API_BASE}/api/v1/discovery/jobs/{job_id}/candidates",
        params=params,
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def get_similar_candidates(candidate_id: str, limit: int = 5) -> dict:
    resp = requests.get(
        f"{API_BASE}/api/v1/discovery/candidates/{candidate_id}/similar",
        params={"limit": limit},
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def get_similar_jobs(job_id: str, limit: int = 5) -> dict:
    resp = requests.get(
        f"{API_BASE}/api/v1/discovery/jobs/{job_id}/similar",
        params={"limit": limit},
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)


def compare_candidates(candidate_ids: list[str], job_id: str | None = None) -> dict:
    payload = {"candidate_ids": candidate_ids, "job_id": job_id}
    resp = requests.post(
        f"{API_BASE}/api/v1/discovery/compare",
        json=payload,
        headers=_headers(),
        timeout=_TIMEOUT,
    )
    return _handle_response(resp)

