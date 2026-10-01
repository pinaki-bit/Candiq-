"""
backend/app/core/sanitizer.py

Phase 16 & 34: Security Hardening, Input Sanitization & Prompt Injection Protection Utilities.
Provides HTML XSS sanitization, path-traversal prevention, tenant boundary verification,
and LLM prompt injection defense.
"""

from __future__ import annotations

import html
import logging
import os
import re
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

# Regex patterns for HTML/JS sanitization
SCRIPT_PATTERN = re.compile(r"<script.*?>.*?</script>", re.IGNORECASE | re.DOTALL)
HTML_TAG_PATTERN = re.compile(r"<[^>]*>")
UNSAFE_PROTOCOLS = re.compile(r"javascript:|data:|vbscript:", re.IGNORECASE)

# Prompt Injection Attack Patterns
PROMPT_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(?:all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"system\s+prompt\s+override", re.IGNORECASE),
    re.compile(r"reveal\s+(?:the\s+)?system\s+prompt", re.IGNORECASE),
    re.compile(r"print\s+(?:the\s+)?system\s+prompt", re.IGNORECASE),
    re.compile(r"bypass\s+safety\s+filters", re.IGNORECASE),
    re.compile(r"disregard\s+(?:the\s+)?above", re.IGNORECASE),
]

# Basic PII Redaction Patterns
SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CREDIT_CARD_PATTERN = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
PHONE_PATTERN = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")


def sanitize_html(text: str | None) -> str:
    """
    Sanitize text input by removing script tags, dangerous HTML tags, and HTML-encoding special characters.
    Prevents Stored & Reflected XSS attacks.
    """
    if not text:
        return ""

    cleaned = SCRIPT_PATTERN.sub("", text)
    cleaned = HTML_TAG_PATTERN.sub("", cleaned)
    cleaned = UNSAFE_PROTOCOLS.sub("", cleaned)
    return html.escape(cleaned.strip())


def sanitize_filepath(filename: str | None) -> str:
    """
    Sanitize filename by stripping directory separators, null bytes, and path traversal sequences.
    Prevents Arbitrary File Overwrite & Path Traversal attacks.
    """
    if not filename:
        return "unnamed_file"

    cleaned = filename.replace("\x00", "")
    cleaned = os.path.basename(cleaned)
    cleaned = cleaned.replace("..", "")
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


def sanitize_prompt_input(text: str | None, max_length: int = 4000) -> str:
    """
    Sanitizes untrusted text before inserting into LLM prompts.
    Strips known prompt-injection commands and truncates excessive input.
    """
    if not text:
        return ""

    cleaned = str(text)

    # Neutralize prompt injection command phrases
    for pattern in PROMPT_INJECTION_PATTERNS:
        cleaned = pattern.sub("[REDACTED_COMMAND]", cleaned)

    # Truncate to maximum allowed input length
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length] + " [TRUNCATED_FOR_LENGTH]"

    return cleaned.strip()


def format_untrusted_data_boundary(text: str | None, label: str = "UNTRUSTED_CANDIDATE_DATA", max_length: int = 4000) -> str:
    """
    Wraps untrusted candidate/job text in strict delimiters and security boundary instructions.
    """
    sanitized = sanitize_prompt_input(text, max_length=max_length)
    return (
        f"<<<DATA_BOUNDARY_START: {label}>>>\n"
        f"{sanitized}\n"
        f"<<<DATA_BOUNDARY_END: {label}>>>"
    )


def sanitize_pii(text: str | None) -> str:
    """
    Redacts sensitive PII (SSN, credit card, phone numbers) before passing to LLM providers.
    """
    if not text:
        return ""

    cleaned = str(text)
    cleaned = SSN_PATTERN.sub("[REDACTED_SSN]", cleaned)
    cleaned = CREDIT_CARD_PATTERN.sub("[REDACTED_CARD]", cleaned)
    cleaned = PHONE_PATTERN.sub("[REDACTED_PHONE]", cleaned)
    return cleaned
