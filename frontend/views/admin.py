from __future__ import annotations

import streamlit as st
from services.api_client import (
    APIError, create_user, list_users, list_model_versions,
    update_user, activate_model_version, sync_model_versions,
)


def render_admin():
    user = st.session_state.get("user") or {}
    if user.get("role") != "admin":
        st.error("Access denied. Admin role required.")
        return

    st.title("⚙️ Admin Panel")

    tab_users, tab_models = st.tabs(["👥 User Management", "🤖 Model Versions"])

    with tab_users:
        _render_users()

    with tab_models:
        _render_models()


def _render_users():
    st.subheader("User Accounts")

    try:
        users = list_users()
    except APIError as e:
        st.error(f"Failed to load users: {e.detail}")
        return

    # Existing users table
    for u in users:
        status_icon = "🟢" if u["is_active"] else "🔴"
        role_icon = {"admin": "👑", "hr": "🧑‍💼", "readonly": "👁️"}.get(u["role"], "")
        with st.expander(
            f"{status_icon} {role_icon} {u.get('full_name') or u['email']} [{u['role']}]"
        ):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Email:** {u['email']}")
                st.write(f"**Created:** {u['created_at'][:10]}")
            with col2:
                new_role = st.selectbox(
                    "Role",
                    ["admin", "hr", "readonly"],
                    index=["admin", "hr", "readonly"].index(u["role"]),
                    key=f"role_{u['id']}",
                )
                new_active = st.toggle("Active", value=u["is_active"], key=f"active_{u['id']}")
            with col3:
                if st.button("Update", key=f"upd_{u['id']}"):
                    try:
                        update_user(u["id"], {"role": new_role, "is_active": new_active})
                        st.success("User updated.")
                        st.rerun()
                    except APIError as e:
                        st.error(f"Update failed: {e.detail}")

    st.divider()
    st.subheader("Create New User")
    with st.form("create_user_form"):
        email = st.text_input("Email *")
        password = st.text_input("Password *", type="password")
        full_name = st.text_input("Full Name")
        role = st.selectbox("Role", ["hr", "admin", "readonly"])
        submitted = st.form_submit_button("Create User", type="primary")

    if submitted:
        if not email or not password:
            st.error("Email and password are required.")
        elif len(password) < 8:
            st.error("Password must be at least 8 characters.")
        else:
            try:
                create_user({
                    "email": email,
                    "password": password,
                    "full_name": full_name or None,
                    "role": role,
                })
                st.success(f"User '{email}' created with role '{role}'.")
                st.rerun()
            except APIError as e:
                st.error(f"Failed to create user: {e.detail}")


def _render_models():
    st.subheader("Trained Model Versions")
    st.caption(
        "Train a model using `ml/scripts/train_model.py`, then register it here. "
        "Only the active model is used for classification."
    )
    # Sync button — always available
    col_sync, _ = st.columns([1, 2])
    with col_sync:
        if st.button("🔄 Sync Models from Disk", use_container_width=True):
            try:
                result = sync_model_versions()
                registered = result.get("registered", 0)
                skipped = result.get("skipped", 0)
                if registered > 0:
                    st.success(f"✅ Registered {registered} new model(s). Skipped {skipped} already-registered.")
                else:
                    st.info(f"No new models found. {skipped} already registered.")
                if result.get("errors"):
                    st.warning("Sync warnings: " + "; ".join(result["errors"]))
                st.rerun()
            except APIError as e:
                st.error(f"Sync failed: {e.detail}")

    st.divider()

    try:
        versions = list_model_versions()
    except APIError as e:
        st.error(f"Failed to load model versions: {e.detail}")
        return

    if not versions:
        st.info(
            "No model versions registered yet.\n\n"
            "Train a model using `ml/scripts/train_model.py`, then click **Sync Models from Disk** above."
        )
        return

    for v in versions:
        active_badge = "🟢 **ACTIVE**" if v["is_active"] else "⚪ Inactive"
        macro_f1 = v.get("test_macro_f1")
        f1_label = f"{macro_f1:.4f}" if macro_f1 is not None else "N/A"
        with st.expander(
            f"{active_badge} — v{v['version_tag']} | macro-F1: {f1_label}"
        ):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Macro F1", f"{macro_f1:.4f}" if macro_f1 is not None else "N/A")
            with c2:
                wf1 = v.get("test_weighted_f1")
                st.metric("Weighted F1", f"{wf1:.4f}" if wf1 is not None else "N/A")
            with c3:
                st.metric("Training Samples", v.get("training_samples", "N/A"))

            st.write(f"**Artifact:** `{v.get('artifact_filename', 'N/A')}`")
            if v.get("deployed_at"):
                st.write(f"**Deployed:** {v['deployed_at'][:19]}")
            if v.get("description"):
                st.caption(v["description"])

            if not v["is_active"]:
                if st.button("🚀 Activate this Model", key=f"activate_{v['id']}", type="primary"):
                    try:
                        activate_model_version(v["id"])
                        st.success(f"Model v{v['version_tag']} is now active. Classification service cache cleared.")
                        st.rerun()
                    except APIError as e:
                        st.error(f"Failed to activate: {e.detail}")
            else:
                st.success("✅ This model is currently active and serving predictions.")

