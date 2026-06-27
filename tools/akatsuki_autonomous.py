import json
import logging
import time
from pathlib import Path
from typing import Optional

from tools.registry import registry, tool_error, tool_result

logger = logging.getLogger(__name__)

AUTONOMOUS_SCHEMA = {
    "name": "akatsuki_autonomous",
    "description": "AKATSUKI Autonomous Operation Agent — analyzes a target objective, decomposes into phases, executes each phase using available tools, evaluates results, and produces a final operation summary.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["plan", "execute", "summarize", "run"],
                "description": "plan: analyze target and create phase plan; execute: run a plan; summarize: produce final report; run: plan + execute + summarize in one call",
            },
            "target": {
                "type": "string",
                "description": "Target domain/IP for the operation",
            },
            "objective": {
                "type": "string",
                "description": "Operation objective description",
            },
            "phases": {
                "type": "string",
                "description": "JSON array of phase names to include (default: all)",
            },
            "plan_json": {
                "type": "string",
                "description": "JSON plan from previous plan() call (for execute action)",
            },
        },
        "required": ["action"],
    },
}


def plan(target: str, objective: str, phases_str: str = "") -> dict:
    obj_lower = objective.lower()
    all_phases = [
        {"name": "recon", "description": "OSINT reconnaissance", "tools": ["akatsuki_recon"]},
        {"name": "scan", "description": "Vulnerability scanning", "tools": ["akatsuki_vuln"]},
        {"name": "payload", "description": "Payload generation", "tools": ["akatsuki_payload"]},
        {"name": "evasion", "description": "Evasion preparation", "tools": ["akatsuki_evasion"]},
        {"name": "c2", "description": "C2 infrastructure", "tools": ["akatsuki_c2"]},
        {"name": "analysis", "description": "Department analysis", "tools": ["akatsuki_dept"]},
        {"name": "report", "description": "Report generation", "tools": ["akatsuki_report"]},
    ]
    if phases_str:
        try:
            selected = json.loads(phases_str) if isinstance(phases_str, str) else phases_str
            all_phases = [p for p in all_phases if p["name"] in selected]
        except Exception:
            pass
    if "web" in obj_lower:
        all_phases.insert(1, {"name": "web_scan", "description": "Web vulnerability scan", "tools": ["akatsuki_vuln"]})
    if "ad" in obj_lower or "domain" in obj_lower:
        all_phases.insert(1, {"name": "ad_recon", "description": "AD reconnaissance", "tools": ["akatsuki_dept"]})
    return {
        "target": target,
        "objective": objective,
        "phases": all_phases,
        "created": time.time(),
    }


def execute_plan(target: str, plan: dict) -> dict:
    results = {}
    for phase in plan.get("phases", []):
        phase_name = phase["name"]
        phase_results = []
        for tool_name in phase.get("tools", []):
            try:
                import importlib
                mod = importlib.import_module(f"tools.{tool_name}")
                handler = getattr(mod, tool_name, None)
                if handler:
                    if tool_name == "akatsuki_recon":
                        res = handler(target)
                    elif tool_name == "akatsuki_vuln":
                        res = handler(target)
                    elif tool_name == "akatsuki_payload":
                        res = handler("python", target, 4444)
                    elif tool_name == "akatsuki_evasion":
                        res = handler("amsi_bypass")
                    elif tool_name == "akatsuki_c2":
                        res = handler("cs_profile", target)
                    elif tool_name == "akatsuki_dept":
                        res = handler("list")
                    elif tool_name == "akatsuki_report":
                        res = handler(target=target, objective=plan.get("objective", ""))
                    else:
                        res = handler(target=target)
                    try:
                        phase_results.append(json.loads(res))
                    except Exception:
                        phase_results.append({"raw": str(res)})
                else:
                    phase_results.append({"error": f"Handler not found: {tool_name}"})
            except Exception as e:
                phase_results.append({"error": str(e)})
        results[phase_name] = {
            "tools_executed": len(phase.get("tools", [])),
            "results": phase_results,
        }
    return {"target": target, "phase_results": results, "phases_completed": len(results)}


def summarize(results: dict) -> str:
    lines = [f"# AKATSUKI Autonomous Operation Report", f""]
    lines.append(f"**Target:** {results.get('target', 'N/A')}")
    lines.append(f"**Phases Completed:** {results.get('phases_completed', 0)}")
    lines.append(f"")
    phase_results = results.get("phase_results", {})
    for phase_name, phase_data in phase_results.items():
        lines.append(f"## Phase: {phase_name}")
        lines.append(f"Tools: {phase_data.get('tools_executed', 0)}")
        for res in phase_data.get("results", []):
            if isinstance(res, dict):
                lines.append(f"- {json.dumps(res)[:200]}")
        lines.append(f"")
    return "\n".join(lines)


def akatsuki_autonomous(action: str, target: str = "", objective: str = "",
                        phases: str = "", plan_json: str = "") -> str:
    if action == "plan":
        if not target:
            return tool_error("target is required for plan action")
        p = plan(target, objective, phases)
        return tool_result(p)

    if action == "execute":
        if not target:
            return tool_error("target is required for execute action")
        try:
            p = json.loads(plan_json) if plan_json else plan(target, objective, phases)
        except json.JSONDecodeError:
            return tool_error("Invalid plan_json")
        results = execute_plan(target, p)
        return tool_result(results)

    if action == "summarize":
        try:
            results = json.loads(plan_json) if plan_json else {}
        except json.JSONDecodeError:
            results = {}
        report = summarize(results)
        return tool_result({"operation_report": report})

    if action == "run":
        if not target:
            return tool_error("target is required for run action")
        p = plan(target, objective, phases)
        results = execute_plan(target, p)
        report = summarize(results)
        return tool_result({
            "plan": p,
            "execution": results,
            "report": report,
        })

    return tool_error(f"Unknown action: {action}")


def check_akatsuki_autonomous_requirements() -> bool:
    return True


registry.register(
    name="akatsuki_autonomous",
    toolset="akatsuki",
    schema=AUTONOMOUS_SCHEMA,
    handler=lambda args, **kw: akatsuki_autonomous(
        action=args["action"],
        target=args.get("target", ""),
        objective=args.get("objective", ""),
        phases=args.get("phases", ""),
        plan_json=args.get("plan_json", ""),
    ),
    check_fn=check_akatsuki_autonomous_requirements,
    emoji="🤖",
)