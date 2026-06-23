"""Hermes Agent tool: AKATSUKI ↔ Obsidian bridge."""
import asyncio
import json
import os
import logging
from typing import Any

logger = logging.getLogger("akatsuki.tools.obsidian")

TOOL_META = {
    "name": "obsidian",
    "description": "Read/write/search/manage Obsidian notes in the AKATSUKI vault",
    "sub_commands": [
        "read", "write", "list", "search", "delete",
        "folders", "tags", "sync", "status", "watch", "help",
    ],
    "emoji": "\uD83D\uDCDD",
}


def register_tools(register_fn):
    register_fn(
        name="obsidian",
        toolset="akatsuki",
        schema={
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": TOOL_META["sub_commands"],
                    "description": "Obsidian operation",
                },
                "path": {"type": "string", "description": "Note path (vault-relative)"},
                "content": {"type": "string", "description": "Note body content (for write)"},
                "title": {"type": "string", "description": "Note title (for write)"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags for the note (for write)",
                },
                "query": {"type": "string", "description": "Search query"},
                "prefix": {"type": "string", "description": "Folder prefix for listing"},
            },
            "required": ["action"],
        },
        handler=_handle_obsidian_tool,
        check_fn=_check_bridge_available,
    )


def _check_bridge_available() -> bool:
    try:
        bridge = _get_bridge()
        return bridge is not None
    except Exception:
        return False


def _handle_obsidian_tool(args: dict) -> str:
    action = args.get("action", "help")
    bridge = _get_bridge()
    if not bridge:
        return _no_bridge_msg()
    try:
        coro = bridge.execute_tool(f"obsidian_{action}", args)
        result = asyncio.run(coro)
        return json.dumps(result, indent=2, ensure_ascii=False)
    except FileNotFoundError as e:
        return f"\u274C Not found: {e}"
    except ConnectionError as e:
        return f"\u26A0\uFE0F Bridge disconnected: {e}"
    except Exception as e:
        logger.exception(f"obsidian/{action} failed")
        return f"\u274C {action} failed: {e}"


def _no_bridge_msg() -> str:
    return (
        "\u26A0\uFE0F Obsidian bridge not running.\n\n"
        "Start the bridge:\n"
        "  python -m hermes_bridge /path/to/your/vault\n\n"
        "Or set env:\n"
        "  export AKATSUKI_VAULT=/path/to/vault\n"
        "  python -m hermes_bridge"
    )


def _get_bridge():
    if not hasattr(_get_bridge, "_instance"):
        try:
            from ..bridge.agent_bridge import AgentBridge
            vault = os.environ.get(
                "AKATSUKI_VAULT",
                os.path.expanduser("~/akatsuki-vault"),
            )
            bridge = AgentBridge(vault)
            _get_bridge._instance = bridge
        except Exception as e:
            logger.warning(f"Cannot init bridge: {e}")
            return None
    return _get_bridge._instance
