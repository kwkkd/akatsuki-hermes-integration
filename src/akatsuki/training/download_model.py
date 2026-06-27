"""Download a model from Hugging Face Hub."""

import sys

try:
    from huggingface_hub import snapshot_download
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install huggingface-hub")
    sys.exit(1)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Download model from Hugging Face Hub")
    parser.add_argument("repo_id", help="Repository ID (e.g., meta-llama/Llama-2-7b)")
    parser.add_argument("--output", "-o", default=None, help="Output directory")
    parser.add_argument("--token", default=None, help="Hugging Face token")
    args = parser.parse_args()

    path = snapshot_download(
        repo_id=args.repo_id,
        local_dir=args.output,
        token=args.token,
        ignore_patterns=["*.safetensors"],
    )
    print(f"Model downloaded to {path}")


if __name__ == "__main__":
    main()
