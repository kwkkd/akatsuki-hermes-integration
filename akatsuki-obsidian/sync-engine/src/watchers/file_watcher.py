import os
import time
import hashlib
import threading
from pathlib import Path
from typing import Callable, Optional


class FileWatcher:
    def __init__(self, vault_path: str, interval: float = 1.0):
        self.vault_path = Path(vault_path)
        self.interval = interval
        self._snapshots: dict[str, tuple[str, float]] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self.on_change: Optional[Callable[[str, str, str], None]] = None

    def start(self):
        self._running = True
        self._scan()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)

    def _scan(self):
        if not self.vault_path.exists():
            return
        for f in self.vault_path.rglob("*.md"):
            rel = str(f.relative_to(self.vault_path))
            try:
                stat = f.stat()
                mtime = stat.st_mtime
                content = f.read_text(encoding="utf-8")
                cs = hashlib.sha256(content.encode()).hexdigest()[:16]
                with self._lock:
                    prev = self._snapshots.get(rel)
                    if prev is None or (prev[0] != cs and prev[1] < mtime):
                        self._snapshots[rel] = (cs, mtime)
            except Exception:
                pass

    def _loop(self):
        while self._running:
            time.sleep(self.interval)
            self._check()

    def _check(self):
        old_snapshot: dict[str, tuple[str, float]] = {}
        with self._lock:
            old_snapshot = dict(self._snapshots)
        if not self.vault_path.exists():
            return
        for f in self.vault_path.rglob("*.md"):
            rel = str(f.relative_to(self.vault_path))
            try:
                stat = f.stat()
                mtime = stat.st_mtime
                content = f.read_text(encoding="utf-8")
                cs = hashlib.sha256(content.encode()).hexdigest()[:16]
                prev = old_snapshot.get(rel)
                with self._lock:
                    if prev is None:
                        self._snapshots[rel] = (cs, mtime)
                        if self.on_change:
                            self.on_change(rel, "created", content)
                    elif prev[0] != cs and prev[1] < mtime:
                        self._snapshots[rel] = (cs, mtime)
                        if self.on_change:
                            self.on_change(rel, "modified", content)
            except Exception:
                pass
        with self._lock:
            current_keys = set(self._snapshots.keys())
        for rel in old_snapshot:
            if rel not in current_keys:
                if self.on_change:
                    self.on_change(rel, "deleted", "")
