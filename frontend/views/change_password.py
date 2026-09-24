"""
frontend/views/change_password.py

Change password page — shown to users flagged with must_change_password,
or accessible anytime via the sidebar.
"""

from __future__ import annotations

import streamlit as st
from services.api_client import APIError, change_password


def render_change_password():
    st.title("🔑 Change Password")

    user = st.session_state.get("user") or {}
    if user.get("must_change_password"):
        st.warning(
            "⚠️ You are using the default password. "
            "You must set a new password before you can use the system."
        )

    st.caption("Enter your current password and a new password (minimum 8 characters).")

    with st.form("change_password_form"):
        current_pw = st.text_input("Current Password", type="password")
        new_pw = st.text_input("New Password", type="password")
        confirm_pw = st.text_input("Confirm New Password", type="password")
        submitted = st.form_submit_button("Update Password", type="primary", use_container_width=True)

    if submitted:
        if not current_pw or not new_pw or not confirm_pw:
            st.error("All fields are required.")
            return
        if len(new_pw) < 8:
            st.error("New password must be at least 8 characters.")
            return
        if new_pw != confirm_pw:
            st.error("New passwords do not match.")
            return
        if current_pw == new_pw:
            st.error("New password must be different from current password.")
            return

        with st.spinner("Updating password…"):
            try:
                result = change_password(current_pw, new_pw)
                # Backend returns a new token — update session
                if result.get("access_token"):
                    st.session_state["access_token"] = result["access_token"]
                # Clear the must_change_password flag in session
                if st.session_state.get("user"):
                    st.session_state["user"]["must_change_password"] = False
                st.success("✅ Password changed successfully! Redirecting to dashboard…")
                st.session_state["page"] = "dashboard"
                st.rerun()
            except APIError as e:
                if e.status_code == 401:
                    st.error("Current password is incorrect.")
                elif e.status_code == 422:
                    st.error(f"Validation error: {e.detail}")
                else:
                    st.error(f"Failed to change password: {e.detail}")
