# AKATSUKI Obsidian Bridge

양방향 Obsidian ↔ Hermes 동기화 및 명령 실행.

## Commands

- `/obsidian list [prefix]` — vault 내 노트 목록
- `/obsidian read <path>` — 특정 노트 읽기
- `/obsidian write --path <p> --content <c>` — 새 노트 작성
- `/obsidian search <query>` — 내용 검색
- `/obsidian delete <path>` — 노트 삭제
- `/obsidian folders` — 폴더 구조 보기
- `/obsidian tags` — 모든 태그 보기
- `/obsidian sync` — 강제 동기화
- `/obsidian status` — 연결 상태 확인

## Architecture

```
Obsidian App  ←WebSocket→  Python Bridge  ←Unix Socket→  Hermes Agent
    │                              │
    └── File Watcher ──────────────┘
```

## Files

- `tools/akatsuki_obsidian.py` — Hermes tool definition
- `hermes_bridge/` — Bridge package (IPC server + sync + models)
- `sync-engine/` — CRDT + file watcher
