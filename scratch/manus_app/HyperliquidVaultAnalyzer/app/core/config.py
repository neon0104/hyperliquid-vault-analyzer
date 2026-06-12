"""
Configuration manager for the Hyperliquid Vault Analyzer.

Persists user-tunable settings (data directory, telegram credentials,
notification provider, alert thresholds, schedule, etc.) to a JSON file.
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List


def _default_data_dir() -> str:
    """Return platform-appropriate default data directory.

    On Windows the requirement is to use D:\\ when available, falling back
    to the user home directory on non-Windows systems or when D:\\ is missing.
    """
    if sys.platform.startswith("win") and os.path.exists("D:\\"):
        return r"D:\HyperliquidVaultAnalyzer"
    return str(Path.home() / "HyperliquidVaultAnalyzer")


def _default_config_path() -> Path:
    """Where the config.json itself is stored.

    We store the config file alongside the application, in the user's home
    directory under a hidden folder, so that the app can locate it even
    before the data directory is configured.
    """
    base = Path.home() / ".hyperliquid_vault_analyzer"
    base.mkdir(parents=True, exist_ok=True)
    return base / "config.json"


@dataclass
class AppConfig:
    # Data storage
    data_dir: str = field(default_factory=_default_data_dir)

    # Collection (specification: ALWAYS fetch the TVL top-200 user vaults)
    top_n_vaults: int = 200            # fixed by product spec
    request_concurrency: int = 5       # conservative default to avoid 429s
    request_timeout_sec: int = 20
    request_retry_max: int = 4         # exponential backoff retries per call
    request_retry_base_sec: float = 0.6  # base sleep for exponential backoff

    # Strategy
    max_portfolio_size: int = 20
    stable_group_ratio: float = 0.5  # 50%
    recovery_group_ratio: float = 0.5  # 50%

    # ----- Protocol Vault exclusion (User Vaults only) -----
    # By default we exclude Hyperliquid's own protocol vaults (HLP and its
    # child strategies / liquidators). Users may extend or override these
    # lists by editing config.json directly.
    exclude_protocol_vaults: bool = True
    exclude_child_vaults: bool = True   # any vault whose relationship.type == 'child'
    exclude_leader_addresses: List[str] = field(
        default_factory=lambda: [
            # HLP master vault leader (operates HLP and its children)
            "0x677d831aef5328190852e24f13c46cac05f984e7",
        ]
    )
    exclude_vault_addresses: List[str] = field(
        default_factory=lambda: [
            # HLP master vault address (also a 'parent' relationship)
            "0xdfc24b077bc1425ad1dea75bcb6f8158e10df303",
            # HLP Strategy A / B and HLP Liquidator 2 (children of HLP)
            "0x010461c14e146ac35fe42271bdc1134ee31c703a",
            "0x31ca8395cf837de08b24da3f660e77761dfb974b",
            "0xb0a55f13d22f66e6d495ac98113841b2326e9540",
        ]
    )
    exclude_name_substrings: List[str] = field(
        default_factory=lambda: [
            "HLP",
            "Hyperliquidity Provider",
            "Liquidator",
        ]
    )

    # Notification
    notification_provider: str = "telegram"  # 'telegram' | 'expo' | 'fcm' | ...
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # Alert triggers
    alert_on_portfolio_change: bool = True
    big_move_threshold_pct: float = 10.0  # +/- % move triggers alert
    daily_report_enabled: bool = True
    daily_report_time: str = "09:00"  # HH:MM 24h
    weekly_report_enabled: bool = False
    weekly_report_day: str = "MON"  # MON..SUN

    # Scheduling
    collection_interval_minutes: int = 60

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppConfig":
        # Filter out unknown keys to avoid breaking on legacy config files.
        valid = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
        return cls(**valid)


class ConfigManager:
    """Loads/saves AppConfig from a JSON file on disk."""

    def __init__(self, path: Path | None = None) -> None:
        self.path: Path = path or _default_config_path()
        self.config: AppConfig = self._load()

    def _load(self) -> AppConfig:
        if not self.path.exists():
            cfg = AppConfig()
            self._save(cfg)
            return cfg
        try:
            with self.path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return AppConfig.from_dict(data)
        except Exception:
            # Corrupt config -> reset to default but keep a backup.
            try:
                backup = self.path.with_suffix(".bak.json")
                self.path.replace(backup)
            except Exception:
                pass
            cfg = AppConfig()
            self._save(cfg)
            return cfg

    def _save(self, cfg: AppConfig) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(cfg.to_dict(), f, indent=2, ensure_ascii=False)

    def save(self) -> None:
        self._save(self.config)

    def update(self, **kwargs: Any) -> None:
        for k, v in kwargs.items():
            if hasattr(self.config, k):
                setattr(self.config, k, v)
        self.save()

    def ensure_data_dir(self) -> Path:
        """Make sure the configured data directory and subfolders exist."""
        base = Path(self.config.data_dir)
        (base / "snapshots").mkdir(parents=True, exist_ok=True)
        (base / "logs").mkdir(parents=True, exist_ok=True)
        return base
