from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from core.websocket_manager import ws_manager
from core.logging import logger
from core.security import decode_access_token

router = APIRouter()


@router.websocket("/ws/conversaciones")
async def websocket_conversaciones(websocket: WebSocket, token: Optional[str] = Query(None)):
    if token:
        payload = decode_access_token(token)
        if not payload:
            logger.warning("[WS] Conexión WebSocket rechazada por token inválido o expirado.")
            await websocket.close(code=1008)
            return

    await ws_manager.connect(websocket)
    try:
        await websocket.send_json({
            "type": "connection_established",
            "message": "Conectado al canal en tiempo real de Consorcio Seliz"
        })
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"[WS] Error en sesión websocket: {e}")
        ws_manager.disconnect(websocket)
