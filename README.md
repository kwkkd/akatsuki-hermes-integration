# AKATSUKI 暁 — Hermes Agent Native Integration

**13 multi-agent departments + kill chain engine → as native Hermes Agent tools**

> AKATSUKI (あかつき·暁)는 13개 전문 부서로 구성된 레드팀 운영 프레임워크입니다.  
> 이 통합은 AKATSUKI를 Hermes Agent(v0.16.0)의 네이티브 도구/스킬/퍼스낼리티로 이식합니다.  
> 별도 MCP 서버, HTTP API, 플러그인 없이 Hermes 자체에 내장됩니다.

---

## Structure

```
akatsuki-hermes-integration/
├── tools/                          # Hermes Agent tools (tools/ 디렉토리에 복사)
│   ├── akatsuki_recon.py           # OSINT 정찰 (DNS, WHOIS, 서브도메인)
│   ├── akatsuki_payload.py         # 리버스 쉘 생성기
│   ├── akatsuki_evasion.py         # AMSI 우회, 난독화, 샌드박스 회피
│   ├── akatsuki_c2.py              # C2 인프라 (Cobalt Strike, nginx, WireGuard, Tor)
│   ├── akatsuki_vuln.py            # CVE 매핑 (Log4j, Exchange, Fortinet, VMware)
│   ├── akatsuki_chain.py           # 킬 체인 빌더/실행기 (6단계)
│   ├── akatsuki_report.py          # 침투 테스트 보고서 (Markdown/PDF)
│   └── akatsuki_dept.py            # 13개 부서 협업 엔진
├── skills/                         # Hermes Agent skills (skills/ 디렉토리에 복사)
│   └── security/akatsuki/
│       ├── SKILL.md                # 메인 스킬 문서
│       ├── playbooks/              # 6개 시나리오 플레이북
│       └── references/             # 팀 명단 + 퍼스낼리티 설정 가이드
├── patches/                        # 기존 Hermes 파일 변경 내역
│   ├── 01-toolsets.py.patch
│   ├── 02-tools_config.py.patch
│   ├── 03-commands.py.patch
│   ├── 04-cli_commands_mixin.py.patch
│   └── 05-cli.py.patch
├── akatsuki-original/              # 원본 AKATSUKI 독립 실행 파일
│   └── (team_agents.py, hacker_team.py, recon_engine.py 등)
├── install.ps1                     # Windows/PowerShell 설치 스크립트
├── install.sh                      # Linux/macOS 설치 스크립트
└── README.md
```

## Quick Install

```bash
# Windows (PowerShell)
.\install.ps1

# Linux / macOS
chmod +x install.sh && ./install.sh
```

설치 스크립트는:
1. `tools/akatsuki_*.py` → `$HERMES_HOME/tools/` 복사
2. `skills/security/akatsuki/` → `$HERMES_HOME/skills/security/akatsuki/` 복사
3. 기존 Hermes 파일(`toolsets.py`, `tools_config.py`, `commands.py`, `cli.py`, `cli_commands_mixin.py`)에 AKATSUKI 등록 코드를 추가합니다.

## Manual Install (선택)

### 1. 툴 파일 복사
```bash
cp tools/akatsuki_*.py /path/to/hermes-agent/tools/
```

### 2. 스킬 복사
```bash
cp -r skills/security/akatsuki /path/to/hermes-agent/skills/security/akatsuki
```

### 3. 기존 파일 패치
`patches/` 디렉토리의 각 `.patch` 파일을 참고하여 다음 파일을 수정합니다:
- `toolsets.py` — `_HERMES_CORE_TOOLS`에 `akatsuki_*` 8개 추가 + `TOOLSETS["akatsuki"]` 정의
- `hermes_cli/tools_config.py` — `CONFIGURABLE_TOOLSETS`에 akatsuki 추가
- `hermes_cli/commands.py` — `COMMAND_REGISTRY`에 `/akatsuki` 명령어 추가
- `cli.py` — `canonical == "akatsuki"` 디스패치 추가
- `hermes_cli/cli_commands_mixin.py` — `_handle_akatsuki_command()` 메서드 추가

### 4. 퍼스낼리티 등록 (선택)
`~/.hermes/config.yaml`에 아래 내용을 추가:
```yaml
agent:
  personalities:
    akatsuki:
      description: "AKATSUKI 暁 — APT 해킹 조직 AI"
      system_prompt: "(skills/security/akatsuki/references/personality-config.md 참조)"
```

## Usage

```bash
# Hermes CLI 실행
hermes

# AKATSUKI 명령어
/akatsuki list                              # 부서 목록
/akatsuki recon example.com                 # OSINT 정찰
/akatsuki dept initial_access "침투 계획"     # 부서 상담
/akatsuki payload bash 10.0.0.1 4444        # 페이로드 생성
/akatsuki evade amsi_bypass                 # AMSI 우회 코드
/akatsuki c2 all 51.15.xx.xx                # C2 인프라
/akatsuki vuln "apache httpd" "2.4.49"      # CVE 매핑
/akatsuki chain execute 192.168.1.1         # 킬 체인 실행
/akatsuki report target.com pdf             # 보고서 생성

# 퍼스낼리티 (등록 후)
/personality akatsuki
```

## Requirements

- **Hermes Agent** v0.16.0+
- **Python** 3.11+
- 선택적 의존성: `dnspython`, `python-whois`, `httpx` (recon 도구), `markdown`, `weasyprint` (PDF 보고서)

## License

AKATSUKI — MIT License  
Hermes Agent — MIT License (Nous Research)
