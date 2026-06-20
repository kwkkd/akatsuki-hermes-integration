"""
あかつき·暁 AKATSUKI Team — Ransomware Syndicate Simulator (Collaborative)
==============================================================
13 departments with REAL collaboration: 2-pass peer review system.
Round 1: independent analysis
Round 2: each agent sees peer results, critiques, refines, reaches consensus
"""
import json, time, httpx
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed
from team_agents import ALL_AGENTS

API_URL = "http://localhost:8000/v1"
MODEL = "hacker-ai"

@dataclass
class Operation:
    id: str
    target: str
    objective: str
    plan: str = ""
    findings: List[Dict] = field(default_factory=list)
    started_at: float = 0.0
    completed_at: float = 0.0
    final_report: str = ""

class AgentWorker:
    def __init__(self, name: str, role):
        self.name = name
        self.title = role.title
        self.sys_prompt = role.system_prompt
        self.expertise = role.expertise
        self.tools = role.tools

    def execute(self, objective: str, context: str = "", max_tokens: int = 2048) -> str:
        prompt = (
            f"### System:\n{self.sys_prompt}\n\n### User:\n[MISSION]\n{objective}\n\n"
            + (f"[CONTEXT]\n{context}\n\n" if context else "")
            + f"[YOUR ROLE]\n{self.title}\n"
            + f"[EXPERTISE]\n{', '.join(self.expertise)}\n"
            + f"[TOOLS AVAILABLE]\n{', '.join(self.tools)}\n\nExecute.\n\n### Assistant:\n"
        )
        try:
            resp = httpx.post(f"{API_URL}/chat/completions", json={
                "model": MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3, "max_tokens": max_tokens, "stream": False,
            }, timeout=120)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"[ERROR] {self.name}: {e}"
        return ""

