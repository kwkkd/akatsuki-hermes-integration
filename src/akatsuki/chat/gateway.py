"""AKATSUKI Gateway status display"""
import os
from ..core.config import CONFIG


def main():
    host = CONFIG.api.host
    port = CONFIG.api.port
    ollama_host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    print("AKATSUKI Gateway Status")
    print(f"  API Server:  http://{host}:{port}")
    print(f"  Ollama Host: {ollama_host}")
    print(f"  Model:       {CONFIG.api.ollama_model}")
    print(f"  Max tokens:  {CONFIG.api.max_tokens}")
    print(f"  Temperature: {CONFIG.api.temperature}")
    print()
    print("To start: akatsuki api")
    print("To chat:  akatsuki chat")
