import sys, os, torch
sys.path.insert(0, os.path.dirname(__file__))
from akatsuki_config import CONFIG
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

def merge_and_save(lora_path: str = None, output_path: str = None):
    lora_path = lora_path or CONFIG.model.lora_path
    output_path = output_path or CONFIG.model.merged_path
    base_model_id = CONFIG.model.id

    print(f"Loading base model: {base_model_id}")
    model = AutoModelForCausalLM.from_pretrained(
        base_model_id, torch_dtype=torch.float16, device_map="auto",
        trust_remote_code=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(base_model_id, trust_remote_code=True)

    print(f"Loading LoRA adapter: {lora_path}")
    model = PeftModel.from_pretrained(model, lora_path)
    model = model.merge_and_unload()

    os.makedirs(output_path, exist_ok=True)
    model.save_pretrained(output_path)
    tokenizer.save_pretrained(output_path)
    print(f"Merged model saved to: {output_path}")
    return output_path

if __name__ == "__main__":
    merge_and_save()
