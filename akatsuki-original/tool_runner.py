import subprocess
import json
import os
import sys
import tempfile
import time
sys.path.insert(0, os.path.dirname(__file__))
from results_parser import ResultsParser

class ToolRunner:
    def __init__(self, sandbox: bool = False):
        self.sandbox = sandbox; self.parser = ResultsParser(); self.timeout = 300; self.tools = self._check_tools()
    def _check_tools(self) -> dict:
        tool_names = ["nmap", "sqlmap", "nuclei", "hydra", "msfconsole", "crackmapexec", "whatweb", "nikto"]
        available = {}
        for tool in tool_names:
            try:
                subprocess.run([tool, "--version"], capture_output=True, timeout=10); available[tool] = True
            except (FileNotFoundError, subprocess.TimeoutExpired):
                try:
                    subprocess.run([tool, "-h"], capture_output=True, timeout=10); available[tool] = True
                except (FileNotFoundError, subprocess.TimeoutExpired): available[tool] = False
        return available
    def run(self, tool: str, args: list, timeout: int = None) -> dict:
        if not self.tools.get(tool): return {"error": f"Tool not available: {tool}", "installed_tools": {k for k,v in self.tools.items() if v}}
        try:
            result = subprocess.run([tool] + args, capture_output=True, text=True, timeout=timeout or self.timeout)
            return {"tool": tool, "args": args, "returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr, "success": result.returncode == 0}
        except subprocess.TimeoutExpired: return {"tool": tool, "error": "Timeout", "success": False}
        except Exception as e: return {"tool": tool, "error": str(e), "success": False}
    def run_nmap(self, target: str, flags: str = "-sV -sC -p-") -> dict:
        raw = self.run("nmap", flags.split() + [target], timeout=600)
        if raw.get("success"): raw["parsed"] = self.parser.parse_nmap(raw["stdout"])
        return raw
    def run_sqlmap(self, url: str, data: str = None, level: int = 3) -> dict:
        args = ["-u", url, "--batch", "--level", str(level), "--risk", "2"]
        if data: args += ["--data", data]
        args += ["--output-dir", tempfile.mkdtemp()]
        raw = self.run("sqlmap", args, timeout=900)
        if raw.get("success"): raw["parsed"] = self.parser.parse_sqlmap(raw["stdout"])
        return raw
    def run_nuclei(self, target: str, templates: str = "cves") -> dict:
        raw = self.run("nuclei", ["-u", target, "-t", templates, "-json", "-silent"], timeout=600)
        if raw.get("success"): raw["parsed"] = self.parser.parse_nuclei(raw["stdout"])
        return raw
    def run_hydra(self, target: str, service: str, userlist: str, passlist: str) -> dict:
        raw = self.run("hydra", ["-L", userlist, "-P", passlist, target, service], timeout=600)
        if raw.get("success"): raw["parsed"] = self.parser.parse_hydra(raw["stdout"])
        return raw
    def run_metasploit(self, module: str, payload: str, options: dict) -> dict:
        rc = tempfile.mktemp(suffix=".rc")
        with open(rc, "w") as f:
            f.write(f"use {module}\n")
            for k, v in options.items(): f.write(f"set {k} {v}\n")
            f.write(f"set PAYLOAD {payload}\n"); f.write("run -j\n"); f.write("sleep 5\n"); f.write("sessions -l\n")
        raw = self.run("msfconsole", ["-q", "-r", rc], timeout=300)
        os.unlink(rc)
        if raw.get("success"): raw["parsed"] = self.parser.parse_msf(raw["stdout"])
        return raw
    def run_scan(self, target: str) -> dict:
        result = {"target": target, "timestamp": time.time(), "findings": []}
        nmap_result = self.run_nmap(target, "-sV -sC -p-")
        result["nmap"] = nmap_result.get("parsed", nmap_result)
        if self.tools.get("nuclei"): result["nuclei"] = self.run_nuclei(target).get("parsed", {})
        if self.tools.get("whatweb"): result["whatweb"] = self.run("whatweb", [target, "--aggression", "3", "--log-json", tempfile.mktemp()])
        return result


