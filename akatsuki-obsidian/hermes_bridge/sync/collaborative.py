import asyncio
import json
import logging
import time
from typing import Optional

logger = logging.getLogger("akatsuki.sync.collaborative")


class CollaborativeSync:
    def __init__(self, node_id: str, bridge_url: str = ""):
        self.node_id = node_id
        self.bridge_url = bridge_url
        self._peers: dict[str, dict] = {}
        self._running = False
        self._sync_callback = None

    def set_sync_callback(self, callback):
        self._sync_callback = callback

    def register_peer(self, peer_id: str, address: str, port: int = 18749):
        self._peers[peer_id] = {
            "id": peer_id,
            "address": address,
            "port": port,
            "connected": False,
            "last_seen": 0,
        }
        logger.info(f"Peer registered: {peer_id} @ {address}:{port}")

    def unregister_peer(self, peer_id: str):
        self._peers.pop(peer_id, None)

    def list_peers(self) -> list[dict]:
        return [
            {"id": pid, "address": p["address"], "port": p["port"],
             "connected": p["connected"], "last_seen": p["last_seen"]}
            for pid, p in self._peers.items()
        ]

    async def sync_with_peer(self, peer_id: str, operations: list[dict]) -> dict:
        peer = self._peers.get(peer_id)
        if not peer:
            return {"error": f"Peer not found: {peer_id}"}
        try:
            import websockets
            url = f"ws://{peer['address']}:{peer['port']}"
            async with websockets.connect(url) as ws:
                msg = json.dumps({
                    "jsonrpc": "2.0",
                    "id": f"sync-{self.node_id}-{int(time.time())}",
                    "method": "sync/merge",
                    "params": {"node_id": self.node_id, "operations": operations},
                })
                await ws.send(msg)
                resp = json.loads(await ws.recv())
                peer["connected"] = True
                peer["last_seen"] = int(time.time())
                return resp.get("result", resp)
        except Exception as e:
            peer["connected"] = False
            logger.warning(f"Sync with {peer_id} failed: {e}")
            return {"error": str(e)}

    async def broadcast_operation(self, op: dict):
        if not self._peers:
            return
        tasks = [self.sync_with_peer(pid, [op]) for pid in self._peers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for pid, result in zip(self._peers.keys(), results):
            if isinstance(result, Exception):
                logger.warning(f"Broadcast to {pid} failed: {result}")

    async def handle_sync_request(self, params: dict) -> dict:
        remote_node = params.get("node_id", "unknown")
        remote_ops = params.get("operations", [])
        merged = []
        if self._sync_callback:
            try:
                merged = self._sync_callback(remote_ops)
            except Exception as e:
                logger.error(f"Sync callback error: {e}")
        logger.info(f"Sync from {remote_node}: {len(remote_ops)} ops received, {len(merged)} new")
        return {"merged": len(merged), "node_id": self.node_id, "ops_received": len(remote_ops)}

    async def discover_peers_mdns(self, service_type: str = "_akatsuki._tcp"):
        try:
            from zeroconf import Zeroconf, ServiceBrowser, ServiceStateChange
            zeroconf = Zeroconf()

            def on_change(zeroconf, service_type, name, state_change):
                if state_change == ServiceStateChange.Added:
                    info = zeroconf.get_service_info(service_type, name)
                    if info:
                        peer_id = name.split(".")[0]
                        address = ".".join(str(b) for b in info.addresses[0]) if info.addresses else ""
                        self.register_peer(peer_id, address, info.port)

            browser = ServiceBrowser(zeroconf, service_type, handlers=[on_change])
            return browser
        except ImportError:
            logger.warning("zeroconf not installed; mDNS peer discovery disabled")
            return None
        except Exception as e:
            logger.warning(f"mDNS discovery failed: {e}")
            return None