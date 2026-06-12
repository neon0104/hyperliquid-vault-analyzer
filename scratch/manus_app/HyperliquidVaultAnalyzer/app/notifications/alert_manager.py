"""
Alert manager: turns analysis results + thresholds into actual messages
sent through the configured NotificationProvider.

Implements the three triggers from the spec:
  (a) Recommended portfolio composition changed
  (b) Big gain/loss on any held or recommended vault (threshold configurable)
  (c) Periodic daily/weekly report
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from app.analysis.portfolio import diff_portfolios
from app.notifications.base import NotificationProvider


LOG = logging.getLogger(__name__)


def _fmt_pct(x: float) -> str:
    return f"{x * 100:+.2f}%"


def _short_addr(a: str) -> str:
    if not a:
        return ""
    return f"{a[:6]}...{a[-4:]}"


class AlertManager:
    def __init__(self, provider: NotificationProvider) -> None:
        self.provider = provider

    # (a) ---------------------------------------------------------------
    def alert_portfolio_change(
        self, prev: Optional[Dict[str, Any]], curr: Dict[str, Any]
    ) -> bool:
        diff = diff_portfolios(prev, curr)
        if not diff["changed"]:
            return False
        lines: List[str] = ["Recommended portfolio has changed."]
        if diff["added"]:
            lines.append("\n*Added:*")
            for h in diff["added"][:10]:
                lines.append(
                    f"- {h.get('name') or _short_addr(h['address'])}  "
                    f"({_short_addr(h['address'])}) weight {h['weight']*100:.1f}%"
                )
        if diff["removed"]:
            lines.append("\n*Removed:*")
            for h in diff["removed"][:10]:
                lines.append(
                    f"- {h.get('name') or _short_addr(h['address'])}  "
                    f"({_short_addr(h['address'])}) prev {h['weight']*100:.1f}%"
                )
        if diff["weight_changes"]:
            lines.append("\n*Weight changes:*")
            for w in diff["weight_changes"][:10]:
                lines.append(
                    f"- {w.get('name') or _short_addr(w['address'])}: "
                    f"{w['prev_weight']*100:.1f}% -> {w['curr_weight']*100:.1f}%"
                )
        return self.provider.send_message(
            "Portfolio Update", "\n".join(lines)
        )

    # (b) ---------------------------------------------------------------
    def alert_big_moves(
        self, holdings: List[Dict[str, Any]], threshold_pct: float
    ) -> int:
        """Send one message per vault with |return_all| >= threshold_pct/100.

        Returns the number of alerts sent.
        """
        sent = 0
        thr = abs(threshold_pct) / 100.0
        for h in holdings:
            r = h.get("return_all") or 0.0
            if abs(r) >= thr:
                direction = "GAIN" if r > 0 else "LOSS"
                title = f"Big {direction} - {h.get('name') or _short_addr(h.get('address',''))}"
                body = (
                    f"Vault: {_short_addr(h.get('address',''))}\n"
                    f"Return: {_fmt_pct(r)}\n"
                    f"MDD: {_fmt_pct(h.get('mdd',0.0))}\n"
                    f"Drawdown now: {_fmt_pct(h.get('drawdown_now',0.0))}\n"
                    f"Recovery factor: {h.get('recovery_factor',0.0):.2f}\n"
                    f"Weight in portfolio: {h.get('weight',0.0)*100:.1f}%"
                )
                if self.provider.send_message(title, body):
                    sent += 1
        return sent

    # (c) ---------------------------------------------------------------
    def send_periodic_report(
        self, portfolio: Dict[str, Any], period_label: str = "Daily"
    ) -> bool:
        holdings = portfolio.get("holdings", [])
        if not holdings:
            return self.provider.send_message(
                f"{period_label} Report",
                "No portfolio is currently recommended (no qualifying vaults).",
            )

        lines = [
            f"*{period_label} Hyperliquid Vault Portfolio Report*",
            f"Total holdings: {len(holdings)}",
            "",
            "*Top picks (by weight):*",
        ]
        top = sorted(holdings, key=lambda x: x.get("weight", 0.0), reverse=True)[:10]
        for h in top:
            lines.append(
                f"- [{h.get('leg','?').upper()}] "
                f"{h.get('name') or _short_addr(h.get('address',''))} "
                f"({_short_addr(h.get('address',''))})  "
                f"w={h.get('weight',0.0)*100:.1f}%  "
                f"ret={_fmt_pct(h.get('return_all',0.0))}  "
                f"mdd={_fmt_pct(h.get('mdd',0.0))}"
            )
        return self.provider.send_message(
            f"{period_label} Vault Report", "\n".join(lines)
        )
