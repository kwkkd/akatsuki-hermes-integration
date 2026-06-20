#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Install AKATSUKI 暁 — Hermes Agent Native Integration
.DESCRIPTION
    Copies AKATSUKI tool files and skills into the Hermes Agent installation
    and patches the required Hermes configuration files.
#>

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# --- Determine Hermes Agent path ---
$HermesHome = $env:HERMES_HOME
if (-not $HermesHome) {
    $HermesHome = Join-Path $env:LOCALAPPDATA "hermes" "hermes-agent"
}
if (-not (Test-Path $HermesHome)) {
    Write-Error "Hermes Agent not found at $HermesHome. Set HERMES_HOME or install Hermes first."
    exit 1
}

$ToolDir = Join-Path $HermesHome "tools"
$SkillDir = Join-Path $HermesHome "skills"

Write-Host "[+] Installing AKATSUKI to $HermesHome" -ForegroundColor Green

# --- 1. Copy tool files ---
Write-Host "[*] Copying tools/akatsuki_*.py ..." -ForegroundColor Cyan
$srcTools = Join-Path $ScriptDir "tools"
Get-ChildItem "$srcTools\akatsuki_*.py" | Copy-Item -Destination $ToolDir -Force
Write-Host "    -> $(@(Get-ChildItem "$srcTools\akatsuki_*.py").Length) tools copied" -ForegroundColor Green

# --- 2. Copy skills ---
Write-Host "[*] Copying skills/security/akatsuki/ ..." -ForegroundColor Cyan
$srcSkills = Join-Path $ScriptDir "skills" "security" "akatsuki"
$dstSkills = Join-Path $SkillDir "security" "akatsuki"
if (Test-Path $dstSkills) {
    Remove-Item -Recurse -Force $dstSkills
}
Copy-Item -Recurse $srcSkills -Destination (Join-Path $SkillDir "security") -Force
Write-Host "    -> skills/security/akatsuki/ installed" -ForegroundColor Green

# --- 3. Patch toolsets.py ---
$toolsetsPy = Join-Path $HermesHome "toolsets.py"
if (-not (Select-String -Path $toolsetsPy -Pattern "akatsuki" -Quiet)) {
    Write-Host "[*] Patching toolsets.py ..." -ForegroundColor Cyan
    $content = Get-Content $toolsetsPy -Raw
    # Add to _HERMES_CORE_TOOLS
    $insertPoint = $content.LastIndexOf('"computer_use"')
    if ($insertPoint -gt 0) {
        $patch = @"
    "computer_use",
    # AKATSUKI Red Team / Cyber Operations
    "akatsuki_dept", "akatsuki_recon", "akatsuki_payload",
    "akatsuki_evasion", "akatsuki_c2", "akatsuki_vuln",
    "akatsuki_chain", "akatsuki_report",
"@
        $content = $content.Replace('"computer_use",', $patch)
    }
    # Add TOOLSETS entry (before the last closing brace of TOOLSETS)
    $tsInsert = $content.LastIndexOf("`n}")
    $tsPatch = @"

    "akatsuki": {
        "description": "AKATSUKI - Red Team / Cyber Operations framework: 13 specialized departments, OSINT reconnaissance, payload generation, AV/EDR evasion, C2 infrastructure, vulnerability mapping, kill chain execution, and report generation.",
        "tools": [
            "akatsuki_dept", "akatsuki_recon", "akatsuki_payload",
            "akatsuki_evasion", "akatsuki_c2", "akatsuki_vuln",
            "akatsuki_chain", "akatsuki_report",
        ],
        "includes": []
    },
"@
        $content = $content.Substring(0, $tsInsert) + $tsPatch + $content.Substring($tsInsert)
        Set-Content -Path $toolsetsPy -Value $content -Encoding UTF8
    }
    Write-Host "    -> toolsets.py patched" -ForegroundColor Green
} else {
    Write-Host "[.] toolsets.py already has akatsuki entries, skipping" -ForegroundColor Yellow
}

