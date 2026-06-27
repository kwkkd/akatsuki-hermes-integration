from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional

from api.main import get_bridge, _security

router = APIRouter()


class NoteResponse(BaseModel):
    id: str = ""
    path: str = ""
    title: str = ""
    content: str = ""
    tags: list[str] = []
    links: list[str] = []
    checksum: str = ""
    version: int = 0
    created: int = 0
    modified: int = 0
    source: str = ""


class NoteListResponse(BaseModel):
    notes: list[NoteResponse]


@router.get("/", response_model=NoteListResponse)
async def list_notes(prefix: str = "", credentials: HTTPAuthorizationCredentials = Depends(_security)):
    bridge = get_bridge()
    session = bridge.auth.validate_token(credentials.credentials)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid token")
    bridge.audit.log("list_notes", actor=session["username"], resource=prefix)
    notes = bridge.notes.list(prefix)
    return NoteListResponse(notes=[NoteResponse(**n.to_dict()) for n in notes])


@router.get("/{path:path}", response_model=NoteResponse)
async def read_note(path: str, credentials: HTTPAuthorizationCredentials = Depends(_security)):
    bridge = get_bridge()
    session = bridge.auth.validate_token(credentials.credentials)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid token")
    bridge.audit.log("read_note", actor=session["username"], resource=path)
    try:
        note = bridge.notes.read(path)
        if note is None:
            raise HTTPException(status_code=404, detail="Note not found")
        result = bridge.crypto.decrypt_note(note.to_dict())
        return NoteResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


class WriteNoteRequest(BaseModel):
    path: str
    title: Optional[str] = ""
    content: Optional[str] = ""
    tags: Optional[list[str]] = []
    links: Optional[list[str]] = []


@router.post("/")
async def write_note(req: WriteNoteRequest, credentials: HTTPAuthorizationCredentials = Depends(_security)):
    bridge = get_bridge()
    session = bridge.auth.validate_token(credentials.credentials)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid token")
    if not bridge.auth.check_permission(credentials.credentials, "note/write"):
        raise HTTPException(status_code=403, detail="Permission denied")
    bridge.audit.log("write_note", actor=session["username"], resource=req.path)
    from hermes_bridge.models.note_model import Note
    note = Note(path=req.path, title=req.title or "", content=req.content or "",
                tags=req.tags or [])
    note.source = "api"
    encrypted = bridge.crypto.encrypt_note({"content": note.content})
    note.content = encrypted.get("content", note.content)
    bridge.notes.write(note)
    return {"success": True, "path": req.path}


@router.delete("/{path:path}")
async def delete_note(path: str, credentials: HTTPAuthorizationCredentials = Depends(_security)):
    bridge = get_bridge()
    session = bridge.auth.validate_token(credentials.credentials)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid token")
    if not bridge.auth.check_permission(credentials.credentials, "note/delete"):
        raise HTTPException(status_code=403, detail="Permission denied")
    bridge.audit.log("delete_note", actor=session["username"], resource=path)
    try:
        bridge.notes.delete(path)
        return {"success": True, "path": path}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/search/", response_model=NoteListResponse)
async def search_notes(q: str = "", credentials: HTTPAuthorizationCredentials = Depends(_security)):
    bridge = get_bridge()
    session = bridge.auth.validate_token(credentials.credentials)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid token")
    if not q:
        return NoteListResponse(notes=[])
    bridge.audit.log("search_notes", actor=session["username"], details={"query": q})
    notes = bridge.notes.search(q)
    return NoteListResponse(notes=[NoteResponse(**n.to_dict()) for n in notes])


@router.get("/tags/")
async def list_tags(credentials: HTTPAuthorizationCredentials = Depends(_security)):
    bridge = get_bridge()
    session = bridge.auth.validate_token(credentials.credentials)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid token")
    tags = bridge.notes.list_tags()
    return {"tags": tags}


@router.get("/folders/")
async def list_folders(credentials: HTTPAuthorizationCredentials = Depends(_security)):
    bridge = get_bridge()
    session = bridge.auth.validate_token(credentials.credentials)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid token")
    folders = bridge.notes.list_folders()
    return {"folders": folders}