import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger("akatsuki.audit")


class AuditLogger:
    def __init__(self, log_dir: str = "", max_bytes: int = 10485760, backup_count: int = 5):
        self.log_dir = Path(log_dir or os.environ.get("AKATSUKI_LOG_DIR", ""))
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self._current_size = 0
        self._log_path = None
        if self.log_dir:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self._log_path = self.log_dir / "akatsuki-audit.jsonl"

    def log(self, event: str, actor: str = "", resource: str = "",
            action: str = "", status: str = "success", details: dict = None,
            ip: str = "", user_agent: str = ""):
        record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event": event,
            "actor": actor or "anonymous",
            "resource": resource or "",
            "action": action or "",
            "status": status,
            "details": details or {},
            "ip": ip or "",
            "user_agent": user_agent or "",
        }
        logger.info(json.dumps(record))
        if self._log_path:
            self._write(record)

    def _write(self, record: dict):
        try:
            line = json.dumps(record, ensure_ascii=False) + "\n"
            if self._log_path.exists() and self._log_path.stat().st_size > self.max_bytes:
                self._rotate()
            with open(self._log_path, "a", encoding="utf-8") as f:
                f.write(line)
        except Exception as e:
            logger.warning(f"Audit write failed: {e}")

    def _rotate(self):
        for i in range(self.backup_count - 1, 0, -1):
            src = self._log_path.with_suffix(f".{i}.jsonl")
            dst = self._log_path.with_suffix(f".{i + 1}.jsonl")
            if src.exists():
                src.rename(dst)
        if self._log_path.exists():
            self._log_path.rename(self._log_path.with_suffix(".1.jsonl"))

    def query(self, filters: dict = None, limit: int = 100, offset: int = 0) -> list[dict]:
        if not self._log_path or not self._log_path.exists():
            return []
        results = []
        with open(self._log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                    if filters:
                        match = all(
                            record.get(k) == v or (isinstance(v, list) and record.get(k) in v)
                            for k, v in filters.items()
                        )
                        if not match:
                            continue
                    results.append(record)
                except json.JSONDecodeError:
                    continue
        return results[offset:offset + limit]

    def count_by_event(self) -> dict[str, int]:
        counts = {}
        if not self._log_path or not self._log_path.exists():
            return counts
        with open(self._log_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    event = record.get("event", "unknown")
                    counts[event] = counts.get(event, 0) + 1
                except Exception:
                    pass
        return counts

    def count_by_status(self) -> dict[str, int]:
        counts = {}
        if not self._log_path or not self._log_path.exists():
            return counts
        with open(self._log_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    status = record.get("status", "unknown")
                    counts[status] = counts.get(status, 0) + 1
                except Exception:
                    pass
        return counts


audit_logger = AuditLogger()