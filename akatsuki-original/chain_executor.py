import time, json, sys, os, importlib
sys.path.insert(0, os.path.dirname(__file__))
from chain_builder import AttackChain, ChainTask

class ChainExecutor:
    def __init__(self, verbose: bool = True):
        self.verbose = verbose; self.results = {}; self.tool_runner = None
    def _log(self, msg: str):
        if self.verbose: print(f"  [CHAIN] {msg}")
    def _get_tool_runner(self):
        if self.tool_runner is None:
            mod = importlib.import_module("tool_runner")
            self.tool_runner = mod.ToolRunner()
        return self.tool_runner
    def _run_task(self, task: ChainTask, target: str) -> dict:
        self._log(f"Running: {task.name} ({task.tool})")
        if task.tool == "nmap":
            tr = self._get_tool_runner()
            result = tr.run_nmap(target, " ".join(task.args[1:-1]) if len(task.args) > 1 else "-sV -sC")
            return {"name": task.name, "success": result.get("success", False), "data": result}
        elif task.tool == "sqlmap":
            tr = self._get_tool_runner()
            url = task.args[1] if len(task.args) > 1 else f"http://{target}"
            result = tr.run_sqlmap(url)
            return {"name": task.name, "success": True, "data": result}
        elif task.tool == "nuclei":
            tr = self._get_tool_runner()
            url = f"http://{target}"
            result = tr.run_nuclei(url)
            return {"name": task.name, "success": True, "data": result}
        else:
            tr = self._get_tool_runner()
            result = tr.run(task.tool, task.args, task.timeout)
            return {"name": task.name, "success": result.get("success", False), "data": result}
    def execute(self, chain: AttackChain) -> dict:
        start = time.time()
        phase_results = {}
        phases = {}
        for task in chain.tasks: phases.setdefault(task.phase, []).append(task)
        for phase_name in ["recon", "weaponize", "deliver", "exploit", "c2", "actions"]:
            if phase_name not in phases: continue
            self._log(f"\n{'='*40}\nPhase: {phase_name.upper()}\n{'='*40}")
            phase_tasks = phases[phase_name]; phase_success = True
            for task in phase_tasks:
                deps_met = all(dep in self.results and self.results[dep].get("success") for dep in task.depends_on)
                if task.depends_on and not deps_met:
                    self._log(f"SKIP {task.name}: deps not met {task.depends_on}")
                    self.results[task.name] = {"name": task.name, "success": False, "skipped": True}; continue
                for attempt in range(task.retry):
                    result = self._run_task(task, chain.target)
                    if result["success"]: self.results[task.name] = result; break
                    self._log(f"Retry {attempt+1}/{task.retry} for {task.name}")
                else:
                    self.results[task.name] = result
                    if task.stop_on_fail: phase_success = False; break
            phase_results[phase_name] = {"tasks": len(phase_tasks), "success": phase_success, "duration": time.time() - start}
        duration = time.time() - start
        return {"target": chain.target, "objective": chain.objective, "duration": duration, "phases": phase_results, "task_results": self.results, "success": all(r.get("success") for r in self.results.values() if not r.get("skipped"))}
    def rollback(self, failed_phase: str):
        self._log(f"Rolling back from phase: {failed_phase}")


