"""Agent team management with Naruto-themed AI agents and operation orchestration."""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Callable, Optional

from .logger import logger


class AgentRole(Enum):
    RECON = "recon"
    EXPLOIT = "exploit"
    PERSIST = "persist"
    DEFENSE = "defense"
    COORDINATOR = "coordinator"


@dataclass
class Agent:
    id: str
    name: str
    role: AgentRole
    description: str
    capabilities: list = field(default_factory=list)
    personality: str = ""
    is_active: bool = True


ALL_AGENTS = {
    "pain": Agent(
        id="agent_pain", name="Pain", role=AgentRole.COORDINATOR,
        description="Supreme leader — coordinates all operations and strategic decisions",
        capabilities=["strategic planning", "mission coordination", "resource allocation", "final approval"],
        personality="Cold, calculated, visionary",
    ),
    "konan": Agent(
        id="agent_konan", name="Konan", role=AgentRole.COORDINATOR,
        description="Second-in-command — manages logistics and intelligence flow",
        capabilities=["intelligence analysis", "logistics management", "communication routing"],
        personality="Calm, meticulous, loyal",
    ),
    "itachi": Agent(
        id="agent_itachi", name="Itachi", role=AgentRole.RECON,
        description="Elite recon — infiltration and intelligence gathering specialist",
        capabilities=["stealth recon", "network scanning", "social engineering", "vulnerability discovery"],
        personality="Mysterious, analytical, patient",
    ),
    "kisame": Agent(
        id="agent_kisame", name="Kisame", role=AgentRole.EXPLOIT,
        description="Brute force and exploitation — breaks through defenses",
        capabilities=["password cracking", "exploit execution", "DDoS", "payload delivery"],
        personality="Aggressive, relentless, loyal",
    ),
    "deidara": Agent(
        id="agent_deidara", name="Deidara", role=AgentRole.EXPLOIT,
        description="Explosives and destruction — creates chaos and backdoors",
        capabilities=["backdoor deployment", "web exploitation", "sql injection", "file upload abuse"],
        personality="Artistic, arrogant, explosive temper",
    ),
    "sasori": Agent(
        id="agent_sasori", name="Sasori", role=AgentRole.PERSIST,
        description="Puppet master — establishes persistence and C2 infrastructure",
        capabilities=["C2 setup", "persistence mechanisms", "rootkit deployment", "traffic tunneling"],
        personality="Cunning, patient, ruthless",
    ),
    "kakuzu": Agent(
        id="agent_kakuzu", name="Kakuzu", role=AgentRole.PERSIST,
        description="Resource gatherer — exfiltrates data and manages stolen assets",
        capabilities=["data exfiltration", "credential harvesting", "lateral movement"],
        personality="Greedy, pragmatic, methodical",
    ),
    "hidan": Agent(
        id="agent_hidan", name="Hidan", role=AgentRole.EXPLOIT,
        description="Ritual executioner — performs precise, repeatable attacks",
        capabilities=["payload execution", "service exploitation", "protocol attacks"],
        personality="Zealot, reckless, ritualistic",
    ),
    "zetsu": Agent(
        id="agent_zetsu", name="Zetsu", role=AgentRole.RECON,
        description="Stealth observer — passive reconnaissance and environment monitoring",
        capabilities=["passive recon", "traffic analysis", "OSINT gathering", "environment monitoring"],
        personality="Observant, secretive, two-faced",
    ),
    "tobi": Agent(
        id="agent_tobi", name="Tobi (Obito)", role=AgentRole.DEFENSE,
        description="Phasing expert — evades detection and covers tracks",
        capabilities=["log cleaning", "IDS evasion", "proxy chaining", "cover tracking"],
        personality="Playful facade, ruthless underneath",
    ),
    "orochimaru": Agent(
        id="agent_orochimaru", name="Orochimaru", role=AgentRole.COORDINATOR,
        description="Researcher — experiments with new exploits and techniques",
        capabilities=["vulnerability research", "0-day analysis", "payload crafting", "technique experimentation"],
        personality="Obsessed with knowledge, snake-like",
    ),
    "juzo": Agent(
        id="agent_juzo", name="Juzo", role=AgentRole.EXPLOIT,
        description="Silent executioner — quick, precise strikes and sabotage",
        capabilities=["physical attacks", "system sabotage", "quick exploitation"],
        personality="Silent, efficient, deadly",
    ),
    "sakura_haruno": Agent(
        id="agent_sakura", name="Sakura Haruno", role=AgentRole.DEFENSE,
        description="Healer — system repair and defensive countermeasures",
        capabilities=["system hardening", "patch management", "incident response", "forensic analysis"],
        personality="Strong-willed, compassionate, fierce",
    ),
}


