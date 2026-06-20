#!/usr/bin/env bash
set -euo pipefail

# AKATSUKI 暁 — Full Stack Installer
# Installs: Hermes Agent + DeepSeek-R1-Distill-Qwen-7B + AKATSUKI integration
# Usage: chmod +x install.sh && ./install.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Determine Hermes Agent path
HERMES_HOME="${HERMES_HOME:-"$HOME/.local/share/hermes/hermes-agent"}"

# 0. Install Hermes Agent if missing
if [ ! -d "$HERMES_HOME" ]; then
    echo "[+] Hermes Agent not found. Installing..."
    mkdir -p "$HERMES_HOME"
    python3 -m venv "$HERMES_HOME/venv"
    "$HERMES_HOME/venv/bin/python" -m pip install --upgrade pip -q
    "$HERMES_HOME/venv/bin/python" -m pip install hermes-agent -q
    echo "[+] Hermes Agent installed."
fi

PYTHON_EXE="$HERMES_HOME/venv/bin/python"
TOOL_DIR="$HERMES_HOME/tools"
SKILL_DIR="$HERMES_HOME/skills"
MODEL_DIR="$HERMES_HOME/models/DeepSeek-R1-Distill-Qwen-7B"

echo "[+] Installing AKATSUKI to $HERMES_HOME"

# 0.5. Download DeepSeek-R1-Distill-Qwen-7B model
if [ ! -d "$MODEL_DIR" ] || [ "$(ls -1 "$MODEL_DIR" 2>/dev/null | wc -l)" -lt 5 ]; then
    echo "[+] Downloading DeepSeek-R1-Distill-Qwen-7B (~15GB)..."
    mkdir -p "$MODEL_DIR"
    $PYTHON_EXE -c "
from transformers import AutoTokenizer, AutoModelForCausalLM
import os
model_id = 'deepseek-ai/DeepSeek-R1-Distill-Qwen-7B'
save_dir = '$MODEL_DIR'
os.makedirs(save_dir, exist_ok=True)
print('[1/2] Downloading tokenizer...')
AutoTokenizer.from_pretrained(model_id, trust_remote_code=True).save_pretrained(save_dir)
print('[2/2] Downloading model...')
AutoModelForCausalLM.from_pretrained(model_id, torch_dtype='auto', device_map='auto', trust_remote_code=True).save_pretrained(save_dir, safe_serialization=True)
print(f'Model saved: {save_dir}')
"
    echo "[+] Model downloaded to $MODEL_DIR"
fi

# 1. Copy tool files
mkdir -p "$TOOL_DIR"
mkdir -p "$SKILL_DIR/security/akatsuki"
echo "[*] Copying tools/akatsuki_*.py ..."
cp "$SCRIPT_DIR/tools/akatsuki_"*.py "$TOOL_DIR/"
echo "    -> $(ls -1 "$SCRIPT_DIR/tools/akatsuki_"*.py 2>/dev/null | wc -l) tools copied"

# 2. Copy skills
echo "[*] Copying skills/security/akatsuki/ ..."
mkdir -p "$SKILL_DIR/security"
cp -r "$SCRIPT_DIR/skills/security/akatsuki" "$SKILL_DIR/security/"
echo "    -> skills/security/akatsuki/ installed"

# 3. Patch toolsets.py
TOOLSETS_PY="$HERMES_HOME/toolsets.py"
if ! grep -q "akatsuki" "$TOOLSETS_PY" 2>/dev/null; then
    echo "[*] Patching toolsets.py ..."
    # Add to _HERMES_CORE_TOOLS (before last closing bracket)
    sed -i '/"computer_use",/a\    # AKATSUKI Red Team / Cyber Operations\n    "akatsuki_dept", "akatsuki_recon", "akatsuki_payload",\n    "akatsuki_evasion", "akatsuki_c2", "akatsuki_vuln",\n    "akatsuki_chain", "akatsuki_report",' "$TOOLSETS_PY"
    # Add TOOLSETS entry before last }
    sed -i '$d' "$TOOLSETS_PY"
    cat >> "$TOOLSETS_PY" << 'EOF'

    "akatsuki": {
        "description": "AKATSUKI - Red Team / Cyber Operations framework: 13 specialized departments, OSINT reconnaissance, payload generation, AV/EDR evasion, C2 infrastructure, vulnerability mapping, kill chain execution, and report generation.",
        "tools": [
            "akatsuki_dept", "akatsuki_recon", "akatsuki_payload",
            "akatsuki_evasion", "akatsuki_c2", "akatsuki_vuln",
            "akatsuki_chain", "akatsuki_report",
        ],
        "includes": []
    },
}
EOF
    echo "    -> toolsets.py patched"
else
    echo "[.] toolsets.py already has akatsuki entries, skipping"
fi

# 4. Patch tools_config.py
TOOLS_CFG="$HERMES_HOME/hermes_cli/tools_config.py"
if ! grep -q "akatsuki" "$TOOLS_CFG" 2>/dev/null; then
    echo "[*] Patching hermes_cli/tools_config.py ..."
    sed -i '/"computer_use",/a\    ("akatsuki",         "🌙 AKATSUKI 暁 Cyber Ops",    "13 depts, recon, payload, evasion, C2, vuln mapping, kill chain, reports"),' "$TOOLS_CFG"
    echo "    -> tools_config.py patched"
else
    echo "[.] tools_config.py already has akatsuki entries, skipping"
fi

# 5. Patch commands.py
CMDS_PY="$HERMES_HOME/hermes_cli/commands.py"
if ! grep -q "akatsuki" "$CMDS_PY" 2>/dev/null; then
    echo "[*] Patching hermes_cli/commands.py ..."
    sed -i '/"bundles",/i\    CommandDef("akatsuki", "AKATSUKI 暁 - Red Team / Cyber Operations: consult departments, recon, payloads, evasion, C2, vuln mapping, kill chains, and reports", "Tools & Skills", args_hint="<dept|recon|payload|evade|c2|vuln|chain|report|list> [args...]", subcommands=("dept", "recon", "payload", "evade", "c2", "vuln", "chain", "report", "list", "scan", "op")),' "$CMDS_PY"
    echo "    -> commands.py patched"
else
    echo "[.] commands.py already has akatsuki entries, skipping"
fi

# 6. Patch cli_commands_mixin.py
MIXIN_PY="$HERMES_HOME/hermes_cli/cli_commands_mixin.py"
if ! grep -q "_handle_akatsuki_command" "$MIXIN_PY" 2>/dev/null; then
    echo "[*] Patching hermes_cli/cli_commands_mixin.py ..."
    cat >> "$MIXIN_PY" << 'PYEOF'

    def _handle_akatsuki_command(self, command):
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
PYEOF
    echo "    -> cli_commands_mixin.py patched"
else
    echo "[.] cli_commands_mixin.py already has akatsuki handler, skipping"
fi

# 7. Patch cli.py
CLI_PY="$HERMES_HOME/cli.py"
if ! grep -q "akatsuki" "$CLI_PY" 2>/dev/null; then
    echo "[*] Patching cli.py ..."
    sed -i '/self._handle_kanban_command/a\        elif canonical == "akatsuki":\n            self._handle_akatsuki_command(cmd_original)' "$CLI_PY"
    echo "    -> cli.py patched"
else
    echo "[.] cli.py already has akatsuki dispatch, skipping"
fi

echo "[+] AKATSUKI integration installed successfully!"
echo "[i] Run 'hermes' to start the CLI, then use /akatsuki commands."
