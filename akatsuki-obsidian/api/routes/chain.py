import json
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel

from api.main import get_bridge, _security

logger = logging.getLogger("akatsuki.api.chain")
router = APIRouter()

PLAYBOOKS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "skills" / "security" / "akatsuki" / "playbooks"


class ExecuteChainRequest(BaseModel):
    target: str
    playbook: str = ""
    objective: str = "Full penetration test"
    options: dict = {}


@router.get("/playbooks")
async def list_playbooks():
    playbooks = []
    if PLAYBOOKS_DIR.exists():
        for f in sorted(PLAYBOOKS_DIR.glob("*.yaml")):
            playbooks.append(f.stem)
    return {"playbooks": playbooks}


@router.post("/execute")
async def execute_chain(req: ExecuteChainRequest,
                         credentials: HTTPAuthorizationCredentials = Depends(_security)):
    bridge = get_bridge()
    session = bridge.auth.validate_token(credentials.credentials)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid token")
    try:
        import importlib
        mod = importlib.import_module("tools.akatsuki_chain")
        result = mod.akatsuki_chain(
            "execute",
            target=req.target,
            objective=req.objective,
            playbook=req.playbook or None,
        )
        try:
            return json.loads(result)
        except Exception:
            return {"result": str(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/build")
async def build_chain(req: ExecuteChainRequest,
                       credentials: HTTPAuthorizationCredentials = Depends(_security)):
    bridge = get_bridge()
    session = bridge.auth.validate_token(credentials.credentials)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid token")
    try:
        import importlib
        mod = importlib.import_module("tools.akatsuki_chain")
        result = mod.akatsuki_chain("build", target=req.target, objective=req.objective)
        try:
            return json.loads(result)
        except Exception:
            return {"result": str(result)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


_ws_clients: dict[str, list] = {}


@router.websocket("/ws/{client_id}")
async def chain_websocket(ws: WebSocket, client_id: str):
    await ws.accept()
    if client_id not in _ws_clients:
        _ws_clients[client_id] = []
    _ws_clients[client_id].append(ws)
    try:
        while True:
            data = await ws.receive_text()
            msg = json.loads(data)
            if msg.get("action") == "execute":
                try:
                    import importlib
                    mod = importlib.import_module("tools.akatsuki_chain")
                    result = mod.akatsuki_chain("execute", target=msg.get("target", ""),
                                                objective=msg.get("objective", ""))
                    await ws.send_text(json.dumps({"type": "result", "data": json.loads(result)}))
                except Exception as e:
                    await ws.send_text(json.dumps({"type": "error", "message": str(e)}))
    except WebSocketDisconnect:
        if client_id in _ws_clients:
            _ws_clients[client_id] = [c for c in _ws_clients[client_id] if c != ws]