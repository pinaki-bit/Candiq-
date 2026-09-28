"""
backend/app/services/websocket_manager.py

Real-Time WebSocket Event Pipeline Connection Manager.
Broadcasts backend processing events to connected frontend clients (e.g., 3D Three.js Visualizer).

Supported Event Types:
  - resume.uploaded
  - resume.extracting
  - resume.nlp_extracted
  - resume.classified
  - resume.matched
  - pipeline.completed
  - pipeline.failed
"""

from __future__ import annotations

import datetime
import json
import logging
from typing import Any, Dict, List

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections and broadcasts events."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket client connected. Total active connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total active connections: {len(self.active_connections)}")

    async def send_personal_event(self, websocket: WebSocket, event_type: str, data: Dict[str, Any]) -> None:
        message = {
            "event_type": event_type,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "data": data,
        }
        try:
            await websocket.send_json(message)
        except Exception as exc:
            logger.warning(f"Failed to send personal WebSocket message: {exc}")

    async def broadcast_event(self, event_type: str, data: Dict[str, Any]) -> None:
        if not self.active_connections:
            return

        message = {
            "event_type": event_type,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "data": data,
        }

        disconnected_clients: List[WebSocket] = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as exc:
                logger.warning(f"Error broadcasting to client ({exc}). Marking for removal.")
                disconnected_clients.append(connection)

        for client in disconnected_clients:
            self.disconnect(client)


# Singleton instance
ws_manager = ConnectionManager()
