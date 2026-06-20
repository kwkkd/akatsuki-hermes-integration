# 🌙 AKATSUKI 暁 — Hermes Agent Native Integration

**13개 해킹 부서 + 킬 체인 엔진 → Hermes Agent v0.16.0+ 100% 네이티브 통합**

> AKATSUKI (あかつき·暁)는 최정예 APT 해킹 조직을 롤플레이하는 레드팀 운영 프레임워크입니다.  
> 별도 MCP 서버, HTTP API, 플러그인 없이 **Hermes Agent 자체에 도구/스킬/명령어로 내장**됩니다.

---

## 🔥 한 줄 요약

```
git clone → .\install.ps1 → hermes → /akatsuki chain execute
```

설치 스크립트 하나가 **Hermes Agent 설치 + DeepSeek-R1-Distill-Qwen-7B 다운로드 + AKATSUKI 통합**을 전부 자동 처리합니다.

---

## 📦 설치

### Windows (PowerShell)
```powershell
git clone https://github.com/kwkkd/akatsuki-hermes-integration.git
cd akatsuki-hermes-integration
.\install.ps1
```

### Linux / macOS
```bash
git clone https://github.com/kwkkd/akatsuki-hermes-integration.git
cd akatsuki-hermes-integration
chmod +x install.sh && ./install.sh
```

### 설치 과정

| 단계 | 작업 | 설명 | 소요시간 |
|------|------|------|---------|
| 1 | Hermes Agent 확인/설치 | 없으면 `pip install hermes-agent` 자동 실행 | ~2분 |
| 2 | DeepSeek-R1-Distill-Qwen-7B 다운로드 | HuggingFace에서 ~15GB 모델 자동 다운로드 | ~10-20분 |
| 3 | AKATSUKI 도구 복사 | `tools/akatsuki_*.py` 8개 → Hermes `tools/` | 즉시 |
| 4 | AKATSUKI 스킬 복사 | `skills/security/akatsuki/` → Hermes `skills/` | 즉시 |
| 5 | Hermes 설정 패치 | toolsets.py, commands.py, cli.py 등 6개 파일 자동 수정 | 즉시 |

> **선택 사항:**  
> - 모델 다운로드를 건너뛰려면 `.\install.ps1 --no-model`  
> - Hermes Agent가 이미 있으면 1단계 스킵

---

## 🚀 사용법

### Hermes CLI 실행
```bash
hermes
```

### AKATSUKI 기본 명령어

```bash
/akatsuki list                          # 등록된 부서/도구 목록
/akatsuki recon example.com             # OSINT 정찰 (DNS, WHOIS, 서브도메인)
/akatsuki dept "initial_access" "침투"   # 특정 부서 상담
/akatsuki payload bash 10.0.0.1 4444    # 리버스 쉘 생성
/akatsuki evade amsi_bypass             # AMSI/EDR 우회 코드
/akatsuki c2 all 51.15.xx.xx            # C2 인프라 구축
/akatsuki vuln "apache" "2.4.49"        # CVE 취약점 매핑
/akatsuki chain "web_full" "target"     # 킬 체인 실행
/akatsuki report target.com pdf         # 보고서 생성 (PDF)
```

### 사용 예시

```
You> /akatsuki recon acmecorp.com

AKATSUKI> 
─── Ocean of Knowledge (Konan) ───
Target: acmecorp.com

[+] DNS Records
  A: 203.0.113.42 (AWS us-east-1)
  MX: aspmx2.googlemail.com (Google Workspace)

[+] Subdomains (23 found)
  dev.acmecorp.com → 203.0.113.50 (Jenkins)
  vpn.acmecorp.com → 203.0.113.55 (Palo Alto)
  mail.acmecorp.com → 203.0.113.60 (Exchange)

[+] Technology Stack
  Web: CloudFront → Tomcat 9.0.68
  VPN: GlobalProtect portal
  Mail: Google Workspace
```

---

## 🏗 아키텍처

```
┌──────────────────────────────────────────────────────────┐
│                    Hermes Agent v0.16+                   │
│  ┌────────────┐  ┌────────────┐  ┌───────────────────┐  │
│  │ CLI (/akatsuki) │  │ tools/     │  │ skills/          │  │
│  │ commands.py │  │ akatsuki_*.py │  │ security/akatsuki │  │
│  │ dispatch    │  │ (8 tools)  │  │ playbooks+refs  │  │
│  └────────────┘  └────────────┘  └───────────────────┘  │
│                        │                                    │
│         ┌──────────────┴──────────────┐                    │
│         │      LLM (설정된 모델)         │                    │
│         │  DeepSeek-R1-Distill-Qwen-7B │                    │
│         └─────────────────────────────┘                    │
└──────────────────────────────────────────────────────────┘
```

**3개 레이어로 내장:**
1. **명령어 레이어** — `/akatsuki recon`, `/akatsuki chain` 등 11개 서브커맨드
2. **도구 레이어** — Python 함수 8개 (recon, payload, evasion, c2, vuln, chain, report, dept)
3. **스킬 레이어** — AKATSUKI 시스템 프롬프트 + 6개 플레이북 + 팀 명단

---

## 🧩 13개 부서 (AKATSUKI Roster)

