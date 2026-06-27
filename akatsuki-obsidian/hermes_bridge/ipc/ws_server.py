import asyncio
import json
import logging
import os
import ssl
from typing import Callable, Optional

logger = logging.getLogger("akatsuki.ipc.ws")

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False


def _load_tls_config() -> dict:
    cfg_path = os.environ.get(
        "AKATSUKI_CONFIG",
        os.path.join(os.path.dirname(__file__), "..", "..", "akatsuki.yaml"),
    )
    if os.path.exists(cfg_path):
        try:
            import yaml
            with open(cfg_path, encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
                return cfg.get("bridge", {})
        except Exception:
            pass
    return {}


def _create_ssl_context(bridge_cfg: dict) -> Optional[ssl.SSLContext]:
    if not bridge_cfg.get("tls_enabled", False):
        return None
    cert = bridge_cfg.get("tls_cert", "")
    key = bridge_cfg.get("tls_key", "")
    if not cert or not key:
        logger.warning("TLS enabled but cert/key not configured")
        return None
    cert_path = os.path.expanduser(cert) if "~" in cert else cert
    key_path = os.path.expanduser(key) if "~" in key else key
    if not os.path.exists(cert_path) or not os.path.exists(key_path):
        logger.warning(f"TLS cert/key not found: {cert_path}, {key_path}")
        return None
    try:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(cert_path, key_path)
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        logger.info(f"TLS enabled with cert: {cert_path}")
        return ctx
    except Exception as e:
        logger.error(f"Failed to create SSL context: {e}")
        return None


class WebSocketServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 18749,
                 tls: bool = False, cert_path: str = "", key_path: str = ""):
        self.host = host
        self.port = port
        self._handlers: dict[str, Callable] = {}
        self._server: Optional[asyncio.AbstractServer] = None
        self._connections: set = set()
        self._ssl_context = None
        if tls:
            bridge_cfg = _load_tls_config()
            bridge_cfg["tls_enabled"] = True
            if cert_path:
                bridge_cfg["tls_cert"] = cert_path
            if key_path:
                bridge_cfg["tls_key"] = key_path
            self._ssl_context = _create_ssl_context(bridge_cfg)

    def on(self, method: str, handler: Callable):
        self._handlers[method] = handler

    async def start(self):
        if not HAS_WEBSOCKETS:
            logger.warning("websockets not installed; WS server disabled")
            return
        scheme = "wss" if self._ssl_context else "ws"
        self._server = await websockets.serve(
            self._handle_client, self.host, self.port, ssl=self._ssl_context
        )
        logger.info(f"WebSocket server on {scheme}://{self.host}:{self.port}")

    async def stop(self):
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        logger.info("WebSocket server stopped")

    async def broadcast(self, method: str, params: dict):
        msg = json.dumps({
            "jsonrpc": "2.0",
            "method": f"event/{method}",
            "params": params,
        })
        for ws in list(self._connections):
            try:
                await ws.send(msg)
            except Exception:
                self._connections.discard(ws)

    async def _handle_client(self, ws: WebSocketServerProtocol):
        self._connections.add(ws)
        try:
            async for raw in ws:
                await self._dispatch(raw, ws)
        except Exception:
            pass
        finally:
            self._connections.discard(ws)

    async def _dispatch(self, raw: str, ws: WebSocketServerProtocol):
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            await self._send_error(ws, "", -32700, "Parse error")
            return
        req_id = msg.get("id", "")
        method = msg.get("method", "")
        params = msg.get("params", {})
        handler = self._handlers.get(method)
        if not handler:
            await self._send_error(ws, req_id, -32601, f"Method not found: {method}")
            return
        try:
            if asyncio.iscoroutinefunction(handler):
                result = await handler(params)
            else:
                result = handler(params)
            resp = {"jsonrpc": "2.0", "id": req_id, "result": result}
            await ws.send(json.dumps(resp))
        except PermissionError as e:
            await self._send_error(ws, req_id, -32001, str(e))
        except FileNotFoundError as e:
            await self._send_error(ws, req_id, -32002, str(e))
        except ValueError as e:
            await self._send_error(ws, req_id, -32602, str(e))
        except Exception as e:
            logger.exception(f"Handler error for {method}")
            await self._send_error(ws, req_id, -32603, str(e)[:500])

    async def _send_error(self, ws: WebSocketServerProtocol, req_id: str, code: int, msg: str):
        resp = {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": msg}}
        await ws.send(json.dumps(resp))