"""Continued pretraining with causal language modeling."""

import sys

try:
    import torch
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        Trainer,
        TrainingArguments,
        DataCollatorForLanguageModeling,
    )
    from datasets import load_dataset
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install torch transformers datasets accelerate")
    sys.exit(1)


def main(model_name=None, dataset_path=None, output_dir="./output"):
    if model_name is None:
        from ..core.config import CONFIG
        model_name = CONFIG.api.ollama_model

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )

    tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token

    dataset = load_dataset("text", data_files=dataset_path, split="train")

    def tokenize_fn(examples):
        return tokenizer(examples["text"], truncation=True, max_length=2048)

    tokenized_dataset = dataset.map(tokenize_fn, batched=True, remove_columns=["text"])

    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
    )

    training_args = TrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=4,
        gradient_accumulation_steps=4,
        num_train_epochs=3,
        learning_rate=5e-5,
        fp16=True,
        save_steps=500,
        logging_steps=50,
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
        data_collator=data_collator,
        tokenizer=tokenizer,
    )

    trainer.train()
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)
    print(f"Pretraining complete. Model saved to {output_dir}")
