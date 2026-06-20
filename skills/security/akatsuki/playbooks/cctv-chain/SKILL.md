---
name: akatsuki-cctv-chain
description: "Surveillance system compromise: camera discovery → cred brute-force → RTSP hijack → physical access."
version: 1.0.0
metadata:
  hermes:
    tags: [cctv, surveillance, iot, camera, hikvision, dahua]
---

# CCTV Surveillance Chain Playbook

## Phases

### Phase 1: Camera Discovery
- `akatsuki_recon` on target network
- `akatsuki_dept` consult cctv team
- `akatsuki_vuln` on Hikvision/Dahua services

### Phase 2: Access
- Default credential attacks
- Known CVEs (CVE-2017-7921, etc.)
- `akatsuki_payload` for IoT implants

### Phase 3: Exploitation
- RTSP stream hijacking
- DVR/NVR firmware backdoor
- `akatsuki_evasion` for persistence

### Phase 4: Coverage
- `akatsuki_report` document findings
