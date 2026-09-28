"""
backend/tests/test_tenant_security.py

Unit test suite for Phase 16: Security Hardening & Multi-Tenant Isolation.
"""

import pytest
from fastapi import HTTPException
from app.core.sanitizer import sanitize_html, sanitize_filepath, verify_tenant_access
from app.api.dependencies import get_current_tenant_id
from app.models.user import User


def test_sanitize_html_xss_protection():
    raw_xss = "<script>alert('xss')</script><b>John Doe</b><img src=x onerror=alert(1)>"
    cleaned = sanitize_html(raw_xss)
    assert "<script>" not in cleaned
    assert "alert" not in cleaned
    assert "onerror" not in cleaned
    assert "John Doe" in cleaned


def test_sanitize_filepath_path_traversal():
    bad_paths = [
        "../../etc/passwd",
        "..\\..\\Windows\\System32\\cmd.exe",
        "resume\x00.pdf",
        "../../../secret.txt",
    ]
    for path in bad_paths:
        safe_name = sanitize_filepath(path)
        assert ".." not in safe_name
        assert "/" not in safe_name
        assert "\\" not in safe_name
        assert "\x00" not in safe_name


def test_verify_tenant_access_boundary():
    # Matching tenant -> should pass without exception
    verify_tenant_access("acme_corp", "acme_corp")

    # Mismatched tenant -> must raise HTTP 403
    with pytest.raises(HTTPException) as exc_info:
        verify_tenant_access("acme_corp", "stark_industries")
    assert exc_info.value.status_code == 403
    assert "Resource belongs to a different tenant" in exc_info.value.detail


def test_get_current_tenant_id_dependency():
    user = User(email="test@tenant.com", role="hr", tenant_id="tenant_alpha")
    tenant_id = get_current_tenant_id(user)
    assert tenant_id == "tenant_alpha"


def test_api_security_headers_present(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"
    assert response.headers.get("Content-Security-Policy") == "default-src 'self'"
