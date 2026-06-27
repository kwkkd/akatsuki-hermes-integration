from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional

from api.main import get_bridge, _security

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    username: str
    role: str


class ValidateResponse(BaseModel):
    valid: bool
    username: Optional[str] = None
    role: Optional[str] = None


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest):
    bridge = get_bridge()
    token = bridge.auth.authenticate(req.username, req.password)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user = bridge.auth.get_user(req.username)
    return LoginResponse(token=token, username=req.username, role=user.role if user else "viewer")


@router.get("/validate", response_model=ValidateResponse)
async def validate(credentials: HTTPAuthorizationCredentials = Depends(_security)):
    bridge = get_bridge()
    if not credentials:
        raise HTTPException(status_code=401, detail="No token provided")
    session = bridge.auth.validate_token(credentials.credentials)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return ValidateResponse(valid=True, username=session["username"], role=session["role"])


@router.get("/users")
async def list_users(credentials: HTTPAuthorizationCredentials = Depends(_security)):
    bridge = get_bridge()
    session = bridge.auth.validate_token(credentials.credentials)
    if not session or session.get("role") not in ("admin",):
        raise HTTPException(status_code=403, detail="Admin access required")
    return {"users": bridge.auth.list_users()}


class AuditQuery(BaseModel):
    filters: Optional[dict] = None
    limit: int = 100
    offset: int = 0


@router.post("/audit/query")
async def query_audit(req: AuditQuery, credentials: HTTPAuthorizationCredentials = Depends(_security)):
    bridge = get_bridge()
    session = bridge.auth.validate_token(credentials.credentials)
    if not session or session.get("role") not in ("admin", "operator"):
        raise HTTPException(status_code=403, detail="Access denied")
    results = bridge.audit.query(req.filters, req.limit, req.offset)
    return {"results": results, "count": len(results)}


@router.get("/audit/stats")
async def audit_stats(credentials: HTTPAuthorizationCredentials = Depends(_security)):
    bridge = get_bridge()
    session = bridge.auth.validate_token(credentials.credentials)
    if not session or session.get("role") not in ("admin",):
        raise HTTPException(status_code=403, detail="Admin access required")
    return {
        "by_event": bridge.audit.count_by_event(),
        "by_status": bridge.audit.count_by_status(),
    }