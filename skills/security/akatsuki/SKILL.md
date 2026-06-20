---
name: akatsuki
description: "AKATSUKI 暁 — Red Team Operations Framework. 13 specialized departments, OSINT recon, payload generation, AV/EDR evasion, C2 infrastructure, vulnerability mapping, kill chain execution, and report generation."
version: 1.0.0
author: AKATSUKI
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [red-team, pentest, security, c2, osint, evasion, ransomware, ad, exploit]
    related_skills: [plan, nmap, sqlmap, python]
---

# AKATSUKI 暁 — Red Team Operations Framework

AKATSUKI is a comprehensive red team operations framework with 13 specialized departments, each with unique expertise and tools.

## Available Tools

### `/akatsuki dept <name> <objective> [context]`
Consult a single AKATSUKI department.

### `/akatsuki parallel <depts> <objective> [context]`
Run multiple departments in parallel for independent analysis.

### `/akatsuki collaborate <depts> <objective> [context]`
Two-pass peer review: Round 1 independent analysis, Round 2 cross-department critique.

### `/akatsuki recon <target>`
Full OSINT reconnaissance: DNS, WHOIS, subdomains, tech detection.

### `/akatsuki payload <type> <lhost> <lport>`
Generate reverse shell payloads (python, bash, php, powershell, netcat).

### `/akatsuki evade <action> [language] [payload]`
Generate AMSI bypass, obfuscation, sandbox evasion, or payload compression.

### `/akatsuki c2 <action> <lhost> [lport]`
Build C2 infrastructure: Cobalt Strike profiles, nginx redirectors, WireGuard, Tor.

### `/akatsuki vuln <service> [version]`
Map services to known CVEs (Apache Log4j, Exchange, Fortinet, VMware, etc.).

### `/akatsuki chain <action> [target] [objective]`
Build and execute multi-phase kill chains with dependency resolution.

### `/akatsuki report <target> [format]`
Generate penetration test reports in Markdown or PDF.

## 13 Departments

| Department | Title | Expertise |
|---|---|---|
| boss | Organization Leader | Multi-identity opsec, strategic planning |
| coo | Operations Director | Cross-dept coordination, internal security |
| finance | Finance Manager | Crypto tracking, budget, procurement |
| rnd_malware | Malware Engineering | Ransomware, packers, AV evasion |
| rnd_exploit | Exploit Development | 0-day research, CVE acquisition |
| initial_access | IAB Lead | Phishing, VPN CVEs, social engineering |
| post_exploit | Post-Exploitation | PrivEsc, AD, exfil, backup destruction |
| infrastructure | C2 Lead | C2 servers, bulletproof hosting, TOR |
| negotiation | Extortion Lead | Victim comms, ransom pricing |
| money_laundering | ML Lead | Crypto mixing, mules, OTC |
| raas_affiliate | Affiliate Manager | Recruitment, revenue share |
| intel_pr | Intel & PR Lead | Leak site, press, competitor tracking |
| cctv | Surveillance Lead | IP cameras, DVRs, physical access |

## Playbooks

- **external_pentest**: External infrastructure penetration test
- **web_full_chain**: Full web application pentest chain
- **ransomware_sim**: Complete ransomware operation lifecycle
- **ad_takeover**: Active Directory takeover
- **cctv_chain**: Surveillance system compromise chain
- **cloud_escape**: Cloud environment escape
