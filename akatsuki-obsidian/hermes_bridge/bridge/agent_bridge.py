import asyncio
import json
import os
import logging
from typing import Any, Optional

logger = logging.getLogger("akatsuki.bridge")

DEFAULT_SOCKET = os.path.expanduser("~/.local/share/hermes/akatsuki-obsidian.sock")
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
from hermes_bridge.sync.server import SyncServer
from hermes_bridge.notifications.manager import NotificationManager, get_manager as get_notif_manager
from hermes_bridge.models.note_model import NoteModel
from hermes_bridge.bridge.auth import AuthManager
from hermes_bridge.bridge.audit import AuditLogger
from hermes_bridge.models.crypto import VaultEncryption


def _load_full_config() -> dict:
    cfg_path = os.environ.get(
        "AKATSUKI_CONFIG",
        os.path.join(os.path.dirname(__file__), "..", "..", "akatsuki.yaml"),
    )
    if os.path.exists(cfg_path):
        try:
            import yaml
            with open(cfg_path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception:
            pass
    return {}


def _sanitize_path(path: str) -> str:
    clean = path.replace("\\", "/").strip()
    clean = clean.lstrip("/").rstrip("/")
    if ".." in clean.split("/"):
        raise ValueError("Path traversal detected")
    return clean


def _validate_path(path: str) -> str:
    if not path:
        raise ValueError("path is required")
    if len(path) > 1024:
        raise ValueError("path too long")
    if path.startswith("/") or path.startswith("\\"):
        raise ValueError("path must be relative")
    return path


class AgentBridge:
    def __init__(self, vault_path: str, socket_path: str = DEFAULT_SOCKET,
                 ws_port: int = DEFAULT_WS_PORT):
        self.vault_path = vault_path
        self.socket_path = socket_path
        self.ws = WebSocketServer(port=ws_port) if HAS_WS else None
        self.unix = UnixSocketServer(socket_path) if HAS_UNIX else None
        self.sync = SyncManager(vault_path)
        self.notes = NoteModel(vault_path)
        self._running = False
        self._config = _load_full_config()
        auth_cfg = self._config.get("auth", {})
        self.auth = AuthManager(auth_cfg)
        self.auth.from_config(auth_cfg)
        audit_cfg = self._config.get("audit", {})
        self.audit = AuditLogger(
            log_dir=audit_cfg.get("log_dir", "logs/audit"),
            max_bytes=audit_cfg.get("max_bytes", 10485760),
            backup_count=audit_cfg.get("backup_count", 5),
        )
        enc_cfg = self._config.get("encryption", {})
        self.crypto = VaultEncryption(enc_cfg.get("master_key", ""))
        self.sync_server = SyncServer(
            node_id=os.environ.get("AKATSUKI_NODE_ID", "akatsuki-node-1"),
            vault_path=vault_path,
        )
        notif_cfg = self._config.get("notifications", {})
        self.notifications = get_notif_manager()
        tg_cfg = notif_cfg.get("telegram", {})
        if tg_cfg.get("bot_token"):
            self.notifications.telegram.configure(
                tg_cfg["bot_token"], tg_cfg.get("chat_id", "")
            )
        wp_cfg = notif_cfg.get("webpush", {})
        if wp_cfg.get("public_key"):
            self.notifications.init_webpush(
                wp_cfg.get("public_key", ""),
                wp_cfg.get("private_key", ""),
                wp_cfg.get("email", "akatsuki@localhost"),
            )

    def _get_token(self, params: dict) -> str:
        return params.get("token") or params.get("auth_token") or ""

    def _require_permission(self, params: dict, permission: str):
        token = self._get_token(params)
        if not self.auth.check_permission(token, permission):
            raise PermissionError(f"Permission denied: {permission} required")

    def _audit(self, event: str, params: dict, status: str = "success",
               resource: str = "", details: dict = None):
        if not self._config.get("audit", {}).get("enabled", True):
            return
        token = self._get_token(params)
        session = self.auth.validate_token(token)
        actor = session["username"] if session else "anonymous"
        self.audit.log(
            event=event,
            actor=actor,
            resource=resource,
            action=event,
            status=status,
            details=details,
            ip=params.get("_ip", ""),
        )

    async def start(self):
        self._register_handlers()
        if self.unix:
            await self.unix.start()
        if self.ws:
            await self.ws.start()
        self.sync.start()
        try:
            await self.sync_server.start()
        except Exception as e:
            logger.warning(f"Sync server start failed: {e}")
        self._running = True
        enc_status = "enabled" if self.crypto.is_enabled() else "disabled"
        aud_status = "enabled" if self._config.get("audit", {}).get("enabled", True) else "disabled"
        logger.info(f"AKATSUKI bridge started (encryption={enc_status}, audit={aud_status})")

    async def stop(self):
        self._running = False
        self.sync.stop()
        try:
            await self.sync_server.stop()
        except Exception:
            pass
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
            "auth/login": self._handle_auth_login,
            "auth/validate": self._handle_auth_validate,
            "ping": self._handle_ping,
        }
        for method, handler in h.items():
            if self.unix:
                self.unix.on(method, handler)
            if self.ws:
                self.ws.on(method, handler)

    async def _handle_auth_login(self, params: dict) -> dict:
        username = params.get("username", "")
        password = params.get("password", "")
        token = self.auth.authenticate(username, password)
        if token:
            self._audit("auth/login", params, "success", resource=username)
            return {"token": token, "username": username, "role": self.auth.get_user(username).role if self.auth.get_user(username) else ""}
        self._audit("auth/login", params, "failure", resource=username)
        raise PermissionError("Invalid credentials")

    async def _handle_auth_validate(self, params: dict) -> dict:
        token = self._get_token(params)
        session = self.auth.validate_token(token)
        if session:
            return {"valid": True, "username": session["username"], "role": session["role"]}
        return {"valid": False}

    async def _handle_read_note(self, params: dict) -> dict:
        path = _sanitize_path(params.get("path", ""))
        _validate_path(path)
        try:
            note = self.notes.read(path)
            if note is None:
                raise FileNotFoundError(f"Note not found: {path}")
            result = note.to_dict()
            result = self.crypto.decrypt_note(result)
            self._audit("note/read", params, resource=path)
            return result
        except Exception as e:
            self._audit("note/read", params, "error", resource=path, details={"error": str(e)})
            raise

    async def _handle_write_note(self, params: dict) -> dict:
        self._require_permission(params, "note/write")
        from ..models.note_model import Note
        note_data = params.get("note", {})
        path = _sanitize_path(note_data.get("path", ""))
        _validate_path(path)
        content = note_data.get("content", "")
        content = content[:1000000]
        note_data["content"] = content
        note_data = self.crypto.encrypt_note(note_data)
        note = Note(
            id=note_data.get("id", ""),
            path=path,
            title=note_data.get("title", ""),
            content=note_data.get("content", ""),
            tags=note_data.get("tags", [])[:100],
            links=note_data.get("links", []),
            frontmatter=note_data.get("frontmatter", {}),
            checksum=note_data.get("checksum", ""),
            version=note_data.get("version", 0),
            created=note_data.get("created", 0),
            modified=note_data.get("modified", 0),
            source="hermes",
        )
        note.source = "hermes"
        try:
            result = self.notes.write(note)
            self.sync.mark_changed(note.path, content)
            self._broadcast("note/changed", {"path": note.path, "action": "write"})
            self._audit("note/write", params, resource=path)
            return result
        except Exception as e:
            self._audit("note/write", params, "error", resource=path, details={"error": str(e)})
            raise

    async def _handle_list_notes(self, params: dict) -> dict:
        prefix = _sanitize_path(params.get("prefix", ""))
        notes = self.notes.list(prefix)
        results = [self.crypto.decrypt_note(n.to_dict()) for n in notes]
        self._audit("note/list", params)
        return {"notes": results}

    async def _handle_search_notes(self, params: dict) -> dict:
        query = params.get("query", "")
        if not query or not isinstance(query, str):
            return {"notes": []}
        query = query.strip()[:200]
        notes = self.notes.search(query)
        results = [self.crypto.decrypt_note(n.to_dict()) for n in notes]
        self._audit("note/search", params)
        return {"notes": results}

    async def _handle_delete_note(self, params: dict) -> dict:
        self._require_permission(params, "note/delete")
        path = _sanitize_path(params.get("path", ""))
        _validate_path(path)
        try:
            self.notes.delete(path)
            self._broadcast("note/changed", {"path": path, "action": "delete"})
            self._audit("note/delete", params, resource=path)
            return {"deleted": True, "path": path}
        except Exception as e:
            self._audit("note/delete", params, "error", resource=path, details={"error": str(e)})
            raise

    async def _handle_list_folders(self, params: dict) -> dict:
        folders = self.notes.list_folders()
        safe_folders = [_sanitize_path(f) for f in folders if isinstance(f, str)]
        self._audit("folder/list", params)
        return {"folders": safe_folders}

    async def _handle_list_tags(self, params: dict) -> dict:
        tags = self.notes.list_tags()
        safe_tags = [str(t)[:200] for t in tags]
        self._audit("tags/list", params)
        return {"tags": safe_tags}

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
            "auth_login": "auth/login",
            "auth_validate": "auth/validate",
        }
        method = method_map.get(tool_name)
        if not method:
            return {"error": f"Unknown tool: {tool_name}"}
        handler_map = {
            "note/read": self._handle_read_note,
            "note/write": self._handle_write_note,
            "note/list": self._handle_list_notes,
            "note/search": self._handle_search_notes,
            "note/delete": self._handle_delete_note,
            "folder/list": self._handle_list_folders,
            "tags/list": self._handle_list_tags,
            "auth/login": self._handle_auth_login,
            "auth/validate": self._handle_auth_validate,
        }
        handler = handler_map.get(method)
        if handler:
            return await handler(params)
        return {"error": f"No handler for {method}"}