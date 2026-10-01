"""
frontend/views/system_health.py

Streamlit System Health, Observability & Performance Dashboard.
Displays real runtime state from API readiness and metrics probes.
Does NOT display secrets or fake graphs.
"""

from __future__ import annotations

import streamlit as st
from frontend.services import api_client


def render_system_health_view() -> None:
    st.title("🖥️ System Health & Observability")
    st.markdown("Real-time system health checks, dependency status, and runtime latency metrics.")

    # Fetch real status from API
    try:
        readiness = api_client.get_readiness_probe()
    except Exception as exc:
        st.error(f"Unable to reach API health endpoint: {exc}")
        readiness = None

    try:
        metrics = api_client.get_runtime_metrics()
    except Exception as exc:
        metrics = None

    st.subheader("System Readiness & Dependency Probes")

    if readiness:
        overall_status = readiness.get("status", "unknown")
        checks = readiness.get("checks", {})

        if overall_status == "ready":
            st.success("🟢 System Status: **READY**")
        else:
            st.error("🔴 System Status: **DEGRADED / NOT READY**")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            db_st = checks.get("database", "unknown")
            st.metric("Database", db_st.upper(), delta="Connected" if db_st == "ok" else "Error")

        with col2:
            ml_st = checks.get("ml_model", "unknown")
            st.metric("ML Classifier", ml_st.upper(), delta="Loaded" if ml_st == "ok" else "Error")

        with col3:
            emb_st = checks.get("embedding", "unknown")
            st.metric("Embeddings", emb_st.upper(), delta="Active" if emb_st == "ok" else "Degraded")

        with col4:
            stg_st = checks.get("storage", "unknown")
            st.metric("File Storage", stg_st.upper(), delta="Writable" if stg_st == "ok" else "Error")
    else:
        st.warning("No readiness probe response received.")

    st.markdown("---")
    st.subheader("Real Runtime Latency & Performance Metrics")

    if not metrics or metrics.get("status") == "No runtime data available":
        st.info("ℹ️ No runtime data available")
    else:
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)

        with m_col1:
            st.metric("Total API Requests", metrics.get("total_requests", 0))

        with m_col2:
            st.metric("Avg API Latency", f"{metrics.get('avg_api_latency_ms', 0.0)} ms")

        with m_col3:
            st.metric("Avg DB Query", f"{metrics.get('avg_db_latency_ms', 0.0)} ms")

        with m_col4:
            st.metric("Avg ML Inference", f"{metrics.get('avg_ml_latency_ms', 0.0)} ms")

        with st.expander("Detailed Runtime Breakdown"):
            st.json(metrics)
