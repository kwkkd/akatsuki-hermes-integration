"""AI inference engine using transformers for model loading and text generation."""

import asyncio
from dataclasses import dataclass, field
from typing import Optional

from .logger import logger


@dataclass
class GenerationResult:
    text: str
    tokens_generated: int = 0
    tokens_per_second: float = 0.0
    model_id: str = ""
    error: Optional[str] = None


class AkatsukiInference:
    """Inference engine for transformer-based language models."""

    def __init__(self, model_id: str = ""):
        self.model_id = model_id
        self._model = None
        self._tokenizer = None
        self._pipeline = None
        self._loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    async def load(self, model_id: Optional[str] = None, use_4bit: bool = True, max_seq_length: int = 8192):
        if self._loaded:
            logger.warning("Model already loaded, skipping")
            return
        model_id = model_id or self.model_id
        if not model_id:
            raise ValueError("model_id is required to load model")
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
            import transformers
            logger.info(f"Loading model: {model_id}")
            self._tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
            load_kwargs = {
                "device_map": "auto",
                "trust_remote_code": True,
                "torch_dtype": torch.float16,
            }
            if use_4bit:
                from transformers import BitsAndBytesConfig
                bnb_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_compute_dtype=torch.float16,
                )
                load_kwargs["quantization_config"] = bnb_config
            self._model = AutoModelForCausalLM.from_pretrained(model_id, **load_kwargs)
            self._model.eval()
            self._pipeline = pipeline(
                "text-generation",
                model=self._model,
                tokenizer=self._tokenizer,
                device_map="auto",
            )
            self._loaded = True
            self.model_id = model_id
            logger.info(f"Model loaded: {model_id}")
        except ImportError as e:
            raise ImportError(f"Missing dependencies: {e}. Install with: pip install torch transformers accelerate bitsandbytes")
        except Exception as e:
            logger.error(f"Failed to load model {model_id}: {e}")
            raise

    async def generate(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 50,
        repetition_penalty: float = 1.1,
    ) -> GenerationResult:
        if not self._loaded:
            return GenerationResult(text="", error="Model not loaded", model_id=self.model_id)
        try:
            import torch
            import time
            inputs = self._tokenizer(prompt, return_tensors="pt").to(self._model.device)
            start = time.time()
            with torch.no_grad():
                outputs = self._model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    top_k=top_k,
                    repetition_penalty=repetition_penalty,
                    do_sample=temperature > 0,
                    pad_token_id=self._tokenizer.eos_token_id,
                )
            elapsed = time.time() - start
            generated = outputs[0][inputs.input_ids.shape[1]:]
            text = self._tokenizer.decode(generated, skip_special_tokens=True)
            tokens_generated = len(generated)
            tps = tokens_generated / elapsed if elapsed > 0 else 0
            return GenerationResult(
                text=text,
                tokens_generated=tokens_generated,
                tokens_per_second=round(tps, 2),
                model_id=self.model_id,
            )
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return GenerationResult(text="", error=str(e), model_id=self.model_id)

    async def generate_stream(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ):
        if not self._loaded:
            yield GenerationResult(text="", error="Model not loaded", model_id=self.model_id)
            return
        try:
            import torch
            inputs = self._tokenizer(prompt, return_tensors="pt").to(self._model.device)
            with torch.no_grad():
                generated = inputs.input_ids[0].tolist()
                for _ in range(max_tokens):
                    outputs = self._model(
                        input_ids=torch.tensor([generated], device=self._model.device)
                    )
                    logits = outputs.logits[0, -1, :]
                    if temperature > 0:
                        probs = torch.softmax(logits / temperature, dim=-1)
                        next_token = torch.multinomial(probs, 1).item()
                    else:
                        next_token = torch.argmax(logits, dim=-1).item()
                    generated.append(next_token)
                    yield self._tokenizer.decode([next_token], skip_special_tokens=True)
                    if next_token == self._tokenizer.eos_token_id:
                        break
        except Exception as e:
            logger.error(f"Stream generation failed: {e}")
            yield GenerationResult(text="", error=str(e), model_id=self.model_id)

    async def unload(self):
        if self._loaded:
            import gc
            import torch
            del self._model
            del self._tokenizer
            del self._pipeline
            self._model = None
            self._tokenizer = None
            self._pipeline = None
            self._loaded = False
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("Model unloaded")
