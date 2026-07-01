import json
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from connection.manager import manager
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent_ws_backend")
app = FastAPI(title="Agent WebSocket Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}
    
@app.websocket("/ws/agent")
async def agent_ws(websocket: WebSocket):
    await websocket.accept()
    logger.info(f"Client connected, session_id={session_id}")
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                payload = json.loads(raw)
                user_message = payload["message"]
            except (json.JSONDecodeError, KeyError):
                await websocket.send_json({"type": "error", "data": {"message": "Expected JSON: {\"message\": \"...\"}"}})
                continue
            await manager.run_agent(websocket, session_id, user_message)

    except WebSocketDisconnect:
        logger.info(f"Client disconnected, session_id={session_id}")
        await manager.cancel_active_run(session_id)
