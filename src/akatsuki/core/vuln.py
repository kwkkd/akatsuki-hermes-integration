"""Vulnerability mapper with hardcoded CVE database and NVD fetch capability."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .logger import logger


@dataclass
class VulnEntry:
    cve_id: str
    description: str
    severity: str
    affected_software: str
    affected_version: str
    cvss_score: float = 0.0
    known_exploit: bool = False
    remediation: str = ""
    source: str = "builtin"
    fetched_at: Optional[str] = None


CVE_DATABASE = {
    "apache": [
        VulnEntry(
            cve_id="CVE-2021-41773",
            description="Apache HTTP Server 2.4.49 path traversal vulnerability",
            severity="critical",
            affected_software="apache http server",
            affected_version="2.4.49",
            cvss_score=7.5,
            known_exploit=True,
            remediation="Upgrade to Apache 2.4.51+",
        ),
        VulnEntry(
            cve_id="CVE-2021-42013",
            description="Apache HTTP Server 2.4.50 path traversal and RCE",
            severity="critical",
            affected_software="apache http server",
            affected_version="2.4.50",
            cvss_score=9.0,
            known_exploit=True,
            remediation="Upgrade to Apache 2.4.51+",
        ),
    ],
    "nginx": [
        VulnEntry(
            cve_id="CVE-2021-23017",
            description="Nginx DNS resolver vulnerability leading to memory corruption",
            severity="high",
            affected_software="nginx",
            affected_version="0.6.18-1.20.0",
            cvss_score=8.1,
            known_exploit=False,
            remediation="Upgrade to Nginx 1.21.0+",
        ),
    ],
    "fortinet": [
        VulnEntry(
            cve_id="CVE-2018-13379",
            description="Fortinet FortiOS SSL VPN path traversal leaking session keys",
            severity="critical",
            affected_software="fortigate fortios",
            affected_version="5.6.0-5.6.7, 6.0.0-6.0.4",
            cvss_score=9.8,
            known_exploit=True,
            remediation="Upgrade to FortiOS 5.6.8+ or 6.0.5+",
        ),
        VulnEntry(
            cve_id="CVE-2022-40684",
            description="Fortinet authentication bypass on administrative interface",
            severity="critical",
            affected_software="fortigate fortios, fortiproxy",
            affected_version="7.0.0-7.0.6, 7.2.0-7.2.1",
            cvss_score=9.6,
            known_exploit=True,
            remediation="Upgrade to FortiOS 7.0.7+ or 7.2.2+",
        ),
    ],
    "openssh": [
        VulnEntry(
            cve_id="CVE-2024-6387",
            description="OpenSSH regreSSHion remote unauthenticated code execution (signal handler race)",
            severity="critical",
            affected_software="openssh",
            affected_version="8.5p1-9.7p1",
            cvss_score=8.1,
            known_exploit=True,
            remediation="Upgrade to OpenSSH 9.8p1+",
        ),
    ],
    "tomcat": [
        VulnEntry(
            cve_id="CVE-2017-12617",
            description="Apache Tomcat PUT method arbitrary JSP upload",
            severity="critical",
            affected_software="apache tomcat",
            affected_version="7.0.0-7.0.79",
            cvss_score=8.1,
            known_exploit=True,
            remediation="Upgrade to Tomcat 7.0.81+ or disable PUT",
        ),
    ],
    "mysql": [
        VulnEntry(
            cve_id="CVE-2012-2122",
            description="MySQL authentication bypass via incorrect type coercion",
            severity="high",
            affected_software="mysql, mariadb",
            affected_version="5.1.x, 5.5.x, 5.6.x prior to patches",
            cvss_score=7.5,
            known_exploit=True,
            remediation="Apply vendor patches for MySQL/MariaDB",
        ),
    ],
    "jenkins": [
        VulnEntry(
            cve_id="CVE-2024-23897",
            description="Jenkins CLI arbitrary file read vulnerability",
            severity="high",
            affected_software="jenkins",
            affected_version="2.441- LTS 2.426.2",
            cvss_score=7.5,
            known_exploit=True,
            remediation="Upgrade to Jenkins 2.442+ or LTS 2.426.3+",
        ),
    ],
    "exchange": [
        VulnEntry(
            cve_id="CVE-2021-26855",
            description="Microsoft Exchange Server SSRF (ProxyLogon)",
            severity="critical",
            affected_software="microsoft exchange server",
            affected_version="2013, 2016, 2019",
            cvss_score=9.8,
            known_exploit=True,
            remediation="Apply Microsoft security patches from March 2021",
        ),
    ],
    "wordpress": [
        VulnEntry(
            cve_id="CVE-2024-52415",
            description="WordPress Deserialization of Untrusted Data vulnerability",
            severity="high",
            affected_software="wordpress",
            affected_version="<6.7.1",
            cvss_score=8.8,
            known_exploit=False,
            remediation="Upgrade to WordPress 6.7.1+",
        ),
    ],
}


class VulnMapper:
    """Maps vulnerabilities to targets based on software signatures."""

    def __init__(self):
        self.cve_index = {}
        self._build_index()

    def _build_index(self):
        for software, entries in CVE_DATABASE.items():
            for entry in entries:
                self.cve_index[entry.cve_id.lower()] = entry

    def lookup(self, cve_id: str) -> Optional[VulnEntry]:
        return self.cve_index.get(cve_id.lower())

    def search(self, query: str) -> list:
        query = query.lower()
        results = []
        for entry in self.cve_index.values():
            if query in entry.cve_id.lower() or query in entry.description.lower() or query in entry.affected_software.lower():
                results.append(entry)
        return results

    def search_by_software(self, software: str) -> list:
        return CVE_DATABASE.get(software.lower(), [])

    def all_vulnerabilities(self) -> list:
        return list(self.cve_index.values())

    async def fetch_nvd_cve(self, cve_id: str) -> Optional[dict]:
        """Fetch CVE details from NVD API (async)."""
        try:
            import aiohttp
            url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={cve_id}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status != 200:
                        logger.warning(f"NVD API returned {resp.status} for {cve_id}")
                        return None
                    data = await resp.json()
                    return data
        except ImportError:
            logger.warning("aiohttp not installed; cannot fetch NVD data")
            return None
        except Exception as e:
            logger.error(f"NVD fetch failed for {cve_id}: {e}")
            return None
