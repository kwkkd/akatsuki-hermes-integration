import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger("akatsuki.inference")


def load_config() -> dict:
    import yaml
    cfg_path = Path(__file__).parent / "akatsuki.yaml"
    if cfg_path.exists():
        with open(cfg_path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


class AkatsukiInference:
    def __init__(self, model_id: str = "", device_map: str = "auto", torch_dtype: str = "auto"):
        self.model_id = model_id
        self.device_map = device_map
        self.torch_dtype = torch_dtype
        self.model = None
        self.tokenizer = None
        self._loaded = False

    def load(self):
        from transformers import AutoModelForCausalLM, AutoTokenizer
        cfg = load_config()
        model_cfg = cfg.get("model", {})
        model_id = self.model_id or model_cfg.get("id", "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B")
        paths_cfg = cfg.get("paths", {})
        models_dir = Path(__file__).parent / paths_cfg.get("models_dir", "models")
        model_path = models_dir / Path(model_id).name
        if model_path.exists():
            model_id = str(model_path)

        logger.info(f"Loading model: {model_id}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=self.torch_dtype or model_cfg.get("torch_dtype", "auto"),
            device_map=self.device_map or model_cfg.get("device_map", "auto"),
            trust_remote_code=True,
        )
        self._loaded = True
        logger.info("Model loaded successfully")

    def chat(self, prompt: str, max_new_tokens: int = 0, temperature: float = 0) -> str:
        if not self._loaded:
            self.load()
        cfg = load_config()
        model_cfg = cfg.get("model", {})
        max_new_tokens = max_new_tokens or model_cfg.get("max_new_tokens", 4096)
        temperature = temperature or model_cfg.get("temperature", 0.7)
        inputs = self.tokenizer(prompt, return_tensors="pt")
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=temperature > 0,
            pad_token_id=self.tokenizer.eos_token_id,
        )
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)

    def is_loaded(self) -> bool:
        return self._loaded


def create_pipeline(model_id: str = "", device: str = "cpu") -> Optional[object]:
    try:
        import torch
        from transformers import pipeline
        cfg = load_config()
        model_cfg = cfg.get("model", {})
        final_id = model_id or model_cfg.get("id", "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B")
        device_map = "auto" if torch.cuda.is_available() else "cpu"
        return pipeline(
            "text-generation",
            model=final_id,
            device_map=device_map,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            trust_remote_code=True,
        )
    except Exception as e:
        logger.error(f"Failed to create pipeline: {e}")
        return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ai = AkatsukiInference()
    response = ai.chat("너는 누구야? 자기소개 해줘.")
    print(f"\nResponse:\n{response}")