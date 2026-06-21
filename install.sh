#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HERMES_HOME="${HERMES_HOME:-"$HOME/.local/share/hermes/hermes-agent"}"
PYTHON_EXE="$HERMES_HOME/venv/bin/python"

echo "========================================="
echo "  AKATSUKI — Full Installer"
echo "========================================="
echo ""

# 1. Hermes Agent 설치
if [ ! -d "$HERMES_HOME" ]; then
    echo "[1/3] Installing Hermes Agent..."
    mkdir -p "$HERMES_HOME"
    python3 -m venv "$HERMES_HOME/venv"
    "$HERMES_HOME/venv/bin/python" -m ensurepip --upgrade
    "$HERMES_HOME/venv/bin/python" -m pip install --upgrade pip
    "$HERMES_HOME/venv/bin/python" -m pip install hermes-agent
    echo "      Done."
else
    echo "[1/3] Hermes Agent found."
fi

# 2. 도구 + 스킬 복사
echo "[2/3] Copying AKATSUKI tools and skills..."
mkdir -p "$HERMES_HOME/tools"
mkdir -p "$HERMES_HOME/skills/security/akatsuki"
cp "$SCRIPT_DIR/tools/akatsuki_"*.py "$HERMES_HOME/tools/" 2>/dev/null || true
cp -r "$SCRIPT_DIR/skills/security/akatsuki" "$HERMES_HOME/skills/security/"
echo "      Done."

# 3. Hermes 설정 패치
echo "[3/3] Patching Hermes configuration..."

if [ -f "$HERMES_HOME/toolsets.py" ] && ! grep -q "akatsuki" "$HERMES_HOME/toolsets.py" 2>/dev/null; then
    sed -i '/"computer_use",/a\    "akatsuki_dept", "akatsuki_recon", "akatsuki_payload",\n    "akatsuki_evasion", "akatsuki_c2", "akatsuki_vuln",\n    "akatsuki_chain", "akatsuki_report",' "$HERMES_HOME/toolsets.py"
fi

if [ -f "$HERMES_HOME/hermes_cli/commands.py" ] && ! grep -q "akatsuki" "$HERMES_HOME/hermes_cli/commands.py" 2>/dev/null; then
    sed -i '/"bundles",/i\    CommandDef("akatsuki", "AKATSUKI Red Team Ops", "Tools & Skills", args_hint="<dept|recon|payload|evade|c2|vuln|chain|report|list> [args...]", subcommands=("dept", "recon", "payload", "evade", "c2", "vuln", "chain", "report", "list")),' "$HERMES_HOME/hermes_cli/commands.py"
fi

if [ -f "$HERMES_HOME/cli.py" ] && ! grep -q "akatsuki" "$HERMES_HOME/cli.py" 2>/dev/null; then
    sed -i '/self._handle_kanban_command/a\        elif canonical == "akatsuki":\n            self._handle_akatsuki_command(cmd_original)' "$HERMES_HOME/cli.py"
fi

echo "      Done."

echo ""
echo "========================================="
echo "  Complete!"
echo "========================================="
echo ""
echo "  hermes"
echo "  /akatsuki list"
