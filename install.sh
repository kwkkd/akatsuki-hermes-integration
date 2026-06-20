#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HERMES_HOME="${HERMES_HOME:-"$HOME/.local/share/hermes/hermes-agent"}"
PYTHON_EXE="$HERMES_HOME/venv/bin/python"

echo "========================================="
echo "  AKATSUKI 暁 — Full Installer"
echo "========================================="
echo ""

# 1. Hermes Agent 설치
if [ ! -d "$HERMES_HOME" ]; then
    echo "[1/5] Installing Hermes Agent..."
    mkdir -p "$HERMES_HOME"
    python3 -m venv "$HERMES_HOME/venv"
    "$HERMES_HOME/venv/bin/python" -m ensurepip --upgrade
    "$HERMES_HOME/venv/bin/python" -m pip install --upgrade pip
    "$HERMES_HOME/venv/bin/python" -m pip install hermes-agent
    echo "      Done."
else
    echo "[1/5] Hermes Agent found."
fi

# 2. pip 설치 확인 + transformers
echo "[2/5] Installing transformers and torch..."
if ! "$HERMES_HOME/venv/bin/python" -m pip --version >/dev/null 2>&1; then
    echo "      pip not found, installing..."
    curl -sS https://bootstrap.pypa.io/get-pip.py | "$HERMES_HOME/venv/bin/python"
fi
"$HERMES_HOME/venv/bin/python" -m pip install transformers torch --quiet
echo "      Done."

# 3. 모델 다운로드
MODEL_DIR="$HERMES_HOME/models/DeepSeek-R1-Distill-Qwen-7B"
if [ ! -d "$MODEL_DIR" ] || [ "$(ls -1 "$MODEL_DIR" 2>/dev/null | wc -l)" -lt 5 ]; then
    echo "[3/5] Downloading DeepSeek-R1-Distill-Qwen-7B (~15GB)..."
    mkdir -p "$MODEL_DIR"
    $PYTHON_EXE << 'PYEOF'
from transformers import AutoTokenizer, AutoModelForCausalLM
import os

model_id = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
save_dir = os.environ.get("MODEL_DIR", "downloaded_model")

print("  [1/2] Downloading tokenizer...")
AutoTokenizer.from_pretrained(model_id, trust_remote_code=True).save_pretrained(save_dir)

print("  [2/2] Downloading model weights...")
AutoModelForCausalLM.from_pretrained(
    model_id, torch_dtype="auto", device_map="auto", trust_remote_code=True
).save_pretrained(save_dir, safe_serialization=True)

print(f"  Model saved: {save_dir}")
PYEOF
    echo "      Done."
else
    echo "[3/5] Model already exists."
fi

# 4. 도구 + 스킬 복사
echo "[4/5] Copying AKATSUKI tools and skills..."
mkdir -p "$HERMES_HOME/tools"
mkdir -p "$HERMES_HOME/skills/security/akatsuki"
cp "$SCRIPT_DIR/tools/akatsuki_"*.py "$HERMES_HOME/tools/" 2>/dev/null || true
cp -r "$SCRIPT_DIR/skills/security/akatsuki" "$HERMES_HOME/skills/security/"
echo "      Done."

# 5. Hermes 설정 패치
echo "[5/5] Patching Hermes configuration..."

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
