import json
import logging
import time
from pathlib import Path
from typing import Optional

from tools.registry import registry, tool_error, tool_result

logger = logging.getLogger(__name__)

AKATSUKI_REPLAY_SCHEMA = {
    "name": "akatsuki_replay",
    "description": "Operation Replay Engine — record, store, and replay operation logs step by step. Navigate forward/backward through operation phases and export as summary.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["record", "list", "step_forward", "step_backward", "current", "export"],
                "description": "record: save operation log; list: show saved operations; step_forward: advance one step; step_backward: go back one step; current: show current state; export: full export",
            },
            "operation_id": {
                "type": "string",
                "description": "Operation identifier",
            },
            "step_data": {
                "type": "string",
                "description": "JSON step data to record (for record action)",
            },
            "phase": {
                "type": "string",
                "description": "Phase name (for record action)",
            },
        },
        "required": ["action"],
    },
}

_replays: dict[str, list[dict]] = {}
_cursors: dict[str, int] = {}
_STORE_PATH = Path(__file__).resolve().parent.parent / "data" / "replays.json"


def _load():
    global _replays
    if _STORE_PATH.exists():
        try:
            _replays = json.loads(_STORE_PATH.read_text())
        except Exception:
            _replays = {}


def _save():
    _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _STORE_PATH.write_text(json.dumps(_replays, indent=2))


_load()


def record(operation_id: str, phase: str, step_data: str) -> dict:
    if operation_id not in _replays:
        _replays[operation_id] = []
        _cursors[operation_id] = -1
    try:
        data = json.loads(step_data) if isinstance(step_data, str) else step_data
    except json.JSONDecodeError:
        return {"error": "Invalid step_data JSON"}
    entry = {
        "phase": phase,
        "timestamp": int(time.time() * 1000),
        "data": data,
    }
    _replays[operation_id].append(entry)
    _cursors[operation_id] = len(_replays[operation_id]) - 1
    _save()
    return {"operation_id": operation_id, "step": len(_replays[operation_id]) - 1, "recorded": True}


def step_forward(operation_id: str) -> dict:
    if operation_id not in _replays or not _replays[operation_id]:
        return {"error": "No steps recorded for this operation"}
    _cursors.setdefault(operation_id, -1)
    if _cursors[operation_id] < len(_replays[operation_id]) - 1:
        _cursors[operation_id] += 1
    idx = _cursors[operation_id]
    return {
        "operation_id": operation_id,
        "step": idx,
        "total": len(_replays[operation_id]),
        "current": _replays[operation_id][idx],
        "progress": f"{idx + 1}/{len(_replays[operation_id])}",
    }


def step_backward(operation_id: str) -> dict:
    if operation_id not in _replays or not _replays[operation_id]:
        return {"error": "No steps recorded"}
    _cursors.setdefault(operation_id, 0)
    if _cursors[operation_id] > 0:
        _cursors[operation_id] -= 1
    idx = _cursors[operation_id]
    return {
        "operation_id": operation_id,
        "step": idx,
        "total": len(_replays[operation_id]),
        "current": _replays[operation_id][idx],
        "progress": f"{idx + 1}/{len(_replays[operation_id])}",
    }


def current(operation_id: str) -> dict:
    if operation_id not in _replays or not _replays[operation_id]:
        return {"error": "No steps recorded"}
    _cursors.setdefault(operation_id, 0)
    idx = _cursors[operation_id]
    return {
        "operation_id": operation_id,
        "step": idx,
        "total": len(_replays[operation_id]),
        "current": _replays[operation_id][idx],
    }


def list_operations() -> dict:
    summary = {}
    for op_id, steps in _replays.items():
        phases = list(dict.fromkeys(s["phase"] for s in steps))
        summary[op_id] = {
            "total_steps": len(steps),
            "phases": phases,
            "duration_ms": steps[-1]["timestamp"] - steps[0]["timestamp"] if len(steps) > 1 else 0,
        }
    return {"operations": summary, "count": len(summary)}


def export_operation(operation_id: str) -> dict:
    steps = _replays.get(operation_id, [])
    if not steps:
        return {"error": f"Operation not found: {operation_id}"}
    return {
        "operation_id": operation_id,
        "total_steps": len(steps),
        "steps": steps,
    }


def akatsuki_replay(action: str, operation_id: str = "",
                    step_data: str = "{}", phase: str = "") -> str:
    if action == "record":
        if not operation_id or not phase:
            return tool_error("operation_id and phase are required")
        return tool_result(record(operation_id, phase, step_data))
    if action == "list":
        return tool_result(list_operations())
    if action == "step_forward":
        if not operation_id:
            return tool_error("operation_id is required")
        return tool_result(step_forward(operation_id))
    if action == "step_backward":
        if not operation_id:
            return tool_error("operation_id is required")
        return tool_result(step_backward(operation_id))
    if action == "current":
        if not operation_id:
            return tool_error("operation_id is required")
        return tool_result(current(operation_id))
    if action == "export":
        if not operation_id:
            return tool_error("operation_id is required")
        return tool_result(export_operation(operation_id))
    return tool_error(f"Unknown action: {action}")


def check_akatsuki_replay_requirements() -> bool:
    return True


registry.register(
    name="akatsuki_replay",
    toolset="akatsuki",
    schema=AKATSUKI_REPLAY_SCHEMA,
    handler=lambda args, **kw: akatsuki_replay(
        action=args["action"],
        operation_id=args.get("operation_id", ""),
        step_data=args.get("step_data", "{}"),
        phase=args.get("phase", ""),
    ),
    check_fn=check_akatsuki_replay_requirements,
    emoji="⏪",
)