"""
frontend/components/ats_analyzer.py

Interactive ATS Compatibility & Parser Compliance Suite UI component.
"""

from __future__ import annotations
import streamlit as st

def render_ats_analyzer():
    st.markdown("### 🔍 ATS Compatibility & Parser Compliance Suite")
    st.caption("Scan document structure, formatting readability, contact information, and skill keyword density.")

    input_text = st.text_area(
        "Paste Resume Text to Scan:",
        placeholder="Paste full resume text here to analyze ATS compliance...",
        height=200,
        key="ats_input_area",
    )

    if st.button("🚀 Run Full ATS Compatibility Scan", type="primary", use_container_width=True, key="btn_run_ats"):
        if not input_text.strip():
            st.warning("Please paste resume text to analyze.")
        else:
            with st.spinner("Scanning 4 ATS compliance dimensions..."):
                try:
                    from frontend.services.api_client import get_api_client
                    api_client = get_api_client()
                    resp = api_client.post("/resumes/ats-check", json={"resume_text": input_text})
                    if resp.status_code == 200:
                        ats = resp.json()
                    else:
                        from app.services.ats_analyzer_service import analyze_ats_compatibility
                        ats = analyze_ats_compatibility(input_text).__dict__
                except Exception:
                    from app.services.ats_analyzer_service import analyze_ats_compatibility
                    ats = analyze_ats_compatibility(input_text).__dict__

                cat = ats.get("compliance_category", "GOOD")
                score = ats.get("overall_score", 0.0)

                if cat == "EXCELLENT":
                    st.success(f"🏆 **Overall ATS Score:** {score}% — EXCELLENT (Top Tier Readability)")
                elif cat == "GOOD":
                    st.info(f"🟢 **Overall ATS Score:** {score}% — GOOD (Parser Compliant)")
                elif cat == "NEEDS_IMPROVEMENT":
                    st.warning(f"🟡 **Overall ATS Score:** {score}% — NEEDS IMPROVEMENT")
                else:
                    st.error(f"🔴 **Overall ATS Score:** {score}% — CRITICAL (High Risk of Rejection)")

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Structure (25)", f"{ats.get('structure_score', 0)}/25")
                c2.metric("Readability (25)", f"{ats.get('readability_score', 0)}/25")
                c3.metric("Contact Info (25)", f"{ats.get('contact_score', 0)}/25")
                c4.metric("Skill Density (25)", f"{ats.get('density_score', 0)}/25")

                st.progress(score / 100.0)

                if ats.get("critical_issues"):
                    st.error("🚨 **Critical ATS Issues Flagged:**")
                    for issue in ats["critical_issues"]:
                        st.markdown(f"• {issue}")

                if ats.get("warnings"):
                    st.warning("⚠️ **Formatting & Parsing Warnings:**")
                    for warn in ats["warnings"]:
                        st.markdown(f"• {warn}")

                if ats.get("actionable_recommendations"):
                    st.success("💡 **Actionable Recommendations for Optimization:**")
                    for rec in ats["actionable_recommendations"]:
                        st.markdown(f"• {rec}")

                with st.expander("📌 Section Detection Analysis"):
                    st.markdown(f"**Detected Sections:** {', '.join(ats.get('detected_sections', []))}")
                    if ats.get("missing_essential_sections"):
                        st.markdown(f"**Missing Essential Sections:** `{', '.join(ats.get('missing_essential_sections', []))}`")
