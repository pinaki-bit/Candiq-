"""
frontend/components/talent_search.py

Interactive Talent Semantic Search Engine UI component.
"""

from __future__ import annotations
import streamlit as st

def render_talent_search():
    st.markdown("### 🔎 Talent Semantic Search Engine")
    st.caption("Search your entire processed candidate pool using natural language queries, semantic vectors, and domain filters.")

    col_q, col_f1, col_f2 = st.columns([3, 1, 1])

    with col_q:
        search_query = st.text_input(
            "Natural Language Search Query:",
            placeholder="e.g. Senior Python backend developer with FastAPI, PostgreSQL, and Docker experience",
            key="ts_query_input",
        )
    with col_f1:
        domain_filter = st.selectbox(
            "Domain Filter:",
            options=["All Domains", "Software Engineering", "Data Science", "DevOps", "Cybersecurity", "Product Management"],
            index=0,
            key="ts_domain_select",
        )
    with col_f2:
        min_confidence = st.selectbox(
            "Min Confidence:",
            options=["Any", "high", "medium", "low"],
            index=0,
            key="ts_conf_select",
        )

    if st.button("🔎 Search Candidate Pool", type="primary", use_container_width=True, key="btn_run_ts"):
        if not search_query.strip():
            st.warning("Please enter a natural language search query.")
        else:
            domain_val = None if domain_filter == "All Domains" else domain_filter
            conf_val = None if min_confidence == "Any" else min_confidence

            with st.spinner("Embedding query & searching candidate talent pool..."):
                try:
                    from frontend.services.api_client import get_api_client
                    api_client = get_api_client()
                    resp = api_client.post(
                        "/screening/talent-search",
                        json={
                            "query": search_query,
                            "domain_filter": domain_val,
                            "min_confidence": conf_val,
                            "limit": 10,
                        },
                    )
                    if resp.status_code == 200:
                        search_res = resp.json()
                    else:
                        search_res = {"query": search_query, "total_candidates_searched": 0, "results_count": 0, "results": []}
                except Exception:
                    search_res = {"query": search_query, "total_candidates_searched": 0, "results_count": 0, "results": []}

                st.markdown(f"**Found {search_res['results_count']} candidate(s)** out of {search_res['total_candidates_searched']} searched.")

                if not search_res.get("results"):
                    st.info("No candidates matched your search criteria. Try broadening your natural language query or removing filters.")
                else:
                    for cand in search_res["results"]:
                        with st.expander(
                            f"📄 {cand['original_filename']} — Match Score: {cand['hybrid_score']}% ({cand.get('predicted_domain', 'General')})",
                            expanded=True,
                        ):
                            c1, c2, c3 = st.columns(3)
                            c1.metric("Hybrid Match Score", f"{cand['hybrid_score']}%")
                            c2.metric("Semantic Vector Sim", f"{cand['semantic_similarity']}%")
                            c3.metric("ML Confidence", f"{cand.get('prediction_confidence', 'N/A')}")

                            st.markdown(f"**Matched Skills:** {', '.join([f'`{s}`' for s in cand.get('matched_skills', [])]) if cand.get('matched_skills') else 'N/A'}")
                            st.markdown(f"**Evidence Excerpt:** *\"{cand.get('snippet', 'N/A')}\"*")
