from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from core.websocket_manager import ws_manager
from core.logging import logger

router = APIRouter()


@router.websocket("/ws/conversaciones")
async def websocket_conversaciones(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        await websocket.send_json({
            "type": "connection_established",
            "message": "Conectado al canal en tiempo real de Consorcio Seliz"
        })
        while True:
            # Mantener conexión viva y procesar pings si el cliente los envía
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"[WS] Error en sesión websocket: {e}")
        ws_manager.disconnect(websocket)
