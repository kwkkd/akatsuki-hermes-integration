# 🌙 AKATSUKI 暁 — Obsidian Bridge (Level 3)

> **⚠️ 이 프로젝트는 재미로 만든 컨셉입니다. 실제 해킹/공격 용도가 아닙니다.**

Hermes Agent + AKATSUKI 13개 부서 ↔ Obsidian vault **양방향 실시간 통합**.

> 별도 HTTP API, MCP 서버, 플러그인 없이 **WebSocket + Unix Socket**으로 Obsidian을 AKATSUKI의 네이티브 스토리지로 만듭니다.

---

## 🏗 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                      Hermes Agent                               │
│  ┌──────────┐  ┌──────────────────┐  ┌─────────────────────┐  │
│  │ CLI      │  │ tools/           │  │ hermes_bridge/      │  │
│  │ /obsidian│  │ akatsuki_obsidian│  │ AgentBridge         │  │
│  │ /akatsuki│  │ akatsuki_recon   │  │ ┌─ IPC Server ──┐  │  │
│  └──────────┘  └──────────────────┘  │ │ WS  :18749    │  │  │
│       │                               │ │ Unix:/tmp/... │  │  │
│       └──────────┬────────────────────┘ └───────┬───────┘  │  │
│                  │                               │          │  │
└──────────────────┼───────────────────────────────┼──────────┘  │
                   │                               │             │
                   │  ┌────────────────────────────┘             │
                   │  │  WebSocket ws://127.0.0.1:18749          │
                   ▼  ▼                                          │
┌──────────────────────────────────────────────────────────┐     │
│                 Obsidian App                              │     │
│  ┌──────────────────────────────────────────┐            │     │
│  │  akatsuki-obsidian plugin                │            │     │
│  │  ┌──────────┐  ┌──────────┐  ┌────────┐ │            │     │
│  │  │ IPC      │  │ Commands │  │ Sync   │ │            │     │
│  │  │ Client   │  │ Push/Sync│  │ Timer  │ │            │     │
│  │  └──────────┘  └──────────┘  └────────┘ │            │     │
│  └──────────────────────────────────────────┘            │     │
│                    │                                      │     │
│              ┌─────┴─────┐                                │     │
│              │ Obsidian  │                                │     │
│              │ Vault     │  (.md notes)                    │     │
│              └───────────┘                                │     │
└──────────────────────────────────────────────────────────┘     │
```

### 데이터 흐름

```
Hermes → akatsuki_obsidian 도구 → JSON-RPC → WebSocket → Obsidian Plugin → Vault

Obsidian Vault → File Watcher → Sync Manager → AgentBridge → WebSocket → Hermes
```

---

## 📦 컴포넌트

### 1. Hermes Bridge (`hermes-bridge/`)
Python IPC 서버. Hermes Agent 안에서 실행되며 Obsidian과의 모든 통신을 중개.

| 파일 | 역할 |
|------|------|
| `bridge/agent_bridge.py` | 메인 브릿지 — 핸들러 등록, 도구 디스패치 |
| `ipc/server.py` | Unix Socket 서버 (Linux/macOS) |
| `ipc/ws_server.py` | WebSocket 서버 (Windows 호환, fallback) |
| `models/note_model.py` | Note CRUD + Frontmatter 파싱/생성 (YAML) |
| `sync/sync_manager.py` | 체크섬 기반 변경 추적, 동기화 상태 관리 |
| `commands/akatsuki_obsidian.py` | Hermes Tool 등록 — `/obsidian read/write/list/...` |

### 2. Obsidian Plugin (`obsidian-plugin/`)
Obsidian 내에서 Hermes와 통신하는 플러그인.

| 파일 | 역할 |
|------|------|
| `src/main.ts` | Plugin 클래스 — 4개 명령어, 설정 탭, 상태바, 자동 동기화 |
| `src/ipc/client.ts` | WebSocket IPC 클라이언트 (JSON-RPC) |
| `src/types/messages.ts` | TypeScript 타입 정의 |

### 3. Sync Engine (`sync-engine/`)
CRDT 기반 충돌 없는 동기화 엔진.

| 파일 | 역할 |
|------|------|
| `crdt/engine.py` | CRDT — INSERT/DELETE/UPDATE/MERGE, Lamport 시계, 머지 |
| `watchers/file_watcher.py` | 파일 변경 감시 (interval poll) |

### 4. Shared Schemas (`schemas/`)
양쪽(Python ↔ TypeScript)이 공유하는 데이터 계약.

| 파일 | 역할 |
|------|------|
| `__init__.py` | Python dataclass: Note, CrdtOperation, JsonRpcRequest/Response |
| `message.ts` | JSON-RPC 메시지 타입 |
| `note.ts` | Note/Folder 타입 |
| `crdt.ts` | CRDT 동기화 타입 |

### 5. IPC Protocol (`proto/ipc.proto`)
Protocol Buffers 명세 (향후 확장용).

---

## 🚀 설치

### 사전 요구사항
- **Hermes Agent** v0.16.0+ (`pip install hermes-agent`)
- **Python** 3.11+
- **Obsidian** v1.5.0+

### 자동 설치
```bash
git clone https://github.com/kwkkd/akatsuki-hermes-integration.git
cd akatsuki-hermes-integration
python akatsuki-obsidian/scripts/install.py
```

### 수동 설치

**1. Hermes 설치**
```bash
pip install hermes-agent
```

**2. AKATSUKI + Bridge 설치**
```powershell
# Windows
.\install.ps1

