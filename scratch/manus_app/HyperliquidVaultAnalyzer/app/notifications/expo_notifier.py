"""
Placeholder Expo Push notifier for the future dedicated mobile app.

Once a dedicated mobile app (Expo/React Native) is built, the desktop
analyzer can switch to this provider by setting
`notification_provider = "expo"` in the app config and entering the
device's Expo push token.
"""
from __future__ import annotations

import logging
from typing import List

import requests

from app.notifications.base import NotificationProvider


LOG = logging.getLogger(__name__)


class ExpoPushNotifier(NotificationProvider):
    API_URL = "https://exp.host/--/api/v2/push/send"

    def __init__(self, token: str, timeout: int = 15) -> None:
        self.token = (token or "").strip()
        self.timeout = timeout

    def is_configured(self) -> bool:
        return self.token.startswith("ExponentPushToken[") and self.token.endswith("]")

    def send_message(self, title: str, message: str) -> bool:
        if not self.is_configured():
            LOG.warning("ExpoPushNotifier not configured (invalid token)")
            return False
        payload: List[dict] = [
            {"to": self.token, "title": title, "body": message, "sound": "default"}
        ]
        try:
            r = requests.post(self.API_URL, json=payload, timeout=self.timeout)
            if r.status_code != 200:
                LOG.warning("Expo push returned %s: %s", r.status_code, r.text[:200])
                return False
            return True
        except Exception as e:  # noqa: BLE001
            LOG.exception("Expo push failed: %s", e)
            return False
