import asyncio
import logging
import os
import signal
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("akatsuki")


def main():
    vault = sys.argv[1] if len(sys.argv) > 1 else os.environ.get(
        "AKATSUKI_VAULT",
        str(Path.home() / "akatsuki-vault"),
    )

    from src.bridge.agent_bridge import AgentBridge
    bridge = AgentBridge(vault)

    async def run():
        await bridge.start()
        logger.info(f"Bridge active for vault: {vault}")
        logger.info(f"  WS:     ws://127.0.0.1:18749")
        logger.info(f"  Socket: {bridge.socket_path}")
        stop = asyncio.Event()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                asyncio.get_running_loop().add_signal_handler(sig, stop.set)
            except NotImplementedError:
                pass
        await stop.wait()
        await bridge.stop()

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("Shutting down")


if __name__ == "__main__":
    main()
