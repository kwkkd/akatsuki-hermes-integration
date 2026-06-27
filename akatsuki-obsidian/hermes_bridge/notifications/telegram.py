import json
import logging
from typing import Optional

logger = logging.getLogger("akatsuki.notifications.telegram")


class TelegramNotifier:
    def __init__(self, bot_token: str = "", chat_id: str = ""):
        self.bot_token = bot_token or ""
        self.chat_id = chat_id or ""
        self._enabled = bool(self.bot_token and self.chat_id)

    def is_enabled(self) -> bool:
        return self._enabled

    def send(self, message: str, parse_mode: str = "markdown") -> bool:
        if not self._enabled:
            logger.info(f"[Telegram disabled] Would send: {message[:100]}")
            return False
        try:
            import httpx
            url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
            resp = httpx.post(url, json={
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True,
            }, timeout=10)
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Telegram send failed: {e}")
            return False

    def send_operation_update(self, operation_id: str, phase: str,
                               status: str, target: str = ""):
        emojis = {"started": "▶️", "completed": "✅", "failed": "❌", "skipped": "⏭️"}
        emoji = emojis.get(status, "ℹ️")
        msg = (
            f"{emoji} *AKATSUKI Operation Update*\n"
            f"`{operation_id}`\n"
            f"**Phase:** {phase}\n"
            f"**Status:** {status}\n"
        )
        if target:
            msg += f"**Target:** {target}\n"
        self.send(msg)

    def send_alert(self, title: str, message: str, severity: str = "info"):
        emojis = {"critical": "🚨", "high": "⚠️", "medium": "⚡", "low": "ℹ️", "info": "📝"}
        emoji = emojis.get(severity, "📝")
        self.send(f"{emoji} *{title}*\n{message}")

    def configure(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self._enabled = bool(bot_token and chat_id)


_notifier = TelegramNotifier()


def get_notifier() -> TelegramNotifier:
    return _notifier