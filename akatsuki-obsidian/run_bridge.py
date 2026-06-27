#!/usr/bin/env python3
"""Run the AKATSUKI Obsidian Bridge."""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

vault = sys.argv[1] if len(sys.argv) > 1 else os.environ.get(
    "AKATSUKI_VAULT",
    str(Path.home() / "akatsuki-vault"),
)

from hermes_bridge.bridge.agent_bridge import AgentBridge
import asyncio
import logging
import signal

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("akatsuki")


async def run():
    bridge = AgentBridge(vault)
    await bridge.start()
    logger.info(f"Bridge active for vault: {vault}")
    logger.info(f"  WebSocket: ws://127.0.0.1:18749")
    stop = asyncio.Event()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            asyncio.get_running_loop().add_signal_handler(sig, stop.set)
        except NotImplementedError:
            pass
    await stop.wait()
    await bridge.stop()


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("Shutdown by user")
