"""MCP server for AKATSUKI."""

import sys
import json

from ..agents import ALL_AGENTS

try:
    import mcp
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("mcp package not installed. Install with: pip install mcp")
    sys.exit(1)


server = Server("akatsuki")


def _run_agent(name, params):
    agent = ALL_AGENTS.get(name)
    if not agent:
        return {"error": f"Agent '{name}' not found"}
    return agent.execute(json.loads(params))


@server.list_tools()
async def list_tools():
    tools = []
    for name, agent in ALL_AGENTS.items():
        tools.append(
            Tool(
                name=f"dept_{name}",
                description=agent.description,
                inputSchema={
                    "type": "object",
                    "properties": {
                        "params": {
                            "type": "string",
                            "description": "JSON parameters for this department tool",
                        }
                    },
                    "required": ["params"],
                },
            )
        )
    tools.append(
        Tool(
            name="run_operation",
            description="Run a multi-step AKATSUKI operation",
            inputSchema={
                "type": "object",
                "properties": {
                    "operation": {"type": "string", "description": "Operation name"},
                    "target": {"type": "string", "description": "Operation target"},
                },
                "required": ["operation", "target"],
            },
        )
    )
    tools.append(
        Tool(
            name="recon",
            description="Run reconnaissance on a target",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "Target to recon"},
                },
                "required": ["target"],
            },
        )
    )
    tools.append(
        Tool(
            name="scan",
            description="Scan a target for vulnerabilities",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "Target to scan"},
                },
                "required": ["target"],
            },
        )
    )
    tools.append(
        Tool(
            name="exploit",
            description="Exploit a vulnerability on a target",
            inputSchema={
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "Target to exploit"},
                    "vuln_id": {"type": "string", "description": "Vulnerability ID"},
                },
                "required": ["target"],
            },
        )
    )
    tools.append(
        Tool(
            name="swarm",
            description="Launch a swarm operation",
            inputSchema={
                "type": "object",
                "properties": {
                    "config": {"type": "string", "description": "Swarm configuration JSON"},
                },
                "required": ["config"],
            },
        )
    )
    return tools


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name.startswith("dept_"):
        agent_name = name[5:]
        result = _run_agent(agent_name, arguments.get("params", "{}"))
    elif name == "recon":
        from ..agents import run_recon
        result = run_recon(arguments["target"])
    elif name == "scan":
        from ..agents import run_scan
        result = run_scan(arguments["target"])
    elif name == "exploit":
        from ..agents import run_exploit
        result = run_exploit(arguments["target"], arguments.get("vuln_id", ""))
    elif name == "swarm":
        from ..agents import run_swarm
        result = run_swarm(json.loads(arguments["config"]))
    elif name == "run_operation":
        from ..agents import run_operation
        result = run_operation(arguments["operation"], arguments["target"])
    else:
        result = {"error": f"Unknown tool: {name}"}

    return [TextContent(type="text", text=json.dumps(result, indent=2))]


async def main():
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
