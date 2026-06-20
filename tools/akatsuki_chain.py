import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from tools.registry import registry, tool_error, tool_result

logger = logging.getLogger(__name__)


@dataclass
class ChainTask:
    name: str
    phase: str
    tool: str
    args: list = field(default_factory=list)
    depends_on: list = field(default_factory=list)
    timeout: int = 300
    retry: int = 2
    stop_on_fail: bool = False


@dataclass
class AttackChain:
    target: str
    objective: str
    tasks: list = field(default_factory=list)


PHASE_ORDER = ["recon", "weaponize", "deliver", "exploit", "c2", "actions"]


def build_chain(target: str, objective: str) -> AttackChain:
    chain = AttackChain(target=target, objective=objective)
    obj_lower = objective.lower()
    chain.tasks.append(ChainTask(
        name="nmap_scan", phase="recon", tool="nmap",
        args=["-sV", "-sC", "-p-", target], timeout=600, retry=1,
    ))
    if "web" in obj_lower or "sqli" in obj_lower or "xss" in obj_lower:
        chain.tasks.append(ChainTask(
            name="sqlmap", phase="exploit", tool="sqlmap",
            args=["-u", f"http://{target}", "--batch", "--level", "3"],
            depends_on=["nmap_scan"], timeout=900,
        ))
        chain.tasks.append(ChainTask(
            name="nuclei_web", phase="exploit", tool="nuclei",
            args=["-u", f"http://{target}", "-t", "cves", "-json", "-silent"],
            depends_on=["nmap_scan"], timeout=600,
        ))
    if "ad" in obj_lower or "domain" in obj_lower or "kerberos" in obj_lower:
        chain.tasks.append(ChainTask(
            name="ad_recon", phase="recon", tool="nmap",
            args=["-p", "88,389,445,636,3268,3269", "-sV", target],
            depends_on=["nmap_scan"], timeout=300,
        ))
    return chain


def _run_tool(tool: str, args: list, timeout: int) -> dict:
    import subprocess
    try:
        result = subprocess.run(
            [tool] + args, capture_output=True, text=True, timeout=timeout,
        )
        return {
            "tool": tool,
            "args": args,
            "returncode": result.returncode,
            "stdout": result.stdout[:5000],
            "stderr": result.stderr[:2000],
            "success": result.returncode == 0,
        }
    except FileNotFoundError:
        return {"tool": tool, "error": f"Tool not found: {tool}", "success": False}
    except subprocess.TimeoutExpired:
        return {"tool": tool, "error": f"Timeout after {timeout}s", "success": False}
    except Exception as e:
        return {"tool": tool, "error": str(e), "success": False}


def _run_task(task: ChainTask, target: str) -> dict:
    logger.info("Running: %s (%s)", task.name, task.tool)
    return _run_tool(task.tool, task.args, task.timeout)


def execute_chain(chain: AttackChain) -> dict:
    start = time.time()
    results = {}
    phases = {}
    for task in chain.tasks:
        phases.setdefault(task.phase, []).append(task)
    phase_results = {}
    for phase_name in PHASE_ORDER:
        if phase_name not in phases:
            continue
        phase_tasks = phases[phase_name]
        phase_success = True
        for task in phase_tasks:
            deps_met = all(
                dep in results and results[dep].get("success")
                for dep in task.depends_on
            )
            if task.depends_on and not deps_met:
                logger.info("SKIP %s: deps unmet %s", task.name, task.depends_on)
                results[task.name] = {
                    "name": task.name, "success": False, "skipped": True,
                }
                continue
            for attempt in range(task.retry):
                result = _run_task(task, chain.target)
                if result["success"]:
                    results[task.name] = result
                    break
                logger.info("Retry %d/%d for %s", attempt + 1, task.retry, task.name)
            else:
                results[task.name] = result
                if task.stop_on_fail:
                    phase_success = False
                    break
        phase_results[phase_name] = {
            "tasks": len(phase_tasks),
            "success": phase_success,
        }
    duration = time.time() - start
    all_success = all(
        r.get("success") for r in results.values() if not r.get("skipped")
    )
    return {
        "target": chain.target,
        "objective": chain.objective,
        "duration_seconds": round(duration, 1),
        "phases": phase_results,
        "task_results": results,
        "success": all_success,
    }


AKATSUKI_CHAIN_SCHEMA = {
    "name": "akatsuki_chain",
    "description": "AKATSUKI Kill Chain Builder & Executor — build or load a multi-phase attack chain (recon → weaponize → deliver → exploit → c2 → actions), execute it against a target, and return phase-by-phase results with automatic dependency resolution and retry logic.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["build", "execute", "list_playbooks"],
                "description": "build: create a chain from objective; execute: run a chain against target; list_playbooks: show available playbooks",
            },
            "target": {
                "type": "string",
                "description": "Target IP/domain (required for build/execute)",
            },
            "objective": {
                "type": "string",
                "description": "Operation objective, e.g. 'web penetration test' or 'AD takeover' (default: full pentest)",
            },
            "playbook": {
                "type": "string",
                "description": "Playbook name to load (optional; if omitted, auto-builds from objective)",
            },
        },
        "required": ["action"],
    },
}


def akatsuki_chain(action: str, target: str = "", objective: str = "Full penetration test",
                   playbook: str = None) -> str:
    if action == "list_playbooks":
        try:
            from akatsuki_config import CONFIG
            pb_dir = Path(CONFIG.paths.playbooks)
        except ImportError:
            pb_dir = Path("playbooks")
        if pb_dir.exists():
            playbooks = sorted([f.stem for f in pb_dir.glob("*.yaml")])
        else:
            playbooks = ["external_pentest", "web_full_chain", "ransomware_sim",
                         "ad_takeover", "cctv_chain", "cloud_escape"]
        return tool_result({"playbooks": playbooks})
    if action == "build":
        if not target:
            return tool_error("target is required for build action")
        chain = build_chain(target, objective)
        return tool_result({
            "target": target,
            "objective": objective,
            "phases": list(dict.fromkeys(t.phase for t in chain.tasks)),
            "tasks": [
                {"name": t.name, "phase": t.phase, "tool": t.tool,
                 "depends_on": t.depends_on}
                for t in chain.tasks
            ],
        })
    if action == "execute":
        if not target:
            return tool_error("target is required for execute action")
        if playbook:
            try:
                from chain_builder import ChainBuilder
                builder = ChainBuilder()
                chain = builder.load_playbook(
                    f"playbooks/{playbook}.yaml" if not playbook.endswith(".yaml") else playbook,
                    target,
                )
            except ImportError:
                chain = build_chain(target, objective)
            except FileNotFoundError:
                return tool_error(f"Playbook not found: {playbook}")
        else:
            chain = build_chain(target, objective)
        result = execute_chain(chain)
        return tool_result(result)
    return tool_error(f"Unknown action: {action}")


def check_akatsuki_chain_requirements() -> bool:
    return True


registry.register(
    name="akatsuki_chain",
    toolset="akatsuki",
    schema=AKATSUKI_CHAIN_SCHEMA,
    handler=lambda args, **kw: akatsuki_chain(
        action=args["action"],
        target=args.get("target", ""),
        objective=args.get("objective", "Full penetration test"),
        playbook=args.get("playbook"),
    ),
    check_fn=check_akatsuki_chain_requirements,
    emoji="⛓️",
)
