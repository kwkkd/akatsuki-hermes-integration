"""Merge LoRA adapters into base model."""

import sys

try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install torch transformers peft")
    sys.exit(1)


def main(model_name=None, adapter_path=None, output_dir=None):
    base_model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)

    model = PeftModel.from_pretrained(base_model, adapter_path)
    merged = model.merge_and_unload()

    merged.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"Merged model saved to {output_dir}")
