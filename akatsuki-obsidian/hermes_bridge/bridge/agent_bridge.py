import asyncio
import json
import os
import logging
from typing import Any, Optional

logger = logging.getLogger("akatsuki.bridge")

DEFAULT_SOCKET = os.path.expanduser(
    "~/.local/share/hermes/akatsuki-obsidian.sock"
)
DEFAULT_WS_PORT = 18749

import sys

try:
    if sys.platform != "win32":
        from hermes_bridge.ipc.server import UnixSocketServer
        HAS_UNIX = True
    else:
        HAS_UNIX = False
except Exception:
    HAS_UNIX = False

try:
    from hermes_bridge.ipc.ws_server import WebSocketServer
    HAS_WS = True
except Exception:
    HAS_WS = False

from hermes_bridge.sync.sync_manager import SyncManager
from hermes_bridge.models.note_model import NoteModel


class AgentBridge:
    def __init__(self, vault_path: str, socket_path: str = DEFAULT_SOCKET, ws_port: int = DEFAULT_WS_PORT):
        self.vault_path = vault_path
        self.socket_path = socket_path
        self.ws = WebSocketServer(port=ws_port) if HAS_WS else None
        self.unix = UnixSocketServer(socket_path) if HAS_UNIX else None
        self.sync = SyncManager(vault_path)
        self.notes = NoteModel(vault_path)
        self._running = False

    async def start(self):
        self._register_handlers()
        if self.unix:
            await self.unix.start()
        if self.ws:
            await self.ws.start()
        self.sync.start()
        self._running = True
        logger.info("AKATSUKI bridge started")

    async def stop(self):
        self._running = False
        self.sync.stop()
        if self.unix:
            await self.unix.stop()
        if self.ws:
            await self.ws.stop()
        logger.info("AKATSUKI bridge stopped")

    def _broadcast(self, method: str, params: dict):
        async def _do():
            if self.unix:
                await self.unix.broadcast(method, params)
            if self.ws:
                await self.ws.broadcast(method, params)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(_do())
        except RuntimeError:
            pass

    def _register_handlers(self):
        h = {
            "note/read": self._handle_read_note,
            "note/write": self._handle_write_note,
            "note/list": self._handle_list_notes,
            "note/search": self._handle_search_notes,
            "note/delete": self._handle_delete_note,
            "folder/list": self._handle_list_folders,
            "tags/list": self._handle_list_tags,
            "ping": self._handle_ping,
        }
        for method, handler in h.items():
            if self.unix:
                self.unix.on(method, handler)
            if self.ws:
                self.ws.on(method, handler)

    async def _handle_read_note(self, params: dict) -> dict:
        path = params.get("path", "")
        note = self.notes.read(path)
        if note is None:
            raise FileNotFoundError(f"Note not found: {path}")
        return note.to_dict()

    async def _handle_write_note(self, params: dict) -> dict:
        from ..models.note_model import Note
        note_data = params.get("note", {})
        note = Note(
            id=note_data.get("id", ""),
            path=note_data.get("path", ""),
            title=note_data.get("title", ""),
            content=note_data.get("content", ""),
            tags=note_data.get("tags", []),
            links=note_data.get("links", []),
            frontmatter=note_data.get("frontmatter", {}),
            checksum=note_data.get("checksum", ""),
            version=note_data.get("version", 0),
            created=note_data.get("created", 0),
            modified=note_data.get("modified", 0),
            source="hermes",
        )
        note.source = "hermes"
        result = self.notes.write(note)
        self._broadcast("note/changed", {"path": note.path, "action": "write"})
        return result

    async def _handle_list_notes(self, params: dict) -> dict:
        prefix = params.get("prefix", "")
        notes = self.notes.list(prefix)
        return {"notes": [n.to_dict() for n in notes]}

    async def _handle_search_notes(self, params: dict) -> dict:
        query = params.get("query", "")
        notes = self.notes.search(query)
        return {"notes": [n.to_dict() for n in notes]}

    async def _handle_delete_note(self, params: dict) -> dict:
        path = params.get("path", "")
        self.notes.delete(path)
        await self.server.broadcast("note/changed", {"path": path, "action": "delete"})
        return {"deleted": True, "path": path}

    async def _handle_list_folders(self, params: dict) -> dict:
        folders = self.notes.list_folders()
        return {"folders": folders}

    async def _handle_list_tags(self, params: dict) -> dict:
        tags = self.notes.list_tags()
        return {"tags": tags}

    async def _handle_ping(self, params: dict) -> dict:
        return {"pong": True, "vault": self.vault_path}

    async def execute_tool(self, tool_name: str, params: dict) -> dict:
        method_map = {
            "obsidian_read": "note/read",
            "obsidian_write": "note/write",
            "obsidian_list": "note/list",
            "obsidian_search": "note/search",
            "obsidian_delete": "note/delete",
            "obsidian_folders": "folder/list",
            "obsidian_tags": "tags/list",
        }
        method = method_map.get(tool_name)
        if not method:
            return {"error": f"Unknown tool: {tool_name}"}
        handler = {
            "note/read": self._handle_read_note,
            "note/write": self._handle_write_note,
            "note/list": self._handle_list_notes,
            "note/search": self._handle_search_notes,
            "note/delete": self._handle_delete_note,
            "folder/list": self._handle_list_folders,
            "tags/list": self._handle_list_tags,
        }.get(method)
        if handler:
            return await handler(params)
        return {"error": f"No handler for {method}"}