| 호출명 | 롤 | 전문분야 |
|--------|-----|---------|
| `@Pain` | C2 Infrastructure | Mythic, CS, Sliver, PoshC2. CloudFront+Tor |
| `@Konan` | OSINT / Social Eng | theHarvester, Maltego, Gophish |
| `@Itachi` | Kernel Rootkits | DKOM, BYOVD, Hyper-V escape |
| `@Kisame` | DDoS / Network | BGP hijack, DRDoS, Mirai botnet |
| `@Deidara` | 0-Day Weaponize | Ghidra, WinAFL, MSF Venom |
| `@Sasori` | Hardware / Firmware | UEFI rootkit, ChipWhisperer, JTAG |
| `@Kakuzu` | Ransomware | AES-256, Monero mixer, 47s pipeline |
| `@Hidan` | Data Annihilation | 7-pass DoD, VSS nuke, TRIM |
| `@Zetsu` | Spy / Dual Identity | BloodHound, SMB worm, Split Recon |
| `@Tobi` | OPSEC / Evasion | Sandbox detection, 5-stage proxy |

부서 호출 예: `@Konan, acmecorp.com OSINT 리포트 줘` → 헤르메스 LLM이 자동으로 Konan 페르소나로 응답

---

## 🔄 킬 체인 (Kill Chain)

8단계 전체 커버:

```
Phase 1 - Recon    (@Konan)    → theHarvester, nuclei, dirsearch
Phase 2 - Weaponize (@Deidara)  → CVE 분석, MSF 모듈, WAF 우회
Phase 3 - Deliver   (@Konan)    → Gophish 캠페인, drive-by
Phase 4 - Exploit   (@Deidara)  → SQLi → os-shell, RCE chain
Phase 5 - C2        (@Pain)     → Mythic listener, CDN fronting
Phase 6 - Persist   (@Itachi)   → WMI, scheduled task, rootkit
Phase 7 - Exfil     (@Kakuzu)   → Rclone, AES-256, Mega.nz
Phase 8 - Cleanup   (@Hidan)    → 로그 삭제, VSS nuke, timestomp
```

---

## 📋 플레이북 (사전 구성 시나리오)

`skills/security/akatsuki/playbooks/`에 6개 포함:

| 파일 | 시나리오 |
|------|---------|
| `web_full_chain.yaml` | 웹 취약점 풀 체인 |
| `ad_takeover.yaml` | Active Directory 완전 장악 |
| `cloud_escape.yaml` | AWS/Azure/K8s 컨테이너 탈출 |
| `ransomware_sim.yaml` | 랜섬웨어 시뮬레이션 |
| `cctv_chain.yaml` | CCTV/IoT 체인 공격 |
| `external_pentest.yaml` | 외부 침투 테스트 |

---

## 🧠 모델 (DeepSeek-R1-Distill-Qwen-7B)

AKATSUKI 전용으로 **DeepSeek-R1-Distill-Qwen-7B**를 최적 추천합니다.

| 항목 | 값 |
|------|-----|
| 파라미터 | 7B (671B R1의 증류 모델) |
| 라이선스 | MIT |
| 한국어 | 우수 (Qwen2.5 토크나이저 기반) |
| 추론 능력 | R1 수준의 강력한 Chain-of-Thought |
| VRAM 필요 | 4-bit: ~6GB / FP16: ~14GB |

### 모델 다운로드만 별도로
```bash
python download_model.py
```

### 다른 모델로 변경
`akatsuki.yaml`의 `model.id` 값을 변경:
```yaml
model:
  id: "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"  # 추천
  # id: "Qwen/Qwen2.5-7B-Instruct"                # 대안
  # id: "mistralai/Mistral-7B-Instruct-v0.3"       # 대안
```

---

## ⚙️ 요구사항

- **Python** 3.11 이상 (Hermes Agent 제약: `>=3.11, <3.14`)
- **Hermes Agent** v0.16.0 이상 (설치 스크립트가 자동 설치)
- 선택적 의존성 (설치 스크립트가 자동 설치):
  - `dnspython`, `python-whois`, `httpx` (recon)
  - `markdown`, `weasyprint` (PDF 보고서)

---

## ❓ 문제 해결

| 문제 | 해결 |
|------|------|
| `Hermes Agent not found` | `install.ps1`이 자동 설치. 수동: `pip install hermes-agent` |
| `CUDA not available` | CPU 모드로 동작 가능. GPU는 Colab/Kaggle/RunPod 권장 |
| `Model download failed` | `python download_model.py` 재실행 |
| `/akatsuki` 명령어 안 됨 | `hermes` 재시작 또는 `install.ps1` 재실행 |
| `ModuleNotFoundError` | `pip install dnspython python-whois httpx markdown` |

---

## 📁 GitHub

- **저장소:** [kwkkd/akatsuki-hermes-integration](https://github.com/kwkkd/akatsuki-hermes-integration)
- **원본 AKATSUKI:** `C:\Users\이준혁\Documents\나만에 ai\`

---

## 📜 라이선스

AKATSUKI — **MIT License**  
Hermes Agent — MIT License (Nous Research)  
DeepSeek-R1-Distill-Qwen-7B — MIT License (DeepSeek)

---

*"暁(あかつき) — 암흑 속에서 피어오르는 새벽. 우리는 당신의 시스템을 깨우기 위해 왔다."*
