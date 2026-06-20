import json
import logging
import re
from urllib.parse import urlparse

from tools.registry import registry, tool_error, tool_result

logger = logging.getLogger(__name__)


def _resolve_dns(domain: str) -> dict:
    records = {}
    try:
        import dns.resolver
        resolver = dns.resolver.Resolver()
        resolver.timeout = 5
        resolver.lifetime = 10
        for rtype in ["A", "AAAA", "MX", "NS", "TXT", "SOA", "CNAME"]:
            try:
                answers = resolver.resolve(domain, rtype)
                records[rtype] = [str(r) for r in answers]
            except Exception:
                records[rtype] = []
    except ImportError:
        records = {"note": "Install dnspython for DNS records"}
    except Exception as e:
        records = {"error": str(e)}
    return records


def _subdomain_enum(domain: str) -> list:
    found = []
    try:
        import dns.resolver
        resolver = dns.resolver.Resolver()
        resolver.timeout = 5
        resolver.lifetime = 10
        common = ["www", "mail", "admin", "api", "dev", "test", "stage",
                  "blog", "portal", "vpn", "remote", "webmail", "cpanel",
                  "ns1", "ns2", "smtp", "pop3", "imap", "ftp", "ssh",
                  "jenkins", "gitlab", "jira", "wiki", "docs", "help",
                  "support", "status", "monitor", "grafana", "prometheus",
                  "kibana", "elastic", "k8s", "kubernetes", "docker",
                  "registry", "nexus", "artifactory", "sonar"]
        for sub in common:
            try:
                resolver.resolve(f"{sub}.{domain}", "A")
                found.append(f"{sub}.{domain}")
            except Exception:
                pass
    except ImportError:
        pass
    return found


def _quick_whois(domain: str) -> dict:
    try:
        import whois as whois_mod
        w = whois_mod.whois(domain)
        return {
            "registrar": w.registrar,
            "creation_date": str(w.creation_date)[:25] if w.creation_date else "",
            "expiration_date": str(w.expiration_date)[:25] if w.expiration_date else "",
            "name_servers": w.name_servers[:5] if w.name_servers else [],
        }
    except ImportError:
        return {"note": "Install python-whois for WHOIS data"}
    except Exception as e:
        return {"error": str(e)}


def _tech_detect(domain: str) -> dict:
    try:
        import httpx
        r = httpx.get(f"https://{domain}", timeout=10, verify=False)
        return {
            "server": r.headers.get("Server", ""),
            "powered_by": r.headers.get("X-Powered-By", ""),
            "status": r.status_code,
        }
    except Exception:
        return {}


def _email_discover(domain: str) -> list:
    patterns = [
        f"admin@{domain}", f"info@{domain}", f"support@{domain}",
        f"sales@{domain}", f"contact@{domain}", f"webmaster@{domain}",
        f"postmaster@{domain}", f"hostmaster@{domain}",
    ]
    return patterns


def _ptr_lookup(ip: str) -> str:
    try:
        import dns.resolver
        return str(dns.resolver.resolve_address(ip)[0])
    except Exception:
        return ""


def _hosting_detect(ip: str) -> str:
    try:
        import httpx
        r = httpx.get(f"https://ipapi.co/{ip}/json/", timeout=10)
        if r.status_code == 200:
            data = r.json()
            return data.get("org", "")
    except Exception:
        pass
    return ""


def domain_recon(domain: str) -> dict:
    return {
        "domain": domain,
        "whois": _quick_whois(domain),
        "dns": _resolve_dns(domain),
        "subdomains": _subdomain_enum(domain),
        "tech": _tech_detect(domain),
        "email_patterns": _email_discover(domain),
    }


def ip_recon(ip: str) -> dict:
    return {
        "ip": ip,
        "ptr": _ptr_lookup(ip),
        "hosting": _hosting_detect(ip),
    }


def url_recon(url: str) -> dict:
    parsed = urlparse(url)
    return {
        "url": url,
        "scheme": parsed.scheme,
        "hostname": parsed.hostname,
        "port": parsed.port,
        "path": parsed.path,
        "params": parsed.params,
        "query": parsed.query,
    }


def email_recon(email: str) -> dict:
    domain = email.split("@")[-1] if "@" in email else ""
    mx = []
    if domain:
        try:
            import dns.resolver
            mx = [str(r.exchange) for r in dns.resolver.resolve(domain, "MX")]
        except Exception:
            pass
    return {"email": email, "domain": domain, "mx_records": mx}


AKATSUKI_RECON_SCHEMA = {
    "name": "akatsuki_recon",
    "description": "AKATSUKI OSINT/Reconnaissance — DNS lookups, WHOIS, subdomain enumeration, technology detection, and email discovery for a given target.",
    "parameters": {
        "type": "object",
        "properties": {
            "target": {
                "type": "string",
                "description": "Target: domain (example.com), IP (8.8.8.8), URL (https://example.com/path), or email (user@example.com)",
            },
        },
        "required": ["target"],
    },
}


def akatsuki_recon(target: str) -> str:
    if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', target):
        return tool_result(ip_recon(target))
    if "@" in target:
        return tool_result(email_recon(target))
    if target.startswith("http"):
        return tool_result(url_recon(target))
    return tool_result(domain_recon(target))


def check_akatsuki_requirements() -> bool:
    return True


registry.register(
    name="akatsuki_recon",
    toolset="akatsuki",
    schema=AKATSUKI_RECON_SCHEMA,
    handler=lambda args, **kw: akatsuki_recon(target=args["target"]),
    check_fn=check_akatsuki_requirements,
    emoji="🔍",
)