class HackerTeam:
    def __init__(self):
        self.workers = {n: AgentWorker(n, r) for n, r in ALL_AGENTS.items()}
        self.operation: Optional[Operation] = None

    def _run(self, agent: str, obj: str, ctx: str = "", mt: int = 2048) -> str:
        w = self.workers.get(agent)
        return f"[ERROR] Unknown: {agent}" if not w else w.execute(obj, ctx, mt)

    def _parallel(self, tasks: List[tuple]) -> Dict[str, str]:
        results = {}
        with ThreadPoolExecutor(max_workers=len(tasks)) as ex:
            fm = {ex.submit(self._run, a, o, c): a for a, o, c in tasks}
            for f in as_completed(fm):
                results[fm[f]] = f.result()
        return results

    def _collab(self, agents: List[str], objectives: Dict[str, str], phase_context: str = "") -> Dict[str, str]:
        peers_str = "  |  ".join([f"{a}: {objectives.get(a,'')[:80]}" for a in agents])
        tasks = [
            (a,
             f"{objectives[a]}\n\n"
             f"TEAM CONTEXT — other departments in this phase:\n{peers_str}\n\n"
             f"COLLABORATION RULES:\n"
             f"1. Address each peer department's perspective explicitly\n"
             f"2. Identify potential conflicts with peer approaches\n"
             f"3. Propose cross-department optimizations\n"
             f"4. If peers would disagree, explain why your approach is still correct\n"
             f"5. End with: 'CONSENSUS: [agree/disagree with peers, and why]'",
             phase_context)
            for a in agents
        ]
        return self._parallel(tasks)

    def run_operation(self, target: str, objective: str, verbose: bool = True) -> Operation:
        op = Operation(id=f"OP-{int(time.time())}", target=target, objective=objective, started_at=time.time())
        self.operation = op
        dec = lambda m: print(f"  {m}") if verbose else None

        print(f"\n{'='*62}")
        print(f"  RANSOMWARE SYNDICATE: {op.id}")
        print(f"  Target: {target}")
        print(f"  Objective: {objective}")
        print(f"  13 depts | 2-pass collaboration | ThreadPoolExecutor")
        print(f"{'='*62}")

        # ── Phase 1: Leadership (sequential chain of command) ──
        print(f"\n[PHASE 1/5] LEADERSHIP CHAIN...")
        plan = self._run("boss", f"Approve/reject: {target}\n{objective}\nRisk & directives.")
        coo = self._run("coo", f"Plan: {target}\n{objective}\nBoss: {plan[:1000]}\nDept coordination.")
        op.plan = f"[BOSS]\n{plan}\n\n[COO]\n{coo}"
        dec("BOSS → COO chain complete")

        # ── Phase 2: Collaborative — Initial Access Strategy (1-pass) ──
        print(f"\n[PHASE 2/5] COLLABORATIVE: INITIAL ACCESS STRATEGY")
        print(f"  Agents: initial_access + rnd_exploit + cctv + finance (parallel, 1-pass)")
        t0 = time.time()
        p2 = self._collab(
            ["initial_access", "rnd_exploit", "cctv", "finance"],
            {
                "initial_access": f"Access strategy for: {target}\nCOO: {coo[:800]}",
                "rnd_exploit": f"Exploit chain for: {target}\nContext: {objective[:500]}",
                "cctv": f"Physical/surveillance recon: {target}\nCameras, access controls, IoT",
                "finance": f"Budget & revenue: {target}\nCosts, expected return, risk",
            },
            f"Target: {target}\nCOO plan: {coo[:500]}"
        )
        for a in p2:
            op.findings.append({"phase": "initial_access", "agent": a, "result": p2[a][:500]})
        dec(f"Phase 2 done ({time.time()-t0:.0f}s)")

        # ── Phase 3: Collaborative — Core Execution (1-pass) ──
        print(f"\n[PHASE 3/5] COLLABORATIVE: CORE EXECUTION")
        print(f"  Agents: post_exploit + rnd_malware + infrastructure (parallel, 1-pass)")
        t0 = time.time()
        p3 = self._collab(
            ["post_exploit", "rnd_malware", "infrastructure"],
            {
                "post_exploit": f"Post-exploit: {target}\nAD dominance, data theft, backup destroy",
                "rnd_malware": f"Ransomware builder: {target}\nEncryption, propagation, evasion, C2",
                "infrastructure": f"C2 infra: {target}\nHosting, domains, proxy, anonymization",
            },
            f"Target: {target}\nAccess plan: {p2.get('initial_access','')[:500]}"
        )
        for a in p3:
            op.findings.append({"phase": "core_execution", "agent": a, "result": p3[a][:500]})
        dec(f"Phase 3 done ({time.time()-t0:.0f}s)")

        # ── Phase 4: Collaborative — Exit & Monetization (1-pass) ──
        print(f"\n[PHASE 4/5] COLLABORATIVE: EXIT & MONETIZATION")
        print(f"  Agents: negotiation + intel_pr + money_laundering + raas (parallel, 1-pass)")
        t0 = time.time()
        p4 = self._collab(
            ["negotiation", "intel_pr", "money_laundering", "raas_affiliate"],
            {
                "negotiation": f"Negotiation: {target}\nDemand, pressure, deadline, leak threats",
                "intel_pr": f"Intel & PR: {target}\nLeak site, media, competitor intel",
                "money_laundering": f"Laundering: {target}\nMixing, layering, cash-out, conversion",
                "raas_affiliate": f"RaaS classify: {target}\nTier, revenue share, support",
            },
            f"Target: {target}\nPost-exploit plan: {p3.get('post_exploit','')[:500]}"
        )
        for a in p4:
            op.findings.append({"phase": "exit_monetization", "agent": a, "result": p4[a][:500]})
        dec(f"Phase 4 done ({time.time()-t0:.0f}s)")

        # ── Phase 5: COO consolidates ──
        print(f"\n[PHASE 5/5] COO: FINAL REPORT...")
        all_results = {**p2, **p3, **p4}
        op.final_report = self._run("coo",
            f"Consolidate all department findings into final ransomware op report for: {target}.\nResolve any inter-department conflicts. Provide unified strategy.",
            json.dumps(all_results, indent=2, ensure_ascii=False)[:5000], mt=4096)

        op.completed_at = time.time()
        dur = op.completed_at - op.started_at
        print(f"\n{'='*62}")
        print(f"  OPERATION COMPLETE")
        print(f"  Duration: {dur:.0f}s (1-pass collab, 0 extra LLM calls)")
        print(f"  Departments: 13 | Collaborations: 3 phases | 1-pass")
        print(f"{'='*62}")
        return op

    def chat(self, user_input: str, history: List[Dict] = None) -> str:
        lower = user_input.lower()
        if any(kw in lower for kw in ["작전", "공격", "침투", "해킹", "op", "ransom", "target"]):
            try:
                r = httpx.post(f"{API_URL}/chat/completions", json={
                    "model": MODEL, "messages": [
                        {"role": "system", "content": "Extract target+objective. Return ONLY JSON: {\"target\":\"...\",\"objective\":\"...\"}"},
                        {"role": "user", "content": user_input}
                    ], "temperature": 0.1, "max_tokens": 256
                }, timeout=30)
                j = json.loads(r.json()["choices"][0]["message"]["content"].strip().removeprefix("```json").removesuffix("```").strip())
                target, obj = j.get("target", user_input[:60]), j.get("objective", user_input)
            except:
                target, obj = user_input[:60], user_input
            op = self.run_operation(target, obj)
            return f"## {op.id}\nTarget: {op.target}\n\n{op.final_report[:3000]}..."
        elif any(kw in lower for kw in ["상태", "status", "진행"]):
            if self.operation:
                return (f"Active: {self.operation.id}\nTarget: {self.operation.target}\nElapsed: {time.time()-self.operation.started_at:.0f}s\nFindings: {len(self.operation.findings)}")
            return "No active operation."
        else:
            return self._run("intel_pr", f"Answer: {user_input}")


def main():
    team = HackerTeam()
    try:
        httpx.get(f"{API_URL}/models", timeout=5)
    except:
        print("[WARN] Start: python api_server.py")

    print("=" * 62)
    print("  HACKERAI RANSOMWARE SYNDICATE")
    print("  13 departments | 2-pass peer review collaboration")
    print("=" * 62)
    print("  '작전 [target]'  - Full collaborative ransomware op")
    print("  '상태'          - Check operation status")
    print("  any question    - Ask intel department")
    print("  'quit'          - Exit")
    print("=" * 62)

    while True:
        try:
            user = input("\n[CMD] ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user or user.lower() in ("quit", "exit", "종료"):
            break
        print(f"\n[SYNDICATE] Processing...\n")
        print(f"[REPORT]\n{team.chat(user)}\n")


if __name__ == "__main__":
    main()
