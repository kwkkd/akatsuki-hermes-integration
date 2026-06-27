import json
import logging
import os
from pathlib import Path

from tools.registry import registry, tool_error, tool_result

logger = logging.getLogger(__name__)


def _load_vuln_db() -> dict:
    db_path = Path(__file__).resolve().parent.parent / "data" / "vuln_db.yaml"
    override = os.environ.get("AKATSUKI_VULN_DB")
    if override:
        db_path = Path(override)
    if db_path.exists():
        try:
            import yaml
            with open(db_path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Failed to load vuln DB from {db_path}: {e}")
    return {}


VULN_DB = _load_vuln_db()


def reload_db():
    global VULN_DB
    VULN_DB = _load_vuln_db()


def classify(service_name: str, version: str = "") -> list:
    results = []
    service_lower = service_name.lower()
    for vendor, vulns in VULN_DB.items():
        if vendor in service_lower:
            for vuln_name, data in vulns.items():
                match = True
                if version and data.get("affected_versions"):
                    match = any(version in av for av in data["affected_versions"])
                if match:
                    results.append({
                        "cve_id": data["cve"],
                        "severity": data["severity"],
                        "cvss_score": data["cvss"],
                        "affected_software": f"{service_name} {version}",
                        "vuln_type": data["type"],
                        "description": data.get("description", f"{service_name} — {vuln_name}"),
                        "exploit_available": bool(data.get("msf")),
                        "metasploit_module": data.get("msf", ""),
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
    "description": "AKATSUKI Vulnerability Mapper — classify services against a CVE database, rank by CVSS, and identify available Metasploit modules. Database loaded from data/vuln_db.yaml.",
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
    if not service or not isinstance(service, str):
        return tool_error("service must be a non-empty string")
    service = service.strip()[:200]
    version = str(version).strip()[:100] if version else ""
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
