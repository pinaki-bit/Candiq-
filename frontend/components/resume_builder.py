"""
frontend/components/resume_builder.py

Dual-Pane Live Candidate Resume Builder & Real-Time Match Simulator UI component.
"""

from __future__ import annotations
import streamlit as st

def render_live_resume_builder():
    st.markdown("### 📝 Live Candidate Resume Builder & ATS Match Simulator")
    st.caption("Dual-pane live editor with real-time ATS formatting score, skill extraction, and job match simulation.")

    col_editor, col_preview = st.columns([1, 1])

    with col_editor:
        st.markdown("#### ✏️ Live Markdown / Text Editor")
        target_job_desc = st.text_area(
            "Target Job Description / Required Skills (Optional):",
            placeholder="Paste target job requirements here to enable live match scoring...",
            height=80,
            key="rb_target_job",
        )

        default_resume = (
            "# ALEX RIDER\n"
            "alex.rider@example.com | (555) 234-5678 | San Francisco, CA\n\n"
            "## PROFESSIONAL SUMMARY\n"
            "Results-driven Senior Backend Engineer with 5+ years of experience designing scalable microservices, REST APIs, and database architectures.\n\n"
            "## WORK EXPERIENCE\n"
            "### Senior Backend Engineer — TechCorp (2022 – Present)\n"
            "• Architected distributed RESTful APIs using Python, FastAPI, and PostgreSQL, handling 100k daily active users.\n"
            "• Containerized core microservices with Docker and deployed automated CI/CD pipelines.\n"
            "• Optimized SQL queries and Redis caching, reducing API response latency by 35%.\n\n"
            "## TECHNICAL SKILLS\n"
            "Python, FastAPI, PostgreSQL, Docker, Git, Redis, REST APIs, SQL, Microservices, CI/CD.\n\n"
            "## EDUCATION\n"
            "B.S. in Computer Science — State University (2018–2022)\n"
        )

        resume_markdown = st.text_area(
            "Resume Content (Markdown / Text):",
            value=default_resume,
            height=420,
            key="rb_resume_md",
        )

    # Calculate real-time analysis
    try:
        from frontend.services.api_client import get_api_client
        api_client = get_api_client()
        resp = api_client.post(
            "/resumes/live-analysis",
            json={
                "resume_markdown": resume_markdown,
                "job_description": target_job_desc if target_job_desc.strip() else None,
            },
        )
        if resp.status_code == 200:
            analysis = resp.json()
        else:
            from app.services.resume_builder_service import analyze_live_resume
            analysis = analyze_live_resume(resume_markdown, job_description=target_job_desc).__dict__
    except Exception:
        from app.services.resume_builder_service import analyze_live_resume
        analysis = analyze_live_resume(resume_markdown, job_description=target_job_desc).__dict__

    with col_preview:
        st.markdown("#### 📊 Live ATS & Match Intelligence Panel")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("ATS Score", f"{analysis['ats_score']}%")
        m2.metric("Match Score", f"{analysis['live_match_score']}%")
        m3.metric("Word Count", f"{analysis['word_count']}")
        m4.metric("Est. Pages", f"{analysis['estimated_pages']}")

        st.progress(analysis['ats_score'] / 100.0, text=f"ATS Readability Compliance: {analysis['ats_score']}%")

        if analysis.get("matched_skills") or analysis.get("missing_skills"):
            st.markdown("##### 🎯 Target Skill Alignment")
            c_matched, c_missing = st.columns(2)
            with c_matched:
                st.markdown("**Matched Target Skills (🟢):**")
                for sk in analysis.get("matched_skills", []):
                    st.markdown(f"• `{sk}`")
            with c_missing:
                st.markdown("**Missing Target Skills (🔴):**")
                for sk in analysis.get("missing_skills", []):
                    st.markdown(f"• `{sk}`")

        st.markdown("##### 🔍 Extracted Technical Skills")
        st.caption(f"NLP detected {len(analysis.get('extracted_skills', []))} canonical skills in your editor.")
        st.write(", ".join([f"`{s}`" for s in analysis.get("extracted_skills", [])]))

        if analysis.get("ats_warnings"):
            with st.expander("⚠️ ATS Readability Warnings & Action Items", expanded=True):
                for warn in analysis.get("ats_warnings", []):
                    st.warning(warn)
                for sugg in analysis.get("suggestions", []):
                    st.info(f"💡 {sugg}")
