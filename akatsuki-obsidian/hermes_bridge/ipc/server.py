import asyncio
import json
import os
import logging
from typing import Callable, Optional

logger = logging.getLogger("akatsuki.ipc")


class UnixSocketServer:
    def __init__(self, socket_path: str):
        self.socket_path = socket_path
        self._server: Optional[asyncio.AbstractServer] = None
        self._handlers: dict[str, Callable] = {}
        self._connections: set = set()

    def on(self, method: str, handler: Callable):
        self._handlers[method] = handler

    async def start(self):
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
        os.makedirs(os.path.dirname(self.socket_path), exist_ok=True)
        self._server = await asyncio.start_unix_server(
            self._handle_client, path=self.socket_path
        )
        os.chmod(self.socket_path, 0o600)
        logger.info(f"Unix socket server listening on {self.socket_path}")

    async def stop(self):
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
        logger.info("Unix socket server stopped")

    async def broadcast(self, method: str, params: dict):
        msg = json.dumps({
            "jsonrpc": "2.0",
            "method": f"event/{method}",
            "params": params,
        })
        for writer in list(self._connections):
            try:
                writer.write((msg + "\n").encode())
                await writer.drain()
            except Exception:
                self._connections.discard(writer)

    async def _handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self._connections.add(writer)
        try:
            while True:
                line = await reader.readline()
                if not line:
                    break
                await self._dispatch(line.strip(), writer)
        except (ConnectionResetError, BrokenPipeError):
            pass
        finally:
            self._connections.discard(writer)
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    async def _dispatch(self, raw: bytes, writer: asyncio.StreamWriter):
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            await self._send_error(writer, "", -32700, "Parse error")
            return
        req_id = msg.get("id", "")
        method = msg.get("method", "")
        params = msg.get("params", {})
        handler = self._handlers.get(method)
        if not handler:
            await self._send_error(writer, req_id, -32601, f"Method not found: {method}")
            return
        try:
            if asyncio.iscoroutinefunction(handler):
                result = await handler(params)
            else:
                result = handler(params)
            resp = {"jsonrpc": "2.0", "id": req_id, "result": result}
            writer.write((json.dumps(resp) + "\n").encode())
            await writer.drain()
        except Exception as e:
            logger.exception(f"Handler error for {method}")
            await self._send_error(writer, req_id, -32603, str(e))

    async def _send_error(self, writer: asyncio.StreamWriter, req_id: str, code: int, msg: str):
        resp = {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": msg}}
        writer.write((json.dumps(resp) + "\n").encode())
        await writer.drain()
