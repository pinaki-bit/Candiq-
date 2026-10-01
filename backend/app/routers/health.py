"""
backend/app/routers/health.py

Production Health, Readiness, Liveness, and Observability Metrics Endpoints.

GET /health          — Liveness summary probe
GET /health/live     — Lightweight Kubernetes liveness probe (200 OK)
GET /health/ready    — Comprehensive readiness probe (DB, ML model, Embedding, Storage)
GET /health/metrics  — Real-time aggregate runtime metrics (no synthetic data)
"""

from __future__ import annotations

import os
import logging
from typing import Dict, Any

from fastapi import APIRouter, Response, status

from app.config import get_settings
from app.database import check_db_connection
from app.core.metrics import metrics_collector
from app.services.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["Health & Reliability Probes"])


@router.get(
    "",
    summary="Liveness summary probe",
    response_description="Basic application status",
)
def health_check() -> Dict[str, Any]:
    """Returns application liveness status summary."""
    settings = get_settings()
    return {
        "status": "ok",
        "version": settings.app_version,
        "environment": settings.app_env,
    }


@router.get(
    "/live",
    summary="Liveness probe",
    response_description="Kubernetes/Load-Balancer Liveness status",
)
def liveness_probe() -> Dict[str, str]:
    """Lightweight liveness probe. Always returns HTTP 200 if process is up."""
    return {"status": "alive"}


@router.get(
    "/db",
    summary="Database connection health check",
    response_description="Database status check",
)
def db_health_check() -> Dict[str, str]:
    """Check database connectivity for legacy health tests."""
    db_connected = check_db_connection()
    return {
        "status": "ok" if db_connected else "error",
        "database": "connected" if db_connected else "disconnected",
    }


@router.get(
    "/ready",
    summary="Readiness probe",
    response_description="Readiness probe verifying DB, ML model, Embeddings, and Storage",
)
def readiness_probe(response: Response) -> Dict[str, Any]:
    """
    Evaluates required system dependencies.
    Fails with HTTP 503 if any required component (DB, ML model, Storage) is unavailable.
    """
    settings = get_settings()
    checks: Dict[str, str] = {}
    is_ready = True

    # 1. Database Check
    db_connected = check_db_connection()
    checks["database"] = "ok" if db_connected else "unreachable"
    if not db_connected:
        is_ready = False

    # 2. ML Model Check
    model_path = settings.active_model_path
    model_ok = os.path.exists(model_path) and os.path.isfile(model_path)
    checks["ml_model"] = "ok" if model_ok else "missing"
    if not model_ok:
        is_ready = False

    # 3. Embedding Provider Check
    try:
        embedder = get_embedding_service()
        checks["embedding"] = "ok" if embedder is not None else "unavailable"
    except Exception as exc:
        logger.warning("Embedding service health check failed: %s", exc)
        checks["embedding"] = "degraded"

    # 4. Storage Directory Check
    upload_dir = settings.upload_dir
    os.makedirs(upload_dir, exist_ok=True)
    storage_ok = os.access(upload_dir, os.W_OK)
    checks["storage"] = "ok" if storage_ok else "unwritable"
    if not storage_ok:
        is_ready = False

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {
            "status": "not_ready",
            "checks": checks,
        }

    return {
        "status": "ready",
        "checks": checks,
    }


@router.get(
    "/metrics",
    summary="Runtime performance metrics",
    response_description="Real aggregate performance and latency measurements",
)
def runtime_metrics() -> Dict[str, Any]:
    """Returns actual runtime performance measurements collected by the application."""
    return metrics_collector.get_summary()
