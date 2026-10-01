"""
frontend/views/candidate_profile.py

Candidate Profile & AI Intelligence Layer View.
"""

from __future__ import annotations

import streamlit as st
from services.api_client import (
    APIError,
    get_resume,
    get_ai_candidate_explanation,
    generate_ai_interview_questions,
    generate_ai_cover_letter,
    rewrite_ai_resume_bullet,
)
from components.resume_advisor import render_resume_advisor


def render_candidate_profile():
    resume_id = st.session_state.get("selected_resume_id")
    candidate_id = st.session_state.get("selected_candidate_id") or resume_id

    if not resume_id:
        st.info("No candidate/resume selected. Go to Screening Results and select a candidate.")
        return

    st.title("👤 Candidate Profile & AI Intelligence")

    try:
        resume = get_resume(resume_id)
    except APIError as e:
        st.error(f"Failed to load candidate resume: {e.detail}")
        return

    # Header
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Predicted Domain", resume.get("predicted_domain") or "Unknown")
    with col2:
        st.metric("Confidence", (resume.get("prediction_confidence") or "N/A").capitalize())
    with col3:
        st.metric("Status", resume.get("status", "unknown").capitalize())

    st.divider()

    # ── AI Intelligence Layer Section ─────────────────────────────────────────
    st.subheader("🤖 AI Intelligence Assistant")
    st.caption("AI-assisted explanations, interview generation, cover letter drafting, and bullet point improvements.")
    st.info("⚠️ **AI Generated — Verify Before Use**. AI outputs are assistive recommendations only.")

    ai_tab_exp, ai_tab_questions, ai_tab_letter, ai_tab_bullets = st.tabs([
        "💡 Candidate Explanation",
        "❓ Interview Questions",
        "✉️ Cover Letter Draft",
        "✏️ Improve Resume Bullet",
    ])

    with ai_tab_exp:
        if st.button("Generate AI Candidate Explanation", key="btn_ai_exp"):
            with st.spinner("Analyzing candidate background & screening results..."):
                try:
                    exp = get_ai_candidate_explanation(candidate_id or resume_id)
                    st.success("Candidate Explanation Generated")
                    st.markdown(f"**Summary:** {exp.get('summary', '')}")
                    c_str, c_con = st.columns(2)
                    with c_str:
                        st.markdown("#### 💪 Key Strengths")
                        for s in exp.get("strengths", []):
                            st.write(f"• {s}")
                    with c_con:
                        st.markdown("#### ⚠️ Key Concerns & Gaps")
                        for c in exp.get("concerns", []):
                            st.write(f"• {c}")

                    st.markdown("#### 📋 Evidence")
                    for ev in exp.get("evidence", []):
                        st.write(f"• {ev}")

                    st.caption(f"Label: {exp.get('label', '')}")
                except APIError as err:
                    st.error(f"Could not generate AI explanation: {err.detail}")

    with ai_tab_questions:
        if st.button("Generate Role-Specific Interview Questions", key="btn_ai_q"):
            with st.spinner("Generating 5-category interview kit..."):
                try:
                    kit = generate_ai_interview_questions(candidate_id or resume_id)
                    st.success("Interview Questions Generated")
                    for q in kit.get("questions", []):
                        with st.expander(f"**{q.get('category')}**: {q.get('question')}", expanded=True):
                            st.write(f"**Why this question:** {q.get('why_this_question')}")
                            st.write(f"**Difficulty:** `{q.get('difficulty')}`")
                            st.write("**Expected Key Points:**")
                            for kp in q.get("expected_key_points", []):
                                st.write(f"  • {kp}")
                except APIError as err:
                    st.error(f"Could not generate interview questions: {err.detail}")

    with ai_tab_letter:
        comp_name = st.text_input("Company Name", value="Target Organization")
        tone_val = st.selectbox("Tone", options=["PROFESSIONAL", "ENTHUSIASTIC", "EXECUTIVE"])
        if st.button("Draft Tailored Cover Letter", key="btn_ai_letter"):
            with st.spinner("Drafting cover letter..."):
                try:
                    letter = generate_ai_cover_letter(candidate_id or resume_id, company_name=comp_name, tone=tone_val)
                    st.success("Cover Letter Draft Ready")
                    st.text_area("Full Cover Letter Draft (Editable)", value=letter.get("full_cover_letter", ""), height=250)
                    st.caption("AI Generated Draft — Verify Before Use")
                except APIError as err:
                    st.error(f"Could not generate cover letter: {err.detail}")

    with ai_tab_bullets:
        bullet_text = st.text_area("Enter Resume Bullet Point to Rewrite", value="Managed backend API deployment and database queries for the web app.")
        rewrite_mode = st.selectbox("Rewrite Focus", options=["STAR", "TECHNICAL", "ATS"])
        if st.button("Optimize Bullet Point", key="btn_ai_bullet"):
            with st.spinner("Optimizing bullet point..."):
                try:
                    res = rewrite_ai_resume_bullet(resume_id, bullet=bullet_text, mode=rewrite_mode)
                    st.success("Bullet Point Optimized")
                    st.markdown(f"**Original:** `{res.get('original_bullet')}`")
                    st.markdown(f"**Optimized:** `{res.get('optimized_bullet')}`")
                    st.markdown(f"**Action Verb Used:** `{res.get('action_verb_used')}`")
                    st.write("**Key Improvements:**")
                    for kc in res.get("key_changes", []):
                        st.write(f"• {kc}")
                    if res.get("placeholders_needed"):
                        st.warning(f"**Placeholders to fill:** {', '.join(res['placeholders_needed'])}")
                except APIError as err:
                    st.error(f"Could not optimize bullet point: {err.detail}")

    st.divider()

    # Extracted skills
    skills = resume.get("extracted_skills", [])
    st.subheader(f"🔧 {len(skills)} Skills Extracted")

    if skills:
        by_domain: dict[str, list] = {}
        for s in skills:
            d = s.get("domain") or "Other"
            by_domain.setdefault(d, []).append(s)

        for domain, domain_skills in sorted(by_domain.items()):
            with st.expander(f"**{domain}** ({len(domain_skills)} skills)", expanded=True):
                for s in sorted(domain_skills, key=lambda x: -x.get("frequency", 1)):
                    badge = "🟢" if s.get("frequency", 1) > 2 else "⚪"
                    st.write(f"{badge} **{s['canonical_name']}** × {s.get('frequency', 1)}")
                    if s.get("evidence_snippet"):
                        st.caption(f"> {s['evidence_snippet']}")
    else:
        st.info("No skills extracted.")

    st.divider()

    # Render Resume Optimization Advisor
    render_resume_advisor(
        confidence=resume.get("prediction_confidence", "low"),
        predicted_domain=resume.get("predicted_domain"),
        char_count=resume.get("text_char_count", 0),
        skill_count=len(skills),
    )

    st.divider()

    # File metadata
    with st.expander("📄 File Metadata"):
        st.write(f"**Original filename:** {resume.get('original_filename')}")
        st.write(f"**File size:** {resume.get('file_size_bytes', 0):,} bytes")
        st.write(f"**Pages:** {resume.get('page_count', 'N/A')}")
        st.write(f"**Text length:** {resume.get('text_char_count', 0):,} characters")
        st.write(f"**Uploaded:** {resume.get('uploaded_at', '')[:19]}")
