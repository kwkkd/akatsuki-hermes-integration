import importlib
import json
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel

from api.main import get_bridge, _security

logger = logging.getLogger("akatsuki.api.tools")
router = APIRouter()

TOOLS_DIR = Path(__file__).resolve().parent.parent.parent.parent / "tools"


def _discover_tools() -> list[str]:
    tools = []
    if TOOLS_DIR.exists():
        for f in sorted(TOOLS_DIR.glob("akatsuki_*.py")):
            tools.append(f.stem)
    return tools


class ExecuteToolRequest(BaseModel):
    tool: str
    params: dict = {}


@router.get("/")
async def list_tools():
    tools = _discover_tools()
    return {"tools": tools, "count": len(tools)}


@router.post("/execute")
async def execute_tool(req: ExecuteToolRequest,
                        credentials: HTTPAuthorizationCredentials = Depends(_security)):
    bridge = get_bridge()
    session = bridge.auth.validate_token(credentials.credentials)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid token")
    allowed_roles = {"tool/recon", "tool/payload", "tool/evasion", "tool/c2",
                     "tool/vuln", "tool/chain", "tool/report", "tool/dept"}
    perm = f"tool/{req.tool.replace('akatsuki_', '')}"
    if perm not in allowed_roles and session.get("role") != "admin":
        if not bridge.auth.check_permission(credentials.credentials, perm):
            raise HTTPException(status_code=403, detail=f"Permission denied for {req.tool}")
    full_name = f"tools.{req.tool}"
    try:
        mod = importlib.import_module(full_name)
    except ImportError as e:
        raise HTTPException(status_code=404, detail=f"Tool not found: {req.tool}")
    handler = getattr(mod, req.tool, None)
    if not handler:
        raise HTTPException(status_code=500, detail=f"No handler in {req.tool}")
    try:
        result = handler(**req.params)
        try:
            return json.loads(result)
        except (TypeError, json.JSONDecodeError):
            return {"result": str(result)}
    except Exception as e:
        logger.exception(f"Tool execution error: {req.tool}")
        raise HTTPException(status_code=500, detail=str(e))


class BulkExecuteRequest(BaseModel):
    tools: list[ExecuteToolRequest]
    parallel: bool = False


@router.post("/bulk")
async def bulk_execute(req: BulkExecuteRequest,
                        credentials: HTTPAuthorizationCredentials = Depends(_security)):
    bridge = get_bridge()
    session = bridge.auth.validate_token(credentials.credentials)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid token")
    results = {}
    for tool_req in req.tools:
        try:
            mod = importlib.import_module(f"tools.{tool_req.tool}")
            handler = getattr(mod, tool_req.tool, None)
            if handler:
                result = handler(**tool_req.params)
                try:
                    results[tool_req.tool] = json.loads(result)
                except Exception:
                    results[tool_req.tool] = {"result": str(result)}
            else:
                results[tool_req.tool] = {"error": "No handler"}
        except Exception as e:
            results[tool_req.tool] = {"error": str(e)}
    return {"results": results, "count": len(results)}