# Linux/macOS
chmod +x install.sh && ./install.sh
```

**3. 브릿지 의존성**
```bash
pip install pyyaml websockets
```

**4. Obsidian 플러그인 설치**
- `<vault>/.obsidian/plugins/akatsuki-obsidian/` 에 `manifest.json`, `main.js` 배치
- Obsidian 설정 → 서드파티 플러그인 → 활성화

---

## 🎮 사용법

### Hermes CLI에서

```bash
# 브릿지 시작
python -m hermes_bridge /path/to/obsidian/vault

# Hermes 실행
hermes

# Obsidian 명령어
/obsidian list                        # 노트 목록
/obsidian list "AKATSUKI/Missions"    # 특정 폴더
/obsidian read AKATSUKI/Missions/OP-001
/obsidian write --path test.md --content "Hello AKATSUKI"
/obsidian search "target"
/obsidian delete old_note.md
/obsidian folders                      # 폴더 구조
/obsidian tags                         # 모든 태그 보기
/obsidian sync                         # 강제 동기화
/obsidian status                       # 연결 상태
```

### Obsidian에서

| 명령어 | 설명 |
|--------|------|
| `AKATSUKI: Sync now with Hermes` | 전체 vault 동기화 |
| `AKATSUKI: Push current note to Hermes` | 현재 노트 전송 |
| `AKATSUKI: Connect to Hermes bridge` | 연결 |
| `AKATSUKI: Disconnect from Hermes bridge` | 해제 |

### 자동 동기화
플러그인 설정에서 활성화:
- **Auto-sync**: ON → 파일 변경 시 자동 푸시
- **Sync interval**: 5000ms 주기로 전체 동기화

---

## 🔌 IPC 프로토콜

### JSON-RPC 2.0 over WebSocket

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "note/read",
  "params": { "path": "AKATSUKI/Missions/OP-001.md" }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "id": "550e8400-...",
    "path": "AKATSUKI/Missions/OP-001.md",
    "title": "OP-001",
    "content": "# Mission Brief...",
    "tags": ["akatsuki", "mission"],
    "version": 3,
    "checksum": "a1b2c3d4",
    "source": "obsidian"
  }
}
```

**Methods:**

| 메서드 | 설명 |
|--------|------|
| `note/read` | 노트 읽기 |
| `note/write` | 노트 쓰기 |
| `note/list` | 목록 |
| `note/search` | 검색 |
| `note/delete` | 삭제 |
| `folder/list` | 폴더 목록 |
| `tags/list` | 태그 목록 |
| `event/note/changed` | 변경 이벤트 (broadcast) |

---

## 🔄 CRDT 동기화

```
Op: {
  op_id: "node1:42",
  op_type: INSERT | DELETE | UPDATE,
  lamport: 1704067200123,
  position: 15,
  value: "target_ip",
  deps: ["node1:41", "node2:37"]
}
```

- **Lamport clock** — 부분 순서 보장
- **Operation IDs** — 멱등성 (중복 적용 방지)
- **Dependencies** — 인과성 추적
- **머지** — 같은 위치 동시 삽입 시 Lamport + NodeID로 결정

---

## 📂 파일 구조

```
akatsuki-obsidian/
├── schemas/                          # 공유 계약
│   ├── __init__.py                   # Python dataclass
│   ├── message.ts                    # JSON-RPC 타입
│   ├── note.ts                       # Note/Folder 타입
│   └── crdt.ts                       # CRDT 타입
├── proto/
│   └── ipc.proto                     # Protobuf 명세
├── hermes-bridge/                    # Python 브릿지
│   └── src/
│       ├── bridge/agent_bridge.py    # 메인 브릿지
│       ├── ipc/server.py             # Unix Socket
│       ├── ipc/ws_server.py          # WebSocket
│       ├── models/note_model.py      # Note CRUD
│       ├── sync/sync_manager.py      # 동기화 관리
│       └── commands/akatsuki_obsidian.py
├── obsidian-plugin/                  # Obsidian 플러그인
│   ├── manifest.json
│   ├── package.json
│   └── src/
│       ├── main.ts                   # Plugin
│       ├── ipc/client.ts             # IPC Client
│       └── types/messages.ts
├── sync-engine/                      # 동기화 엔진
│   └── src/
│       ├── crdt/engine.py            # CRDT
│       └── watchers/file_watcher.py
├── skills/                           # Hermes Skill
│   └── akatsuki-obsidian/SKILL.md
└── scripts/install.py                # 설치 스크립트
```

---

## 🧪 상태

| 계층 | 상태 | 설명 |
|------|------|------|
| **L1** (Core) | ✅ 완료 | 8개 AKATSUKI 도구, CLI 등록, 스킬 |
| **L2** (Automation) | ✅ 완료 | 플레이북 6개, 킬 체인 템플릿 |
| **L3** (Obsidian Bridge) | ✅ 완료 (v1) | 양방향 IPC, CRDT 싱크, 플러그인 |

---

## 📜 라이선스

MIT License. Hermes Agent — MIT (Nous Research).

---

*"暁(あかつき) — Obsidian은 AKATSUKI의 두 번째 뇌입니다."*
