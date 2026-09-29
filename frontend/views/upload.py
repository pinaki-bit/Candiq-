"""
frontend/pages/upload.py

Secure resume upload page.
"""

from __future__ import annotations

import streamlit as st
from services.api_client import APIError, upload_resume, upload_batch_resumes, list_jobs
from components.resume_advisor import render_resume_advisor


_CONFIDENCE_COLOR = {
    "high": "🟢",
    "medium": "🟡",
    "low": "🔴",
    "unavailable": "⚫",
}

_STATUS_LABEL = {
    "completed": "✅ Completed",
    "needs_review": "⚠️ Needs Review",
    "failed": "❌ Failed",
    "uploaded": "📥 Uploaded",
    "processing": "⏳ Processing",
}


def render_upload():
    st.title("📤 Upload Resumes")
    st.caption(
        "Upload one or multiple text-based PDF resumes. "
        "The system extracts skills, classifies domain, evaluates OOD status, and links candidate records."
    )

    user = st.session_state.get("user") or {}
    role = user.get("role", "readonly")
    if role == "readonly":
        st.warning("Read-only users cannot upload resumes.")
        return

    # Job selection for auto-screening
    try:
        active_jobs = list_jobs(active_only=True)
    except Exception:
        active_jobs = []

    job_options = {"(None — Upload without auto-matching)": None}
    for j in active_jobs:
        job_options[f"💼 {j['title']} ({j.get('domain', 'General')})"] = j["public_id"]

    with st.form("upload_form", clear_on_submit=True):
        uploaded_files = st.file_uploader(
            "Select PDF Resumes (single or multiple)",
            type=["pdf"],
            accept_multiple_files=True,
            help="Maximum file size: 10 MB per file. Text-based PDFs only.",
        )
        selected_job_label = st.selectbox(
            "Auto-match uploaded resumes to job (optional)",
            options=list(job_options.keys()),
        )
        candidate_ref = st.text_input(
            "Candidate Reference Code (optional for single uploads)",
            placeholder="e.g. CAND-2024-001",
            help="Link single resume upload to an existing or new candidate reference code.",
        )
        submitted = st.form_submit_button("Upload & Process Batch", type="primary", use_container_width=True)

    if submitted:
        if not uploaded_files:
            st.error("Please select at least one PDF file to upload.")
            return

        target_job_id = job_options[selected_job_label]

        if len(uploaded_files) == 1:
            f = uploaded_files[0]
            with st.spinner(f"Processing '{f.name}'…"):
                try:
                    result = upload_resume(
                        file_bytes=f.read(),
                        filename=f.name,
                        candidate_ref=candidate_ref.strip() or None,
                    )
                    st.success(f"Processed single resume '{f.name}'")
                    _display_result(result)
                except APIError as e:
                    st.error(f"Upload failed: {e.detail}")
        else:
            file_tuples = [(f.name, f.read()) for f in uploaded_files]
            with st.spinner(f"Processing batch of {len(file_tuples)} resumes…"):
                try:
                    results = upload_batch_resumes(file_tuples, job_id=target_job_id)
                    st.success(f"✅ Batch processing complete: {len(results)} resumes processed.")
                    for res in results:
                        st.markdown(
                            f"- **{res.get('original_filename')}**: Domain = `{res.get('predicted_domain') or 'Unknown'}`, "
                            f"Status = `{res.get('status')}`"
                        )
                    if target_job_id:
                        st.info("Resumes auto-matched against selected job. View complete rankings in 'Screening Results'.")
                except APIError as e:
                    st.error(f"Batch upload failed: {e.detail}")


def _display_result(result: dict):
    status = result.get("status", "unknown")
    icon = _STATUS_LABEL.get(status, status)
    conf = result.get("prediction_confidence", "unavailable")
    conf_icon = _CONFIDENCE_COLOR.get(conf, "⚫")

    st.success(f"**Processing complete** — {icon}")
    st.divider()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Status", icon)
    with c2:
        st.metric("Predicted Domain", result.get("predicted_domain") or "Unknown")
    with c3:
        st.metric("Confidence", f"{conf_icon} {conf.capitalize()}")
    with c4:
        st.metric("Text Extracted", f"{result.get('text_char_count', 0):,} chars")

    # Skills
    skills = result.get("extracted_skills", [])
    if skills:
        st.subheader(f"🔧 {len(skills)} Skills Extracted")
        # Group by domain
        by_domain: dict[str, list] = {}
        for s in skills:
            d = s.get("domain") or "Other"
            by_domain.setdefault(d, []).append(s)
        for domain, domain_skills in by_domain.items():
            with st.expander(f"**{domain}** ({len(domain_skills)} skills)"):
                for s in sorted(domain_skills, key=lambda x: -x.get("frequency", 1)):
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        st.write(f"**{s['canonical_name']}**")
                        if s.get("evidence_snippet"):
                            st.caption(f"…{s['evidence_snippet']}…")
                    with col_b:
                        st.caption(f"×{s.get('frequency', 1)}")
    else:
        st.info("No skills were extracted from this resume.")

    if status == "needs_review":
        st.warning(
            "⚠️ Classification confidence is low. "
            "This resume is flagged for human review before any screening decision."
        )
    if result.get("error_message"):
        st.error(f"Processing note: {result['error_message']}")

    st.divider()
    # Resume Optimization & Confidence Advisor
    render_resume_advisor(
        confidence=conf,
        predicted_domain=result.get("predicted_domain"),
        char_count=result.get("text_char_count", 0),
        skill_count=len(skills),
    )
    st.divider()

    # Actions
    col_l, col_r = st.columns(2)
    with col_l:
        if st.button("🔍 Screen Against a Job", use_container_width=True, type="primary"):
            st.session_state["selected_resume_id"] = result["public_id"]
            st.session_state["page"] = "results"
            st.rerun()
    with col_r:
        if st.button("📤 Upload Another", use_container_width=True):
            st.rerun()