# --- 4. Patch tools_config.py ---
$toolsConfigPy = Join-Path $HermesHome "hermes_cli" "tools_config.py"
if (-not (Select-String -Path $toolsConfigPy -Pattern "akatsuki" -Quiet)) {
    Write-Host "[*] Patching hermes_cli/tools_config.py ..." -ForegroundColor Cyan
    $content = Get-Content $toolsConfigPy -Raw
    # Add CONFIGURABLE_TOOLSETS entry
    $insertPoint = $content.LastIndexOf('"computer_use",')
    if ($insertPoint -gt 0) {
        $patch = @'
    ("computer_use",     "🖱️  Computer Use (macOS)",     "background desktop control via cua-driver"),
    ("akatsuki",         "🌙 AKATSUKI 暁 Cyber Ops",    "13 depts, recon, payload, evasion, C2, vuln mapping, kill chain, reports"),
'@
        $content = $content.Replace('"computer_use",', $patch)
        Set-Content -Path $toolsConfigPy -Value $content -Encoding UTF8
    }
    Write-Host "    -> tools_config.py patched" -ForegroundColor Green
} else {
    Write-Host "[.] tools_config.py already has akatsuki entries, skipping" -ForegroundColor Yellow
}

# --- 5. Patch commands.py ---
$commandsPy = Join-Path $HermesHome "hermes_cli" "commands.py"
if (-not (Select-String -Path $commandsPy -Pattern "akatsuki" -Quiet)) {
    Write-Host "[*] Patching hermes_cli/commands.py ..." -ForegroundColor Cyan
    $content = Get-Content $commandsPy -Raw
    $insertPoint = $content.IndexOf('"bundles"')
    if ($insertPoint -gt 0) {
        $patch = @'
    CommandDef("bundles", "List skill bundles (aliases /<name> for multiple skills)",
               "Tools & Skills"),
    CommandDef("akatsuki", "AKATSUKI 暁 - Red Team / Cyber Operations: consult departments, recon, payloads, evasion, C2, vuln mapping, kill chains, and reports",
               "Tools & Skills",
               args_hint="<dept|recon|payload|evade|c2|vuln|chain|report|list> [args...]",
               subcommands=("dept", "recon", "payload", "evade", "c2", "vuln", "chain", "report", "list", "scan", "op")),
'@
        $content = $content.Replace('"bundles"', $patch)
        Set-Content -Path $commandsPy -Value $content -Encoding UTF8
    }
    Write-Host "    -> commands.py patched" -ForegroundColor Green
} else {
    Write-Host "[.] commands.py already has akatsuki entries, skipping" -ForegroundColor Yellow
}

