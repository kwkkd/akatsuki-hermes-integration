import sys, os, json, math, torch, argparse
from pathlib import Path
from datasets import load_dataset
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(__file__))
from akatsuki_config import CONFIG

@dataclass
class PretrainConfig:
    base_model: str = "Qwen/Qwen2.5-7B-Instruct"
    corpus_path: str = "corpus/security_corpus.jsonl"
    output_dir: str = "pretrained_akatsuki"
    block_size: int = 2048
    batch_size: int = 1
    grad_accum: int = 8
    learning_rate: float = 5e-5
    num_epochs: int = 1
    warmup_ratio: float = 0.05
    save_steps: int = 500
    logging_steps: int = 10
    use_deepspeed: bool = True
    use_flash_attn: bool = True
    qlora: bool = False

def continue_pretrain(cfg: PretrainConfig):
    from transformers import (
        AutoModelForCausalLM, AutoTokenizer, TrainingArguments,
        Trainer, DataCollatorForLanguageModeling,
    )

    print(f"Loading base model: {cfg.base_model}")
    tokenizer = AutoTokenizer.from_pretrained(cfg.base_model, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    attn_impl = "flash_attention_2" if cfg.use_flash_attn else "eager"
    if cfg.qlora:
        from transformers import BitsAndBytesConfig
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16,
        )
        model = AutoModelForCausalLM.from_pretrained(
            cfg.base_model, quantization_config=bnb_config,
            device_map="auto", torch_dtype=torch.bfloat16,
            trust_remote_code=True,
        )
        model = prepare_model_for_kbit_training(model)
        lora_cfg = LoraConfig(
            r=16, lora_alpha=32, lora_dropout=0.05,
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj",
                            "gate_proj", "up_proj", "down_proj"],
            bias="none", task_type="CAUSAL_LM",
        )
        model = get_peft_model(model, lora_cfg)
        model.print_trainable_parameters()
    else:
        model = AutoModelForCausalLM.from_pretrained(
            cfg.base_model, torch_dtype=torch.bfloat16,
            attn_implementation=attn_impl,
            device_map="auto" if not cfg.use_deepspeed else None,
            trust_remote_code=True,
        )
    model.gradient_checkpointing_enable()
    model.config.use_cache = False

    print(f"Loading corpus: {cfg.corpus_path}")
    dataset = load_dataset("json", data_files=cfg.corpus_path, split="train")

    def tokenize_fn(examples):
        outputs = tokenizer(
            examples["text"],
            truncation=True,
            max_length=cfg.block_size,
            padding=False,
            return_overflowing_tokens=False,
        )
        return {"input_ids": outputs["input_ids"], "attention_mask": outputs["attention_mask"]}

    tokenized = dataset.map(
        tokenize_fn,
        remove_columns=["text"],
        batched=True,
        num_proc=4,
        desc="Tokenizing",
    )
    print(f"  Tokenized samples: {len(tokenized):,}")
    total_tokens = sum(len(x) for x in tokenized["input_ids"])
    print(f"  Total tokens: {total_tokens:,} ({total_tokens/1e6:.1f}M)")

    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
    )

    training_args = TrainingArguments(
        output_dir=cfg.output_dir,
        overwrite_output_dir=True,
        num_train_epochs=cfg.num_epochs,
        per_device_train_batch_size=cfg.batch_size,
        gradient_accumulation_steps=cfg.grad_accum,
        learning_rate=cfg.learning_rate,
        weight_decay=0.01,
        warmup_ratio=cfg.warmup_ratio,
        lr_scheduler_type="cosine",
        logging_steps=cfg.logging_steps,
        save_steps=cfg.save_steps,
        save_total_limit=3,
        bf16=True,
        fp16=False,
        dataloader_num_workers=4,
        report_to="none",
        ddp_find_unused_parameters=False if cfg.use_deepspeed else None,
        deepspeed="ds_config.json" if cfg.use_deepspeed else None,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized,
        data_collator=data_collator,
        tokenizer=tokenizer,
    )

    trainer.train()
    trainer.save_model(cfg.output_dir)
    tokenizer.save_pretrained(cfg.output_dir)
    print(f"Pre-trained model saved to: {cfg.output_dir}")
    return cfg.output_dir

def generate_ds_config():
    config = {
        "bf16": {"enabled": True},
        "zero_optimization": {
            "stage": 3,
            "offload_optimizer": {"device": "cpu", "pin_memory": True},
            "offload_param": {"device": "cpu", "pin_memory": True},
            "overlap_comm": True,
            "contiguous_gradients": True,
            "sub_group_size": 1e9,
            "reduce_bucket_size": "auto",
            "stage3_prefetch_bucket_size": "auto",
            "stage3_param_persistence_threshold": "auto",
            "stage3_max_live_parameters": 1e9,
            "stage3_max_reuse_distance": 1e9,
            "gather_16bit_weights_on_model_save": True,
        },
        "gradient_accumulation_steps": "auto",
        "gradient_clipping": "auto",
        "steps_per_print": 10,
        "train_batch_size": "auto",
        "train_micro_batch_size_per_gpu": "auto",
        "wall_clock_breakdown": False,
    }
    with open("ds_config.json", "w") as f:
        json.dump(config, f, indent=2)
    print("Deepspeed config written: ds_config.json")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AKATSUKI Continual Pre-training")
    parser.add_argument("--qlora", action="store_true", help="QLoRA 4-bit mode (single GPU friendly)")
    parser.add_argument("--batch_size", type=int, default=2, help="Per-device batch size")
    parser.add_argument("--lr", type=float, default=5e-5, help="Learning rate")
    parser.add_argument("--epochs", type=int, default=1, help="Number of epochs")
    parser.add_argument("--corpus", type=str, default="corpus/security_corpus.jsonl", help="Corpus path")
    parser.add_argument("--output", type=str, default="pretrained_akatsuki", help="Output directory")
    args = parser.parse_args()

    cfg = PretrainConfig()
    cfg.qlora = args.qlora
    cfg.batch_size = args.batch_size
    cfg.learning_rate = args.lr
    cfg.num_epochs = args.epochs
    cfg.corpus_path = args.corpus
    cfg.output_dir = args.output

    print("=== AKATSUKI Continual Pre-training ===\n")

    if not os.path.exists(cfg.corpus_path):
        print(f"Corpus not found: {cfg.corpus_path}")
        print("Run corpus_builder.py first to generate the corpus.")
        sys.exit(1)

    num_gpus = torch.cuda.device_count()
    print(f"GPUs available: {num_gpus}")

    if cfg.use_deepspeed and num_gpus >= 2 and not cfg.qlora:
        generate_ds_config()
    else:
        cfg.use_deepspeed = False
        if cfg.qlora:
            print("QLoRA mode: Deepspeed disabled")
        else:
            print("Deepspeed disabled (need 2+ GPUs)")

    output = continue_pretrain(cfg)
    print(f"\nDone. Model: {output}")
