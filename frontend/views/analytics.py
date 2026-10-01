"""
frontend/views/analytics.py

Advanced Recruiter Analytics & Hiring Insights View.
Render real analytics metrics from persisted database records only.
"""

from __future__ import annotations

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

from services.api_client import (
    APIError,
    get_summary,
    get_analytics_funnel,
    get_job_analytics,
    get_skill_intelligence,
    get_score_distribution,
    get_time_series_analytics,
    get_job_comparison,
    get_candidate_pipeline_insights,
    get_recruiter_activity,
    get_skill_heatmap,
    get_domain_distribution,
    list_jobs,
)


def render_analytics():
    st.title("📈 Advanced Recruiter Analytics & Hiring Insights")
    st.caption(
        "Real-time analytics computed directly from persisted database records. "
        "No simulated or synthetic metrics."
    )

    tab_overview, tab_skills, tab_trends, tab_comparison, tab_pipeline = st.tabs([
        "📊 Summary & Funnel",
        "💡 Skill Intelligence",
        "📈 Time-Series Trends",
        "🔀 Job Comparison",
        "🔎 Pipeline & Activity",
    ])

    with tab_overview:
        _render_overview_and_funnel()

    with tab_skills:
        _render_skill_intelligence()

    with tab_trends:
        _render_time_series_trends()

    with tab_comparison:
        _render_job_comparison()

    with tab_pipeline:
        _render_pipeline_insights()


def _render_overview_and_funnel():
    st.subheader("High-Level Recruiter Overview")

    try:
        summary = get_summary()
    except APIError as e:
        st.error(f"Could not load summary metrics: {e.detail}")
        return

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric("Total Candidates", summary.get("total_candidates", 0))
    with c2:
        st.metric("Total Screenings", summary.get("total_screenings", 0))
    with c3:
        st.metric("Pending Reviews", summary.get("pending_reviews", 0))
    with c4:
        st.metric("Shortlisted / Approved", summary.get("approved_candidates", 0))
    with c5:
        st.metric("Rejected Candidates", summary.get("rejected_candidates", 0))

    st.caption(summary.get("explainability", ""))
    st.divider()

    st.subheader("Screening Funnel Progression")
    try:
        funnel_data = get_analytics_funnel()
        stages = funnel_data.get("stages", [])
    except APIError as e:
        st.warning(f"Could not load screening funnel: {e.detail}")
        stages = []

    if stages:
        stage_names = [s["stage"] for s in stages]
        stage_counts = [s["count"] for s in stages]
        stage_pcts = [s["percentage"] for s in stages]

        fig = go.Figure(go.Bar(
            x=stage_counts,
            y=stage_names,
            orientation="h",
            marker_color=["#6C63FF", "#48CAE4", "#06D6A0", "#FFD166", "#00B4D8", "#FFA500", "#EF476F"],
            text=[f"{c} ({p:.1f}%)" for c, p in zip(stage_counts, stage_pcts)],
            textposition="inside",
        ))
        fig.update_layout(
            yaxis=dict(autorange="reversed"),
            xaxis_title="Candidate Count",
            height=340,
            margin=dict(l=20, r=20, t=20, b=20),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Relevance Score & Coverage Distribution")

    try:
        hist_data = get_score_distribution()
    except APIError as e:
        st.warning(f"Could not load score distribution: {e.detail}")
        return

    buckets = hist_data.get("buckets", [])
    if buckets:
        ranges = [b["range"] for b in buckets]
        counts = [b["count"] for b in buckets]
        pcts = [b["percentage"] for b in buckets]

        fig2 = go.Figure(go.Bar(
            x=ranges,
            y=counts,
            marker_color="#6C63FF",
            text=[f"{p:.0f}%" for p in pcts],
            textposition="outside",
        ))
        fig2.update_layout(
            xaxis_title="Relevance Score Bucket (%)",
            yaxis_title="Candidates",
            height=280,
            margin=dict(t=20, b=20),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig2, use_container_width=True)


def _render_skill_intelligence():
    st.subheader("Skill Intelligence & Gap Analysis")
    st.caption("Extracted from real candidate-job screening results.")

    try:
        skills_data = get_skill_intelligence()
    except APIError as e:
        st.error(f"Could not load skill intelligence: {e.detail}")
        return

    top_matched = skills_data.get("top_matched_required", [])
    top_missing = skills_data.get("top_missing_required", [])

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### ✅ Top Matched Required Skills")
        if top_matched:
            for item in top_matched[:8]:
                st.write(f"**{item['skill']}**: {item['count']} candidates ({item['percentage']}%)")
        else:
            st.info("No skill matches recorded yet.")

    with col2:
        st.markdown("#### ❌ Top Missing Required Skills")
        if top_missing:
            for item in top_missing[:8]:
                st.write(f"**{item['skill']}**: Missing in {item['count']} matches ({item['percentage']}%)")
        else:
            st.info("No skill gaps detected.")

    st.caption(skills_data.get("explainability", ""))

    st.divider()
    st.markdown("#### 🔥 Skill Frequency Heatmap across Domains")
    try:
        heatmap_data = get_skill_heatmap(top_n=10)
        domains_data = heatmap_data.get("domains", {})
        if domains_data:
            all_skills = sorted({s["skill"] for skills in domains_data.values() for s in skills})
            domains = sorted(domains_data.keys())
            matrix = []
            for domain in domains:
                skill_map = {s["skill"]: s["frequency"] for s in domains_data.get(domain, [])}
                matrix.append([skill_map.get(skill, 0) for skill in all_skills])

            if matrix and all_skills:
                fig = go.Figure(go.Heatmap(
                    z=matrix,
                    x=all_skills,
                    y=domains,
                    colorscale="Viridis",
                    showscale=True,
                ))
                fig.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=80))
                st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.warning(f"Heatmap unavailable: {e}")


