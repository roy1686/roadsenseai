import sys
from pathlib import Path

# Ensure backend/api is in sys.path for seamless execution from root or backend
api_dir = str(Path(__file__).resolve().parent.parent)
if api_dir not in sys.path:
    sys.path.insert(0, api_dir)

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.api.endpoints import router
from app.config import settings
from app.db.session import init_db

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="ROADSense AI — Production Autonomous Road Infrastructure Vision Intelligence Platform",
    version=settings.VERSION
)

# CORS Middleware with production protection
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount primary API v1 and legacy compatibility alias
app.include_router(router, prefix=settings.API_V1_STR)
app.include_router(router, prefix=settings.LEGACY_API_STR)

@app.get("/health")
def root_health():
    return {
        "status": "healthy",
        "service": "ROADSense AI Production Backend",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT
    }

@app.get("/health/ready")
def root_readiness():
    return {"status": "ready"}

# Mount static frame previews if available
dist_frames = Path(__file__).resolve().parents[4] / "frontend" / "dist" / "frames"
dist_frames.mkdir(parents=True, exist_ok=True)
app.mount("/frames", StaticFiles(directory=str(dist_frames)), name="frames")

from fastapi import WebSocket, WebSocketDisconnect

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            event = data.get("event")
            if not event:
                await websocket.send_json({"error": "missing event type"})
            elif event == "ping":
                await websocket.send_json({"event": "pong"})
            else:
                await websocket.send_json({"error": f"unknown event: {event}"})
    except WebSocketDisconnect:
        pass
    except Exception:
        try:
            await websocket.close()
        except Exception:
            pass

@app.on_event("startup")
def startup_event():
    print(f"[STARTUP] Initializing {settings.PROJECT_NAME} v{settings.VERSION} [{settings.ENVIRONMENT}]...")
    init_db()
    print("[STARTUP] Database tables verified & recovery routine completed.")
