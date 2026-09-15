"""
AI Virtual Hospital (AI-VH) Main Backend Application
Serves REST endpoints and WebSocket live streaming for the 3D Hospital and Physician Review Dashboard.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import logging
import json

from .api.router import api_router
from .simulation.event_bus import event_bus
from .llm.medgemma_service import medgemma_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("AIVH-Server")

app = FastAPI(
    title="AI Virtual Hospital (AI-VH) Platform",
    description="Autonomous Multi-Agent Healthcare Simulation & Reinforcement Learning Platform",
    version="1.0.0"
)


@app.on_event("startup")
async def load_medgemma_model():
    """Loads MedGemma + DPO LoRA adapter onto the GPU at server startup so live
    comparative inference is actually reachable through the running app instead
    of only via standalone verification scripts."""
    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(None, medgemma_service.load_model)
        logger.info(
            f"MedGemma service ready: model_loaded={medgemma_service.model is not None}, "
            f"adapter_loaded={medgemma_service._is_adapter_loaded and medgemma_service.adapter_model is not None}"
        )
    except Exception as e:
        logger.error(f"MedGemma model failed to load at startup: {e}. Server will use the heuristic clinical engine.")

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.websocket("/ws/simulation")
async def websocket_simulation_endpoint(websocket: WebSocket):
    await websocket.accept()
    queue = asyncio.Queue(maxsize=100)
    event_bus.register_broadcast_queue(queue)
    logger.info("New WebSocket client connected to live simulation stream")

    try:
        # Send initial backlog of recent events
        recent = event_bus.get_recent_events(limit=20)
        for evt in recent:
            await websocket.send_text(json.dumps(evt.to_dict()))

        # Stream new events as they happen
        while True:
            event = await queue.get()
            await websocket.send_text(json.dumps(event.to_dict()))
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.warning(f"WebSocket streaming interrupted: {e}")
    finally:
        event_bus.unregister_broadcast_queue(queue)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=False)
