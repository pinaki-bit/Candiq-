"""
frontend/pages/results.py

Screening results page — ranked candidates per job, with match breakdown and review.
"""

from __future__ import annotations

import streamlit as st
import plotly.graph_objects as go
from services.api_client import (
    APIError, list_jobs, list_resumes, match_resume_to_job,
    get_job_results, update_review, bulk_update_reviews, match_all_resumes_to_job
)


_TIER_COLOR = {
    "Excellent": "#06D6A0",
    "Good": "#48CAE4",
    "Fair": "#FFD166",
    "Low Match": "#EF476F",
}

_REVIEW_OPTIONS = ["pending", "approved", "rejected", "on_hold"]


def render_results():
    st.title("🔍 Candidate Ranking & Review Dashboard")
    st.caption("AI-assisted ranking signals with transparent score breakdowns. Recruiter explicit decision required.")

    tab1, tab2 = st.tabs(["📊 Candidate Rankings", "⚡ Batch Screening & Match"])

    with tab1:
        _render_ranked_results()
    with tab2:
        _render_run_screening()


def _render_ranked_results():
    try:
        jobs = list_jobs()
    except APIError as e:
        st.error(f"Failed to load jobs: {e.detail}")
        return

    if not jobs:
        st.info("No active jobs found. Create a job first.")
        return

    col_j, col_f, col_s = st.columns([3, 2, 2])
    with col_j:
        job_options = {j["title"]: j["public_id"] for j in jobs}
        selected_title = st.selectbox("Select Job Position", options=list(job_options.keys()))
        job_id = job_options[selected_title]

    with col_f:
        review_filter = st.selectbox("Filter by Review Status", ["All"] + _REVIEW_OPTIONS)
        status_param = None if review_filter == "All" else review_filter

    with col_s:
        sort_by = st.selectbox("Sort Candidates By", ["Match Score (Default)", "Required Coverage", "Domain Match"])

    try:
        ranked = get_job_results(job_id, review_status=status_param)
    except APIError as e:
        st.error(f"Failed to load candidate results: {e.detail}")
        return

    if not ranked:
        st.info("No screening results for this job yet. Use 'Batch Screening & Match' to evaluate resumes.")
        if st.button("⚡ Match All Resumes to Job Now", type="primary"):
            with st.spinner("Matching all uploaded resumes against job requirements…"):
                try:
                    res_list = match_all_resumes_to_job(job_id)
                    st.success(f"Matched {len(res_list)} candidate resumes!")
                    st.rerun()
                except APIError as exc:
                    st.error(f"Batch match failed: {exc.detail}")
        return

    # Client-side sorting override if selected
    if sort_by == "Required Coverage":
        ranked.sort(key=lambda r: -(r.get("required_coverage") or 0.0))
    elif sort_by == "Domain Match":
        ranked.sort(key=lambda r: (r.get("predicted_domain") or ""))

    st.caption(f"**{len(ranked)} candidates** screened for position **{selected_title}**")

    # Quick Summary Metrics
    c_tot, c_short, c_pend, c_rej = st.columns(4)
    with c_tot:
        st.metric("Total Candidates", len(ranked))
    with c_short:
        st.metric("Shortlisted (Approved)", sum(1 for r in ranked if r.get("review_status") == "approved"))
    with c_pend:
        st.metric("Pending Review", sum(1 for r in ranked if r.get("review_status") == "pending"))
    with c_rej:
        st.metric("Rejected", sum(1 for r in ranked if r.get("review_status") == "rejected"))

    # Horizontal Score Distribution Bar Chart
    names = [f"#{r['rank']} candidate (`{r.get('public_id', '')[:6]}`)" for r in ranked]
    scores = [r["relevance_score"] for r in ranked]
    colors = [_TIER_COLOR.get(r["tier"], "#888") for r in ranked]

    fig = go.Figure(go.Bar(
        x=scores, y=names, orientation="h",
        marker_color=colors,
        text=[f"{s:.1f}%" for s in scores],
        textposition="outside",
    ))
    fig.update_layout(
        height=max(180, len(ranked) * 35),
        margin=dict(l=20, r=60, t=10, b=10),
        xaxis=dict(range=[0, 105], title="Composite Match Score (%)"),
        yaxis=dict(autorange="reversed"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    # Bulk Action Section
    st.subheader("⚡ Bulk Recruiter Actions")
    col_b1, col_b2 = st.columns([4, 2])
    with col_b1:
        selected_cand_ids = st.multiselect(
            "Select Candidates for Bulk Decision",
            options=[r["public_id"] for r in ranked],
            format_func=lambda x: f"Candidate `{x[:8]}`",
        )
    with col_b2:
        bulk_action = st.selectbox("Bulk Decision", ["approved", "rejected", "on_hold", "pending"])
        if st.button("Apply Bulk Decision", type="secondary", disabled=not selected_cand_ids):
            try:
                bulk_update_reviews(selected_cand_ids, bulk_action, notes=f"Bulk updated to '{bulk_action}'")
                st.success(f"Updated {len(selected_cand_ids)} candidates to '{bulk_action}'.")
                st.rerun()
            except APIError as e:
                st.error(f"Bulk update failed: {e.detail}")

    st.divider()

    # Detailed Candidate Cards
    st.subheader("📋 Candidate Ranking & Evidence Cards")
    for r in ranked:
        tier = r.get("tier", "Unknown")
        color = _TIER_COLOR.get(tier, "#888")
        status_badge = r.get("review_status", "pending").upper()

        with st.expander(
            f"**#{r['rank']}** — Match: **{r['relevance_score']:.1f}%** [{tier}] | Status: `{status_badge}` | Candidate `{r.get('public_id', '')[:8]}`",
            expanded=(r["rank"] <= 2),
        ):
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Required Coverage", f"{r.get('required_coverage', 0):.1f}%")
            with c2:
                st.metric("Preferred Coverage", f"{r.get('preferred_coverage', 0):.1f}%")
            with c3:
                st.metric("Predicted Domain", r.get("predicted_domain") or "Unclassified")
            with c4:
                st.metric("Confidence", (r.get("prediction_confidence") or "N/A").capitalize())

            # Skill Visualization Chips
            bd = r.get("score_breakdown") or {}
            matched_req = bd.get("matched_required_skills") or bd.get("matched_required") or []
            missing_req = bd.get("missing_required_skills") or bd.get("missing_required") or []

            st.markdown("#### Skill Analysis")
            col_sk1, col_sk2 = st.columns(2)
            with col_sk1:
                st.markdown("**Matched Required Skills:**")
                if matched_req:
                    st.markdown(" ".join(f"`✅ {s}`" for s in matched_req))
                else:
                    st.write("None matched")
            with col_sk2:
                st.markdown("**Missing Required Skills:**")
                if missing_req:
                    st.markdown(" ".join(f"`❌ {s}`" for s in missing_req))
                else:
                    st.write("None missing")

            # Score Breakdown / Transparent Formula
            with st.expander("📊 Transparent Score Breakdown & Evidence", expanded=False):
                if isinstance(bd, dict):
                    st.json(bd)
                else:
                    st.write("Breakdown not available.")

            # Individual Recruiter Review Action
            st.markdown("---")
            col_rev, col_note, col_btn = st.columns([2, 3, 1])
            with col_rev:
                new_status = st.selectbox(
                    "Set Recruiter Decision",
                    _REVIEW_OPTIONS,
                    index=_REVIEW_OPTIONS.index(r.get("review_status", "pending")),
                    key=f"rev_status_{r['public_id']}",
                )
            with col_note:
                note = st.text_input(
                    "Recruiter Note",
                    key=f"rev_note_{r['public_id']}",
                    placeholder="Enter persistent recruiter note…",
                )
            with col_btn:
                st.write("") # spacing
                if st.button("💾 Save", key=f"save_rev_{r['public_id']}", use_container_width=True):
                    try:
                        update_review(r["public_id"], new_status, note or None)
                        st.success("Saved.")
                        st.rerun()
                    except APIError as e:
                        st.error(f"Failed: {e.detail}")


def _render_run_screening():
    st.subheader("Match Resumes to Job")

    try:
        jobs = list_jobs()
        resumes = list_resumes(status_filter=None)
    except APIError as e:
        st.error(f"Failed to load data: {e.detail}")
        return

    if not jobs:
        st.info("No active jobs. Create a job first.")
        return

    if not resumes:
        st.info("No resumes uploaded yet. Upload resumes first.")
        return

    job_options = {j["title"]: j["public_id"] for j in jobs}
    selected_job_title = st.selectbox("Select Target Job Position", list(job_options.keys()))
    selected_job_id = job_options[selected_job_title]

    col_single, col_all = st.columns(2)

    with col_single:
        st.markdown("#### Single Resume Match")
        resume_options = {
            f"Resume {r['public_id'][:8]}… — {r['predicted_domain'] or 'Unclassified'} [{r['status']}]": r["public_id"]
            for r in resumes
        }
        selected_resume_label = st.selectbox("Select Resume", list(resume_options.keys()))

        if st.button("▶ Match Selected Resume", type="primary", use_container_width=True):
            resume_id = resume_options[selected_resume_label]
            with st.spinner("Computing match…"):
                try:
                    res = match_resume_to_job(selected_job_id, resume_id)
                    st.success(f"Match complete — Score: **{res['relevance_score']:.1f}%**")
                    st.rerun()
                except APIError as e:
                    st.error(f"Matching failed: {e.detail}")

    with col_all:
        st.markdown("#### Batch Match All Resumes")
        st.caption("Screen all available processed resumes against the selected job position in one click.")
        if st.button("⚡ Match All Resumes to Job", type="secondary", use_container_width=True):
            with st.spinner("Running batch match for all candidates…"):
                try:
                    res_list = match_all_resumes_to_job(selected_job_id)
                    st.success(f"Matched {len(res_list)} resumes to '{selected_job_title}'!")
                    st.rerun()
                except APIError as e:
                    st.error(f"Batch matching failed: {e.detail}")
