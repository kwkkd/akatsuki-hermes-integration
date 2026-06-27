"""Tool definitions and function registry for AKATSUKI agents."""

from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class ToolDef:
    name: str
    description: str
    parameters: dict = field(default_factory=dict)
    handler: Optional[Callable] = None
    category: str = "general"
    requires_approval: bool = False


TOOL_REGISTRY: dict[str, ToolDef] = {
    "nmap_scan": ToolDef(
        name="nmap_scan",
        description="Run an nmap scan against a target",
        parameters={"target": {"type": "string"}, "ports": {"type": "string"}},
        category="recon",
    ),
    "sqlmap_scan": ToolDef(
        name="sqlmap_scan",
        description="Run sqlmap against a URL",
        parameters={"url": {"type": "string"}},
        category="exploit",
    ),
    "nuclei_scan": ToolDef(
        name="nuclei_scan",
        description="Run nuclei template scanner",
        parameters={"target": {"type": "string"}, "templates": {"type": "string"}},
        category="recon",
    ),
    "hydra_brute": ToolDef(
        name="hydra_brute",
        description="Run hydra brute force",
        parameters={"target": {"type": "string"}, "service": {"type": "string"}, "userlist": {"type": "string"}, "passlist": {"type": "string"}},
        category="exploit",
    ),
    "generate_payload": ToolDef(
        name="generate_payload",
        description="Generate a reverse/bind shell payload",
        parameters={"language": {"type": "string"}, "payload_type": {"type": "string"}, "host": {"type": "string"}, "port": {"type": "integer"}},
        category="weapon",
    ),
    "recon_domain": ToolDef(
        name="recon_domain",
        description="Reconnaissance on a domain",
        parameters={"domain": {"type": "string"}},
        category="recon",
    ),
    "recon_ip": ToolDef(
        name="recon_ip",
        description="Reconnaissance on an IP address",
        parameters={"ip": {"type": "string"}},
        category="recon",
    ),
    "cve_lookup": ToolDef(
        name="cve_lookup",
        description="Look up a CVE by ID",
        parameters={"cve_id": {"type": "string"}},
        category="intel",
    ),
    "search_vulns": ToolDef(
        name="search_vulns",
        description="Search vulnerabilities by software name",
        parameters={"query": {"type": "string"}},
        category="intel",
    ),
    "generate_report": ToolDef(
        name="generate_report",
        description="Generate a markdown report",
        parameters={"title": {"type": "string"}, "data": {"type": "object"}},
        category="report",
    ),
    "build_attack_chain": ToolDef(
        name="build_attack_chain",
        description="Build a multi-step attack chain",
        parameters={"steps": {"type": "array"}},
        category="planning",
    ),
    "c2_config": ToolDef(
        name="c2_config",
        description="Build a C2 channel configuration",
        parameters={"protocol": {"type": "string"}, "server": {"type": "string"}, "port": {"type": "integer"}},
        category="c2",
    ),
    "swarm_execute": ToolDef(
        name="swarm_execute",
        description="Execute a full swarm operation",
        parameters={"target": {"type": "string"}},
        category="swarm",
    ),
}


def get_tool(name: str) -> Optional[ToolDef]:
    return TOOL_REGISTRY.get(name)


def list_tools(category: Optional[str] = None) -> list[ToolDef]:
    if category:
        return [t for t in TOOL_REGISTRY.values() if t.category == category]
    return list(TOOL_REGISTRY.values())


def register_tool(tool: ToolDef) -> bool:
    if tool.name in TOOL_REGISTRY:
        return False
    TOOL_REGISTRY[tool.name] = tool
    return True
