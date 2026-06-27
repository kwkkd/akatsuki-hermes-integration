---
name: akatsuki-cloud-escape
description: "Cloud environment escape: metadata service abuse → container breakout → cross-account pivot."
version: 1.0.0
metadata:
  hermes:
    tags: [cloud, aws, azure, gcp, kubernetes, container, escape]
---

# Cloud Escape Playbook

## Phases

### Phase 1: Cloud Recon
- `akatsuki_recon` on cloud endpoints
- `akatsuki_vuln` on identified cloud services
- `akatsuki_dept` consult initial_access team

### Phase 2: Metadata Service
- Cloud metadata API exploitation (169.254.169.254)
- IAM credential extraction
- `akatsuki_chain` execute with cloud objective

### Phase 3: Container/K8s Escape
- `akatsuki_evasion` for container detection bypass
- `akatsuki_payload` for container breakouts
- `akatsuki_c2` for cloud C2 redirectors

### Phase 4: Cross-Account Pivot
- `akatsuki_dept` collaborate: post_exploit + infrastructure
- `akatsuki_report` generate findings
