"""
backend/tests/test_websocket.py

Unit test suite for Phase 12: Real-Time WebSocket Event Pipeline System.
"""

import pytest
from app.services.websocket_manager import ConnectionManager, ws_manager


@pytest.mark.asyncio
async def test_connection_manager_broadcast():
    manager = ConnectionManager()
    assert len(manager.active_connections) == 0
    # Broadcasting to 0 connections should execute cleanly without error
    await manager.broadcast_event("test.event", {"status": "ok"})


def test_websocket_pipeline_endpoint(client):
    with client.websocket_connect("/ws/pipeline") as websocket:
        websocket.send_text("ping")
        response = websocket.receive_text()
        assert response == "pong"
