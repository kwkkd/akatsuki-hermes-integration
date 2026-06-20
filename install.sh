#!/usr/bin/env bash
set -euo pipefail

# AKATSUKI 暁 — Hermes Agent Integration
# Usage: chmod +x install.sh && ./install.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HERMES_HOME="${HERMES_HOME:-"$HOME/.local/share/hermes/hermes-agent"}"

echo "========================================="
echo "  AKATSUKI 暁 — Hermes Agent Installer"
echo "========================================="
echo ""

# 0. Install Hermes Agent if missing
if [ ! -d "$HERMES_HOME" ]; then
    echo "[+] Installing Hermes Agent..."
    mkdir -p "$HERMES_HOME"
    python3 -m venv "$HERMES_HOME/venv"
    "$HERMES_HOME/venv/bin/python" -m pip install --upgrade pip
    "$HERMES_HOME/venv/bin/python" -m pip install hermes-agent
    echo "[+] Hermes Agent installed."
else
    echo "[.] Hermes Agent found at $HERMES_HOME"
fi

PYTHON_EXE="$HERMES_HOME/venv/bin/python"

# 1. Create directories
echo ""
echo "[+] Creating directories..."
mkdir -p "$HERMES_HOME/tools"
mkdir -p "$HERMES_HOME/skills/security/akatsuki"
mkdir -p "$HERMES_HOME/models"
echo "    Done."

# 2. Copy tool files
echo ""
echo "[+] Copying AKATSUKI tools..."
cp "$SCRIPT_DIR/tools/akatsuki_"*.py "$HERMES_HOME/tools/" 2>/dev/null || true
TOOL_COUNT=$(ls -1 "$SCRIPT_DIR/tools/akatsuki_"*.py 2>/dev/null | wc -l)
echo "    Copied $TOOL_COUNT tools."

# 3. Copy skills
echo ""
echo "[+] Copying AKATSUKI skills..."
cp -r "$SCRIPT_DIR/skills/security/akatsuki" "$HERMES_HOME/skills/security/" 2>/dev/null || true
echo "    Done."

# 4. Patch Hermes files
echo ""
echo "[+] Patching Hermes configuration files..."

# toolsets.py
if [ -f "$HERMES_HOME/toolsets.py" ] && ! grep -q "akatsuki" "$HERMES_HOME/toolsets.py" 2>/dev/null; then
    sed -i '/"computer_use",/a\    # AKATSUKI Red Team\n    "akatsuki_dept", "akatsuki_recon", "akatsuki_payload",\n    "akatsuki_evasion", "akatsuki_c2", "akatsuki_vuln",\n    "akatsuki_chain", "akatsuki_report",' "$HERMES_HOME/toolsets.py"
    echo "    toolsets.py patched."
else
    echo "    toolsets.py: already patched or not found."
fi

# commands.py
if [ -f "$HERMES_HOME/hermes_cli/commands.py" ] && ! grep -q "akatsuki" "$HERMES_HOME/hermes_cli/commands.py" 2>/dev/null; then
    sed -i '/"bundles",/i\    CommandDef("akatsuki", "AKATSUKI Red Team Ops", "Tools & Skills", args_hint="<dept|recon|payload|evade|c2|vuln|chain|report|list> [args...]", subcommands=("dept", "recon", "payload", "evade", "c2", "vuln", "chain", "report", "list")),' "$HERMES_HOME/hermes_cli/commands.py"
    echo "    commands.py patched."
else
    echo "    commands.py: already patched or not found."
fi

# cli.py
if [ -f "$HERMES_HOME/cli.py" ] && ! grep -q "akatsuki" "$HERMES_HOME/cli.py" 2>/dev/null; then
    sed -i '/self._handle_kanban_command/a\        elif canonical == "akatsuki":\n            self._handle_akatsuki_command(cmd_original)' "$HERMES_HOME/cli.py"
    echo "    cli.py patched."
else
    echo "    cli.py: already patched or not found."
fi

echo ""
echo "========================================="
echo "  Installation complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "  1. Download the model (optional, ~15GB):"
echo "     $PYTHON_EXE $SCRIPT_DIR/download_model.py"
echo ""
echo "  2. Run Hermes:"
echo "     hermes"
echo ""
echo "  3. Use AKATSUKI:"
echo "     /akatsuki list"
echo "     /akatsuki recon example.com"
echo "     /akatsuki chain execute target"
