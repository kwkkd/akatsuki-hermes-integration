---
name: akatsuki-ransomware-sim
description: "Complete ransomware operation lifecycle simulation: initial access → core execution → monetization."
version: 1.0.0
metadata:
  hermes:
    tags: [ransomware, simulation, red-team, ad, encryption]
---

# Full Ransomware Simulation Playbook

## Phases

### Phase 1: Initial Access (stop on fail)
- Network scan for exposed services
- `akatsuki_dept` consult initial_access team
- `akatsuki_vuln` prioritize entry vectors

### Phase 2: Core Execution (stop on fail)
- Lateral movement via `akatsuki_dept` post_exploit
- `akatsuki_evasion` for EDR bypass
- `akatsuki_c2` deploy C2 infrastructure
- `akatsuki_payload` generate deployment payloads
- Backup enumeration and destruction

### Phase 3: Monetization
- `akatsuki_dept` consult negotiation team
- `akatsuki_dept` consult money_laundering team
- `akatsuki_report` generate full operation report
