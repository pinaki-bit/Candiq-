"""
frontend/components/cover_letter_generator.py

Interactive AI Cover Letter Generator UI component.
"""

from __future__ import annotations
import streamlit as st

def render_cover_letter_generator(
    default_candidate_name: str = "Candidate",
    default_skills: list[str] | None = None,
):
    st.markdown("### ✉️ AI Cover Letter Generator")
    st.caption("Generate a tailored, professional cover letter matching candidate background with job requirements.")

    col_inputs, col_options = st.columns([2, 1])

    with col_inputs:
        job_title = st.text_input("Target Job Title *", placeholder="e.g. Senior Backend Engineer", key="cl_job_title")
        company_name = st.text_input("Company Name *", placeholder="e.g. Acme Innovations", key="cl_company_name")
        candidate_name = st.text_input("Candidate Name", value=default_candidate_name, key="cl_candidate_name")

    with col_options:
        tone = st.selectbox(
            "Cover Letter Tone:",
            options=["PROFESSIONAL", "ENTHUSIASTIC", "EXECUTIVE"],
            index=0,
            key="cl_tone",
        )
        skills_input = st.text_input(
            "Highlight Key Skills (comma-separated):",
            value=", ".join(default_skills) if default_skills else "Python, FastApi, PostgreSQL, Docker",
            key="cl_skills",
        )

    job_description = st.text_area(
        "Job Description / Key Requirements (Optional):",
        placeholder="Paste key responsibilities or requirements...",
        height=100,
        key="cl_job_desc",
    )

    if st.button("✨ Generate AI Cover Letter", type="primary", use_container_width=True, key="btn_gen_cl"):
        if not job_title.strip() or not company_name.strip():
            st.warning("Please provide both Target Job Title and Company Name.")
        else:
            parsed_skills = [s.strip() for s in skills_input.split(",") if s.strip()]
            with st.spinner("Drafting tailored cover letter using AI..."):
                try:
                    from frontend.services.api_client import get_api_client
                    api_client = get_api_client()
                    resp = api_client.post(
                        "/resumes/generate-cover-letter",
                        json={
                            "job_title": job_title,
                            "company_name": company_name,
                            "candidate_name": candidate_name,
                            "candidate_skills": parsed_skills,
                            "job_description": job_description if job_description.strip() else None,
                            "tone": tone,
                        },
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        st.success(f"🎉 **Generated Cover Letter ({data['tone_used']} Tone):**")
                        
                        st.text_area(
                            "Full Cover Letter Output (Editable / Copyable):",
                            value=data["full_cover_letter"],
                            height=320,
                            key="cl_output_area",
                        )
                        
                        with st.expander("🔍 Structural Breakdown"):
                            st.markdown(f"**Salutation:** `{data['salutation']}`")
                            st.markdown(f"**Opening Hook:** {data['opening_hook']}")
                            st.markdown(f"**Core Value Proposition:** {data['core_value_proposition']}")
                            st.markdown(f"**Company Alignment:** {data['company_alignment_paragraph']}")
                            st.markdown(f"**Call to Action:** {data['closing_call_to_action']}")
                    else:
                        st.error(f"Failed to generate cover letter: {resp.text}")
                except Exception as exc:
                    # Fallback offline generator
                    from app.services.cover_letter_service import generate_cover_letter
                    result = generate_cover_letter(
                        job_title=job_title,
                        company_name=company_name,
                        candidate_name=candidate_name,
                        candidate_skills=parsed_skills,
                        job_description=job_description if job_description.strip() else None,
                        tone=tone,
                    )
                    st.success(f"🎉 **Generated Cover Letter ({result.tone_used} Tone):**")
                    st.text_area(
                        "Full Cover Letter Output (Editable / Copyable):",
                        value=result.full_cover_letter,
                        height=320,
                        key="cl_output_fallback",
                    )
