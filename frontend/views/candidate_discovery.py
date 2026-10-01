"""
frontend/views/candidate_discovery.py

Phase 36 — Advanced Candidate Discovery & Hiring Intelligence Interface.
"""

import streamlit as st
from services import api_client


def render_candidate_discovery_page():
    st.title("🔍 Candidate Discovery & Hiring Intelligence")
    st.caption("Search, discover, filter, compare, and investigate real candidates using production semantic vector embeddings and hybrid matching.")

    # 1. Top Natural Language Search Bar
    search_query = st.text_input(
        "🔎 Natural Language Candidate Search",
        placeholder="e.g. Find candidates with Python, FastAPI, and cloud backend experience",
    )

    st.divider()

    col_filters, col_results, col_intelligence = st.columns([1.0, 1.8, 1.2])

    # ── LEFT: RECRUITER FILTERS ───────────────────────────────────────────────
    with col_filters:
        st.subheader("🎛️ Discovery Filters")

        domain_filter = st.selectbox("Domain", ["All Domains", "Engineering", "Data Science", "DevOps", "Management"])
        domain_val = None if domain_filter == "All Domains" else domain_filter

        min_req_cov = st.slider("Min Required Coverage (%)", 0, 100, 0, step=5)
        min_sem_sim = st.slider("Min Semantic Similarity (%)", 0, 100, 0, step=5)

        ood_filter = st.selectbox("OOD Review Status", ["All Statuses", "in_domain_like", "possible_out_of_domain"])
        ood_val = None if ood_filter == "All Statuses" else ood_filter

        review_filter = st.selectbox("Recruiter Decision", ["All Decisions", "pending", "shortlisted", "rejected"])
        review_val = None if review_filter == "All Decisions" else review_filter

    # ── CENTER: CANDIDATE RESULT CARDS ───────────────────────────────────────
    with col_results:
        st.subheader("📄 Candidate Results")

        try:
            res = api_client.search_discovery_candidates(
                query=search_query,
                domain=domain_val,
                min_required_cov=float(min_req_cov) if min_req_cov > 0 else None,
                min_semantic_sim=float(min_sem_sim) if min_sem_sim > 0 else None,
                ood_status=ood_val,
                review_status=review_val,
            )
        except Exception as exc:
            st.error(f"Search failed: {exc}")
            return

        parsed = res.get("parsed_filters", {})
        if parsed.get("extracted_skills"):
            st.caption(f"**Extracted Query Keywords:** {', '.join(parsed['extracted_skills'])}")

        candidates = res.get("results", [])
        st.caption(f"Found **{res.get('total_count', 0)}** matching candidate(s)")

        if not candidates:
            st.info("No candidates match the specified search query and filter criteria.")

        selected_cand_id = None
        for idx, c in enumerate(candidates):
            with st.container():
                c_col1, c_col2 = st.columns([3, 1])
                with c_col1:
                    st.markdown(f"### {c.get('full_name')} ({c.get('domain', 'General')})")
                    st.caption(f"**Snippet:** _{c.get('snippet')}_")
                with c_col2:
                    st.metric("Discovery Relevance", f"{c.get('discovery_relevance_score')}%")

                st.progress(c.get("semantic_similarity", 0.0) / 100.0, text=f"Semantic Vector Similarity: {c.get('semantic_similarity')}%")

                if c.get("matched_skills"):
                    st.markdown(f"**Matched Skills:** {', '.join(c.get('matched_skills'))}")
                if c.get("missing_required_skills"):
                    st.markdown(f"**Missing Required:** {', '.join(c.get('missing_required_skills'))}")

                if st.button("🔍 Investigate Candidate", key=f"inv_{c.get('candidate_id')}_{idx}"):
                    st.session_state["selected_discovery_cand"] = c.get("candidate_id")

    # ── RIGHT: SELECTED CANDIDATE INTELLIGENCE & COMPARISON ──────────────────
    with col_intelligence:
        st.subheader("📊 Candidate Intelligence")
        cand_id = st.session_state.get("selected_discovery_cand")
        if not cand_id:
            st.info("👈 Select a candidate card to inspect detailed hiring intelligence & similar candidates.")
        else:
            st.write(f"**Target Candidate Public ID:** `{cand_id}`")
            try:
                similar_res = api_client.get_similar_candidates(cand_id, limit=5)
                st.caption(f"**{similar_res.get('label', 'Semantically Similar Candidates')}**")
                for sim in similar_res.get("similar_candidates", []):
                    st.info(f"• **{sim.get('full_name')}** ({sim.get('domain')}) — Similarity: **{sim.get('semantic_similarity')}%**")
            except Exception as exc:
                st.warning(f"Could not load similar candidates: {exc}")
