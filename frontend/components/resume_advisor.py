"""
frontend/components/resume_advisor.py

Interactive Resume Optimization & Confidence Upgrade Advisor.
"""

from __future__ import annotations
import streamlit as st

def render_resume_advisor(
    confidence: str,
    predicted_domain: str | None = None,
    char_count: int = 0,
    skill_count: int = 0,
):
    confidence = (confidence or "low").lower()
    domain_str = predicted_domain or "General Tech / Unclassified"

    st.markdown("### 💡 Resume Upgrade & ATS Optimization Advisor")
    st.caption("Actionable, AI-driven recommendations to elevate your resume's classification confidence and ATS score.")

    if confidence == "low" or confidence == "unavailable":
        st.error(
            f"🔻 **Current Classification Status:** Low Confidence / Uncertain ({domain_str})\n\n"
            "**Target:** Upgrade to **Medium Confidence (🟡)**"
        )
        
        st.markdown("#### 🎯 Priority Action Plan to Reach Medium Confidence:")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                """
                <div style="background-color: #2b1f1d; border-left: 4px solid #ef476f; padding: 1rem; border-radius: 6px; margin-bottom: 1rem;">
                    <h4 style="margin: 0 0 0.5rem 0; color: #ef476f;">1. Define Explicit Target Role</h4>
                    <p style="font-size: 0.9rem; color: #ccc; margin: 0;">
                        Add a clear title header at the top of your resume (e.g., <i>"Data Scientist & ML Engineer"</i> or <i>"Full-Stack Web Developer"</i>). ML classifiers need explicit role markers in the intro snippet.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                """
                <div style="background-color: #2b1f1d; border-left: 4px solid #ef476f; padding: 1rem; border-radius: 6px; margin-bottom: 1rem;">
                    <h4 style="margin: 0 0 0.5rem 0; color: #ef476f;">2. Add Standardized Section Headers</h4>
                    <p style="font-size: 0.9rem; color: #ccc; margin: 0;">
                        Use clear, standard headings in ALL CAPS: <code>WORK EXPERIENCE</code>, <code>TECHNICAL SKILLS</code>, <code>PROJECTS</code>, and <code>EDUCATION</code>. Custom or non-standard headers cause NLP parsers to skip sections.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown(
                """
                <div style="background-color: #2b1f1d; border-left: 4px solid #ef476f; padding: 1rem; border-radius: 6px; margin-bottom: 1rem;">
                    <h4 style="margin: 0 0 0.5rem 0; color: #ef476f;">3. Enrich Core Technical Taxonomy</h4>
                    <p style="font-size: 0.9rem; color: #ccc; margin: 0;">
                        Your resume currently has <b>{}</b> extracted skills. Include at least 8-12 canonical domain tools (e.g. <i>Python, SQL, React, AWS, Docker, Git</i>) in a dedicated Skills block.
                    </p>
                </div>
                """.format(skill_count),
                unsafe_allow_html=True,
            )
            st.markdown(
                """
                <div style="background-color: #2b1f1d; border-left: 4px solid #ef476f; padding: 1rem; border-radius: 6px; margin-bottom: 1rem;">
                    <h4 style="margin: 0 0 0.5rem 0; color: #ef476f;">4. Expand Resume Text Depth</h4>
                    <p style="font-size: 0.9rem; color: #ccc; margin: 0;">
                        Text extracted: <b>{:,} characters</b>. Brief or 1-page sparse resumes lack sufficient TF-IDF feature density. Aim for 400–800 words describing concrete responsibilities.
                    </p>
                </div>
                """.format(char_count),
                unsafe_allow_html=True,
            )

        with st.expander("✅ Checklist to Upgrade from Low to Medium Confidence"):
            st.checkbox("Add primary target job title in the summary statement", key="chk_low_1")
            st.checkbox("List 8+ core technical skills matching target domain", key="chk_low_2")
            st.checkbox("Format sections with standard capital headers (EXPERIENCE, SKILLS, EDUCATION)", key="chk_low_3")
            st.checkbox("Ensure PDF text is selectable (not a scanned image)", key="chk_low_4")

    elif confidence == "medium":
        st.warning(
            f"🟡 **Current Classification Status:** Medium Confidence ({domain_str})\n\n"
            "**Target:** Upgrade to **High Confidence (🟢)**"
        )
        
        st.markdown("#### 🚀 Priority Action Plan to Reach High Confidence (Top Tier Match):")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                """
                <div style="background-color: #2b281d; border-left: 4px solid #ffd166; padding: 1rem; border-radius: 6px; margin-bottom: 1rem;">
                    <h4 style="margin: 0 0 0.5rem 0; color: #ffd166;">1. Quantify Project Impact & Metrics</h4>
                    <p style="font-size: 0.9rem; color: #ccc; margin: 0;">
                        Replace general descriptions with hard metrics. E.g. change <i>"Built web app"</i> to <i>"Architected microservice processing 50k requests/sec, reducing API latency by 40%"</i>.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                """
                <div style="background-color: #2b281d; border-left: 4px solid #ffd166; padding: 1rem; border-radius: 6px; margin-bottom: 1rem;">
                    <h4 style="margin: 0 0 0.5rem 0; color: #ffd166;">2. Specify Frameworks & Architecture</h4>
                    <p style="font-size: 0.9rem; color: #ccc; margin: 0;">
                        Instead of high-level category words (e.g. <i>"Cloud"</i>, <i>"Database"</i>), detail precise frameworks (e.g. <i>"AWS ECS, Terraform, PostgreSQL, Redis, Kubernetes"</i>).
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown(
                """
                <div style="background-color: #2b281d; border-left: 4px solid #ffd166; padding: 1rem; border-radius: 6px; margin-bottom: 1rem;">
                    <h4 style="margin: 0 0 0.5rem 0; color: #ffd166;">3. Reinforce Keyword Frequency</h4>
                    <p style="font-size: 0.9rem; color: #ccc; margin: 0;">
                        Ensure your top target skills appear multiple times across experience bullet points to boost TF-IDF term weights in the ML classification engine.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                """
                <div style="background-color: #2b281d; border-left: 4px solid #ffd166; padding: 1rem; border-radius: 6px; margin-bottom: 1rem;">
                    <h4 style="margin: 0 0 0.5rem 0; color: #ffd166;">4. Highlight Industry Certifications</h4>
                    <p style="font-size: 0.9rem; color: #ccc; margin: 0;">
                        Add recognized domain credentials (e.g., <i>AWS Solutions Architect</i>, <i>Google Professional Data Engineer</i>, <i>CKA</i>).
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with st.expander("✅ Checklist to Upgrade from Medium to High Confidence"):
            st.checkbox("Include numerical metrics in at least 3 bullet points (e.g., %, $, throughput)", key="chk_med_1")
            st.checkbox("Replace generic terms with specific libraries & cloud services", key="chk_med_2")
            st.checkbox("Align work experience bullet points with target domain job descriptions", key="chk_med_3")
            st.checkbox("Add professional certifications / specialized coursework section", key="chk_med_4")

    else:  # High confidence
        st.success(
            f"🟢 **Current Classification Status:** High Confidence ({domain_str})\n\n"
            "**Status:** Outstanding! Your resume strongly signals domain authority to ATS parsers and ML classifiers."
        )

        st.markdown(
            """
            <div style="background-color: #1d2b24; border-left: 4px solid #06d6a0; padding: 1rem; border-radius: 6px; margin-bottom: 1rem;">
                <h4 style="margin: 0 0 0.5rem 0; color: #06d6a0;">🌟 Maintaining Top 1% ATS Performance:</h4>
                <ul style="color: #ccc; font-size: 0.9rem; margin: 0; padding-left: 1.2rem;">
                    <li>Keep PDF structure clean with single-column layout without tables or graphics overlaying text.</li>
                    <li>Ensure skill names match industry standard spellings (e.g., "Node.js" rather than "NodeJS").</li>
                    <li>Keep content updated with recent projects and leadership achievements.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # -----------------------------------------------------------------------
    # Interactive AI Bullet Rewriter Tool (Phase 6 Integration)
    # -----------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### ✍️ Interactive AI Resume Bullet Optimizer")
    st.caption("Transform weak or unquantified experience bullets into high-impact statements using AI (STAR, Technical, or ATS modes).")

    with st.expander("⚡ Open AI Bullet Point Optimizer", expanded=False):
        col_input, col_config = st.columns([3, 1])

        with col_input:
            input_bullet = st.text_area(
                "Paste your work experience bullet point:",
                placeholder="e.g. Built microservices for payment processing and optimized database queries.",
                height=100,
                key="advisor_bullet_input",
            )
        
        with col_config:
            mode = st.selectbox(
                "Optimization Mode:",
                options=["STAR", "TECHNICAL", "ATS"],
                index=0,
                help="STAR: Situation-Task-Action-Result | TECHNICAL: Tools & scale | ATS: Parser keyword density",
                key="advisor_mode_select",
            )
            target_role = st.text_input(
                "Target Role (Optional):",
                placeholder="e.g. Backend Engineer",
                key="advisor_role_input",
            )

        if st.button("🚀 Rewrite Bullet with AI", type="primary", use_container_width=True, key="btn_rewrite_bullet"):
            if not input_bullet.strip():
                st.warning("Please paste a bullet point to rewrite.")
            else:
                with st.spinner(f"Optimizing bullet using AI ({mode} mode)..."):
                    try:
                        from frontend.services.api_client import get_api_client
                        api_client = get_api_client()
                        response = api_client.post(
                            "/resumes/rewrite-bullet",
                            json={
                                "bullet": input_bullet,
                                "mode": mode,
                                "target_job_title": target_role if target_role else None,
                            },
                        )
                        if response.status_code == 200:
                            data = response.json()
                            st.success(f"✨ **Optimized Bullet ({data['mode']} Mode):**")
                            st.code(data["optimized_bullet"], language="markdown")
                            
                            c1, c2 = st.columns(2)
                            with c1:
                                st.markdown("**Key Improvements Made:**")
                                for change in data.get("key_changes", []):
                                    st.markdown(f"- {change}")
                            with c2:
                                st.markdown("**Action Verb Used:**")
                                st.info(f"🔑 `{data.get('action_verb_used', 'Action')}`")
                                if data.get("placeholders_needed"):
                                    st.warning(f"⚠️ **Metrics to Add:** {', '.join(data['placeholders_needed'])}")
                        else:
                            st.error(f"Failed to rewrite bullet: {response.text}")
                    except Exception as exc:
                        # Fallback offline rewrite display
                        from app.services.bullet_rewriter import rewrite_bullet_point
                        result = rewrite_bullet_point(input_bullet, mode=mode, target_job_title=target_role)
                        st.success(f"✨ **Optimized Bullet ({result.mode} Mode):**")
                        st.code(result.optimized_bullet, language="markdown")
                        st.markdown("**Key Improvements Made:**")
                        for change in result.key_changes:
                            st.markdown(f"- {change}")
