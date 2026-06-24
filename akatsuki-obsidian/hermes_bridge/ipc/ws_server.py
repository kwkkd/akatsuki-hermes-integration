import asyncio
import json
import logging
from typing import Callable, Optional

logger = logging.getLogger("akatsuki.ipc.ws")

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False


class WebSocketServer:
    def __init__(self, host: str = "127.0.0.1", port: int = 18749):
        self.host = host
        self.port = port
        self._handlers: dict[str, Callable] = {}
        self._server: Optional[asyncio.AbstractServer] = None
        self._connections: set = set()

    def on(self, method: str, handler: Callable):
        self._handlers[method] = handler

    async def start(self):
        if not HAS_WEBSOCKETS:
            logger.warning("websockets not installed; WS server disabled")
            return
        self._server = await websockets.serve(
            self._handle_client, self.host, self.port
        )
        logger.info(f"WebSocket server on ws://{self.host}:{self.port}")

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
        except Exception as e:
            logger.exception(f"Handler error for {method}")
            await self._send_error(ws, req_id, -32603, str(e))

    async def _send_error(self, ws: WebSocketServerProtocol, req_id: str, code: int, msg: str):
        resp = {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": msg}}
        await ws.send(json.dumps(resp))
