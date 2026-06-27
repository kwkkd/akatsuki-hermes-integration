import os
import time
import json
import logging
import hashlib
from typing import Optional
from pathlib import Path

logger = logging.getLogger("akatsuki.sync")

SYNC_STATE_FILE = "akatsuki-sync-state.json"


class CrdtOperation:
    def __init__(self, op_id: str, op_type: str, node_id: str, seq: int,
                 lamport: int, path: str = "", value: str = "",
                 deps: Optional[list] = None):
        self.op_id = op_id
        self.op_type = op_type
        self.node_id = node_id
        self.seq = seq
        self.lamport = lamport
        self.path = path
        self.value = value
        self.deps = deps or []

    def to_dict(self) -> dict:
        return {
            "op_id": self.op_id,
            "op_type": self.op_type,
            "node_id": self.node_id,
            "seq": self.seq,
            "lamport": self.lamport,
            "path": self.path,
            "value": self.value,
            "deps": self.deps,
        }


class SyncManager:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.state_path = self.vault_path / ".obsidian" / SYNC_STATE_FILE
        self._state: dict = {}
        self._running = False
        self._ops: dict[str, CrdtOperation] = {}
        self._seq = 0
        self._lamport = 0
        self._load_state()

    def start(self):
        self._running = True
        logger.info(f"Sync manager started for vault: {self.vault_path}")

    def stop(self):
        self._running = False
        self._save_state()
        logger.info("Sync manager stopped")

    def _load_state(self):
        if self.state_path.exists():
            try:
                self._state = json.loads(self.state_path.read_text())
            except Exception:
                self._state = {}
        self._state.setdefault("node_id", self._generate_node_id())
        self._state.setdefault("lamport", 0)
        self._state.setdefault("last_sync", 0)
        self._state.setdefault("checksums", {})
        self._state.setdefault("ops", {})
        self._lamport = self._state.get("lamport", 0)

    def _save_state(self):
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            ops_dict = {k: v.to_dict() for k, v in self._ops.items()}
            self._state["ops"] = ops_dict
            self._state["lamport"] = self._lamport
            self.state_path.write_text(json.dumps(self._state, indent=2))
        except Exception as e:
            logger.warning(f"Failed to save sync state: {e}")

    def _generate_node_id(self) -> str:
        import uuid
        seed = f"{uuid.getnode()}-{self.vault_path}"
        return hashlib.sha256(seed.encode()).hexdigest()[:12]

    def _tick(self) -> int:
        now = int(time.time() * 1000)
        self._lamport = max(self._lamport, now) + 1
        return self._lamport

    def _next_seq(self) -> int:
        self._seq += 1
        return self._seq

    def _op_id(self) -> str:
        return f"{self._state['node_id']}:{self._seq}"

    def _checksum(self, content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def get_state(self) -> dict:
        return dict(self._state)

    def create_op(self, op_type: str, path: str, value: str = "",
                  deps: Optional[list] = None) -> CrdtOperation:
        lamport = self._tick()
        op = CrdtOperation(
            op_id=self._op_id(),
            op_type=op_type,
            node_id=self._state["node_id"],
            seq=self._next_seq(),
            lamport=lamport,
            path=path,
            value=value,
            deps=deps or [],
        )
        self._ops[op.op_id] = op
        self._save_state()
        return op

    def merge_ops(self, remote_ops: list[dict]) -> list[CrdtOperation]:
        new_ops = []
        for raw in remote_ops:
            if raw["op_id"] not in self._ops:
                op = CrdtOperation(**raw)
                self._ops[op.op_id] = op
                self._lamport = max(self._lamport, op.lamport) + 1
                new_ops.append(op)
        if new_ops:
            self._save_state()
        return new_ops

    def record_sync(self, checksums: dict[str, str]):
        self._state["checksums"].update(checksums)
        self._state["last_sync"] = int(time.time() * 1000)
        self._save_state()

    def mark_changed(self, path: str, content: str = ""):
        cs = self._checksum(content) if content else ""
        self._state["checksums"][path] = cs
        self._state["last_sync"] = int(time.time() * 1000)
        self.create_op("UPDATE", path, content)
        self._save_state()

    def get_changed(self) -> list[tuple[str, str]]:
        changed = []
        for f in self.vault_path.rglob("*.md"):
            rel = str(f.relative_to(self.vault_path))
            try:
                content = f.read_text(encoding="utf-8")
                cs = self._checksum(content)
                prev = self._state["checksums"].get(rel)
                if prev != cs:
                    changed.append((rel, cs))
            except Exception:
                pass
        return changed

    def resolve_conflict(self, local_op: CrdtOperation,
                         remote_op: CrdtOperation) -> CrdtOperation:
        if local_op.lamport > remote_op.lamport:
            return local_op
        if remote_op.lamport > local_op.lamport:
            return remote_op
        if local_op.node_id > remote_op.node_id:
            return local_op
        return remote_op
