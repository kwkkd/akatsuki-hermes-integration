import json
import logging
from typing import Optional

from tools.registry import registry, tool_error, tool_result

logger = logging.getLogger(__name__)


AKATSUKI_GRAPH_SCHEMA = {
    "name": "akatsuki_graph",
    "description": "Attack Path Graph Generator — build network topology graphs, find attack paths between hosts, analyze choke points, and visualize with Mermaid.js or DOT format.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["build", "find_path", "analyze", "render"],
                "description": "build: create topology graph; find_path: find attack paths; analyze: identify choke points; render: generate visualization",
            },
            "nodes_json": {
                "type": "string",
                "description": "JSON array of nodes: [{\"id\": \"host1\", \"type\": \"host\", \"services\": [\"http\",\"ssh\"], \"vulns\": [\"CVE-2021-41773\"]}]",
            },
            "edges_json": {
                "type": "string",
                "description": "JSON array of edges: [{\"source\": \"host1\", \"target\": \"host2\", \"type\": \"network\", \"port\": 445}]",
            },
            "source": {
                "type": "string",
                "description": "Source node ID for path finding",
            },
            "target": {
                "type": "string",
                "description": "Target node ID for path finding",
            },
            "format": {
                "type": "string",
                "enum": ["mermaid", "dot"],
                "description": "Output format for render action",
            },
        },
        "required": ["action"],
    },
}


def build_graph(nodes: list[dict], edges: list[dict]) -> dict:
    node_map = {n["id"]: n for n in nodes}
    adj = {}
    for e in edges:
        s, t = e.get("source"), e.get("target")
        adj.setdefault(s, []).append(t)
        adj.setdefault(t, []).append(s)
    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": [{"id": n["id"], "type": n.get("type", "unknown"), "services": n.get("services", [])} for n in nodes],
        "edges": edges,
    }


def find_paths(nodes: list[dict], edges: list[dict], source: str, target: str) -> list[list[str]]:
    adj = {}
    for e in edges:
        s, t = e.get("source"), e.get("target")
        adj.setdefault(s, set()).add(t)
        adj.setdefault(t, set()).add(s)
    paths = []
    visited = set()
    def dfs(current, path):
        if current == target:
            paths.append(path + [current])
            return
        if current in visited:
            return
        visited.add(current)
        for neighbor in adj.get(current, set()):
            dfs(neighbor, path + [current])
        visited.discard(current)
    dfs(source, [])
    return sorted(paths, key=len)[:5]


def analyze(nodes: list[dict], edges: list[dict]) -> dict:
    adj = {}
    for e in edges:
        s, t = e.get("source"), e.get("target")
        adj.setdefault(s, set()).add(t)
        adj.setdefault(t, set()).add(s)
    choke_points = []
    for n in adj:
        if len(adj[n]) > 2:
            choke_points.append({"node": n, "connections": len(adj[n])})
    vuln_hosts = []
    for n in nodes:
        if n.get("vulns"):
            vuln_hosts.append({"id": n["id"], "vulns": n["vulns"]})
    return {
        "choke_points": sorted(choke_points, key=lambda x: -x["connections"]),
        "vulnerable_hosts": vuln_hosts,
        "total_hosts": len(nodes),
    }


def render_mermaid(nodes: list[dict], edges: list[dict]) -> str:
    lines = ["graph TD"]
    node_ids = {}
    for i, n in enumerate(nodes):
        nid = f"N{i}"
        label = n.get("id", "").replace("-", "_").replace(".", "_")
        services = ", ".join(n.get("services", []))
        label_str = f"{label}" + (f" [{services}]" if services else "")
        node_ids[n["id"]] = nid
        lines.append(f"    {nid}[{label_str}]")
    for e in edges:
        s = node_ids.get(e.get("source", ""))
        t = node_ids.get(e.get("target", ""))
        if s and t:
            lines.append(f"    {s} --> {t}")
    return "\n".join(lines)


def render_dot(nodes: list[dict], edges: list[dict]) -> str:
    lines = ["digraph G {", "    rankdir=LR;"]
    for n in nodes:
        nid = n.get("id", "").replace("-", "_").replace(".", "_")
        lines.append(f'    {nid} [label="{n.get("id", "")}"];')
    for e in edges:
        s = e.get("source", "").replace("-", "_").replace(".", "_")
        t = e.get("target", "").replace("-", "_").replace(".", "_")
        lines.append(f"    {s} -> {t};")
    lines.append("}")
    return "\n".join(lines)


def akatsuki_graph(action: str, nodes_json: str = "[]", edges_json: str = "[]",
                   source: str = "", target: str = "", format: str = "mermaid") -> str:
    try:
        nodes = json.loads(nodes_json) if isinstance(nodes_json, str) else nodes_json
        edges = json.loads(edges_json) if isinstance(edges_json, str) else edges_json
    except json.JSONDecodeError:
        return tool_error("Invalid JSON input")

    if action == "build":
        return tool_result(build_graph(nodes, edges))
    if action == "find_path":
        if not source or not target:
            return tool_error("source and target are required")
        paths = find_paths(nodes, edges, source, target)
        return tool_result({"paths": paths, "count": len(paths)})
    if action == "analyze":
        return tool_result(analyze(nodes, edges))
    if action == "render":
        if format == "dot":
            return tool_result({"format": "dot", "graph": render_dot(nodes, edges)})
        return tool_result({"format": "mermaid", "graph": render_mermaid(nodes, edges)})
    return tool_error(f"Unknown action: {action}")


def check_akatsuki_graph_requirements() -> bool:
    return True


registry.register(
    name="akatsuki_graph",
    toolset="akatsuki",
    schema=AKATSUKI_GRAPH_SCHEMA,
    handler=lambda args, **kw: akatsuki_graph(
        action=args["action"],
        nodes_json=args.get("nodes_json", "[]"),
        edges_json=args.get("edges_json", "[]"),
        source=args.get("source", ""),
        target=args.get("target", ""),
        format=args.get("format", "mermaid"),
    ),
    check_fn=check_akatsuki_graph_requirements,
    emoji="🕸️",
)