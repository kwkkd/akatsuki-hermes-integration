---
name: akatsuki-web-full-chain
description: "Full web application penetration test: whatweb → nmap → nuclei → sqlmap → post-exploit → report."
version: 1.0.0
metadata:
  hermes:
    tags: [web, pentest, sqlmap, nuclei, xss, sqli]
---

# Web Application Full Chain Playbook

## Phases

### Phase 1: Recon
- WhatWeb fingerprinting
- Nmap port scan
- `akatsuki_recon` on domain

### Phase 2: Scan
- Nuclei CVE templates
- `akatsuki_vuln` classify web services

### Phase 3: Exploit
- SQLMap on identified SQL endpoints
- `akatsuki_payload` for reverse shells
- `akatsuki_evasion` for WAF bypass

### Phase 4: Post-Exploit
- Lateral movement via `akatsuki_dept` post_exploit
- Data exfiltration planning

### Phase 5: Report
- `akatsuki_report` generate findings
