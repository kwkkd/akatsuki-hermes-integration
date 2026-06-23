import os
import time
import json
import logging
from typing import Optional
from pathlib import Path

logger = logging.getLogger("akatsuki.sync")

SYNC_STATE_FILE = "akatsuki-sync-state.json"


class SyncManager:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.state_path = self.vault_path / ".obsidian" / SYNC_STATE_FILE
        self._state: dict = {}
        self._running = False
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

    def _save_state(self):
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            self.state_path.write_text(json.dumps(self._state, indent=2))
        except Exception as e:
            logger.warning(f"Failed to save sync state: {e}")

    def _generate_node_id(self) -> str:
        import hashlib, uuid
        seed = f"{uuid.getnode()}-{self.vault_path}"
        return hashlib.sha256(seed.encode()).hexdigest()[:12]

    def get_state(self) -> dict:
        return dict(self._state)

    def record_sync(self, checksums: dict[str, str]):
        self._state["checksums"].update(checksums)
        self._state["last_sync"] = int(time.time() * 1000)
        self._save_state()

    def mark_changed(self, path: str, checksum: str):
        self._state["checksums"][path] = checksum
        self._state["last_sync"] = int(time.time() * 1000)
        self._save_state()

    def get_changed(self) -> list[tuple[str, str]]:
        vault_path = Path(self.vault_path)
        changed = []
        for f in vault_path.rglob("*.md"):
            rel = str(f.relative_to(vault_path))
            try:
                content = f.read_text(encoding="utf-8")
                import hashlib
                cs = hashlib.sha256(content.encode()).hexdigest()[:16]
                prev = self._state["checksums"].get(rel)
                if prev != cs:
                    changed.append((rel, cs))
            except Exception:
                pass
        return changed
