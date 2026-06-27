"""Attack chain builder and executor for multi-stage operations."""

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

from .logger import logger


class ChainStepType(Enum):
    RECON = "recon"
    SCAN = "scan"
    EXPLOIT = "exploit"
    ESCALATE = "escalate"
    PERSIST = "persist"
    EXFIL = "exfil"
    CLEANUP = "cleanup"
    CUSTOM = "custom"


@dataclass
class AttackStep:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    step_type: ChainStepType = ChainStepType.CUSTOM
    target: str = ""
    tool: str = ""
    params: dict = field(default_factory=dict)
    depends_on: list = field(default_factory=list)
    timeout: int = 60
    retry_count: int = 0


@dataclass
class AttackChain:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    steps: list[AttackStep] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: dict = field(default_factory=dict)


class ChainBuilder:
    """Builds attack chains step by step with dependency management."""

    def __init__(self):
        self.steps: list[AttackStep] = []
        self._step_index: dict[str, AttackStep] = {}

    def add_step(
        self,
        name: str,
        step_type: ChainStepType,
        target: str = "",
        tool: str = "",
        params: dict = None,
        depends_on: list = None,
        timeout: int = 60,
        retry_count: int = 0,
    ) -> "ChainBuilder":
        step = AttackStep(
            name=name,
            step_type=step_type,
            target=target,
            tool=tool,
            params=params or {},
            depends_on=depends_on or [],
            timeout=timeout,
            retry_count=retry_count,
        )
        self.steps.append(step)
        self._step_index[step.id] = step
        return self

    def remove_step(self, step_id: str) -> bool:
        step = self._step_index.pop(step_id, None)
        if step:
            self.steps = [s for s in self.steps if s.id != step_id]
            return True
        return False

    def insert_after(self, after_step_id: str, step: AttackStep) -> bool:
        idx = next((i for i, s in enumerate(self.steps) if s.id == after_step_id), -1)
        if idx == -1:
            return False
        self.steps.insert(idx + 1, step)
        self._step_index[step.id] = step
        return True

    def build(self, name: str = "") -> AttackChain:
        chain = AttackChain(name=name, steps=list(self.steps))
        self.steps.clear()
        self._step_index.clear()
        return chain

    def from_dict(self, data: dict) -> AttackChain:
        chain = AttackChain(
            id=data.get("id", str(uuid.uuid4())[:8]),
            name=data.get("name", ""),
            steps=[AttackStep(**s) for s in data.get("steps", [])],
            metadata=data.get("metadata", {}),
        )
        return chain


class ChainExecutor:
    """Executes attack chains with dependency resolution and parallel step support."""

    def __init__(self, step_handler: Optional[Callable[[AttackStep], Any]] = None):
        self.step_handler = step_handler or self._default_handler
        self.results: dict[str, Any] = {}

    async def _default_handler(self, step: AttackStep) -> dict:
        await asyncio.sleep(0.3)
        return {"step_id": step.id, "step_name": step.name, "status": "completed", "output": f"Executed {step.tool} on {step.target}"}

    def _get_dependency_order(self, steps: list[AttackStep]) -> list[AttackStep]:
        ordered = []
        visited = set()
        temp_mark = set()

        def dfs(step_id: str, step_map: dict):
            if step_id in visited:
                return
            if step_id in temp_mark:
                raise ValueError(f"Circular dependency detected for step {step_id}")
            temp_mark.add(step_id)
            step = step_map.get(step_id)
            if step:
                for dep_id in step.depends_on:
                    if dep_id in step_map:
                        dfs(dep_id, step_map)
                ordered.append(step)
                visited.add(step_id)
            temp_mark.discard(step_id)

        step_map = {s.id: s for s in steps}
        for step in steps:
            if step.id not in visited:
                dfs(step.id, step_map)
        return ordered

    async def execute(self, chain: AttackChain, parallel: bool = False) -> list[dict]:
        ordered = self._get_dependency_order(chain.steps)
        logger.info(f"Executing chain '{chain.name}' with {len(ordered)} steps")

        if parallel:
            tasks = [self._run_step(step) for step in ordered]
            return await asyncio.gather(*tasks, return_exceptions=True)

        results = []
        for step in ordered:
            result = await self._run_step(step)
            results.append(result)
            self.results[step.id] = result
        return results

    async def _run_step(self, step: AttackStep) -> dict:
        last_error = None
        for attempt in range(step.retry_count + 1):
            try:
                result = await asyncio.wait_for(self.step_handler(step), timeout=step.timeout)
                self.results[step.id] = result
                logger.info(f"Step {step.name} ({step.id}) completed")
                return result
            except asyncio.TimeoutError:
                last_error = f"Timeout after {step.timeout}s"
                logger.warning(f"Step {step.name} timeout (attempt {attempt + 1})")
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Step {step.name} failed (attempt {attempt + 1}): {e}")
        return {"step_id": step.id, "step_name": step.name, "status": "failed", "error": last_error}


class C2Builder:
    """Builds command and control channel configurations."""

    def __init__(self):
        self.protocols = {
            "dns": {"type": "dns", "port": 53, "encoder": "base64", "interval": 5},
            "http": {"type": "http", "port": 443, "encoder": "aes", "interval": 10},
            "https": {"type": "https", "port": 443, "encoder": "aes", "interval": 15},
            "websocket": {"type": "websocket", "port": 443, "encoder": "xor", "interval": 3},
            "icmp": {"type": "icmp", "port": 0, "encoder": "base64", "interval": 30},
        }

    def build_config(
        self,
        protocol: str,
        server: str,
        port: Optional[int] = None,
        custom_params: dict = None,
    ) -> dict:
        proto = self.protocols.get(protocol.lower())
        if not proto:
            raise ValueError(f"Unknown protocol: {protocol}")
        config = dict(proto)
        config["server"] = server
        if port:
            config["port"] = port
        config["id"] = str(uuid.uuid4())[:8]
        config["created_at"] = datetime.utcnow().isoformat()
        if custom_params:
            config.update(custom_params)
        return config

    def list_protocols(self) -> list:
        return list(self.protocols.keys())