class OperationStatus(Enum):
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Operation:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    objective: str = ""
    target: str = ""
    status: OperationStatus = OperationStatus.PLANNING
    assigned_agents: list = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None
    result: Optional[dict] = None


class OrgManager:
    """Manages agent assignments and operational planning."""

    def __init__(self):
        self.agents = dict(ALL_AGENTS)
        self.operations: list[Operation] = []

    def get_agent(self, name: str) -> Optional[Agent]:
        return self.agents.get(name.lower())

    def get_agents_by_role(self, role: AgentRole) -> list[Agent]:
        return [a for a in self.agents.values() if a.role == role and a.is_active]

    def activate_agent(self, name: str) -> bool:
        agent = self.get_agent(name)
        if agent:
            agent.is_active = True
            return True
        return False

    def deactivate_agent(self, name: str) -> bool:
        agent = self.get_agent(name)
        if agent:
            agent.is_active = False
            return True
        return False

    def create_operation(self, name: str, objective: str, target: str) -> Operation:
        op = Operation(name=name, objective=objective, target=target)
        self.operations.append(op)
        logger.info(f"Operation created: {op.id} - {name}")
        return op

    def assign_to_operation(self, operation_id: str, agent_names: list) -> bool:
        op = next((o for o in self.operations if o.id == operation_id), None)
        if not op:
            return False
        for name in agent_names:
            agent = self.get_agent(name)
            if agent and agent.is_active and agent not in op.assigned_agents:
                op.assigned_agents.append(agent)
        return True

    def complete_operation(self, operation_id: str, result: dict = None) -> bool:
        op = next((o for o in self.operations if o.id == operation_id), None)
        if not op:
            return False
        op.status = OperationStatus.COMPLETED
        op.completed_at = datetime.utcnow().isoformat()
        op.result = result
        return True


class AgentWorker:
    """Executes tasks for individual agents."""

    def __init__(self, agent: Agent, task_func: Optional[Callable] = None):
        self.agent = agent
        self.task_func = task_func or self._default_task

    async def _default_task(self, context: dict) -> dict:
        await asyncio.sleep(0.1)
        return {"agent": self.agent.name, "status": "simulated", "context": context}

    async def execute(self, context: dict) -> dict:
        logger.info(f"Agent {self.agent.name} executing task")
        try:
            return await self.task_func(context)
        except Exception as e:
            logger.error(f"Agent {self.agent.name} failed: {e}")
            return {"agent": self.agent.name, "status": "failed", "error": str(e)}


class HackerTeam:
    """Orchestrates multiple agent workers for an operation."""

    def __init__(self, org_manager: OrgManager):
        self.org = org_manager
        self.workers: dict[str, AgentWorker] = {}

    def build_team(self, agent_names: list[str]) -> "HackerTeam":
        for name in agent_names:
            agent = self.org.get_agent(name)
            if agent:
                self.workers[name] = AgentWorker(agent)
        return self

    async def run_operation(self, context: dict) -> list[dict]:
        tasks = [worker.execute(context) for worker in self.workers.values()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r if isinstance(r, dict) else {"error": str(r)} for r in results]
