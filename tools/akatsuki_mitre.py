import json
import logging
from pathlib import Path

from tools.registry import registry, tool_error, tool_result

logger = logging.getLogger(__name__)


def _load_attack_db() -> dict:
    db_path = Path(__file__).resolve().parent.parent / "data" / "mitre_attack.yaml"
    if db_path.exists():
        try:
            import yaml
            with open(db_path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Failed to load MITRE DB: {e}")
    return {}


ATTACK_DB = _load_attack_db()

TOOL_MAPPING = {
    "akatsuki_recon": ["T1595", "T1590", "T1046"],
    "akatsuki_vuln": ["T1190", "T1068"],
    "akatsuki_payload": ["T1059", "T1027"],
    "akatsuki_evasion": ["T1562", "T1027", "T1140"],
    "akatsuki_c2": ["T1071", "T1090", "T1573"],
    "akatsuki_chain": ["T1190", "T1068", "T1562", "T1041"],
    "akatsuki_report": [],
    "akatsuki_dept": ["T1588", "T1587"],
    "akatsuki_obsidian": [],
}


AKATSUKI_MITRE_SCHEMA = {
    "name": "akatsuki_mitre",
    "description": "MITRE ATT&CK mapping — map findings, tools, or techniques to MITRE ATT&CK framework IDs. Generate heatmap data and coverage reports.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["map_tool", "map_finding", "lookup", "coverage", "heatmap"],
                "description": "Action to perform",
            },
            "tool_name": {
                "type": "string",
                "description": "AKATSUKI tool name to map (for map_tool action)",
            },
            "finding": {
                "type": "string",
                "description": "Finding description to map (for map_finding action)",
            },
            "technique_id": {
                "type": "string",
                "description": "ATT&CK technique ID (e.g., T1190) for lookup action",
            },
            "phase": {
                "type": "string",
                "description": "Filter by ATT&CK phase for heatmap (optional)",
            },
        },
        "required": ["action"],
    },
}


def map_tool(tool_name: str) -> dict:
    techniques = TOOL_MAPPING.get(tool_name, [])
    mapped = []
    for tid in techniques:
        for phase, techniques_in_phase in ATTACK_DB.items():
            if tid in techniques_in_phase:
                info = techniques_in_phase[tid]
                mapped.append({
                    "technique_id": tid,
                    "name": info.get("name", ""),
                    "phase": info.get("phase", phase),
                    "platforms": info.get("platforms", []),
                })
    return {"tool": tool_name, "techniques": mapped, "count": len(mapped)}


def map_finding(finding: str) -> dict:
    finding_lower = finding.lower()
    matches = []
    for phase, techniques in ATTACK_DB.items():
        for tid, info in techniques.items():
            name = info.get("name", "").lower()
            if any(kw in finding_lower for kw in name.split()):
                matches.append({
                    "technique_id": tid,
                    "name": info.get("name", ""),
                    "phase": info.get("phase", phase),
                    "confidence": "medium",
                })
    return {"finding": finding, "matches": matches, "count": len(matches)}


def lookup(technique_id: str) -> dict:
    tid_upper = technique_id.upper()
    for phase, techniques in ATTACK_DB.items():
        if tid_upper in techniques:
            info = techniques[tid_upper]
            return {
                "technique_id": tid_upper,
                "name": info.get("name", ""),
                "phase": info.get("phase", phase),
                "platforms": info.get("platforms", []),
            }
    return {"technique_id": tid_upper, "error": "Technique not found"}


def coverage() -> dict:
    all_techniques = set()
    for tool_name, tids in TOOL_MAPPING.items():
        for tid in tids:
            all_techniques.add(tid)
    total_techniques = sum(len(v) for v in ATTACK_DB.values())
    return {
        "total_techniques_in_db": total_techniques,
        "covered_techniques": len(all_techniques),
        "coverage_pct": round(len(all_techniques) / max(total_techniques, 1) * 100, 1),
        "covered_ids": sorted(all_techniques),
        "phase_breakdown": {
            phase: {
                "total": len(techniques),
                "covered": len([t for t in techniques if t in all_techniques]),
            }
            for phase, techniques in ATTACK_DB.items()
        },
    }


def heatmap(phase: str = "") -> dict:
    data = {}
    for p, techniques in ATTACK_DB.items():
        if phase and p != phase:
            continue
        data[p] = [
            {
                "id": tid,
                "name": info.get("name", ""),
                "covered": any(tid in v for v in TOOL_MAPPING.values()),
            }
            for tid, info in techniques.items()
        ]
    return {"heatmap": data, "total_phases": len(data)}


def akatsuki_mitre(action: str, tool_name: str = "", finding: str = "",
                   technique_id: str = "", phase: str = "") -> str:
    if action == "map_tool":
        if not tool_name:
            return tool_error("tool_name is required")
        return tool_result(map_tool(tool_name))
    if action == "map_finding":
        if not finding:
            return tool_error("finding is required")
        return tool_result(map_finding(finding))
    if action == "lookup":
        if not technique_id:
            return tool_error("technique_id is required")
        return tool_result(lookup(technique_id))
    if action == "coverage":
        return tool_result(coverage())
    if action == "heatmap":
        return tool_result(heatmap(phase))
    return tool_error(f"Unknown action: {action}")


def check_akatsuki_mitre_requirements() -> bool:
    return True


registry.register(
    name="akatsuki_mitre",
    toolset="akatsuki",
    schema=AKATSUKI_MITRE_SCHEMA,
    handler=lambda args, **kw: akatsuki_mitre(
        action=args["action"],
        tool_name=args.get("tool_name", ""),
        finding=args.get("finding", ""),
        technique_id=args.get("technique_id", ""),
        phase=args.get("phase", ""),
    ),
    check_fn=check_akatsuki_mitre_requirements,
    emoji="📊",
)