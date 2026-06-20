"""
AKATSUKI Model Downloader
Downloads DeepSeek-R1-Distill-Qwen-7B and configures AKATSUKI to use it.
"""
import os, sys, argparse
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.resolve()
DEFAULT_SAVE_DIR = PROJECT_DIR / "models" / "DeepSeek-R1-Distill-Qwen-7B"

def download_model(save_dir: str = None, hf_token: str = None):
    from transformers import AutoModelForCausalLM, AutoTokenizer

    model_id = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
    save_dir = save_dir or str(DEFAULT_SAVE_DIR)

    if os.path.exists(save_dir) and len(os.listdir(save_dir)) > 5:
        print(f"Model already exists at: {save_dir}")
        print(f"  Files: {len(os.listdir(save_dir))}")
        yn = input("Download again? (y/N): ").strip().lower()
        if yn != "y":
            print("Skipping download.")
            return save_dir

    os.makedirs(save_dir, exist_ok=True)
    print(f"Downloading {model_id} → {save_dir}")
    print("  Size: ~15GB (may take 10-30 min)")

    kwargs = {"trust_remote_code": True}
    if hf_token:
        kwargs["token"] = hf_token

    print("\n[1/2] Downloading tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_id, **kwargs)
    tokenizer.save_pretrained(save_dir)
    print("  Tokenizer saved.")

    print("\n[2/2] Downloading model (this is the big one)...")
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype="auto",
        device_map="auto",
        **kwargs,
    )
    model.save_pretrained(save_dir, safe_serialization=True)
    print("  Model saved.")

    print(f"\nDone! Model saved to: {save_dir}")
    print(f"  Total files: {len(os.listdir(save_dir))}")
    return save_dir

def configure_akatsuki(model_path: str):
    cfg_path = PROJECT_DIR / "akatsuki.yaml"

    if not cfg_path.exists():
        print(f"Config not found: {cfg_path}")
        return

    with open(cfg_path, "r", encoding="utf-8") as f:
        content = f.read()

    new_path = model_path.replace("\\", "/")
    if "model:" in content:
        lines = content.split("\n")
        new_lines = []
        for line in lines:
            if line.strip().startswith("id:"):
                new_lines.append(f'  id: "{new_path}"')
            else:
                new_lines.append(line)
        content = "\n".join(new_lines)
    else:
        content = f"model:\n  id: \"{new_path}\"\n" + content

    with open(cfg_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Updated akatsuki.yaml → model.id = \"{new_path}\"")

def test_inference():
    sys.path.insert(0, str(PROJECT_DIR))
    from akatsuki_config import CONFIG
    from inference import AkatsukiInference

    print(f"\nTesting model: {CONFIG.model.id}")
    ai = AkatsukiInference()
    ai.load()
    response = ai.chat("너는 누구야? 자기소개 해줘.")
    print(f"\nResponse:\n{response}")
    return response

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download DeepSeek-R1-Distill-Qwen-7B for AKATSUKI")
    parser.add_argument("--save_dir", type=str, default=None, help="Custom save directory")
    parser.add_argument("--token", type=str, default=None, help="HuggingFace token (for gated models)")
    parser.add_argument("--no-test", action="store_true", help="Skip inference test")
    parser.add_argument("--hermes", action="store_true", help="Also configure for Hermes Agent")
    args = parser.parse_args()

    print("=== AKATSUKI Model Downloader ===\n")

    save_dir = download_model(args.save_dir, args.token)

    configure_akatsuki(save_dir)

    if args.hermes:
        hermes_path = os.path.expanduser(
            "~/AppData/Local/hermes/hermes-agent"
        )
        hermes_cfg = os.path.join(hermes_path, "akatsuki.yaml")
        if os.path.exists(hermes_cfg):
            hermes_save = os.path.join(hermes_path, "models", "DeepSeek-R1-Distill-Qwen-7B")
            os.makedirs(os.path.dirname(hermes_save), exist_ok=True)
            configure_akatsuki(hermes_save)
            print(f"Hermes Agent config updated: {hermes_cfg}")

    if not args.no_test:
        test_inference()

    print("\nDone. Run 'python inference.py' to chat with AKATSUKI.")
