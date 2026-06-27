import json
import logging
from pathlib import Path

logger = logging.getLogger("akatsuki.notifications.webpush")


class WebPushNotifier:
    def __init__(self, vapid_public_key: str = "", vapid_private_key: str = "",
                 vapid_claim_email: str = "akatsuki@localhost"):
        self.vapid_public_key = vapid_public_key
        self.vapid_private_key = vapid_private_key
        self.vapid_claim_email = vapid_claim_email
        self._subscriptions: list[dict] = []
        self._enabled = bool(vapid_public_key and vapid_private_key)
        self._store_path = Path("data") / "push_subscriptions.json"
        self._load()

    def _load(self):
        if self._store_path.exists():
            try:
                data = json.loads(self._store_path.read_text())
                self._subscriptions = data.get("subscriptions", [])
            except Exception:
                self._subscriptions = []

    def _save(self):
        self._store_path.parent.mkdir(parents=True, exist_ok=True)
        self._store_path.write_text(json.dumps({"subscriptions": self._subscriptions}))

    def is_enabled(self) -> bool:
        return self._enabled

    def subscribe(self, subscription: dict) -> bool:
        if subscription not in self._subscriptions:
            self._subscriptions.append(subscription)
            self._save()
        return True

    def unsubscribe(self, endpoint: str) -> bool:
        self._subscriptions = [s for s in self._subscriptions if s.get("endpoint") != endpoint]
        self._save()
        return True

    def send(self, title: str, body: str, icon: str = "", url: str = "") -> int:
        if not self._enabled:
            logger.info(f"[WebPush disabled] Would push: {title}")
            return 0
        from pywebpush import webpush, WebPushException
        sent = 0
        payload = json.dumps({
            "title": title,
            "body": body,
            "icon": icon or "https://akatsuki.local/icon.png",
            "data": {"url": url},
        })
        for sub in self._subscriptions[:]:
            try:
                webpush(
                    subscription_info=sub,
                    data=payload,
                    vapid_private_key=self.vapid_private_key,
                    vapid_claims={"sub": f"mailto:{self.vapid_claim_email}"},
                )
                sent += 1
            except WebPushException as e:
                if e.response and e.response.status_code == 410:
                    self._subscriptions.remove(sub)
                    self._save()
                logger.warning(f"Push failed: {e}")
        return sent