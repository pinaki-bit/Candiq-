"""
backend/tests/test_ats_adapters.py

Unit test suite for Phase 14: Enterprise ATS Adapter Architecture & API Endpoints.
"""

import pytest
from app.schemas.ats import ATSProviderEnum, ATSCredentials
from app.services.ats_adapters import (
    ATSFactory,
    MockATSAdapter,
    GreenhouseAdapter,
    LeverAdapter,
    WorkdayAdapter,
)


def test_ats_factory_instantiation():
    mock_adapter = ATSFactory.get_adapter("mock")
    assert isinstance(mock_adapter, MockATSAdapter)

    gh_adapter = ATSFactory.get_adapter("greenhouse")
    assert isinstance(gh_adapter, GreenhouseAdapter)

    lever_adapter = ATSFactory.get_adapter("lever")
    assert isinstance(lever_adapter, LeverAdapter)

    wd_adapter = ATSFactory.get_adapter("workday")
    assert isinstance(wd_adapter, WorkdayAdapter)


def test_mock_ats_adapter_flow():
    adapter = ATSFactory.get_adapter("mock")
    conn_res = adapter.test_connection()
    assert conn_res.success is True
    assert conn_res.provider == "mock"

    sync_res = adapter.sync_jobs()
    assert sync_res.success is True
    assert sync_res.synced_jobs_count > 0

    export_res = adapter.export_candidate(
        resume_data={"filename": "test_resume.pdf", "candidate_id": 1},
        notes="High match score candidate",
    )
    assert export_res.success is True
    assert export_res.ats_candidate_id.startswith("MOCK-CAND-")

    status_res = adapter.get_candidate_status(export_res.ats_candidate_id)
    assert status_res["status"] == "ACTIVE"


def test_greenhouse_adapter_flow():
    # Unauthenticated test
    adapter_unauth = GreenhouseAdapter(ATSCredentials(api_key=None))
    conn_unauth = adapter_unauth.test_connection()
    assert conn_unauth.success is False

    # Authenticated test
    adapter_auth = GreenhouseAdapter(ATSCredentials(api_key="gh_test_key_12345"))
    conn_auth = adapter_auth.test_connection()
    assert conn_auth.success is True

    sync_res = adapter_auth.sync_jobs()
    assert sync_res.success is True
    assert len(sync_res.jobs) > 0

    export_res = adapter_auth.export_candidate({"filename": "john.pdf"})
    assert export_res.success is True
    assert export_res.ats_candidate_id.startswith("GH-CAND-")


def test_lever_adapter_flow():
    adapter = LeverAdapter(ATSCredentials(api_key="lever_test_key_99"))
    assert adapter.test_connection().success is True
    assert adapter.sync_jobs().success is True
    export_res = adapter.export_candidate({"filename": "jane.pdf"})
    assert export_res.ats_candidate_id.startswith("LEV-OPP-")


def test_workday_adapter_flow():
    adapter = WorkdayAdapter(ATSCredentials(client_id="wd_client", client_secret="wd_secret", tenant_id="acme_corp"))
    assert adapter.test_connection().success is True
    assert adapter.sync_jobs().success is True
    export_res = adapter.export_candidate({"filename": "alex.pdf"})
    assert export_res.ats_candidate_id.startswith("WD-CAND-")


# ── REST API Endpoint Integration Tests ────────────────────────────────────

def test_api_get_ats_providers(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = client.get("/api/v1/ats/providers", headers=headers)
    assert response.status_code == 200
    providers = response.json()
    assert "mock" in providers
    assert "greenhouse" in providers
    assert "lever" in providers
    assert "workday" in providers


def test_api_test_ats_connection(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {
        "provider": "mock",
        "credentials": {"environment": "sandbox"},
    }
    response = client.post("/api/v1/ats/test-connection", json=payload, headers=headers)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["provider"] == "mock"


def test_api_sync_jobs_endpoint(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {
        "provider": "mock",
        "auto_create_local": True,
    }
    response = client.post("/api/v1/ats/sync-jobs", json=payload, headers=headers)
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["synced_jobs_count"] > 0
