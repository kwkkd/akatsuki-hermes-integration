import json
import logging
from typing import Optional

from tools.registry import registry, tool_error, tool_result

logger = logging.getLogger(__name__)


class MsfRpcClient:
    def __init__(self, host: str = "127.0.0.1", port: int = 55553,
                 password: str = "", ssl: bool = False):
        self.host = host
        self.port = port
        self.password = password
        self.ssl = ssl
        self._client = None
        self._token = None

    def connect(self) -> bool:
        try:
            from msgpack import Unpacker
            import socket
            import ssl as ssl_mod
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            if self.ssl:
                ctx = ssl_mod.create_default_context()
                sock = ctx.wrap_socket(sock, server_hostname=self.host)
            sock.connect((self.host, self.port))
            self._client = sock
            auth = self._call("auth.login", [self.password])
            if auth and auth.get(b"result") == b"success":
                self._token = auth.get(b"token", b"").decode()
                return True
            return False
        except ImportError:
            logger.warning("msgpack not installed; MSFRPC disabled")
            return False
        except Exception as e:
            logger.error(f"MSFRPC connect failed: {e}")
            return False

    def _call(self, method: str, args: list) -> Optional[dict]:
        if not self._client:
            return None
        try:
            import msgpack
            msg = msgpack.dumps({"method": method, "token": self._token or "", "args": args})
            self._client.send(msg)
            import struct
            raw_len = self._client.recv(4)
            if len(raw_len) < 4:
                return None
            msg_len = struct.unpack(">I", raw_len)[0]
            raw = b""
            while len(raw) < msg_len:
                chunk = self._client.recv(msg_len - len(raw))
                if not chunk:
                    break
                raw += chunk
            return msgpack.unpackb(raw) if raw else None
        except Exception as e:
            logger.error(f"MSFRPC call error: {e}")
            return None

    def list_modules(self, module_type: str = "exploit") -> list:
        res = self._call(f"module.{module_type}", [])
        if res:
            return [m.decode() if isinstance(m, bytes) else m for m in res.get(b"modules", [])]
        return []

    def list_sessions(self) -> list[dict]:
        res = self._call("session.list", [])
        if res:
            sessions = {}
            raw = res.get(b"sessions", {})
            if isinstance(raw, dict):
                for k, v in raw.items():
                    sid = int(k) if not isinstance(k, int) else k
                    sessions[str(sid)] = {
                        "type": v.get(b"type", b"").decode() if isinstance(v.get(b"type"), bytes) else "",
                        "tunnel": v.get(b"tunnel_local", b"").decode() if isinstance(v.get(b"tunnel_local"), bytes) else "",
                        "target": v.get(b"target_host", b"").decode() if isinstance(v.get(b"target_host"), bytes) else "",
                    }
            return list(sessions.values())
        return []

    def execute_module(self, module_type: str, module_name: str,
                       options: dict = None) -> dict:
        opts = []
        if options:
            for k, v in options.items():
                opts.extend([k, str(v)])
        res = self._call(f"module.execute_{module_type}", [
            module_name, opts or []
        ])
        if res:
            return {
                "job_id": res.get(b"job_id", 0),
                "result": res.get(b"result", b"").decode() if isinstance(res.get(b"result"), bytes) else "",
            }
        return {"error": "No response"}

    def disconnect(self):
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None
            self._token = None


_clients: dict[str, MsfRpcClient] = {}


def _get_client(host: str = "127.0.0.1", port: int = 55553,
                password: str = "", ssl: bool = False) -> MsfRpcClient:
    key = f"{host}:{port}"
    if key not in _clients:
        _clients[key] = MsfRpcClient(host, port, password, ssl)
    return _clients[key]


AKATSUKI_MSFRPC_SCHEMA = {
    "name": "akatsuki_msfrpc",
    "description": "Metasploit RPC integration — connect to MSFRPC daemon, list exploits/modules, manage sessions, and execute modules remotely.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["connect", "list_modules", "list_sessions", "execute", "disconnect"],
                "description": "MSFRPC action to perform",
            },
            "host": {
                "type": "string",
                "description": "MSFRPC host (default: 127.0.0.1)",
            },
            "port": {
                "type": "integer",
                "description": "MSFRPC port (default: 55553)",
            },
            "password": {
                "type": "string",
                "description": "MSFRPC password",
            },
            "module_type": {
                "type": "string",
                "enum": ["exploit", "auxiliary", "post", "payload", "encoder", "nop"],
                "description": "Module type for listing/execution",
            },
            "module_name": {
                "type": "string",
                "description": "Full module name (e.g., exploit/multi/handler)",
            },
            "options": {
                "type": "string",
                "description": "JSON object of module options",
            },
            "ssl": {
                "type": "boolean",
                "description": "Use SSL for MSFRPC connection",
            },
        },
        "required": ["action"],
    },
}


def akatsuki_msfrpc(action: str, host: str = "127.0.0.1", port: int = 55553,
                    password: str = "", module_type: str = "exploit",
                    module_name: str = "", options: str = "{}",
                    ssl: bool = False) -> str:
    client = _get_client(host, port, password, ssl)

    if action == "connect":
        ok = client.connect()
        if ok:
            return tool_result({"connected": True, "host": host, "port": port})
        return tool_error(f"Failed to connect to MSFRPC at {host}:{port}")

    if action == "list_modules":
        if not client._token:
            ok = client.connect()
            if not ok:
                return tool_error("Not connected to MSFRPC")
        modules = client.list_modules(module_type)
        return tool_result({"module_type": module_type, "count": len(modules), "modules": modules[:50]})

    if action == "list_sessions":
        if not client._token:
            ok = client.connect()
            if not ok:
                return tool_error("Not connected to MSFRPC")
        sessions = client.list_sessions()
        return tool_result({"session_count": len(sessions), "sessions": sessions})

    if action == "execute":
        if not client._token:
            ok = client.connect()
            if not ok:
                return tool_error("Not connected to MSFRPC")
        if not module_name:
            return tool_error("module_name is required for execute action")
        try:
            opts = json.loads(options) if isinstance(options, str) else options
        except json.JSONDecodeError:
            return tool_error("Invalid options JSON")
        result = client.execute_module(module_type, module_name, opts)
        return tool_result(result)

    if action == "disconnect":
        client.disconnect()
        key = f"{host}:{port}"
        _clients.pop(key, None)
        return tool_result({"disconnected": True})

    return tool_error(f"Unknown action: {action}")


def check_akatsuki_msfrpc_requirements() -> bool:
    try:
        import msgpack
        return True
    except ImportError:
        return False


registry.register(
    name="akatsuki_msfrpc",
    toolset="akatsuki",
    schema=AKATSUKI_MSFRPC_SCHEMA,
    handler=lambda args, **kw: akatsuki_msfrpc(
        action=args["action"],
        host=args.get("host", "127.0.0.1"),
        port=args.get("port", 55553),
        password=args.get("password", ""),
        module_type=args.get("module_type", "exploit"),
        module_name=args.get("module_name", ""),
        options=args.get("options", "{}"),
        ssl=args.get("ssl", False),
    ),
    check_fn=check_akatsuki_msfrpc_requirements,
    emoji="💀",
)