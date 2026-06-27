"""External security tool runner wrapping nmap, sqlmap, nuclei, hydra, msfconsole."""

import asyncio
import json
import os
import shutil
import tempfile
from dataclasses import dataclass, field
from typing import Optional

from .logger import logger


@dataclass
class ToolResult:
    tool: str
    command: str
    stdout: str = ""
    stderr: str = ""
    return_code: int = -1
    timed_out: bool = False
    parsed_output: Optional[dict] = None
    error: Optional[str] = None


class ToolRunner:
    """Wraps external security tools (nmap, sqlmap, nuclei, hydra, msfconsole)."""

    def __init__(self, timeout: int = 300):
        self.timeout = timeout
        self._env = os.environ.copy()
        self._tools_cache = {}

    def _check_tool(self, tool_name: str) -> bool:
        if tool_name not in self._tools_cache:
            self._tools_cache[tool_name] = shutil.which(tool_name) is not None
        return self._tools_cache[tool_name]

    async def _run_command(self, cmd: list[str], tool: str) -> ToolResult:
        result = ToolResult(tool=tool, command=" ".join(cmd))
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self._env,
            )
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=self.timeout
                )
                result.stdout = stdout.decode("utf-8", errors="replace")
                result.stderr = stderr.decode("utf-8", errors="replace")
                result.return_code = proc.returncode or 0
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                result.timed_out = True
                result.error = f"Command timed out after {self.timeout}s"
        except FileNotFoundError:
            result.error = f"Tool '{tool}' not found on system"
        except Exception as e:
            result.error = str(e)
            logger.error(f"Tool execution failed: {e}")
        return result

    async def run_nmap(
        self, target: str, ports: str = "1-1000", flags: str = "-sV -sC"
    ) -> ToolResult:
        if not self._check_tool("nmap"):
            return ToolResult(tool="nmap", command="", error="nmap not found")
        cmd = ["nmap", flags, "-p", ports, target]
        return await self._run_command(cmd, "nmap")

    async def run_sqlmap(
        self, url: str, flags: str = "--batch --level=1 --risk=1"
    ) -> ToolResult:
        if not self._check_tool("sqlmap"):
            return ToolResult(tool="sqlmap", command="", error="sqlmap not found")
        cmd = ["sqlmap", "-u", url, *flags.split()]
        return await self._run_command(cmd, "sqlmap")

    async def run_nuclei(
        self, target: str, templates: str = "cves", severity: str = "critical,high"
    ) -> ToolResult:
        if not self._check_tool("nuclei"):
            return ToolResult(tool="nuclei", command="", error="nuclei not found")
        cmd = [
            "nuclei",
            "-u", target,
            "-t", templates,
            "-severity", severity,
            "-json",
        ]
        return await self._run_command(cmd, "nuclei")

    async def run_hydra(
        self, target: str, service: str, userlist: str, passlist: str, flags: str = "-t 4"
    ) -> ToolResult:
        if not self._check_tool("hydra"):
            return ToolResult(tool="hydra", command="", error="hydra not found")
        cmd = [
            "hydra", flags,
            "-L", userlist,
            "-P", passlist,
            f"{service}://{target}",
        ]
        return await self._run_command(cmd, "hydra")

    async def run_msfconsole(self, resource_script: str) -> ToolResult:
        if not self._check_tool("msfconsole"):
            return ToolResult(tool="msfconsole", command="", error="msfconsole not found")
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".rc", delete=False, encoding="utf-8")
        tmp.write(resource_script)
        tmp.close()
        try:
            cmd = ["msfconsole", "-q", "-r", tmp.name]
            result = await self._run_command(cmd, "msfconsole")
            return result
        finally:
            try:
                os.unlink(tmp.name)
            except OSError:
                pass

    async def run_custom(self, command: list[str], tool_name: str = "custom") -> ToolResult:
        return await self._run_command(command, tool_name)
