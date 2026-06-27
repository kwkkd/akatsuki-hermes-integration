---
name: akatsuki-ad-takeover
description: "Active Directory takeover playbook: AD recon → privilege escalation → domain dominance."
version: 1.0.0
metadata:
  hermes:
    tags: [ad, active-directory, kerberos, domain, bloodhound]
---

# Active Directory Takeover Playbook

## Phases

### Phase 1: AD Recon
- Port scan for AD services (88, 389, 445, 636, 3268, 3269)
- `akatsuki_dept` consult post_exploit team
- `akatsuki_vuln` on MS Exchange / AD services

### Phase 2: Privilege Escalation
- Kerberos attack planning
- `akatsuki_chain` execute with AD objective
- `akatsuki_evasion` for AMSI bypass on lateral movement

### Phase 3: Domain Dominance
- `akatsuki_c2` establish persistent C2
- `akatsuki_dept` parallel: post_exploit + infrastructure
- Dump NTDS.dit, crack credentials

### Phase 4: Exfiltration & Cleanup
- `akatsuki_report` generate findings
