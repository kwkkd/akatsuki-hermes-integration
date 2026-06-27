import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from hermes_bridge.bridge.agent_bridge import AgentBridge
from hermes_bridge.bridge.auth import AuthManager
from hermes_bridge.bridge.audit import AuditLogger

logger = logging.getLogger("akatsuki.api")

try:
    from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    from fastapi.staticfiles import StaticFiles
    from pydantic import BaseModel
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False
    FastAPI = object

app = FastAPI(
    title="AKATSUKI API",
    description="AKATSUKI Red Team Operations Framework REST API",
    version="1.0.0",
) if HAS_FASTAPI else object()

_bridge: Optional[AgentBridge] = None
_security = HTTPBearer(auto_error=False) if HAS_FASTAPI else None


def get_bridge() -> AgentBridge:
    global _bridge
    if _bridge is None:
        vault = os.environ.get("AKATSUKI_VAULT", str(Path.home() / "akatsuki-vault"))
        _bridge = AgentBridge(vault)
    return _bridge


if HAS_FASTAPI:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from fastapi import APIRouter
    from api.routes import notes, tools, chain, auth as auth_routes, dashboard as dashboard_routes

    app.include_router(auth_routes.router)
    app.include_router(notes.router)
    app.include_router(tools.router)
    app.include_router(chain.router)
    app.include_router(dashboard_routes.router)

    dashboard_dist = Path(__file__).resolve().parent.parent / "dashboard" / "dist"
    if dashboard_dist.exists():
        app.mount("/", StaticFiles(directory=str(dashboard_dist), html=True), name="dashboard")

    @app.on_event("startup")
    async def startup():
        bridge = get_bridge()
        await bridge.start()
        logger.info("AKATSUKI API server started")

    @app.on_event("shutdown")
    async def shutdown():
        bridge = get_bridge()
        await bridge.stop()
        logger.info("AKATSUKI API server stopped")

    @app.get("/api/health", tags=["system"])
    @app.get("/api/healthz")
    async def healthz():
        return {"status": "ok"}

    @app.get("/api/health", tags=["system"])
    async def health():
        bridge = get_bridge()
        return {
            "status": "running",
            "vault": bridge.vault_path,
            "auth_enabled": bridge.auth is not None,
            "encryption_enabled": bridge.crypto.is_enabled(),
            "audit_enabled": True,
        }


def run(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    if not HAS_FASTAPI:
        logger.error("FastAPI not installed. Install with: pip install fastapi uvicorn")
        return
    import uvicorn
    uvicorn.run("api.main:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    run()