# --- 6. Patch cli_commands_mixin.py ---
$mixinPy = Join-Path $HermesHome "hermes_cli" "cli_commands_mixin.py"
if (-not (Select-String -Path $mixinPy -Pattern "_handle_akatsuki_command" -Quiet)) {
    Write-Host "[*] Patching hermes_cli/cli_commands_mixin.py ..." -ForegroundColor Cyan
    $content = Get-Content $mixinPy -Raw
    # Append handler before last line
    $handlerCode = @'

    def _handle_akatsuki_command(self, command):
        """Handle /akatsuki subcommands."""
        from cli import _cprint
        parts = command.strip().split(maxsplit=2)
        if len(parts) < 2:
            _cprint("Usage: /akatsuki <dept|recon|payload|evade|c2|vuln|chain|report|list> [args...]")
            return
        sub = parts[1].lower().strip()
        args = parts[2] if len(parts) > 2 else ""
        if sub == "list":
            from tools.registry import registry
            tools = registry.get_tool_names_for_toolset("akatsuki")
            _cprint(f"Akatsuki tools available ({len(tools)}):")
            for t in tools:
                entry = registry.get_entry(t)
                if entry:
                    _cprint(f"  /akatsuki {t.replace('akatsuki_', '')} - {entry.description[:80]}")
        elif sub == "dept":
            dp = args.split(maxsplit=1)
            if len(dp) < 1: _cprint("Usage: /akatsuki dept <name> <objective>"); return
            from tools.akatsuki_dept import akatsuki_dept
            _cprint(akatsuki_dept(action="consult", department=dp[0], objective=dp[1] if len(dp) > 1 else ""))
        elif sub == "recon":
            if not args: _cprint("Usage: /akatsuki recon <target>"); return
            from tools.akatsuki_recon import akatsuki_recon
            _cprint(akatsuki_recon(target=args))
        elif sub == "payload":
            pp = args.split()
            if len(pp) < 3: _cprint("Usage: /akatsuki payload <type> <lhost> <lport>"); return
            from tools.akatsuki_payload import akatsuki_payload
            _cprint(akatsuki_payload(payload_type=pp[0], lhost=pp[1], lport=int(pp[2])))
        elif sub == "evade":
            ep = args.split(maxsplit=1)
            if not ep: _cprint("Usage: /akatsuki evade <action> [args...]"); return
            from tools.akatsuki_evasion import akatsuki_evasion
            _cprint(akatsuki_evasion(action=ep[0], payload=ep[1] if len(ep) > 1 else None))
        elif sub == "c2":
            cp = args.split()
            if len(cp) < 2: _cprint("Usage: /akatsuki c2 <action> <lhost> [lport]"); return
            from tools.akatsuki_c2 import akatsuki_c2
            _cprint(akatsuki_c2(action=cp[0], lhost=cp[1], lport=int(cp[2]) if len(cp) > 2 else 443))
        elif sub == "vuln":
            vp = args.split(maxsplit=1)
            if not vp: _cprint("Usage: /akatsuki vuln <service> [version]"); return
            from tools.akatsuki_vuln import akatsuki_vuln
            _cprint(akatsuki_vuln(service=vp[0], version=vp[1] if len(vp) > 1 else ""))
        elif sub == "chain":
            chp = args.split(maxsplit=2)
            if not chp: _cprint("Usage: /akatsuki chain <action> [target] [objective]"); return
            from tools.akatsuki_chain import akatsuki_chain
            _cprint(akatsuki_chain(action=chp[0], target=chp[1] if len(chp) > 1 else "", objective=chp[2] if len(chp) > 2 else ""))
        elif sub == "report":
            if not args: _cprint("Usage: /akatsuki report <target> [format]"); return
            rp = args.split(maxsplit=1)
            from tools.akatsuki_report import akatsuki_report
            _cprint(akatsuki_report(target=rp[0], format=rp[1] if len(rp) > 1 else "markdown"))
        else:
            _cprint("Unknown subcommand. Available: dept, recon, payload, evade, c2, vuln, chain, report, list")

'@
        $content = $content.TrimEnd() + "`n" + $handlerCode
        Set-Content -Path $mixinPy -Value $content -Encoding UTF8
    }
    Write-Host "    -> cli_commands_mixin.py patched" -ForegroundColor Green
} else {
    Write-Host "[.] cli_commands_mixin.py already has akatsuki handler, skipping" -ForegroundColor Yellow
}

# --- 7. Patch cli.py ---
$cliPy = Join-Path $HermesHome "cli.py"
if (-not (Select-String -Path $cliPy -Pattern "akatsuki" -Quiet)) {
    Write-Host "[*] Patching cli.py ..." -ForegroundColor Cyan
    $content = Get-Content $cliPy -Raw
    # Add dispatch after kanban
    $insertPoint = $content.IndexOf('self._handle_kanban_command(cmd_original)')
    if ($insertPoint -gt 0) {
        $patch = "self._handle_kanban_command(cmd_original)`n        elif canonical == 'akatsuki':`n            self._handle_akatsuki_command(cmd_original)"
        $content = $content.Replace('self._handle_kanban_command(cmd_original)', $patch)
        Set-Content -Path $cliPy -Value $content -Encoding UTF8
    }
    Write-Host "    -> cli.py patched" -ForegroundColor Green
} else {
    Write-Host "[.] cli.py already has akatsuki dispatch, skipping" -ForegroundColor Yellow
}

Write-Host "[+] AKATSUKI integration installed successfully!" -ForegroundColor Green
Write-Host "[i] Run 'hermes' to start the CLI, then use /akatsuki commands." -ForegroundColor Cyan
