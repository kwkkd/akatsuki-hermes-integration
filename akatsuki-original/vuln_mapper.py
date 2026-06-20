import json
from typing import List
from dataclasses import dataclass

@dataclass
class VulnEntry:
    cve_id: str
    severity: str
    cvss_score: float
    affected_software: str
    vuln_type: str
    description: str
    exploit_available: bool
    metasploit_module: str = ""

class VulnMapper:
    VULN_DB = {
        "apache": {"log4j": {"cve": "CVE-2021-44228", "severity": "CRITICAL", "cvss": 10.0, "type": "RCE", "msf": "exploit/multi/http/log4j_header_injection"}},
        "fortinet": {"fortigate_sslvpn": {"cve": "CVE-2018-13379", "severity": "HIGH", "cvss": 9.8, "type": "Path Traversal", "msf": ""}},
        "microsoft": {"exchange_proxylogon": {"cve": "CVE-2021-26855", "severity": "CRITICAL", "cvss": 9.8, "type": "SSRF", "msf": "exploit/windows/http/exchange_proxylogon_rce"}},
        "hikvision": {"cve_2017_7921": {"cve": "CVE-2017-7921", "severity": "HIGH", "cvss": 8.5, "type": "Auth Bypass", "msf": ""}},
        "vmware": {"vcenter_rce": {"cve": "CVE-2021-21972", "severity": "CRITICAL", "cvss": 9.8, "type": "RCE", "msf": "exploit/multi/http/vmware_vcenter_rce"}},
    }

    def classify(self, service_name: str, version: str = "", port: int = 0) -> List[VulnEntry]:
        results = []
        service_lower = service_name.lower()
        for vendor, vulns in self.VULN_DB.items():
            if vendor in service_lower:
                for vuln_name, data in vulns.items():
                    results.append(VulnEntry(
                        cve_id=data["cve"], severity=data["severity"],
                        cvss_score=data["cvss"], affected_software=f"{service_name} {version}",
                        vuln_type=data["type"], description=f"{service_name} {vuln_name}",
                        exploit_available=bool(data["msf"]), metasploit_module=data["msf"]
                    ))
        return results

    def map_from_nmap(self, nmap_result: dict) -> List[VulnEntry]:
        all_vulns = []
        for port_info in nmap_result.get("ports", []):
            service = port_info.get("service", "")
            version = port_info.get("version", "")
            all_vulns.extend(self.classify(service, version, port_info.get("port", 0)))
        return all_vulns

    def map_from_nuclei(self, nuclei_findings: list) -> List[VulnEntry]:
        all_vulns = []
        for finding in nuclei_findings:
            if isinstance(finding, dict):
                cve = finding.get("info", {}).get("classification", {}).get("cve_id", "") or finding.get("info", {}).get("name", "N/A")
                severity = finding.get("info", {}).get("severity", "unknown")
                cvss = finding.get("info", {}).get("classification", {}).get("cvss-score", 0.0)
                desc = finding.get("info", {}).get("description", "")
                all_vulns.append(VulnEntry(
                    cve_id=cve, severity=severity.upper(), cvss_score=float(cvss) if cvss else 0.0,
                    affected_software=finding.get("host", ""), vuln_type=finding.get("type", ""),
                    description=desc[:200], exploit_available=True
                ))
        return all_vulns

    def prioritize(self, vulns: List[VulnEntry], max_results: int = 10) -> List[VulnEntry]:
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "UNKNOWN": 4}
        return sorted(vulns, key=lambda v: (severity_order.get(v.severity.upper(), 4), -v.cvss_score))[:max_results]

if __name__ == "__main__":
    mapper = VulnMapper()
    test_vulns = mapper.classify("apache httpd", "2.4.49")
    print(json.dumps([vars(v) for v in test_vulns], indent=2, ensure_ascii=False))
