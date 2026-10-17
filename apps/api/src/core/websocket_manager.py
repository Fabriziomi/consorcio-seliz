from typing import Set, Dict, Any
from fastapi import WebSocket
from core.logging import logger
import json


class WebSocketManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"[WS] Nueva conexión activa. Conexiones totales: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"[WS] Conexión cerrada. Conexiones restantes: {len(self.active_connections)}")

    async def broadcast(self, event_type: str, payload: Dict[str, Any]):
        if not self.active_connections:
            return

        message = {
            "type": event_type,
            "data": payload
        }
        dead_connections = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"[WS] Error enviando a cliente WebSocket: {e}")
                dead_connections.add(connection)

        for dead in dead_connections:
            self.active_connections.discard(dead)


ws_manager = WebSocketManager()
