"""Telegram bot command handlers."""

import json
from ..agents import ALL_AGENTS


def cmd_chat(bot, message, args):
    from ..api.client import AkatsukiAPIClient
    client = AkatsukiAPIClient()
    response = client.chat([{"role": "user", "content": " ".join(args)}])
    bot.reply_to(message, response)


def cmd_scan(bot, message, args):
    if not args:
        bot.reply_to(message, "Usage: /scan <target>")
        return
    agent = ALL_AGENTS.get("vuln")
    if agent:
        result = agent.execute({"target": args[0]})
        bot.reply_to(message, json.dumps(result, indent=2))
    else:
        bot.reply_to(message, "Scan agent not available")


def cmd_exploit(bot, message, args):
    if len(args) < 1:
        bot.reply_to(message, "Usage: /exploit <target> [vuln_id]")
        return
    agent = ALL_AGENTS.get("weapon")
    if agent:
        result = agent.execute({"target": args[0], "vuln_id": args[1] if len(args) > 1 else ""})
        bot.reply_to(message, json.dumps(result, indent=2))
    else:
        bot.reply_to(message, "Exploit agent not available")


def cmd_payload(bot, message, args):
    if len(args) < 2:
        bot.reply_to(message, "Usage: /payload <target> <vector>")
        return
    agent = ALL_AGENTS.get("payload")
    if agent:
        result = agent.execute({"target": args[0], "vector": args[1]})
        bot.reply_to(message, json.dumps(result, indent=2))
    else:
        bot.reply_to(message, "Payload agent not available")


def cmd_recon(bot, message, args):
    if not args:
        bot.reply_to(message, "Usage: /recon <target>")
        return
    agent = ALL_AGENTS.get("recon")
    if agent:
        result = agent.execute({"target": args[0]})
        bot.reply_to(message, json.dumps(result, indent=2))
    else:
        bot.reply_to(message, "Recon agent not available")


def cmd_status(bot, message, args):
    from ..api.client import ollama_detected
    lines = [
        "AKATSUKI Status",
        f"  Agents: {len(ALL_AGENTS)} loaded",
        f"  Ollama: {'detected' if ollama_detected else 'not detected'}",
    ]
    for name, agent in ALL_AGENTS.items():
        lines.append(f"  - {name}: {agent.description}")
    bot.reply_to(message, "\n".join(lines))


def cmd_report(bot, message, args):
    parts = " ".join(args) if args else "all"
    bot.reply_to(message, f"Generating report for: {parts}\n(Report generation not yet implemented)")


def cmd_c2(bot, message, args):
    bot.reply_to(message, "C2 channel not yet connected")


def cmd_chain(bot, message, args):
    bot.reply_to(message, "Attack chaining not yet implemented")


COMMAND_HANDLERS = {
    "chat": cmd_chat,
    "scan": cmd_scan,
    "exploit": cmd_exploit,
    "payload": cmd_payload,
    "recon": cmd_recon,
    "status": cmd_status,
    "report": cmd_report,
    "c2": cmd_c2,
    "chain": cmd_chain,
}
