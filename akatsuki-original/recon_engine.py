import dns.resolver
import json
import os
import sys
import re
from urllib.parse import urlparse
sys.path.insert(0, os.path.dirname(__file__))

class ReconEngine:
    def __init__(self):
        self.resolver = dns.resolver.Resolver()
        self.resolver.timeout = 5; self.resolver.lifetime = 10
    def domain_recon(self, domain: str) -> dict:
        return {"domain": domain, "whois": self._quick_whois(domain), "dns": self._dns_records(domain), "subdomains": self._subdomain_enum(domain), "tech": self._tech_detect(domain), "email": self._email_discover(domain)}
    def ip_recon(self, ip: str) -> dict:
        return {"ip": ip, "ptr": self._ptr_lookup(ip), "hosting": self._hosting_detect(ip)}
    def url_recon(self, url: str) -> dict:
        parsed = urlparse(url)
        return {"url": url, "scheme": parsed.scheme, "hostname": parsed.hostname, "port": parsed.port, "path": parsed.path, "params": parsed.params, "query": parsed.query}
    def email_recon(self, email: str) -> dict:
        domain = email.split("@")[-1] if "@" in email else ""
        return {"email": email, "domain": domain, "mx_records": self._mx_lookup(domain) if domain else []}
    def full_recon(self, target: str) -> dict:
        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', target): return self.ip_recon(target)
        if "@" in target: return self.email_recon(target)
        if target.startswith("http"): return self.url_recon(target)
        return self.domain_recon(target)
    def _dns_records(self, domain: str) -> dict:
        records = {}
        for rtype in ["A", "AAAA", "MX", "NS", "TXT", "SOA", "CNAME", "SPF", "DMARC"]:
            try: answers = self.resolver.resolve(domain, rtype); records[rtype] = [str(r) for r in answers]
            except Exception: records[rtype] = []
        return records
    def _subdomain_enum(self, domain: str) -> list:
        common = ["www", "mail", "admin", "api", "dev", "test", "stage", "blog", "portal", "vpn", "remote", "webmail", "cpanel", "ns1", "ns2", "smtp", "pop3", "imap", "ftp", "ssh", "jenkins", "gitlab", "jira", "confluence", "wiki", "docs", "help", "support", "status", "monitor", "grafana", "prometheus", "kibana", "elastic", "k8s", "kubernetes", "docker", "registry", "nexus", "artifactory", "sonar", "sonarqube", "harbor"]
        found = []
        for sub in common:
            try: self.resolver.resolve(f"{sub}.{domain}", "A"); found.append(f"{sub}.{domain}")
            except Exception: pass
        return found
    def _ptr_lookup(self, ip: str) -> str:
        try: return str(self.resolver.resolve_address(ip)[0])
        except Exception: return ""
    def _mx_lookup(self, domain: str) -> list:
        try: return [str(r.exchange) for r in self.resolver.resolve(domain, "MX")]
        except Exception: return []
    def _quick_whois(self, domain: str) -> dict:
        try:
            import whois as whois_mod
            w = whois_mod.whois(domain)
            return {"registrar": w.registrar, "creation_date": str(w.creation_date)[:25] if w.creation_date else "", "expiration_date": str(w.expiration_date)[:25] if w.expiration_date else "", "name_servers": w.name_servers[:5] if w.name_servers else []}
        except ImportError: return {"note": "Install python-whois for WHOIS data"}
        except Exception as e: return {"error": str(e)}
    def _tech_detect(self, domain: str) -> list:
        try:
            import httpx
            r = httpx.get(f"https://{domain}", timeout=10, verify=False)
            return {"server": r.headers.get("Server", ""), "powered_by": r.headers.get("X-Powered-By", ""), "status": r.status_code}
        except Exception:
            try:
                import httpx
                r = httpx.get(f"http://{domain}", timeout=10)
                return {"server": r.headers.get("Server", ""), "status": r.status_code}
            except Exception as e: return {"error": str(e)}
    def _hosting_detect(self, ip: str) -> dict:
        try:
            import httpx
            r = httpx.get(f"https://ipinfo.io/{ip}/json", timeout=10)
            if r.status_code == 200:
                d = r.json()
                return {"org": d.get("org", ""), "asn": d.get("asn", {}).get("asn", "") if isinstance(d.get("asn"), dict) else d.get("asn", ""), "country": d.get("country", ""), "city": d.get("city", "")}
        except Exception: pass
        return {}
    def _email_discover(self, domain: str) -> list:
        patterns = ["admin@{d}", "info@{d}", "contact@{d}", "support@{d}", "sales@{d}", "help@{d}", "noreply@{d}", "webmaster@{d}", "postmaster@{d}", "hostmaster@{d}", "abuse@{d}"]
        return [p.format(d=domain) for p in patterns]


