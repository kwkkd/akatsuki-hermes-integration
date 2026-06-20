import sys
import os
import yaml
import time
from pathlib import Path
from dataclasses import dataclass, field
sys.path.insert(0, os.path.dirname(__file__))
from akatsuki_config import CONFIG

@dataclass
class ChainTask:
    name: str; phase: str; tool: str
    args: list = field(default_factory=list)
    depends_on: list = field(default_factory=list)
    timeout: int = 300; retry: int = 2; stop_on_fail: bool = False
    condition: str = ""

@dataclass
class AttackChain:
    target: str; objective: str
    tasks: list = field(default_factory=list)
    created_at: float = 0.0

class ChainBuilder:
    PHASES = ["recon", "weaponize", "deliver", "exploit", "c2", "actions"]
    def __init__(self): self.playbook_dir = Path(CONFIG.paths.playbooks)
    def build(self, target: str, objective: str) -> AttackChain:
        chain = AttackChain(target=target, objective=objective, created_at=time.time())
        obj_lower = objective.lower()
        chain.tasks.append(ChainTask(name="nmap_scan", phase="recon", tool="nmap", args=["-sV", "-sC", "-p-", target], timeout=600, retry=1))
        if "web" in obj_lower or "sqli" in obj_lower or "xss" in obj_lower:
            chain.tasks.append(ChainTask(name="sqlmap", phase="exploit", tool="sqlmap", args=["-u", f"http://{target}", "--batch", "--level", "3"], depends_on=["nmap_scan"], timeout=900))
            chain.tasks.append(ChainTask(name="nuclei_web", phase="exploit", tool="nuclei", args=["-u", f"http://{target}", "-t", "cves", "-json", "-silent"], depends_on=["nmap_scan"], timeout=600))
        if "ad" in obj_lower or "domain" in obj_lower or "kerberos" in obj_lower:
            chain.tasks.append(ChainTask(name="ad_recon", phase="recon", tool="nmap", args=["-p", "88,389,445,636,3268,3269", "-sV", target], depends_on=["nmap_scan"], timeout=300))
        return chain
    def load_playbook(self, path: str, target: str) -> AttackChain:
        p = Path(path)
        if not p.exists(): p = self.playbook_dir / path
        if not p.exists(): raise FileNotFoundError(f"Playbook not found: {path}")
        with open(p, encoding="utf-8") as f: data = yaml.safe_load(f)
        chain = AttackChain(target=target, objective=data.get("objective", ""), created_at=time.time())
        for phase_data in data.get("phases", []):
            for tool in phase_data.get("tools", []):
                chain.tasks.append(ChainTask(name=f"{phase_data['name']}_{tool}", phase=phase_data["name"], tool=tool, depends_on=phase_data.get("depends_on", []), stop_on_fail=phase_data.get("stop_on_fail", False)))
        return chain
    def list_playbooks(self) -> list:
        if not self.playbook_dir.exists(): return []
        return sorted([str(f.name) for f in self.playbook_dir.glob("*.yaml")])


