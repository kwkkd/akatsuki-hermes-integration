"""
AKATSUKI Swarm Orchestrator — 동적 에이전트 협력 + 작업 큐 + 컨센서스
=================================================================
"""
import json
import sys
import os
import random
from queue import PriorityQueue
from typing import Optional, List, Dict, Any

sys.path.insert(0, os.path.dirname(__file__))
from swarm_protocol import SwarmMessage, MessageType, SharedMemory

try:
    HAS_AGENTS = True
except ImportError:
    HAS_AGENTS = False


class SwarmOrchestrator:
    """
    Dynamic agent task assignment and collaboration for AKATSUKI operations.
    Manages task queues, shared memory for inter-agent communication,
    and consensus building among the swarm.
    """

    def __init__(self) -> None:
        """Initialize the swarm orchestrator with queues and memory."""
        self.task_queue: PriorityQueue = PriorityQueue()
        self.shared_memory: SharedMemory = SharedMemory()
        self.agent_pool: Dict[str, Any] = {}
        self.results: Dict[str, Dict[str, str]] = {}
        self._load_agents()

    def _load_agents(self) -> None:
        """Load predefined agents into the agent pool if available."""
        if HAS_AGENTS:
            from team_agents import ALL_AGENTS
            self.agent_pool = dict(ALL_AGENTS)

    def assign_task(self, objective: str, required_expertise: Optional[List[str]] = None) -> str:
        """
        Find the best agent for a given task based on their required expertise.
        
        Args:
            objective: The task description or objective.
            required_expertise: A list of keywords matching the required expertise.
            
        Returns:
            The name of the chosen agent.
        """
        if not self.agent_pool:
            return "intel_pr"

        if required_expertise:
            best_agent = None
            best_score = 0
            for name, role in self.agent_pool.items():
                score = sum(1 for exp in required_expertise if exp.lower() in " ".join(role.expertise).lower())
                if score > best_score:
                    best_score = score
                    best_agent = name
            if best_agent:
                return best_agent

        return random.choice(list(self.agent_pool.keys()))

    def execute_swarm(self, objective: str, phases: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Execute a multi-agent collaboration across several phases.
        
        Args:
            objective: The main goal of the swarm operation.
            phases: An optional list of phases (e.g., recon, exploit).
            
        Returns:
            A dictionary containing operation results, consensus, and metrics.
        """
        if phases is None:
            phases = ["recon", "analysis", "exploit", "report"]

        for phase in phases:
            msg = SwarmMessage(
                type=MessageType.BROADCAST,
                sender="orchestrator",
                phase=phase,
                content=f"Phase: {phase}\\nObjective: {objective}",
            )
            self.shared_memory.write(msg)

            agents = list(self.agent_pool.keys()) if HAS_AGENTS else ["boss", "coo"]
            for agent in agents[:3]:
                task_msg = SwarmMessage(
                    type=MessageType.TASK_ASSIGN,
                    sender="orchestrator",
                    recipient=agent,
                    phase=phase,
                    content=f"Execute in phase {phase}: {objective[:200]}",
                )
                self.shared_memory.write(task_msg)
                self.results.setdefault(phase, {})[agent] = "Task dispatched"

        consensus = self.shared_memory.get_consensus(phases[-1]) if phases else {}
        return {
            "phases": phases,
            "agents": list(self.agent_pool.keys()) if HAS_AGENTS else [],
            "messages": len(self.shared_memory.messages),
            "consensus": consensus,
            "results": self.results,
        }

    def chat(self, user_input: str) -> str:
        """Process a direct chat message by assigning it to a suitable agent."""
        agent = self.assign_task(user_input)
        return f"[{agent}] Processing: {user_input[:100]}..."



