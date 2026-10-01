"""
frontend/views/resume_builder.py

Phase 35 — AI Resume Builder & Live ATS Match Optimization Interface.
"""

import streamlit as st
from services import api_client


def render_resume_builder_page():
    st.title("📝 AI Resume Builder & Live ATS Match Optimizer")
    st.caption("Build, edit, and optimize your resume in real-time against real target jobs using production 6-signal ATS matching.")

    # 1. Fetch available target jobs for real matching
    jobs = []
    try:
        jobs = api_client.list_jobs()
    except Exception as exc:
        st.warning(f"Could not load jobs list: {exc}")

    job_options = {"None": None}
    for j in jobs:
        j_id = j.get("public_id") or str(j.get("id"))
        job_options[f"{j.get('title')} ({j.get('department', 'General')})"] = j_id

    # 2. Select or Create Draft Workspace
    drafts = []
    try:
        drafts = api_client.list_resume_drafts()
    except Exception:
        pass

    col_top1, col_top2 = st.columns([3, 1])
    with col_top1:
        draft_options = {"-- Select a Resume Draft --": None}
        for d in drafts:
            draft_options[f"{d.get('title')} (Updated: {d.get('updated_at', '')[:10]})"] = d.get("id")
        
        selected_draft_id = st.selectbox("Active Resume Draft Workspace", list(draft_options.keys()))
        active_draft_id = draft_options.get(selected_draft_id)

    with col_top2:
        if st.button("➕ Create New Draft", type="primary", use_container_width=True):
            try:
                new_draft = api_client.create_resume_draft({"title": "New Resume Draft"})
                st.success("Created new resume draft workspace!")
                st.rerun()
            except Exception as exc:
                st.error(f"Failed to create draft: {exc}")

    if not active_draft_id:
        st.info("👈 Please select an existing draft workspace or click **Create New Draft** to begin.")
        return

    # Load Active Draft Data
    try:
        draft_data = api_client.get_resume_draft(active_draft_id)
    except Exception as exc:
        st.error(f"Failed to load draft data: {exc}")
        return

    st.divider()

    # 3-Column Studio Layout
    col_editor, col_preview, col_ats = st.columns([1.1, 1.0, 1.1])

    # ── COLUMN 1: RESUME EDITOR ──────────────────────────────────────────────
    with col_editor:
        st.subheader("🛠️ Resume Section Editor")
        
        draft_title = st.text_input("Draft Title", value=draft_data.get("title", "Untitled Draft"))
        selected_job_name = st.selectbox("Target Job", list(job_options.keys()), index=0)
        target_job_id = job_options.get(selected_job_name)

        struct_content = draft_data.get("structured_content", {})
        pinfo = struct_content.get("personal_info", {})

        with st.expander("👤 Personal & Contact Info", expanded=True):
            full_name = st.text_input("Full Name", value=pinfo.get("full_name", ""))
            email = st.text_input("Email", value=pinfo.get("email", ""))
            phone = st.text_input("Phone", value=pinfo.get("phone", ""))
            location = st.text_input("Location", value=pinfo.get("location", ""))
            linkedin = st.text_input("LinkedIn URL", value=pinfo.get("linkedin", ""))

        with st.expander("📝 Professional Summary", expanded=True):
            summary = st.text_area("Summary Statement", value=struct_content.get("summary", ""), height=100)

        with st.expander("⚡ Technical Skills", expanded=True):
            skills_raw = st.text_area(
                "Skills (Comma-separated)",
                value=", ".join(struct_content.get("skills", [])),
                help="e.g. Python, FastAPI, PostgreSQL, Docker, AWS"
            )

        with st.expander("💼 Work Experience", expanded=False):
            exp_list = struct_content.get("experience", [])
            exp_title = st.text_input("Job Title", value=exp_list[0].get("title", "") if exp_list else "")
            exp_comp = st.text_input("Company", value=exp_list[0].get("company", "") if exp_list else "")
            exp_bullets_raw = st.text_area(
                "Bullets (One per line)",
                value="\n".join(exp_list[0].get("bullets", [])) if exp_list else "",
                height=100
            )

        if st.button("💾 Save & Autosave Draft", type="primary", use_container_width=True):
            skills_list = [s.strip() for s in skills_raw.split(",") if s.strip()]
            bullets_list = [b.strip() for b in exp_bullets_raw.split("\n") if b.strip()]

            new_struct = {
                "personal_info": {
                    "full_name": full_name,
                    "email": email,
                    "phone": phone,
                    "location": location,
                    "linkedin": linkedin,
                },
                "summary": summary,
                "skills": skills_list,
                "experience": [
                    {
                        "title": exp_title,
                        "company": exp_comp,
                        "bullets": bullets_list,
                    }
                ] if (exp_title or exp_comp) else [],
                "education": struct_content.get("education", []),
                "projects": struct_content.get("projects", []),
                "certifications": struct_content.get("certifications", []),
                "achievements": struct_content.get("achievements", []),
            }

            try:
                api_client.update_resume_draft(
                    active_draft_id,
                    {
                        "title": draft_title,
                        "target_job_id": target_job_id,
                        "structured_content": new_struct,
                    }
                )
                st.success("Draft saved successfully!")
                st.rerun()
            except Exception as exc:
                st.error(f"Save failed: {exc}")

    # ── COLUMN 2: LIVE PREVIEW & VERSION CONTROL ──────────────────────────────
    with col_preview:
        st.subheader("📄 Live Resume Preview")
        raw_md = draft_data.get("raw_markdown", "")
        st.code(raw_md if raw_md else "# Your Resume Preview will appear here...", language="markdown")

        st.divider()
        st.subheader("📚 Versions & Export")
        ver_label = st.text_input("Snapshot Label", value=f"Version {draft_data.get('versions_count', 0) + 1}")
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            if st.button("📌 Save Snapshot", use_container_width=True):
                try:
                    api_client.create_resume_version(active_draft_id, label=ver_label)
                    st.success("Version snapshot saved!")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Version save failed: {exc}")

        with col_v2:
            export_url = f"{api_client.API_BASE}/api/v1/resume-builder/{active_draft_id}/export-pdf"
            st.markdown(f"[📥 Download PDF Export]({export_url})")

        # Version History List
        try:
            versions = api_client.list_resume_versions(active_draft_id)
            if versions:
                st.caption(f"**Saved Snapshots ({len(versions)})**")
                for v in versions:
                    v_col1, v_col2 = st.columns([3, 1])
                    with v_col1:
                        st.caption(f"v{v.get('version_number')}: {v.get('label')} ({v.get('created_at', '')[:10]})")
                    with v_col2:
                        if st.button("Restore", key=f"rst_{v.get('id')}"):
                            try:
                                api_client.restore_resume_version(active_draft_id, v.get("id"))
                                st.success("Restored version!")
                                st.rerun()
                            except Exception as exc:
                                st.error(f"Restore failed: {exc}")
        except Exception:
            pass

    # ── COLUMN 3: REAL-TIME ATS MATCH & AI ASSISTANT ──────────────────────────
    with col_ats:
        st.subheader("🎯 Real 6-Signal ATS Match")
        
        if not target_job_id:
            st.warning("Select a target job in the Editor to calculate live ATS match score.")
        else:
            if st.button("🔄 Recalculate Live ATS Match", type="primary", use_container_width=True):
                try:
                    match_res = api_client.calculate_resume_match(active_draft_id, {"job_id": target_job_id})
                    st.session_state[f"match_{active_draft_id}"] = match_res
                except Exception as exc:
                    st.error(f"Match calculation failed: {exc}")

            match_res = st.session_state.get(f"match_{active_draft_id}")
            if match_res:
                score = match_res.get("match_score", 0.0)
                st.metric("Overall 6-Signal ATS Score", f"{score}%", delta=match_res.get("score_delta"))

                st.caption("**6-Signal Breakdown (Production Weights)**")
                st.progress(match_res.get("required_coverage", 0.0) / 100.0, text=f"Required Skills Coverage (35%): {match_res.get('required_coverage')}%")
                st.progress(match_res.get("preferred_coverage", 0.0) / 100.0, text=f"Preferred Skills Coverage (15%): {match_res.get('preferred_coverage')}%")
                st.progress(match_res.get("semantic_similarity", 0.0) / 100.0, text=f"Semantic Similarity (25%): {match_res.get('semantic_similarity')}%")
                st.progress(match_res.get("lexical_similarity", 0.0) / 100.0, text=f"Lexical Token Overlap (10%): {match_res.get('lexical_similarity')}%")
                st.progress(match_res.get("experience_depth", 0.0) / 100.0, text=f"Experience Depth (10%): {match_res.get('experience_depth')}%")
                st.progress(match_res.get("domain_alignment", 0.0) / 100.0, text=f"Domain Alignment (5%): {match_res.get('domain_alignment')}%")

                st.markdown("#### 💡 Live Deterministic Feedback")
                for s in match_res.get("suggestions", []):
                    st.info(f"• {s}")

                if match_res.get("missing_required_skills"):
                    st.error(f"**Missing Required Skills:** {', '.join(match_res.get('missing_required_skills'))}")
                if match_res.get("missing_preferred_skills"):
                    st.warning(f"**Missing Preferred Skills:** {', '.join(match_res.get('missing_preferred_skills'))}")

        st.divider()
        st.subheader("🤖 AI Resume Assistant")
        st.caption("AI Generated — Verify Before Use")
        assist_type = st.selectbox(
            "AI Assistance Feature",
            ["summary", "bullet", "keywords", "review"],
            format_func=lambda x: {
                "summary": "✨ Professional Summary Generator",
                "bullet": "🎯 STAR Bullet Optimizer",
                "keywords": "🔑 ATS Keyword Suggestions",
                "review": "🔍 Resume Review & Tips",
            }[x]
        )

        if st.button("✨ Run AI Assistant", use_container_width=True):
            try:
                ai_res = api_client.ai_resume_builder_assist(
                    active_draft_id, assist_type=assist_type, target_job_id=target_job_id
                )
                st.session_state[f"ai_assist_{active_draft_id}"] = ai_res
            except Exception as exc:
                st.error(f"AI Assistant failed: {exc}")

        ai_out = st.session_state.get(f"ai_assist_{active_draft_id}")
        if ai_out:
            st.warning("⚠️ **AI Generated — Verify Before Use**")
            st.json(ai_out)
