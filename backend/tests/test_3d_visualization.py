"""
backend/tests/test_3d_visualization.py

Unit test suite for Phase 13: 3D AI Visualization Integration.
"""

import sys
import os
from pathlib import Path

# Add project root and frontend to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
frontend_dir = root_dir / "frontend"
if str(frontend_dir) not in sys.path:
    sys.path.insert(0, str(frontend_dir))

from components.visualization_3d import get_3d_visualization_html


def test_3d_visualization_html_generation():
    ws_url = "ws://127.0.0.1:8000/ws/pipeline"
    html = get_3d_visualization_html(ws_url=ws_url)

    assert "<title>3D AI Candidate Talent Core</title>" in html
    assert ws_url in html
    assert "three.min.js" in html
    assert "OrbitControls.js" in html
    assert 'id="fallback-notice"' in html
    assert 'id="canvas-container"' in html
    assert "spawnPipelineParticle" in html
    assert "triggerSimulatedEvent" in html


def test_3d_visualization_websocket_url_injection():
    custom_ws = "wss://custom-domain.com/ws/pipeline"
    html = get_3d_visualization_html(ws_url=custom_ws)
    assert custom_ws in html
