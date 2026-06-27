"""Alternative MCP server using async httpx for HackerAI compatibility."""

import sys
import json

from ..agents import ALL_AGENTS

try:
    import mcp
except ImportError:
    print("mcp package not installed. Install with: pip install mcp")
    sys.exit(1)


TOOL_DEFINITIONS = []

for name, agent in ALL_AGENTS.items():
    TOOL_DEFINITIONS.append({
        "name": f"dept_{name}",
        "description": agent.description,
        "inputSchema": {
            "type": "object",
            "properties": {
                "params": {"type": "string", "description": "JSON parameters"}
            },
            "required": ["params"],
        },
    })

TOOL_DEFINITIONS.extend([
    {
        "name": "recon",
        "description": "Run reconnaissance on a target",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Target to recon"}
            },
            "required": ["target"],
        },
    },
    {
        "name": "scan",
        "description": "Scan a target for vulnerabilities",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Target to scan"}
            },
            "required": ["target"],
        },
    },
    {
        "name": "swarm",
        "description": "Launch a swarm operation",
        "inputSchema": {
            "type": "object",
            "properties": {
                "config": {"type": "string", "description": "Swarm configuration JSON"}
            },
            "required": ["config"],
        },
    },
])


async def handle_tool_call(name: str, arguments: dict):
    if name.startswith("dept_"):
        agent_name = name[5:]
        agent = ALL_AGENTS.get(agent_name)
        if not agent:
            return {"error": f"Unknown department: {agent_name}"}
        return agent.execute(json.loads(arguments.get("params", "{}")))
    elif name == "recon":
        from ..agents import run_recon
        return run_recon(arguments["target"])
    elif name == "scan":
        from ..agents import run_scan
        return run_scan(arguments["target"])
    elif name == "swarm":
        from ..agents import run_swarm
        return run_swarm(json.loads(arguments["config"]))
    return {"error": f"Unknown tool: {name}"}
