"""
frontend/views/visualizer_3d.py

Phase 13: 3D Talent Visualizer Page View.
"""

from __future__ import annotations

import streamlit as st
from components.visualization_3d import render_3d_visualization


def render_visualizer_3d_page():
    st.title("🌐 3D Talent Intelligence Space")
    st.caption("Interactive 3D WebGL Constellation of Candidates & Real-Time Resume Pipeline Telemetry")

    st.markdown(
        """
        Subscribed to the **Real-Time WebSocket Pipeline Stream** (`ws://localhost:8000/ws/pipeline`). 
        As resumes are uploaded, extracted, classified, and matched in the backend, 3D nodes spawn and orbit towards candidate domain centers.
        """
    )

    render_3d_visualization(ws_url="ws://localhost:8000/ws/pipeline", height=600)
