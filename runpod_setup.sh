# AKATSUKI Continual Pre-training — RunPod Deployment Script
# https://runpod.io → GPU Cloud → RTX 6000 Ada (48GB) or A100 (80GB)
#
# Usage:
#   1. Create a Pod with "RunPod PyTorch 2.3" template
#   2. Upload this repo or git clone
#   3. Run this script inside the pod

set -e

echo "=== AKATSUKI RunPod Setup ==="
echo ""

# ── Hardware ──
echo "GPU(s):"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
NUM_GPUS=$(nvidia-smi --query-gpu=name --format=csv,noheader | wc -l)
echo "Count: $NUM_GPUS"
echo ""

# ── Dependencies ──
echo "Installing dependencies..."
pip install -q torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
pip install -q transformers accelerate bitsandbytes peft trl datasets
pip install -q deepspeed ninja packaging
pip install -q pyyaml jinja2 scipy

# ── Flash Attention (optional, speeds up 2x) ──
echo "Installing flash-attention..."
pip install -q flash-attn --no-build-isolation 2>/dev/null || echo "flash-attn skipped (will use eager)"

# ── Clone Repo ──
if [ ! -d "akatsuki" ]; then
    echo "Cloning AKATSUKI..."
    git clone https://github.com/kwkkd/akatsuki-hermes-integration akatsuki
fi
cd akatsuki

# ── Generate Corpus ──
echo "Generating training corpus..."
python corpus_builder.py

# ── Continual Pre-training ──
echo ""
echo "=== Starting Continual Pre-training ==="
echo "Model: Qwen/Qwen2.5-7B-Instruct"
echo "GPUs: $NUM_GPUS"
echo ""

python continue_pretrain.py

echo ""
echo "=== Pre-training Complete ==="
echo "Model saved to: pretrained_akatsuki/"

# ── SFT Training ──
echo ""
echo "=== Starting SFT (AKATSUKI Style Training) ==="
echo ""

# Update config to use pre-trained model as base
sed -i 's|id: "Qwen/Qwen2.5-7B-Instruct"|id: "./pretrained_akatsuki"|' akatsuki.yaml

python train.py

echo ""
echo "=== AKATSUKI Model Pipeline Complete! ==="
echo ""
echo "Outputs:"
echo "  - pretrained_akatsuki/  (domain knowledge)"
echo "  - merged_hacker_ai_model/  (final AKATSUKI model)"
echo ""
echo "To download: tar czf akatsuki_model.tar.gz merged_hacker_ai_model/"
