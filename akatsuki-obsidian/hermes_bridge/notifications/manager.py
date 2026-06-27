import logging
from typing import Optional

from hermes_bridge.notifications.telegram import TelegramNotifier, get_notifier as get_telegram
from hermes_bridge.notifications.webpush import WebPushNotifier

logger = logging.getLogger("akatsuki.notifications.manager")


class NotificationManager:
    def __init__(self):
        self.telegram: TelegramNotifier = get_telegram()
        self.webpush: Optional[WebPushNotifier] = None

    def init_webpush(self, public_key: str = "", private_key: str = "",
                     email: str = "akatsuki@localhost"):
        self.webpush = WebPushNotifier(public_key, private_key, email)

    def notify_operation(self, operation_id: str, phase: str,
                          status: str, target: str = "") -> dict:
        results = {}
        try:
            results["telegram"] = self.telegram.send_operation_update(
                operation_id, phase, status, target
            )
        except Exception as e:
            results["telegram"] = False
            logger.error(f"Telegram notification failed: {e}")
        return results

    def notify_alert(self, title: str, message: str, severity: str = "info") -> dict:
        results = {}
        try:
            results["telegram"] = self.telegram.send_alert(title, message, severity)
        except Exception as e:
            results["telegram"] = False
            logger.error(f"Telegram alert failed: {e}")
        if self.webpush and self.webpush.is_enabled():
            try:
                results["webpush"] = self.webpush.send(title, message)
            except Exception as e:
                results["webpush"] = 0
                logger.error(f"WebPush alert failed: {e}")
        return results

    def broadcast(self, title: str, body: str) -> dict:
        results = {"telegram": False, "webpush": 0}
        try:
            results["telegram"] = self.telegram.send(f"*{title}*\n{body}")
        except Exception as e:
            logger.error(f"Telegram broadcast failed: {e}")
        if self.webpush and self.webpush.is_enabled():
            try:
                results["webpush"] = self.webpush.send(title, body)
            except Exception as e:
                logger.error(f"WebPush broadcast failed: {e}")
        return results


_notification_manager = NotificationManager()


def get_manager() -> NotificationManager:
    return _notification_manager