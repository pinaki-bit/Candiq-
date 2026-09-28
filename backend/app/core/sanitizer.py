"""
backend/app/core/sanitizer.py

Phase 16: Security Hardening & Input Sanitization Utilities.
Provides HTML XSS sanitization, path-traversal prevention, and tenant boundary verification.
"""

from __future__ import annotations

import re
import os
import html
import logging
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

# Regex patterns for HTML/JS sanitization
SCRIPT_PATTERN = re.compile(r"<script.*?>.*?</script>", re.IGNORECASE | re.DOTALL)
HTML_TAG_PATTERN = re.compile(r"<[^>]*>")
UNSAFE_PROTOCOLS = re.compile(r"javascript:|data:|vbscript:", re.IGNORECASE)


def sanitize_html(text: str | None) -> str:
    """
    Sanitize text input by removing script tags, dangerous HTML tags, and HTML-encoding special characters.
    Prevents Stored & Reflected XSS attacks.
    """
    if not text:
        return ""

    # Remove script tags and inner contents
    cleaned = SCRIPT_PATTERN.sub("", text)
    # Remove all HTML tags
    cleaned = HTML_TAG_PATTERN.sub("", cleaned)
    # Remove inline javascript protocols
    cleaned = UNSAFE_PROTOCOLS.sub("", cleaned)
    # Escape HTML special characters
    return html.escape(cleaned.strip())


def sanitize_filepath(filename: str | None) -> str:
    """
    Sanitize filename by stripping directory separators, null bytes, and path traversal sequences ('../', '..\\').
    Prevents Arbitrary File Overwrite & Path Traversal attacks.
    """
    if not filename:
        return "unnamed_file"

    # Remove null bytes
    cleaned = filename.replace("\x00", "")
    # Extract basename only (removes any leading paths)
    cleaned = os.path.basename(cleaned)
    # Strip any remaining '..'
    cleaned = cleaned.replace("..", "")
    # Keep only safe alphanumeric characters, dots, dashes, and underscores
    cleaned = re.sub(r"[^\w\.-]", "_", cleaned)

    return cleaned or "sanitized_file"


def verify_tenant_access(resource_tenant_id: str, current_tenant_id: str) -> None:
    """
    Enforces multi-tenant data boundary isolation.
    Raises HTTP 403 Forbidden if current user attempts to access a resource from another tenant.
    """
    if resource_tenant_id != current_tenant_id:
        logger.warning(
            f"Multi-tenant access violation! Current tenant '{current_tenant_id}' "
            f"attempted unauthorized access to resource belonging to tenant '{resource_tenant_id}'."
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Resource belongs to a different tenant organization.",
        )
