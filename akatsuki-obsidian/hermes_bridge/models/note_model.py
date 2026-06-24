from __future__ import annotations
import os
import re
import json
import time
import hashlib
import uuid
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Note:
    id: str = ""
    path: str = ""
    title: str = ""
    content: str = ""
    tags: list = field(default_factory=list)
    links: list = field(default_factory=list)
    frontmatter: dict = field(default_factory=dict)
    checksum: str = ""
    version: int = 0
    created: int = 0
    modified: int = 0
    source: str = "user"

    def to_dict(self):
        return {
            "id": self.id,
            "path": self.path,
            "title": self.title,
            "content": self.content,
            "tags": self.tags,
            "links": self.links,
            "frontmatter": self.frontmatter,
            "checksum": self.checksum,
            "version": self.version,
            "created": self.created,
            "modified": self.modified,
            "source": self.source,
        }


class NoteModel:
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)

    def _resolve(self, path: str) -> Path:
        p = self.vault_path / path
        if not p.suffix:
            p = p.with_suffix(".md")
        return p

    def read(self, path: str) -> Optional[Note]:
        fpath = self._resolve(path)
        if not fpath.exists() or not fpath.is_file():
            return None
        content = fpath.read_text(encoding="utf-8")
        frontmatter, body = self._parse_frontmatter(content)
        stat = fpath.stat()
        return Note(
            id=self._generate_id(fpath),
            path=str(fpath.relative_to(self.vault_path)),
            title=frontmatter.get("title", fpath.stem),
            content=body,
            tags=frontmatter.get("tags", []),
            links=self._extract_links(body),
            frontmatter=frontmatter,
            checksum=hashlib.sha256(content.encode()).hexdigest()[:16],
            version=frontmatter.get("version", 0),
            created=int(stat.st_ctime * 1000),
            modified=int(stat.st_mtime * 1000),
            source="obsidian",
        )

    def write(self, note: Note) -> dict:
        fpath = self._resolve(note.path)
        fpath.parent.mkdir(parents=True, exist_ok=True)
        note.checksum = hashlib.sha256(note.content.encode()).hexdigest()[:16]
        note.version += 1
        note.modified = int(time.time() * 1000)
        yaml_fm = self._format_frontmatter(note)
        content = f"---\n{yaml_fm}\n---\n\n{note.content}"
        fpath.write_text(content, encoding="utf-8")
        return {"path": note.path, "version": note.version, "checksum": note.checksum}

    def delete(self, path: str):
        fpath = self._resolve(path)
        if fpath.exists():
            fpath.unlink()

    def list(self, prefix: str = "") -> list[Note]:
        notes = []
        base = self.vault_path / prefix if prefix else self.vault_path
        if not base.exists():
            return notes
        for f in sorted(base.rglob("*.md")):
            rel = str(f.relative_to(self.vault_path))
            note = self.read(rel)
            if note:
                notes.append(note)
        return notes

    def search(self, query: str) -> list[Note]:
        results = []
        for f in self.vault_path.rglob("*.md"):
            try:
                content = f.read_text(encoding="utf-8")
                if query.lower() in content.lower():
                    rel = str(f.relative_to(self.vault_path))
                    note = self.read(rel)
                    if note:
                        results.append(note)
            except Exception:
                pass
        return results

    def list_folders(self) -> list[str]:
        folders = set()
        for f in self.vault_path.rglob("*.md"):
            rel = f.relative_to(self.vault_path)
            if rel.parent:
                folders.add(str(rel.parent))
        return sorted(folders)

    def list_tags(self) -> list[str]:
        tags = set()
        for f in self.vault_path.rglob("*.md"):
            try:
                content = f.read_text(encoding="utf-8")
                tags.update(re.findall(r"#(\w+)", content))
                fm, _ = self._parse_frontmatter(content)
                fm_tags = fm.get("tags", [])
                if isinstance(fm_tags, list):
                    tags.update(fm_tags)
            except Exception:
                pass
        return sorted(tags)

    def _parse_frontmatter(self, content: str) -> tuple[dict, str]:
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    fm = yaml.safe_load(parts[1]) or {}
                except Exception:
                    fm = {}
                return fm, parts[2].strip()
        return {}, content

    def _format_frontmatter(self, note: Note) -> str:
        fm = dict(note.frontmatter)
        fm.setdefault("title", note.title)
        fm.setdefault("tags", note.tags)
        fm.setdefault("version", note.version)
        fm.setdefault("id", note.id)
        return yaml.dump(fm, default_flow_style=False, allow_unicode=True).strip()

    def _generate_id(self, fpath: Path) -> str:
        ns = uuid.NAMESPACE_URL
        return str(uuid.uuid5(ns, str(fpath)))

    def _extract_links(self, content: str) -> list[str]:
        return re.findall(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", content)
