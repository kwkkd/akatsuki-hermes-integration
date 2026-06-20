import sys, os, json, torch, argparse
from datasets import Dataset
sys.path.insert(0, os.path.dirname(__file__))
from akatsuki_config import CONFIG

def train(model_id: str = None, output_dir: str = None):
    from transformers import AutoModelForCausalLM, AutoTokenizer, TrainingArguments, BitsAndBytesConfig
    from trl import SFTTrainer
    from peft import LoraConfig

    model_id = model_id or CONFIG.model.id
    output_dir = output_dir or CONFIG.model.lora_path

    bnb_config = BitsAndBytesConfig(
        load_in_4bit=CONFIG.model.use_4bit,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
    )

    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    if tokenizer.chat_template is None:
        tokenizer.chat_template = (
            "{% for message in messages %}{% if message['role'] == 'system' %}"
            "{{ '<|im_start|>system\\n' + message['content'] + '<|im_end|>\\n' }}"
            "{% elif message['role'] == 'user' %}"
            "{{ '<|im_start|>user\\n' + message['content'] + '<|im_end|>\\n' }}"
            "{% elif message['role'] == 'assistant' %}"
            "{{ '<|im_start|>assistant\\n' + message['content'] + '<|im_end|>\\n' }}"
            "{% endif %}{% endfor %}{% if add_generation_prompt %}"
            "{{ '<|im_start|>assistant\\n' }}{% endif %}"
        )

    model = AutoModelForCausalLM.from_pretrained(
        model_id, quantization_config=bnb_config, device_map="auto",
        trust_remote_code=True, torch_dtype=torch.float16,
    )
    model.config.use_cache = False
    model.gradient_checkpointing_enable()

    lora_config = LoraConfig(
        r=CONFIG.training.lora_r, lora_alpha=CONFIG.training.lora_alpha,
        lora_dropout=CONFIG.training.lora_dropout,
        target_modules=CONFIG.training.lora_target_modules,
        bias="none", task_type="CAUSAL_LM",
    )

    dataset_path = CONFIG.paths.dataset
    if not os.path.exists(dataset_path):
        print(f"Dataset not found: {dataset_path}")
        samples = []
        for i in range(50):
            samples.append({
                "instruction": f"Sample instruction {i}",
                "output": f"Sample output {i}",
                "system": CONFIG.system_prompt[:500],
            })
        with open(dataset_path, "w", encoding="utf-8") as f:
            for s in samples:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")

    dataset = Dataset.from_json(dataset_path)

    def format_func(example):
        system = example.get("system", CONFIG.system_prompt[:500])
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": example["instruction"]},
            {"role": "assistant", "content": example["output"]},
        ]
        return tokenizer.apply_chat_template(messages, tokenize=False)

    training_args = TrainingArguments(
        output_dir=output_dir, num_train_epochs=CONFIG.training.num_epochs,
        per_device_train_batch_size=CONFIG.training.batch_size,
        gradient_accumulation_steps=CONFIG.training.gradient_accumulation_steps,
        learning_rate=CONFIG.training.learning_rate,
        warmup_ratio=CONFIG.training.warmup_ratio,
        logging_steps=10, save_strategy="epoch",
        fp16=True, bf16=False, optim="paged_adamw_8bit",
        report_to="none", ddp_find_unused_parameters=False,
    )

    trainer = SFTTrainer(
        model=model, tokenizer=tokenizer, args=training_args,
        train_dataset=dataset, max_seq_length=CONFIG.model.max_seq_length,
        formatting_func=format_func, peft_config=lora_config,
        dataset_kwargs={"add_special_tokens": False},
    )

    trainer.train()
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"Model saved to {output_dir}")

    from merge_model import merge_and_save
    merge_and_save()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AKATSUKI SFT Training")
    parser.add_argument("--model_id", type=str, default=None, help="Base model path or HF ID")
    parser.add_argument("--output_dir", type=str, default=None, help="LoRA output directory")
    args = parser.parse_args()
    train(model_id=args.model_id, output_dir=args.output_dir)
