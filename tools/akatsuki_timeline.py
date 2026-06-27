import json
import logging
import time
from pathlib import Path
from typing import Optional

from tools.registry import registry, tool_error, tool_result

logger = logging.getLogger(__name__)


AKATSUKI_TIMELINE_SCHEMA = {
    "name": "akatsuki_timeline",
    "description": "Operation Timeline — record and visualize kill chain phases as Gantt charts. Track phase start/end times, status, and generate timeline reports.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["record", "list", "gantt", "export"],
                "description": "record: save phase completion; list: show all timelines; gantt: generate Mermaid Gantt chart; export: JSON export",
            },
            "operation_id": {
                "type": "string",
                "description": "Operation identifier",
            },
            "phase": {
                "type": "string",
                "description": "Phase name (required for record action)",
            },
            "status": {
                "type": "string",
                "enum": ["started", "completed", "failed", "skipped"],
                "description": "Phase status (required for record action)",
            },
            "details": {
                "type": "string",
                "description": "JSON details for this phase",
            },
        },
        "required": ["action"],
    },
}

_timelines: dict[str, list[dict]] = {}
_STORE_PATH = Path(__file__).resolve().parent.parent / "data" / "timelines.json"


def _load_timelines():
    global _timelines
    if _STORE_PATH.exists():
        try:
            _timelines = json.loads(_STORE_PATH.read_text())
        except Exception:
            _timelines = {}


def _save_timelines():
    _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _STORE_PATH.write_text(json.dumps(_timelines, indent=2))


_load_timelines()


def record(operation_id: str, phase: str, status: str, details: str = "") -> dict:
    if operation_id not in _timelines:
        _timelines[operation_id] = []
    entry = {
        "phase": phase,
        "status": status,
        "timestamp": int(time.time() * 1000),
        "details": details[:500] if details else "",
    }
    if status == "started":
        entry["started_at"] = entry["timestamp"]
    elif status in ("completed", "failed"):
        existing = _timelines[operation_id]
        for e in reversed(existing):
            if e["phase"] == phase and "started_at" in e:
                entry["duration_ms"] = entry["timestamp"] - e["started_at"]
                break
    _timelines[operation_id].append(entry)
    _save_timelines()
    return {"operation_id": operation_id, "phase": phase, "status": status, "recorded": True}


def list_timelines(operation_id: str = "") -> dict:
    if operation_id:
        return {"operation_id": operation_id, "phases": _timelines.get(operation_id, [])}
    summary = {}
    for op_id, phases in _timelines.items():
        completed = sum(1 for p in phases if p["status"] == "completed")
        failed = sum(1 for p in phases if p["status"] == "failed")
        summary[op_id] = {"total_phases": len(phases), "completed": completed, "failed": failed}
    return {"operations": summary, "count": len(summary)}


def export_timeline(operation_id: str) -> dict:
    phases = _timelines.get(operation_id, [])
    if not phases:
        return {"error": f"Operation not found: {operation_id}"}
    total_duration = 0
    phase_details = []
    for p in phases:
        if "duration_ms" in p:
            total_duration += p["duration_ms"]
        phase_details.append(p)
    return {
        "operation_id": operation_id,
        "total_phases": len(phase_details),
        "total_duration_ms": total_duration,
        "phases": phase_details,
    }


def generate_gantt(operation_id: str) -> str:
    phases = _timelines.get(operation_id, [])
    if not phases:
        return "No data for operation: " + operation_id
    lines = ["gantt", f"    title Operation Timeline: {operation_id}", "    dateFormat X", "    axisFormat %s"]
    for p in phases:
        if "started_at" in p and "duration_ms" in p:
            start_secs = p["started_at"] // 1000
            dur_secs = max(p["duration_ms"] // 1000, 1)
            status_label = p["status"]
            lines.append(f"    section {p['phase']}")
            lines.append(f"    {status_label} :{start_secs}, {dur_secs}s")
    return "\n".join(lines)


def akatsuki_timeline(action: str, operation_id: str = "", phase: str = "",
                      status: str = "completed", details: str = "") -> str:
    if action == "record":
        if not operation_id or not phase:
            return tool_error("operation_id and phase are required")
        return tool_result(record(operation_id, phase, status, details))
    if action == "list":
        return tool_result(list_timelines(operation_id))
    if action == "gantt":
        if not operation_id:
            return tool_error("operation_id is required")
        chart = generate_gantt(operation_id)
        return tool_result({"operation_id": operation_id, "gantt_chart": chart})
    if action == "export":
        if not operation_id:
            return tool_error("operation_id is required")
        return tool_result(export_timeline(operation_id))
    return tool_error(f"Unknown action: {action}")


def check_akatsuki_timeline_requirements() -> bool:
    return True


registry.register(
    name="akatsuki_timeline",
    toolset="akatsuki",
    schema=AKATSUKI_TIMELINE_SCHEMA,
    handler=lambda args, **kw: akatsuki_timeline(
        action=args["action"],
        operation_id=args.get("operation_id", ""),
        phase=args.get("phase", ""),
        status=args.get("status", "completed"),
        details=args.get("details", ""),
    ),
    check_fn=check_akatsuki_timeline_requirements,
    emoji="📅",
)