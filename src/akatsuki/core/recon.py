"""Reconnaissance engine for domain, IP, email, and URL intelligence gathering."""

import asyncio
import ipaddress
import re
import socket
from dataclasses import dataclass, field
from typing import Optional

try:
    import dns.resolver
    import dns.exception
    HAS_DNS = True
except ImportError:
    HAS_DNS = False

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

from .logger import logger


@dataclass
class ReconResult:
    target: str
    target_type: str
    ip_addresses: list = field(default_factory=list)
    hostnames: list = field(default_factory=list)
    open_ports: list = field(default_factory=list)
    whois_info: dict = field(default_factory=dict)
    dns_records: dict = field(default_factory=dict)
    http_headers: dict = field(default_factory=dict)
    technologies: list = field(default_factory=list)
    subdomains: list = field(default_factory=list)
    emails: list = field(default_factory=list)
    error: Optional[str] = None


class ReconEngine:
    """Performs reconnaissance on domains, IPs, emails, and URLs."""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.session = None

    async def _ensure_session(self):
        if self.session is None and HAS_AIOHTTP:
            import aiohttp
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))

    async def close(self):
        if self.session:
            await self.session.close()
            self.session = None

    def _resolve_ip(self, hostname: str) -> list:
        ips = []
        try:
            for info in socket.getaddrinfo(hostname, None):
                addr = info[4][0]
                if addr not in ips:
                    ips.append(addr)
        except Exception as e:
            logger.debug(f"DNS resolution failed for {hostname}: {e}")
        return ips

    async def _resolve_dns(self, domain: str) -> dict:
        records = {}
        if not HAS_DNS:
            return records
        for rtype in ("A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"):
            try:
                answers = await asyncio.to_thread(
                    dns.resolver.resolve, domain, rtype, raise_on_no_answer=False
                )
                if answers:
                    records[rtype] = [str(r) for r in answers]
            except (dns.exception.DNSException, Exception) as e:
                logger.debug(f"DNS {rtype} lookup failed for {domain}: {e}")
        return records

    async def _fetch_headers(self, url: str) -> dict:
        if not HAS_AIOHTTP:
            return {}
        await self._ensure_session()
        try:
            async with self.session.get(url, ssl=False, allow_redirects=True) as resp:
                return dict(resp.headers)
        except Exception as e:
            logger.debug(f"HTTP header fetch failed for {url}: {e}")
            return {}

    async def recon_domain(self, domain: str) -> ReconResult:
        result = ReconResult(target=domain, target_type="domain")
        try:
            result.ip_addresses = self._resolve_ip(domain)
            result.dns_records = await self._resolve_dns(domain)
            result.http_headers = await self._fetch_headers(f"https://{domain}")
            if not result.http_headers:
                result.http_headers = await self._fetch_headers(f"http://{domain}")
            tech = []
            server = result.http_headers.get("Server", "")
            if server:
                tech.append(server)
            x_powered = result.http_headers.get("X-Powered-By", "")
            if x_powered:
                tech.append(x_powered)
            result.technologies = tech
        except Exception as e:
            result.error = str(e)
            logger.error(f"Domain recon failed for {domain}: {e}")
        return result

    async def recon_ip(self, ip: str) -> ReconResult:
        result = ReconResult(target=ip, target_type="ip")
        try:
            ipaddress.ip_address(ip)
            try:
                hostname, _, _ = await asyncio.to_thread(socket.gethostbyaddr, ip)
                result.hostnames = [hostname]
            except (socket.herror, Exception):
                pass
            result.http_headers = await self._fetch_headers(f"https://{ip}")
        except Exception as e:
            result.error = str(e)
            logger.error(f"IP recon failed for {ip}: {e}")
        return result

    async def recon_email(self, email: str) -> ReconResult:
        result = ReconResult(target=email, target_type="email")
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            result.error = "Invalid email format"
            return result
        try:
            domain = email.split("@")[1]
            result.dns_records = await self._resolve_dns(domain)
            result.ip_addresses = self._resolve_ip(domain)
        except Exception as e:
            result.error = str(e)
            logger.error(f"Email recon failed for {email}: {e}")
        return result

    async def recon_url(self, url: str) -> ReconResult:
        result = ReconResult(target=url, target_type="url")
        try:
            result.http_headers = await self._fetch_headers(url)
            parsed = url.split("/")[2] if "://" in url else url.split("/")[0]
            result.ip_addresses = self._resolve_ip(parsed)
            tech = []
            server = result.http_headers.get("Server", "")
            if server:
                tech.append(server)
            x_powered = result.http_headers.get("X-Powered-By", "")
            if x_powered:
                tech.append(x_powered)
            result.technologies = tech
        except Exception as e:
            result.error = str(e)
            logger.error(f"URL recon failed for {url}: {e}")
        return result

    async def run(self, target: str) -> ReconResult:
        if re.match(r"^\d{1,3}(\.\d{1,3}){3}$", target):
            return await self.recon_ip(target)
        if "@" in target:
            return await self.recon_email(target)
        if target.startswith(("http://", "https://")):
            return await self.recon_url(target)
        if "." in target:
            return await self.recon_domain(target)
        return ReconResult(target=target, target_type="unknown", error="Unrecognized target type")
