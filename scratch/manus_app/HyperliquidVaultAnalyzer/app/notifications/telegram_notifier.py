"""
TelegramNotifier - 1st-class push channel for the desktop app.

The user is expected to:
  1) Talk to @BotFather on Telegram and create a bot to get a bot token.
  2) Start a conversation with the bot, then visit
     https://api.telegram.org/bot<TOKEN>/getUpdates to find the chat_id.
  3) Paste both into the app's Settings tab.
"""
from __future__ import annotations

import logging
from typing import Optional

import requests

from app.notifications.base import NotificationProvider


LOG = logging.getLogger(__name__)


class TelegramNotifier(NotificationProvider):
    API_URL = "https://api.telegram.org/bot{token}/sendMessage"

    def __init__(self, bot_token: str, chat_id: str, timeout: int = 15) -> None:
        self.bot_token = (bot_token or "").strip()
        self.chat_id = (chat_id or "").strip()
        self.timeout = timeout

    def is_configured(self) -> bool:
        return bool(self.bot_token) and bool(self.chat_id)

    def send_message(self, title: str, message: str) -> bool:
        if not self.is_configured():
            LOG.warning("TelegramNotifier not configured (missing token or chat_id)")
            return False
        text = f"*{_escape_md(title)}*\n\n{message}"
        url = self.API_URL.format(token=self.bot_token)
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }
        try:
            r = requests.post(url, json=payload, timeout=self.timeout)
            if r.status_code != 200:
                LOG.warning("Telegram returned %s: %s", r.status_code, r.text[:200])
                return False
            return True
        except Exception as e:  # noqa: BLE001
            LOG.exception("Telegram sendMessage failed: %s", e)
            return False


def _escape_md(s: Optional[str]) -> str:
    if not s:
        return ""
    # Minimal escape for legacy Markdown parse mode
    for ch in ("_", "*", "`", "["):
        s = s.replace(ch, "\\" + ch)
    return s
