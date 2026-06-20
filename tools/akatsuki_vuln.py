import json
import logging
from dataclasses import dataclass
from typing import List

from tools.registry import registry, tool_error, tool_result

logger = logging.getLogger(__name__)


VULN_DB = {
    "apache": {
        "log4j": {"cve": "CVE-2021-44228", "severity": "CRITICAL", "cvss": 10.0, "type": "RCE", "msf": "exploit/multi/http/log4j_header_injection"},
        "httpd_2_4_49": {"cve": "CVE-2021-41773", "severity": "CRITICAL", "cvss": 9.8, "type": "Path Traversal RCE", "msf": "exploit/multi/http/apache_normalize_path_rce"},
    },
    "fortinet": {
        "fortigate_sslvpn": {"cve": "CVE-2018-13379", "severity": "HIGH", "cvss": 9.8, "type": "Path Traversal", "msf": ""},
    },
    "microsoft": {
        "exchange_proxylogon": {"cve": "CVE-2021-26855", "severity": "CRITICAL", "cvss": 9.8, "type": "SSRF", "msf": "exploit/windows/http/exchange_proxylogon_rce"},
        "exchange_proxyshell": {"cve": "CVE-2021-34473", "severity": "CRITICAL", "cvss": 9.8, "type": "RCE", "msf": "exploit/windows/http/exchange_proxyshell_rce"},
    },
    "hikvision": {
        "cve_2017_7921": {"cve": "CVE-2017-7921", "severity": "HIGH", "cvss": 8.5, "type": "Auth Bypass", "msf": ""},
    },
    "vmware": {
        "vcenter_rce": {"cve": "CVE-2021-21972", "severity": "CRITICAL", "cvss": 9.8, "type": "RCE", "msf": "exploit/multi/http/vmware_vcenter_rce"},
    },
    "confluence": {
        "cve_2022_26134": {"cve": "CVE-2022-26134", "severity": "CRITICAL", "cvss": 9.8, "type": "OGNL RCE", "msf": "exploit/multi/http/atlassian_confluence_ognl_rce"},
    },
}


def classify(service_name: str, version: str = "") -> list:
    results = []
    service_lower = service_name.lower()
    for vendor, vulns in VULN_DB.items():
        if vendor in service_lower:
            for vuln_name, data in vulns.items():
                results.append({
                    "cve_id": data["cve"],
                    "severity": data["severity"],
                    "cvss_score": data["cvss"],
                    "affected_software": f"{service_name} {version}",
                    "vuln_type": data["type"],
                    "description": f"{service_name} — {vuln_name}",
                    "exploit_available": bool(data["msf"]),
                    "metasploit_module": data["msf"],
                })
    return results


def prioritize(vulns: list, max_results: int = 10) -> list:
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "UNKNOWN": 4}
    return sorted(
        vulns,
        key=lambda v: (severity_order.get(v["severity"].upper(), 4), -v["cvss_score"]),
    )[:max_results]


AKATSUKI_VULN_SCHEMA = {
    "name": "akatsuki_vuln",
    "description": "AKATSUKI Vulnerability Mapper — classify services against a CVE database (Apache Log4j, Exchange ProxyLogon, Fortinet, VMware, Confluence, Hikvision), rank by CVSS, and identify available Metasploit modules.",
    "parameters": {
        "type": "object",
        "properties": {
            "service": {
                "type": "string",
                "description": "Service name to classify (e.g., 'apache httpd', 'microsoft exchange', 'fortinet fortigate')",
            },
            "version": {
                "type": "string",
                "description": "Optional version string for more precise matching",
            },
        },
        "required": ["service"],
    },
}


def akatsuki_vuln(service: str, version: str = "") -> str:
    found = classify(service, version)
    if not found:
        return tool_result({
            "service": service,
            "version": version,
            "cve_count": 0,
            "vulnerabilities": [],
            "note": "No known CVEs in AKATSUKI database for this service. Try a broader service name.",
        })
    ranked = prioritize(found)
    return tool_result({
        "service": service,
        "version": version,
        "cve_count": len(ranked),
        "vulnerabilities": ranked,
    })


def check_akatsuki_vuln_requirements() -> bool:
    return True


registry.register(
    name="akatsuki_vuln",
    toolset="akatsuki",
    schema=AKATSUKI_VULN_SCHEMA,
    handler=lambda args, **kw: akatsuki_vuln(
        service=args["service"],
        version=args.get("version", ""),
    ),
    check_fn=check_akatsuki_vuln_requirements,
    emoji="🎯",
)
