"""FastAPI server for AKATSUKI."""

import os
import asyncio
import httpx
import uvicorn
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..core.config import CONFIG
from ..agents import ALL_AGENTS


OLLAMA_BASE = "http://localhost:11434"
ollama_available = False


async def probe_ollama():
    global ollama_available
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{OLLAMA_BASE}/api/tags")
            ollama_available = resp.status_code == 200
    except Exception:
        ollama_available = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    await probe_ollama()
    yield


app = FastAPI(title="AKATSUKI API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    api_key = CONFIG.api.api_key
    if api_key:
        header_key = request.headers.get("Authorization", "").removeprefix("Bearer ")
        if header_key != api_key:
            return JSONResponse(status_code=401, content={"detail": "Invalid API key"})
    return await call_next(request)


@app.get("/health")
async def health():
    return {"status": "ok", "ollama": ollama_available}


@app.get("/v1/models")
async def list_models():
    if not ollama_available:
        raise HTTPException(503, "Ollama not available")
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(f"{OLLAMA_BASE}/api/tags")
        return resp.json()


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    if not ollama_available:
        raise HTTPException(503, "Ollama not available")
    body = await request.json()
    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(f"{OLLAMA_BASE}/v1/chat/completions", json=body)
        if resp.status_code != 200:
            raise HTTPException(502, "Ollama upstream error")
        return resp.json()


@app.get("/v1/team/status")
async def team_status():
    from ..agents import get_team_status
    return get_team_status()


@app.get("/v1/team/info")
async def team_info():
    from ..agents import get_team_info
    return get_team_info()


@app.get("/v1/tools")
async def list_tools():
    return {
        "tools": [{"name": name, "description": agent.description} for name, agent in ALL_AGENTS.items()]
    }


@app.get("/v1/dept/{name}")
async def dept_info(name: str):
    agent = ALL_AGENTS.get(name)
    if not agent:
        raise HTTPException(404, f"Department '{name}' not found")
    return {
        "name": name,
        "description": agent.description,
        "capabilities": agent.capabilities,
    }


def start_server(host="127.0.0.1", port=8000, reload=False):
    uvicorn.run("src.akatsuki.api.server:app", host=host, port=port, reload=reload)
