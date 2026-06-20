#!/usr/bin/env pwsh
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$HermesHome = $env:HERMES_HOME
if (-not $HermesHome) { $HermesHome = Join-Path $env:LOCALAPPDATA "hermes" "hermes-agent" }
$PythonExe = "$HermesHome\venv\Scripts\python.exe"

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  AKATSUKI — Full Installer" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# 1. Hermes Agent
if (-not (Test-Path $HermesHome)) {
    Write-Host "[1/5] Installing Hermes Agent..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path (Split-Path -Parent $HermesHome) -Force | Out-Null
    & python -m venv "$HermesHome\venv"
    & $PythonExe -m pip install --upgrade pip
    & $PythonExe -m pip install hermes-agent
} else {
    Write-Host "[1/5] Hermes Agent found." -ForegroundColor Cyan
}

# 2. transformers + torch
Write-Host "[2/5] Installing transformers and torch..." -ForegroundColor Yellow
& $PythonExe -m pip install transformers torch --quiet

# 3. Model download
$ModelDir = Join-Path $HermesHome "models" "DeepSeek-R1-Distill-Qwen-7B"
if (-not (Test-Path $ModelDir) -or (Get-ChildItem $ModelDir -File -ErrorAction SilentlyContinue).Count -lt 5) {
    Write-Host "[3/5] Downloading DeepSeek-R1-Distill-Qwen-7B (~15GB)..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $ModelDir -Force | Out-Null
    $env:MODEL_DIR = $ModelDir
    & $PythonExe -c @"
from transformers import AutoTokenizer, AutoModelForCausalLM
import os
model_id = 'deepseek-ai/DeepSeek-R1-Distill-Qwen-7B'
save_dir = os.environ.get('MODEL_DIR', '$ModelDir')
print('  [1/2] Downloading tokenizer...')
AutoTokenizer.from_pretrained(model_id, trust_remote_code=True).save_pretrained(save_dir)
print('  [2/2] Downloading model weights...')
AutoModelForCausalLM.from_pretrained(model_id, torch_dtype='auto', device_map='auto', trust_remote_code=True).save_pretrained(save_dir, safe_serialization=True)
print(f'  Model saved: {save_dir}')
"@
} else {
    Write-Host "[3/5] Model already exists." -ForegroundColor Cyan
}

# 4. Copy tools + skills
Write-Host "[4/5] Copying AKATSUKI tools and skills..." -ForegroundColor Yellow
New-Item -ItemType Directory -Path "$HermesHome\tools" -Force | Out-Null
New-Item -ItemType Directory -Path "$HermesHome\skills\security\akatsuki" -Force | Out-Null
Get-ChildItem "$ScriptDir\tools\akatsuki_*.py" -ErrorAction SilentlyContinue | Copy-Item -Destination "$HermesHome\tools\" -Force
Copy-Item -Recurse -Force "$ScriptDir\skills\security\akatsuki" -Destination "$HermesHome\skills\security\"

# 5. Patch Hermes
Write-Host "[5/5] Patching Hermes configuration..." -ForegroundColor Yellow

$toolsetsPy = Join-Path $HermesHome "toolsets.py"
if ((Test-Path $toolsetsPy) -and -not (Select-String -Path $toolsetsPy -Pattern "akatsuki" -Quiet -ErrorAction SilentlyContinue)) {
    $c = Get-Content $toolsetsPy -Raw
    $c = $c.Replace('"computer_use",', '"computer_use",`n    "akatsuki_dept", "akatsuki_recon", "akatsuki_payload",`n    "akatsuki_evasion", "akatsuki_c2", "akatsuki_vuln",`n    "akatsuki_chain", "akatsuki_report",')
    Set-Content -Path $toolsetsPy -Value $c -Encoding UTF8
}

$commandsPy = Join-Path $HermesHome "hermes_cli" "commands.py"
if ((Test-Path $commandsPy) -and -not (Select-String -Path $commandsPy -Pattern "akatsuki" -Quiet -ErrorAction SilentlyContinue)) {
    $c = Get-Content $commandsPy -Raw
    $c = $c.Replace('"bundles"', '"bundles",`n    CommandDef("akatsuki", "AKATSUKI Red Team Ops", "Tools & Skills", args_hint="<dept|recon|payload|evade|c2|vuln|chain|report|list> [args...]", subcommands=("dept", "recon", "payload", "evade", "c2", "vuln", "chain", "report", "list")),')
    Set-Content -Path $commandsPy -Value $c -Encoding UTF8
}

$cliPy = Join-Path $HermesHome "cli.py"
if ((Test-Path $cliPy) -and -not (Select-String -Path $cliPy -Pattern "akatsuki" -Quiet -ErrorAction SilentlyContinue)) {
    $c = Get-Content $cliPy -Raw
    $c = $c.Replace('self._handle_kanban_command(cmd_original)', 'self._handle_kanban_command(cmd_original)`n        elif canonical == "akatsuki":`n            self._handle_akatsuki_command(cmd_original)')
    Set-Content -Path $cliPy -Value $c -Encoding UTF8
}

Write-Host "      Done." -ForegroundColor Green
Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host "  Complete!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host "  hermes" -ForegroundColor Cyan
Write-Host "  /akatsuki list" -ForegroundColor Cyan
