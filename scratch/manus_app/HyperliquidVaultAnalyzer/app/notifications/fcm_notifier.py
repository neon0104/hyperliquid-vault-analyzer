"""
Placeholder Firebase Cloud Messaging notifier (legacy HTTP API).

Reserved for the future native mobile app. To enable, set
`notification_provider = "fcm"` and provide the FCM server key plus a
device registration token.
"""
from __future__ import annotations

import logging

import requests

from app.notifications.base import NotificationProvider


LOG = logging.getLogger(__name__)


class FCMNotifier(NotificationProvider):
    API_URL = "https://fcm.googleapis.com/fcm/send"

    def __init__(self, server_key: str, device_token: str, timeout: int = 15) -> None:
        self.server_key = (server_key or "").strip()
        self.device_token = (device_token or "").strip()
        self.timeout = timeout

    def is_configured(self) -> bool:
        return bool(self.server_key) and bool(self.device_token)

    def send_message(self, title: str, message: str) -> bool:
        if not self.is_configured():
            return False
        headers = {
            "Authorization": f"key={self.server_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "to": self.device_token,
            "notification": {"title": title, "body": message},
            "priority": "high",
        }
        try:
            r = requests.post(self.API_URL, json=payload, headers=headers, timeout=self.timeout)
            if r.status_code != 200:
                LOG.warning("FCM returned %s: %s", r.status_code, r.text[:200])
                return False
            return True
        except Exception as e:  # noqa: BLE001
            LOG.exception("FCM send failed: %s", e)
            return False
