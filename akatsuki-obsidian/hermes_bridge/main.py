"""AKATSUKI Obsidian Bridge - Hermes Agent integration entry point."""
import asyncio
import logging
import signal
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("akatsuki.main")


def main():
    vault = sys.argv[1] if len(sys.argv) > 1 else os.environ.get(
        "AKATSUKI_VAULT", str(Path.home() / "akatsuki-vault")
    )
    bridge = AgentBridge(vault)

    async def run():
        await bridge.start()
        logger.info(f"Bridge active for vault: {vault}")
        stop_event = asyncio.Event()
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop = asyncio.get_running_loop()
                loop.add_signal_handler(sig, stop_event.set)
            except NotImplementedError:
                pass
        await stop_event.wait()
        await bridge.stop()

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("Shutdown by user")


if __name__ == "__main__":
    import os
    from hermes_bridge.bridge.agent_bridge import AgentBridge
    main()
