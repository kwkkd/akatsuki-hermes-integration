#!/usr/bin/env pwsh
<#
.SYNOPSIS
    AKATSUKI 暁 — Hermes Agent Integration Installer
.DESCRIPTION
    Installs AKATSUKI tools, skills, and patches Hermes Agent configuration.
    Model download is separate (run download_model.py after install).
.USAGE
    .\install.ps1
#>

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$HermesHome = $env:HERMES_HOME
if (-not $HermesHome) {
    $HermesHome = Join-Path $env:LOCALAPPDATA "hermes" "hermes-agent"
}

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  AKATSUKI 暁 — Hermes Agent Installer" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# 0. Install Hermes Agent if missing
if (-not (Test-Path $HermesHome)) {
    Write-Host "[+] Installing Hermes Agent..." -ForegroundColor Yellow
    $parentDir = Split-Path -Parent $HermesHome
    if (-not (Test-Path $parentDir)) { New-Item -ItemType Directory -Path $parentDir -Force | Out-Null }
    & python -m venv "$HermesHome\venv"
    & "$HermesHome\venv\Scripts\python.exe" -m pip install --upgrade pip
    & "$HermesHome\venv\Scripts\python.exe" -m pip install hermes-agent
    Write-Host "[+] Hermes Agent installed." -ForegroundColor Green
} else {
    Write-Host "[.] Hermes Agent found at $HermesHome" -ForegroundColor Cyan
}

$PythonExe = "$HermesHome\venv\Scripts\python.exe"

# 1. Create directories
Write-Host ""
Write-Host "[+] Creating directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path "$HermesHome\tools" -Force | Out-Null
New-Item -ItemType Directory -Path "$HermesHome\skills\security\akatsuki" -Force | Out-Null
New-Item -ItemType Directory -Path "$HermesHome\models" -Force | Out-Null
Write-Host "    Done." -ForegroundColor Green

# 2. Copy tool files
Write-Host ""
Write-Host "[+] Copying AKATSUKI tools..." -ForegroundColor Yellow
$srcTools = Join-Path $ScriptDir "tools"
$dstTools = Join-Path $HermesHome "tools"
Get-ChildItem "$srcTools\akatsuki_*.py" -ErrorAction SilentlyContinue | Copy-Item -Destination $dstTools -Force
Write-Host "    Copied $(@(Get-ChildItem "$srcTools\akatsuki_*.py" -ErrorAction SilentlyContinue).Count) tools." -ForegroundColor Green

# 3. Copy skills
Write-Host ""
Write-Host "[+] Copying AKATSUKI skills..." -ForegroundColor Yellow
$srcSkills = Join-Path $ScriptDir "skills" "security" "akatsuki"
$dstSkills = Join-Path $HermesHome "skills" "security"
Copy-Item -Recurse -Force $srcSkills -Destination $dstSkills
Write-Host "    Done." -ForegroundColor Green

# 4. Patch Hermes files
Write-Host ""
Write-Host "[+] Patching Hermes configuration files..." -ForegroundColor Yellow

$toolsetsPy = Join-Path $HermesHome "toolsets.py"
if ((Test-Path $toolsetsPy) -and -not (Select-String -Path $toolsetsPy -Pattern "akatsuki" -Quiet -ErrorAction SilentlyContinue)) {
    $content = Get-Content $toolsetsPy -Raw
    $insertPoint = $content.LastIndexOf('"computer_use"')
    if ($insertPoint -gt 0) {
        $patch = @"
    "computer_use",
    # AKATSUKI Red Team
    "akatsuki_dept", "akatsuki_recon", "akatsuki_payload",
    "akatsuki_evasion", "akatsuki_c2", "akatsuki_vuln",
    "akatsuki_chain", "akatsuki_report",
"@
        $content = $content.Replace('"computer_use",', $patch)
        Set-Content -Path $toolsetsPy -Value $content -Encoding UTF8
    }
    Write-Host "    toolsets.py patched." -ForegroundColor Green
} else {
    Write-Host "    toolsets.py: already patched or not found." -ForegroundColor Yellow
}

$commandsPy = Join-Path $HermesHome "hermes_cli" "commands.py"
if ((Test-Path $commandsPy) -and -not (Select-String -Path $commandsPy -Pattern "akatsuki" -Quiet -ErrorAction SilentlyContinue)) {
    $content = Get-Content $commandsPy -Raw
    $insertPoint = $content.IndexOf('"bundles"')
    if ($insertPoint -gt 0) {
        $patch = @'
    CommandDef("bundles", "List skill bundles (aliases /<name> for multiple skills)",
               "Tools & Skills"),
    CommandDef("akatsuki", "AKATSUKI Red Team Ops", "Tools & Skills",
               args_hint="<dept|recon|payload|evade|c2|vuln|chain|report|list> [args...]",
               subcommands=("dept", "recon", "payload", "evade", "c2", "vuln", "chain", "report", "list")),
'@
        $content = $content.Replace('"bundles"', $patch)
        Set-Content -Path $commandsPy -Value $content -Encoding UTF8
    }
    Write-Host "    commands.py patched." -ForegroundColor Green
} else {
    Write-Host "    commands.py: already patched or not found." -ForegroundColor Yellow
}

$cliPy = Join-Path $HermesHome "cli.py"
if ((Test-Path $cliPy) -and -not (Select-String -Path $cliPy -Pattern "akatsuki" -Quiet -ErrorAction SilentlyContinue)) {
    $content = Get-Content $cliPy -Raw
    $insertPoint = $content.IndexOf('self._handle_kanban_command(cmd_original)')
    if ($insertPoint -gt 0) {
        $patch = "self._handle_kanban_command(cmd_original)`n        elif canonical == 'akatsuki':`n            self._handle_akatsuki_command(cmd_original)"
        $content = $content.Replace('self._handle_kanban_command(cmd_original)', $patch)
        Set-Content -Path $cliPy -Value $content -Encoding UTF8
    }
    Write-Host "    cli.py patched." -ForegroundColor Green
} else {
    Write-Host "    cli.py: already patched or not found." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host "  Installation complete!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Download the model (optional, ~15GB):"
Write-Host "     $PythonExe $ScriptDir\download_model.py"
Write-Host ""
Write-Host "  2. Run Hermes:"
Write-Host "     hermes"
Write-Host ""
Write-Host "  3. Use AKATSUKI:"
Write-Host "     /akatsuki list"
Write-Host "     /akatsuki recon example.com"
