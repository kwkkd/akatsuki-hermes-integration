"""AKATSUKI built-in interactive chat CLI"""
import sys
import os
import asyncio
from typing import Optional
from ..api.client import AkatsukiAPIClient
from ..core.config import CONFIG

_DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", CONFIG.api.ollama_model)


async def interactive_loop(model: str):
    client = AkatsukiAPIClient()
    history = []
    print("AKATSUKI Chat (type '/help' for commands, '/quit' to exit)")
    print("-" * 50)
    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print(); break
        if not user_input: continue
        if user_input.lower() in ("/quit", "/exit", "/q"): break
        if user_input.lower() == "/help":
            print("Commands: /quit /exit /q  /clear  /model <name>  /tools"); continue
        if user_input.lower() == "/clear":
            history.clear(); print("History cleared."); continue
        if user_input.lower() == "/tools":
            from .tools import get_registry
            for t in get_registry().list_tools():
                print(f"  {t.name}: {t.description}")
            continue
        if user_input.lower().startswith("/model "):
            model = user_input.split(" ", 1)[1].strip(); print(f"Model set to: {model}"); continue
        try:
            response = await client.chat(history + [{"role": "user", "content": user_input}], model=model)
        except ConnectionError as e:
            print(f"\n[!] {e}"); continue
        history.append({"role": "user", "content": user_input})
        history.append({"role": "assistant", "content": response})
        print(f"\nAKATSUKI: {response}")


def main(argv: list = None):
    import argparse
    parser = argparse.ArgumentParser(description="AKATSUKI interactive chat", prog="akatsuki chat")
    parser.add_argument("--model", default=_DEFAULT_MODEL, help="Model name")
    parser.add_argument("message", nargs="*", help="Single message (non-interactive mode)")
    args = parser.parse_args(argv)

    if args.message:
        message = " ".join(args.message)
        client = AkatsukiAPIClient()
        try:
            response = asyncio.run(client.chat([{"role": "user", "content": message}], model=args.model))
            print(response)
        except ConnectionError as e:
            print(f"[!] {e}")
            sys.exit(1)
    else:
        asyncio.run(interactive_loop(args.model))
