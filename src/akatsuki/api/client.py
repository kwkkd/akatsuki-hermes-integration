"""AKATSUKI API Client with auto Ollama detection and retry"""
import os
import asyncio
import socket
import httpx
from typing import List, Dict, Optional
from ..core.config import CONFIG


class AkatsukiAPIClient:
    _ollama_url = ""

    @classmethod
    def _probe_ollama(cls) -> str:
        if cls._ollama_url:
            return cls._ollama_url
        candidates = ["http://localhost:11434"]
        for url in candidates:
            try:
                host = url.replace("http://", "").split(":")[0]
                port = int(url.split(":")[-1])
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                if s.connect_ex((host, port)) == 0:
                    cls._ollama_url = url
                s.close()
                if cls._ollama_url:
                    return cls._ollama_url
            except Exception:
                pass
        cls._ollama_url = ""
        return ""

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, max_retries: int = 2):
        default_url = f"http://{CONFIG.api.host}:{CONFIG.api.port}/v1"
        self.base_url = base_url or os.environ.get("AKATSUKI_API_URL", default_url)
        self.api_key = api_key or os.environ.get("AKATSUKI_API_KEY", "")
        self.direct_ollama = (
            os.environ.get("AKATSUKI_OLLAMA_DIRECT", "")
            or os.environ.get("OLLAMA_HOST", "")
            or self._probe_ollama()
        )
        self.max_retries = max_retries

    async def chat(self, messages: List[Dict], model: str = "", max_tokens: int = 2048, temperature: float = 0.7) -> str:
        model = model or CONFIG.api.ollama_model
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=120) as c:
                    r = await c.post(
                        f"{self.base_url}/chat/completions",
                        json={"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": temperature},
                        headers=headers,
                    )
                    if r.status_code == 200:
                        return r.json()["choices"][0]["message"]["content"]
                    if r.status_code in (401, 503):
                        raise ConnectionError(r.json().get("detail", str(r.status_code)))
                    if attempt < self.max_retries:
                        await asyncio.sleep((attempt + 1))
                        continue
                    raise ConnectionError(f"API error {r.status_code}")
            except httpx.ConnectError:
                if attempt < self.max_retries:
                    await asyncio.sleep((attempt + 1))
                    continue

        if self.direct_ollama:
            for attempt in range(self.max_retries + 1):
                try:
                    async with httpx.AsyncClient(timeout=120) as c:
                        r = await c.post(
                            f"{self.direct_ollama}/v1/chat/completions",
                            json={"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": temperature},
                        )
                        if r.status_code == 200:
                            return r.json()["choices"][0]["message"]["content"]
                except Exception:
                    if attempt < self.max_retries:
                        await asyncio.sleep((attempt + 1))
                        continue

        raise ConnectionError(
            f"Cannot reach API server ({self.base_url}) or Ollama ({self.direct_ollama}). "
            f"Start the API server: akatsuki api"
        )
