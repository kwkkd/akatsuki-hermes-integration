import os, json
from pathlib import Path
from pydantic import BaseModel

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

class APIConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list = ["*"]
    max_tokens: int = 2048
    temperature: float = 0.7
    ollama_model: str = "dolphin-mistral:7b"

class ModelConfig(BaseModel):
    id: str = "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B"
    lora_path: str = str(PROJECT_ROOT / "hacker_ai_model")
    merged_path: str = str(PROJECT_ROOT / "merged_hacker_ai_model")
    use_4bit: bool = True
    max_seq_length: int = 8192
    load_in_8bit: bool = False

class TrainingConfig(BaseModel):
    num_epochs: int = 3
    batch_size: int = 1
    gradient_accumulation_steps: int = 8
    learning_rate: float = 2e-4
    warmup_ratio: float = 0.05
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    lora_target_modules: list = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    dpo_beta: float = 0.1

class TelegramConfig(BaseModel):
    bot_token_env: str = "TELEGRAM_BOT_TOKEN"
    allowed_ids_env: str = "TELEGRAM_ALLOWED_IDS"

class PathsConfig(BaseModel):
    dataset: str = str(PROJECT_ROOT / "dataset.jsonl")
    evaluations: str = str(PROJECT_ROOT / "evaluations")
    playbooks: str = str(PROJECT_ROOT / "playbooks")
    knowledge_base: str = str(PROJECT_ROOT / "knowledge_base")

class SwarmConfig(BaseModel):
    max_agents_per_phase: int = 3
    consensus_threshold: float = 0.6

class GlobalConfig(BaseModel):
    debug: bool = False
    verbose: bool = False
    api: APIConfig = APIConfig()
    model: ModelConfig = ModelConfig()
    training: TrainingConfig = TrainingConfig()
    telegram: TelegramConfig = TelegramConfig()
    paths: PathsConfig = PathsConfig()
    swarm: SwarmConfig = SwarmConfig()
    system_prompt: str = "You are AKATSUKI - an elite APT simulation AI assistant."

CONFIG = GlobalConfig()
