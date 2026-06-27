"""Swarm orchestration engine with shared memory and multi-phase execution."""

import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

from .logger import logger
from .team import Agent, AgentRole


class SwarmPhase(Enum):
    RECONNAISSANCE = "reconnaissance"
    WEAPONIZATION = "weaponization"
    EXPLOITATION = "exploitation"
    POST_EXPLOIT = "post_exploit"


@dataclass
class SwarmMessage:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    sender: str = ""
    phase: str = ""
    content: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: dict = field(default_factory=dict)


class SharedMemory:
    """Thread-safe shared memory for swarm agents to exchange data."""

    def __init__(self):
        self._store: dict[str, Any] = {}
        self._messages: list[SwarmMessage] = []
        self._lock = asyncio.Lock()

    async def set(self, key: str, value: Any):
        async with self._lock:
            self._store[key] = value

    async def get(self, key: str, default: Any = None) -> Any:
        async with self._lock:
            return self._store.get(key, default)

    async def post_message(self, message: SwarmMessage):
        async with self._lock:
            self._messages.append(message)

    async def get_messages(self, phase: Optional[str] = None) -> list[SwarmMessage]:
        async with self._lock:
            if phase:
                return [m for m in self._messages if m.phase == phase]
            return list(self._messages)

    async def clear(self):
        async with self._lock:
            self._store.clear()
            self._messages.clear()


class SwarmOrchestrator:
    """Orchestrates a 4-phase swarm attack lifecycle."""

    def __init__(self, agents: list[Agent], phase_handlers: Optional[dict[SwarmPhase, Callable]] = None):
        self.agents = agents
        self.memory = SharedMemory()
        self.phase_handlers = phase_handlers or {}
        self.current_phase: Optional[SwarmPhase] = None

    async def run_phase(
        self, phase: SwarmPhase, agent_filter: Optional[Callable[[Agent], bool]] = None
    ) -> list[dict]:
        self.current_phase = phase
        selected = [a for a in self.agents if (agent_filter is None or agent_filter(a)) and a.is_active]
        logger.info(f"Swarm phase {phase.value} with {len(selected)} agents")

        handler = self.phase_handlers.get(phase, self._default_phase_handler)
        tasks = [self._run_agent(agent, phase, handler) for agent in selected]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r if isinstance(r, dict) else {"agent": "unknown", "error": str(r)} for r in results]

    async def _run_agent(self, agent: Agent, phase: SwarmPhase, handler: Callable) -> dict:
        try:
            result = await handler(agent, self.memory)
            msg = SwarmMessage(sender=agent.name, phase=phase.value, content=result)
            await self.memory.post_message(msg)
            return {"agent": agent.name, "phase": phase.value, "result": result}
        except Exception as e:
            logger.error(f"Swarm agent {agent.name} failed in phase {phase.value}: {e}")
            return {"agent": agent.name, "phase": phase.value, "error": str(e)}

    async def _default_phase_handler(self, agent: Agent, memory: SharedMemory) -> dict:
        await asyncio.sleep(0.2)
        return {"agent": agent.name, "action": f"executing {self.current_phase.value} tasks", "status": "ok"}

    async def run_all(self) -> dict[str, list[dict]]:
        phase_results = {}

        phase_filter = {
            SwarmPhase.RECONNAISSANCE: lambda a: a.role in (AgentRole.RECON, AgentRole.COORDINATOR),
            SwarmPhase.WEAPONIZATION: lambda a: a.role in (AgentRole.EXPLOIT, AgentRole.COORDINATOR),
            SwarmPhase.EXPLOITATION: lambda a: a.role in (AgentRole.EXPLOIT, AgentRole.PERSIST, AgentRole.COORDINATOR),
            SwarmPhase.POST_EXPLOIT: lambda a: a.role in (AgentRole.PERSIST, AgentRole.DEFENSE, AgentRole.COORDINATOR),
        }

        for phase in SwarmPhase:
            filt = phase_filter.get(phase)
            results = await self.run_phase(phase, agent_filter=filt)
            phase_results[phase.value] = results
            await asyncio.sleep(0.1)

        logger.info("Swarm execution completed across all phases")
        return phase_results

    async def consensus(self, threshold: float = 0.6) -> dict:
        messages = await self.memory.get_messages()
        if not messages:
            return {"consensus": False, "reason": "No messages to evaluate"}
        total = len(messages)
        positive = sum(1 for m in messages if m.content.get("status") == "ok" or "error" not in m.content)
        agreement = positive / total if total > 0 else 0
        return {
            "consensus": agreement >= threshold,
            "agreement_ratio": round(agreement, 3),
            "total_messages": total,
            "positive_messages": positive,
            "threshold": threshold,
        }
