import hashlib
import json
import time
from typing import Optional
from schemas import CrdtOperation, OpType, CrdtOperation as Op


class CrdtEngine:
    def __init__(self, node_id: str):
        self.node_id = node_id
        self.seq = 0
        self.lamport = 0
        self.ops: dict[str, Op] = {}
        self.heads: set[str] = set()
        self.documents: dict[str, str] = {}

    def _next_seq(self) -> int:
        self.seq += 1
        return self.seq

    def _tick(self) -> int:
        now = int(time.time() * 1000)
        self.lamport = max(self.lamport, now) + 1
        return self.lamport

    def _op_id(self) -> str:
        return f"{self.node_id}:{self.seq}"

    def _checksum(self, content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def insert(self, doc_id: str, position: int, value: str, deps: Optional[list[str]] = None) -> Op:
        lamport = self._tick()
        op = Op(
            op_id=self._op_id(),
            op_type=OpType.INSERT,
            node_id=self.node_id,
            seq=self._next_seq(),
            lamport=lamport,
            position=position,
            length=len(value),
            value=value,
            deps=deps or list(self.heads),
        )
        self.ops[op.op_id] = op
        self.heads.add(op.op_id)
        self._apply(op, doc_id)
        return op

    def delete(self, doc_id: str, position: int, length: int, deps: Optional[list[str]] = None) -> Op:
        lamport = self._tick()
        op = Op(
            op_id=self._op_id(),
            op_type=OpType.DELETE,
            node_id=self.node_id,
            seq=self._next_seq(),
            lamport=lamport,
            position=position,
            length=length,
            deps=deps or list(self.heads),
        )
        self.ops[op.op_id] = op
        self.heads.add(op.op_id)
        self._apply(op, doc_id)
        return op

    def update(self, doc_id: str, path: list[str], value: str, deps: Optional[list[str]] = None) -> Op:
        lamport = self._tick()
        op = Op(
            op_id=self._op_id(),
            op_type=OpType.UPDATE,
            node_id=self.node_id,
            seq=self._next_seq(),
            lamport=lamport,
            path=path,
            value=value,
            deps=deps or list(self.heads),
        )
        self.ops[op.op_id] = op
        self.heads.add(op.op_id)
        self._apply(op, doc_id)
        return op

    def _apply(self, op: Op, doc_id: str):
        content = self.documents.get(doc_id, "")
        if op.op_type == OpType.INSERT:
            pos = min(op.position or 0, len(content))
            content = content[:pos] + (op.value or "") + content[pos:]
        elif op.op_type == OpType.DELETE:
            pos = min(op.position or 0, len(content))
            end = min(pos + (op.length or 0), len(content))
            content = content[:pos] + content[end:]
        elif op.op_type == OpType.UPDATE:
            pass  # metadata update, not text content
        self.documents[doc_id] = content

    def merge(self, remote_ops: list[Op]) -> list[Op]:
        new_ops = []
        for op in remote_ops:
            if op.op_id not in self.ops:
                self.ops[op.op_id] = op
                self.lamport = max(self.lamport, op.lamport) + 1
                self.heads.add(op.op_id)
                new_ops.append(op)
        for op in new_ops:
            doc_id = self._doc_id_for_op(op)
            if doc_id:
                self._apply(op, doc_id)
        return new_ops

    def _doc_id_for_op(self, op: Op) -> Optional[str]:
        for doc_id in self.documents:
            return doc_id
        return None

    def get_missing_ops(self, known_heads: set[str]) -> list[Op]:
        missing = []
        for op_id, op in self.ops.items():
            if op_id not in known_heads:
                missing.append(op)
        return sorted(missing, key=lambda o: (o.lamport, o.seq))

    def snapshot(self, doc_id: str) -> str:
        return self.documents.get(doc_id, "")

    def reset(self):
        self.seq = 0
        self.lamport = 0
        self.ops.clear()
        self.heads.clear()
        self.documents.clear()

    def state(self) -> dict:
        return {
            "node_id": self.node_id,
            "seq": self.seq,
            "lamport": self.lamport,
            "heads": list(self.heads),
            "ops_count": len(self.ops),
        }