def _render_time_series_trends():
    st.subheader("Time-Series Processing & Review Trends")

    days_option = st.selectbox(
        "Select Time Period",
        options=["7d", "30d", "90d", "all"],
        index=1,
        format_func=lambda x: "Last 7 Days" if x == "7d" else ("Last 30 Days" if x == "30d" else ("Last 90 Days" if x == "90d" else "All Time")),
    )

    try:
        ts_data = get_time_series_analytics(days=days_option)
    except APIError as e:
        st.error(f"Could not load time-series analytics: {e.detail}")
        return

    if not ts_data.get("has_sufficient_data"):
        st.info(f"ℹ️ {ts_data.get('message', 'Insufficient historical data for selected date range.')}")
        return

    series = ts_data.get("series", [])
    dates = [s["date"] for s in series]
    uploads = [s["uploads"] for s in series]
    screenings = [s["screenings"] for s in series]
    reviews = [s["reviews"] for s in series]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=uploads, mode="lines+markers", name="Resume Uploads", line=dict(color="#6C63FF", width=2)))
    fig.add_trace(go.Scatter(x=dates, y=screenings, mode="lines+markers", name="Screenings", line=dict(color="#06D6A0", width=2)))
    fig.add_trace(go.Scatter(x=dates, y=reviews, mode="lines+markers", name="Recruiter Reviews", line=dict(color="#FFD166", width=2)))

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Event Count",
        height=350,
        margin=dict(l=20, r=20, t=20, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(ts_data.get("explainability", ""))


def _render_job_comparison():
    st.subheader("Job Description Comparative Metrics")
    st.caption("Compare candidate volume, score metrics, and skill coverage across jobs.")

    try:
        comp_data = get_job_comparison()
        comparison = comp_data.get("comparison", [])
    except APIError as e:
        st.error(f"Could not load job comparison: {e.detail}")
        return

    if not comparison:
        st.info("No active jobs available for comparison.")
        return

    table_data = []
    for item in comparison:
        table_data.append({
            "Job Title": item["title"],
            "Department": item["department"] or "N/A",
            "Candidates": item["candidate_volume"],
            "Screenings": item["screening_volume"],
            "Avg Score": f"{item['avg_relevance_score']:.1f}%" if item["avg_relevance_score"] is not None else "N/A",
            "Avg Req Coverage": f"{item['avg_required_coverage']:.1f}%" if item["avg_required_coverage"] is not None else "N/A",
            "Avg Pref Coverage": f"{item['avg_preferred_coverage']:.1f}%" if item["avg_preferred_coverage"] is not None else "N/A",
            "Review %": f"{item['review_percentage']:.1f}%",
            "Shortlist %": f"{item['shortlist_percentage']:.1f}%",
            "Top Missing Skills": ", ".join(item["top_missing_skills"][:3]) if item["top_missing_skills"] else "None",
        })

    st.dataframe(table_data, use_container_width=True)
    st.caption(comp_data.get("explainability", ""))


def _render_pipeline_insights():
    st.subheader("Job Pipeline & Recruiter Activity")

    try:
        jobs = list_jobs(active_only=True)
    except APIError:
        jobs = []

    if not jobs:
        st.info("No jobs available.")
        return

    job_map = {f"{j['title']} ({j['public_id'][:8]})": j["public_id"] for j in jobs}
    selected_label = st.selectbox("Select Job Description", options=list(job_map.keys()))
    selected_job_id = job_map[selected_label]

    try:
        pipe_data = get_candidate_pipeline_insights(selected_job_id)
    except APIError as e:
        st.error(f"Could not load pipeline insights: {e.detail}")
        return

    st.markdown(f"### Pipeline Insights for **{pipe_data.get('job_title')}**")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Total Candidates Screened", pipe_data.get("total_candidates", 0))
    with c2:
        proc = pipe_data.get("processing_summary", {})
        st.metric("Processing Completed", proc.get("completed", 0))
    with c3:
        sep = pipe_data.get("pipeline_separation", {})
        st.metric("AI OOD Review Required", sep.get("ood_review_count", 0))

    st.caption("Note: AI OOD review flags remain distinct from human recruiter decisions.")

    st.divider()
    st.markdown("#### 🕒 Real Recruiter Activity Timeline")
    try:
        activity_data = get_recruiter_activity(limit=15)
        activities = activity_data.get("activity", [])
        if activities:
            for act in activities:
                st.write(f"• **{act['action']}** (Date: `{act['reviewed_at'][:19] if act['reviewed_at'] else 'N/A'}`)")
                if act.get("review_notes"):
                    st.caption(f"  Note: {act['review_notes']}")
        else:
            st.info("No recruiter activity logged yet.")
    except Exception as e:
        st.warning(f"Activity log unavailable: {e}")
