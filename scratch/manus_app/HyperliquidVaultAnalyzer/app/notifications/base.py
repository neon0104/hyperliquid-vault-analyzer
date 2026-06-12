"""
Pluggable notification provider system.

Adding a new channel later (e.g., a dedicated mobile app push via Expo or
FCM) is just a matter of subclassing NotificationProvider and registering
the implementation in `build_provider`.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class NotificationProvider(ABC):
    """Abstract base for all push channels."""

    @abstractmethod
    def send_message(self, title: str, message: str) -> bool:
        """Send a notification. Return True on success."""

    def is_configured(self) -> bool:
        """Whether the provider has all credentials it needs."""
        return True


def build_provider(config_dict: Dict[str, Any]) -> NotificationProvider:
    """Factory: instantiate the right provider from a config dict.

    Expected keys:
      - notification_provider : 'telegram' (initial), 'expo', 'fcm', ...
      - telegram_bot_token, telegram_chat_id
      - (future) expo_push_token, fcm_server_key, fcm_token, ...
    """
    name = (config_dict.get("notification_provider") or "telegram").lower()

    if name == "telegram":
        from app.notifications.telegram_notifier import TelegramNotifier

        return TelegramNotifier(
            bot_token=config_dict.get("telegram_bot_token", ""),
            chat_id=config_dict.get("telegram_chat_id", ""),
        )

    if name in {"expo", "expo_push", "expo-push"}:
        # Placeholder: future implementation lives in app/notifications/expo_notifier.py
        from app.notifications.expo_notifier import ExpoPushNotifier  # type: ignore

        return ExpoPushNotifier(token=config_dict.get("expo_push_token", ""))

    if name in {"fcm", "firebase"}:
        from app.notifications.fcm_notifier import FCMNotifier  # type: ignore

        return FCMNotifier(
            server_key=config_dict.get("fcm_server_key", ""),
            device_token=config_dict.get("fcm_token", ""),
        )

    raise ValueError(f"Unknown notification provider: {name}")
