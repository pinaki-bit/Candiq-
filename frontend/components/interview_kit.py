"""
frontend/components/interview_kit.py

Interactive 5-Category Technical Interview Intelligence Kit UI component.
"""

from __future__ import annotations
import streamlit as st

def render_interview_kit(
    default_job_title: str = "Software Engineer",
    candidate_skills: list[str] | None = None,
    missing_skills: list[str] | None = None,
):
    st.markdown("### 🎯 Grounded 5-Category Technical Interview Intelligence Kit")
    st.caption("AI-generated interview questions mapped directly to candidate resume evidence and identified skill gaps.")

    c1, c2 = st.columns([2, 1])
    with c1:
        job_title = st.text_input("Target Position Title:", value=default_job_title, key="ik_job_title")
        cand_skills_in = st.text_input(
            "Candidate Verified Skills (comma-separated):",
            value=", ".join(candidate_skills) if candidate_skills else "Python, FastAPI, SQL, Docker",
            key="ik_cand_skills",
        )
    with c2:
        gap_skills_in = st.text_input(
            "Identified Missing Skill Gaps (comma-separated):",
            value=", ".join(missing_skills) if missing_skills else "Kubernetes, System Architecture",
            key="ik_gap_skills",
        )

    if st.button("⚡ Generate Technical Interview Kit", type="primary", use_container_width=True, key="btn_gen_ik"):
        parsed_skills = [s.strip() for s in cand_skills_in.split(",") if s.strip()]
        parsed_gaps = [s.strip() for s in gap_skills_in.split(",") if s.strip()]

        with st.spinner("Generating grounded 5-category interview kit..."):
            try:
                from frontend.services.api_client import get_api_client
                api_client = get_api_client()
                resp = api_client.post(
                    "/screening/interview-kit",
                    json={
                        "job_title": job_title,
                        "candidate_skills": parsed_skills,
                        "missing_skills": parsed_gaps,
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    st.success(f"📋 **Generated Technical Interview Kit for {data['job_title']}**")
                    
                    for q in data.get("questions", []):
                        with st.expander(f"Question {q['question_id']}: [{q['category']}] ({q['difficulty']} Difficulty)", expanded=True):
                            st.markdown(f"#### ❓ {q['question']}")
                            st.info(f"💡 **Why this question?** {q['why_this_question']}")
                            
                            st.markdown("**Interviewer Evaluation Criteria (Expected Key Points):**")
                            for idx, point in enumerate(q.get("expected_key_points", []), 1):
                                st.checkbox(f"{point}", key=f"chk_ik_{q['question_id']}_{idx}")
                else:
                    st.error(f"Failed to generate interview kit: {resp.text}")
            except Exception as exc:
                # Fallback offline interview kit
                from app.services.interview_service import generate_interview_kit
                result = generate_interview_kit(
                    job_title=job_title,
                    candidate_skills=parsed_skills,
                    missing_skills=parsed_gaps,
                )
                st.success(f"📋 **Generated Technical Interview Kit for {result.job_title}**")
                for q in result.questions:
                    with st.expander(f"Question {q.question_id}: [{q.category}] ({q.difficulty} Difficulty)", expanded=True):
                        st.markdown(f"#### ❓ {q.question}")
                        st.info(f"💡 **Why this question?** {q.why_this_question}")
                        st.markdown("**Interviewer Evaluation Criteria (Expected Key Points):**")
                        for idx, point in enumerate(q.expected_key_points, 1):
                            st.checkbox(f"{point}", key=f"chk_ik_fb_{q.question_id}_{idx}")
