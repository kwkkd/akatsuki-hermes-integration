import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Optional

from sync_engine.src.crdt.engine import CrdtEngine

logger = logging.getLogger("akatsuki.sync.server")


class SyncServer:
    def __init__(self, node_id: str, host: str = "0.0.0.0", port: int = 18750,
                 vault_path: Optional[str] = None):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.crdt = CrdtEngine(node_id)
        self._peers: dict[str, dict] = {}
        self._running = False
        self._server = None
        self._vault_path = vault_path

    async def start(self):
        try:
            import websockets
        except ImportError:
            logger.warning("websockets not installed; sync server disabled")
            return
        self._running = True
        self._server = await websockets.serve(
            self._handle_peer,
            self.host,
            self.port,
            ping_interval=30,
            ping_timeout=10,
        )
        logger.info(f"Sync server listening on ws://{self.host}:{self.port}")

    async def stop(self):
        self._running = False
        if self._server:
            self._server.close()
            await self._server.wait_closed()

    async def _handle_peer(self, ws):
        peer_id = f"peer-{id(ws):x}"
        self._peers[peer_id] = {"ws": ws, "connected_at": time.time()}
        logger.info(f"Sync peer connected: {peer_id}")
        try:
            async for raw in ws:
                try:
                    msg = json.loads(raw)
                    resp = await self._dispatch(msg)
                    await ws.send(json.dumps(resp))
                except Exception as e:
                    await ws.send(json.dumps({
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {"code": -32700, "message": str(e)},
                    }))
        except Exception as e:
            logger.info(f"Sync peer disconnected: {peer_id} ({e})")
        finally:
            self._peers.pop(peer_id, None)

    async def _dispatch(self, msg: dict) -> dict:
        method = msg.get("method", "")
        params = msg.get("params", {})
        msg_id = msg.get("id", None)
        try:
            if method == "sync/merge":
                remote_ops = params.get("operations", [])
                new_ops = self.crdt.merge(remote_ops)
                self._broadcast_ops(new_ops, exclude=None)
                return {"jsonrpc": "2.0", "id": msg_id, "result": {
                    "merged": len(new_ops),
                    "node_id": self.node_id,
                }}
            elif method == "sync/pull":
                known_heads = set(params.get("heads", []))
                missing = self.crdt.get_missing_ops(known_heads)
                return {"jsonrpc": "2.0", "id": msg_id, "result": {
                    "operations": [op._asdict() if hasattr(op, '_asdict') else op.__dict__ for op in missing],
                    "node_id": self.node_id,
                }}
            elif method == "sync/state":
                return {"jsonrpc": "2.0", "id": msg_id, "result": self.crdt.state()}
            elif method == "sync/peers":
                return {"jsonrpc": "2.0", "id": msg_id, "result": {
                    "peers": list(self._peers.keys()),
                    "count": len(self._peers),
                }}
            else:
                return {"jsonrpc": "2.0", "id": msg_id,
                        "error": {"code": -32601, "message": f"Unknown method: {method}"}}
        except Exception as e:
            return {"jsonrpc": "2.0", "id": msg_id,
                    "error": {"code": -32603, "message": str(e)}}

    def _broadcast_ops(self, ops: list, exclude: Optional[str] = None):
        if not ops:
            return
        msg = json.dumps({
            "jsonrpc": "2.0",
            "method": "event/sync/ops",
            "params": {"operations": [op._asdict() if hasattr(op, '_asdict') else op.__dict__ for op in ops]},
        })
        for pid, peer in list(self._peers.items()):
            if pid == exclude:
                continue
            try:
                asyncio.create_task(peer["ws"].send(msg))
            except Exception:
                pass