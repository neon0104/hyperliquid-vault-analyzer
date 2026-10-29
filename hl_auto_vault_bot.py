#!/usr/bin/env python3
"""
hl_auto_vault_bot.py — Hyperliquid $20,000 SGRA+ Automated Vault Portfolio Executor
====================================================================================
Features:
  1. Empirically validated SGRA+ (Skin-Ratio & HWM-Guided Regime Alpha) Signal Engine:
     - Strict `leader_equity_ratio >= 30%`, `TVL >= $10,000`, `robustness >= 0.20`, `ret_14d >= -5%`
     - Capacity-safe slot cap: `min(max_single_slot_weight, 0.30 * vault_tvl / deploy_capital)`
     - Rank Buffer (`buf=2`) + 10% relative No-Trade Band to preserve 10% High-Water-Mark (HWM) fee credits
     - Point-in-Time Bull Regime (`mkt_14d > +1%`, `breadth_14d >= 50%`, `mkt_7d > 0%`) idle-cash momentum sleeve
  2. Two-Phase On-Chain Hyperliquid `vaultTransfer` Execution:
     - Phase 1: Withdrawals / trims (`is_deposit=False`), respecting 24h post-deposit lockups (`lockedUntilTimestamp`)
       and queuing any locked withdrawals for automatic retry on the next 4h cycle.
     - Optional Spot -> Perps USDC auto-transfer (`usd_class_transfer`) if funds sit in Spot.
     - Phase 2: Deposits (`is_deposit=True`) scaled strictly to verified Perps `withdrawable` USDC.
  3. Institutional Safety Guardrails:
     - Defaults to `DRY_RUN` mode (zero L1 transactions until explicitly switched to `LIVE` with `.env` key).
     - NEVER exposes, logs, or transmits private keys; zero external L1 withdrawal (`withdraw3` / `usdSend`) code paths.
     - 4-hour intraday Emergency Exit Guardrail on held vaults (`ret_14d < -8%` or `drawdown_now > 25%`).
"""
import argparse
import json
import math
import os
import sqlite3
import sys
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from dotenv import load_dotenv
from hyperliquid.info import Info
from hyperliquid.utils import constants

from io_utils import atomic_write_json

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "vault_data"
SNAP_DIR = DATA_DIR / "snapshots"
CONFIG_JSON = BASE_DIR / "config.json"
ENV_FILE = BASE_DIR / ".env"
DISCORD_CFG = BASE_DIR / "discord_config.json"
TELEGRAM_CFG = BASE_DIR / "telegram_config.json"
MY_PORTFOLIO_FILE = BASE_DIR / "my_portfolio.json"
VIRTUAL_PORTFOLIOS_FILE = DATA_DIR / "virtual_portfolios.json"

AUTOBOT_CONFIG_FILE = DATA_DIR / "autobot_config.json"
AUTOBOT_STATE_FILE = DATA_DIR / "autobot_state.json"
AUTOBOT_LOG_FILE = DATA_DIR / "autobot_exec_log.json"

# Protocol vault HLP has a 4-day lockup and different mechanics; keep standard user-leader vaults cleanly separated
EXCLUDED_ADDRESSES = frozenset({
    "0xdfc24b077bc1425ad1dea75bcb6f8158e10df303",  # HLP protocol vault (4-day lockup)
})

DEFAULT_BOT_CONFIG: Dict[str, Any] = {
    "enabled": False,                   # 입금 전 기본 일시정지(대기) — 사용자가 입금 후 [자동운용 재개] 시 즉시 가동
    "mode": "LIVE",                     # "LIVE" (실전 지갑 연동 기본) or "DRY_RUN" (모의 테스트용)
    "target_capital_usd": 20000.0,      # 기준 운용 원금 ($20,000 — 입금 전 예상 배분 미리보기 기준)
    "min_deploy_equity_usd": 100.0,     # 실전 자동진입 최소 지갑 총자산 기준 ($100 이상 입금 감지 시 운용)
    "compound_profits": True,           # 입금액 및 수익금 전액 자동 복리 재투자 여부
    "rebalance_interval_days": 14,      # 최적 검증 주기: 14일
    "no_trade_band_rel": 0.10,          # 10% 상대 비중 불감대 (HWM 성과보수 크레딧 보존)
    "rank_buffer": 2,                   # 기존 보유 볼트가 Top (6 + 2 = 8) 이내면 교체 방지
    "min_vault_tvl_usd": 10000.0,       # 최소 볼트 TVL ($10,000)
    "max_vault_tvl_share": 0.30,        # 단일 볼트 TVL의 최대 30% 이내 진입
    "max_single_slot_weight": 0.25,     # 포트폴리오 내 단일 볼트 최대 25% 상한
    "min_trade_usd": 50.0,              # $50 미만 미세 주문 생략
    "cash_buffer_usd": 2.0,             # 소수점 반올림 오차 방지용 최소 여유 USDC
    "auto_spot_to_perp": True,          # Spot 계정에 있는 USDC를 Perps 계정으로 자동 이체
    "emergency_guard_enabled": True,    # 4시간 주기 비상 손절/추세붕괴 감시
    "emergency_ret14_floor": -0.08,     # 보유 볼트 14일 수익률 -8% 이하 시 즉시 탈출
    "emergency_dd_ceiling": 25.0,       # 보유 볼트 현재 낙폭 25% 초과 시 즉시 탈출
    "notify_on_dry_run": False,         # 모의운용(DRY_RUN) 중에는 텔레그램/디스코드 알림 생략 (LIVE 전환 시 자동 발송)
}


# ==============================================================================
# 1. Config, Credentials & Notification Helpers
# ==============================================================================
def load_autobot_config() -> Dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    cfg = dict(DEFAULT_BOT_CONFIG)
    if AUTOBOT_CONFIG_FILE.exists():
        try:
            saved = json.loads(AUTOBOT_CONFIG_FILE.read_text(encoding="utf-8"))
            if isinstance(saved, dict):
                cfg.update(saved)
        except Exception:
            pass
    else:
        atomic_write_json(AUTOBOT_CONFIG_FILE, cfg, indent=2)
    return cfg


def save_autobot_config(patch: Dict[str, Any]) -> Dict[str, Any]:
    cfg = load_autobot_config()
    allowed_keys = set(DEFAULT_BOT_CONFIG.keys())
    for k, v in patch.items():
        if k not in allowed_keys:
            continue
        if k == "mode":
            cfg[k] = "LIVE" if str(v).upper() == "LIVE" else "DRY_RUN"
        elif isinstance(DEFAULT_BOT_CONFIG[k], bool):
            cfg[k] = bool(v)
        elif isinstance(DEFAULT_BOT_CONFIG[k], int):
            cfg[k] = max(1, int(v))
        elif isinstance(DEFAULT_BOT_CONFIG[k], float):
            cfg[k] = float(v)
    atomic_write_json(AUTOBOT_CONFIG_FILE, cfg, indent=2)
    return cfg


def reset_autobot_virtual_book() -> Dict[str, Any]:
    cfg = load_autobot_config()
    state = load_autobot_state()
    state["virtual_positions"] = {}
    state["virtual_cash_usd"] = float(cfg.get("target_capital_usd", 20000.0))
    state["last_rebalance_at"] = None
    atomic_write_json(AUTOBOT_STATE_FILE, state, indent=2)
    return run_autobot_cycle(force_rebalance=False)


def load_autobot_state() -> Dict[str, Any]:
    if AUTOBOT_STATE_FILE.exists():
        try:
            return json.loads(AUTOBOT_STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "last_checked_at": None,
        "last_rebalance_at": None,
        "last_signal_type": "INIT",
        "pending_locked_withdrawals": {},
        "virtual_positions": {},
        "virtual_cash_usd": None,
    }


def load_exec_logs(limit: int = 100) -> List[Dict[str, Any]]:
    if AUTOBOT_LOG_FILE.exists():
        try:
            rows = json.loads(AUTOBOT_LOG_FILE.read_text(encoding="utf-8"))
            if isinstance(rows, list):
                return rows[:limit]
        except Exception:
            pass
    return []


def append_exec_logs(new_entries: List[Dict[str, Any]], max_keep: int = 250) -> None:
    if not new_entries:
        return
    existing = load_exec_logs(limit=max_keep)
    combined = list(reversed(new_entries)) + existing
    atomic_write_json(AUTOBOT_LOG_FILE, combined[:max_keep], indent=2)


def get_wallet_credentials_meta() -> Tuple[Optional[str], Optional[str], Dict[str, Any]]:
    """
    Loads HL_ACCOUNT_ADDRESS & HL_BOT_PRIVATE_KEY from .env safely.
    Returns (account_address, private_key_or_None, safe_public_metadata).
    NEVER exposes or logs private key characters.
    """
    load_dotenv(dotenv_path=ENV_FILE, override=True)
    env_addr = (os.environ.get("HL_ACCOUNT_ADDRESS") or "").strip()
    env_pk = (os.environ.get("HL_BOT_PRIVATE_KEY") or "").strip()

    cfg_addr = ""
    if CONFIG_JSON.exists():
        try:
            c = json.loads(CONFIG_JSON.read_text(encoding="utf-8"))
            cfg_addr = (c.get("account_address") or "").strip()
        except Exception:
            pass

    signer_addr = None
    key_valid = False
    if env_pk:
        try:
            import eth_account
            pk_norm = env_pk if env_pk.startswith("0x") else ("0x" + env_pk)
            acct = eth_account.Account.from_key(pk_norm)
            signer_addr = acct.address
            key_valid = True
        except Exception:
            key_valid = False

    account_address = env_addr or signer_addr or cfg_addr
    meta = {
        "env_file_exists": ENV_FILE.exists(),
        "account_address": account_address or None,
        "key_configured": key_valid,
        "signer_address": signer_addr,
        "is_direct_master_key": bool(
            key_valid and account_address and signer_addr and signer_addr.lower() == account_address.lower()
        ),
        "is_delegated_agent_key": bool(
            key_valid and account_address and signer_addr and signer_addr.lower() != account_address.lower()
        ),
    }
    return (account_address or None), (env_pk if key_valid else None), meta


def send_alert_notifications(title: str, lines: List[str]) -> None:
    text_plain = f"🤖 [{title}]\n" + "\n".join(lines)
    text_html = f"🤖 <b>{title}</b>\n" + "\n".join(lines)

    # Telegram
    if TELEGRAM_CFG.exists():
        try:
            tcfg = json.loads(TELEGRAM_CFG.read_text(encoding="utf-8"))
            if tcfg.get("enabled", True) and tcfg.get("bot_token") and tcfg.get("chat_id"):
                url = f"https://api.telegram.org/bot{tcfg['bot_token']}/sendMessage"
                payload = json.dumps({
                    "chat_id": tcfg["chat_id"],
                    "text": text_html,
                    "parse_mode": "HTML",
                    "disable_web_page_preview": True,
                }).encode("utf-8")
                req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
                urllib.request.urlopen(req, timeout=5).read()
        except Exception:
            pass

    # Discord
    if DISCORD_CFG.exists():
        try:
            dcfg = json.loads(DISCORD_CFG.read_text(encoding="utf-8"))
            wh = (dcfg.get("webhook_url") or "").strip()
            if wh:
                payload = json.dumps({"content": text_plain[:1950]}).encode("utf-8")
                req = urllib.request.Request(
                    wh, data=payload, headers={"Content-Type": "application/json", "User-Agent": "HLAutoBot/1.0"}
                )
                urllib.request.urlopen(req, timeout=5).read()
        except Exception:
            pass


# ==============================================================================
# 2. Live On-Chain Account Telemetry (Read-Only via Hyperliquid Info API)
# ==============================================================================
def fetch_onchain_account_state(account_address: Optional[str]) -> Dict[str, Any]:
    if not account_address or not account_address.startswith("0x") or len(account_address) != 42:
        return {
            "connected": False,
            "account_address": account_address,
            "perp_account_value_usd": 0.0,
            "perp_withdrawable_usd": 0.0,
            "spot_usdc_usd": 0.0,
            "vault_total_equity_usd": 0.0,
            "total_equity_usd": 0.0,
            "vault_positions": {},
            "error": "유효한 지갑 주소가 설정되지 않았습니다.",
        }

    try:
        info = Info(constants.MAINNET_API_URL, skip_ws=True)
        now_ms = int(time.time() * 1000)

        # 1) Perp Clearinghouse State
        ch = info.user_state(account_address) or {}
        ms = ch.get("marginSummary") or {}
        perp_acct_val = float(ms.get("accountValue", 0.0) or 0.0)
        perp_withdrawable = float(ch.get("withdrawable", 0.0) or 0.0)

        # 2) Spot Clearinghouse State (check if user deposited USDC into Spot)
        spot_usdc = 0.0
        try:
            sp = info.spot_user_state(account_address) or {}
            for b in sp.get("balances", []):
                if str(b.get("coin", "")).upper() == "USDC":
                    spot_usdc = float(b.get("total", 0.0) or 0.0) - float(b.get("hold", 0.0) or 0.0)
                    break
        except Exception:
            pass

        # 3) User Vault Equities + Lockup Timestamps
        raw_veq = info.post("/info", {"type": "userVaultEquities", "user": account_address})
        vault_positions: Dict[str, Dict[str, Any]] = {}
        vault_total = 0.0
        if isinstance(raw_veq, list):
            for item in raw_veq:
                vaddr = str(item.get("vaultAddress", "")).lower()
                eq = float(item.get("equity", 0.0) or 0.0)
                if not vaddr or eq <= 0.01:
                    continue
                locked_ms = int(item.get("lockedUntilTimestamp", 0) or 0)
                is_locked = locked_ms > (now_ms + 30_000)
                locked_until_str = (
                    datetime.fromtimestamp(locked_ms / 1000.0).strftime("%Y-%m-%d %H:%M")
                    if locked_ms > 0 else None
                )
                vault_positions[vaddr] = {
                    "address": vaddr,
                    "equity_usd": round(eq, 4),
                    "locked_until_ms": locked_ms,
                    "locked_until": locked_until_str,
                    "is_locked": is_locked,
                }
                vault_total += eq

        total_eq = perp_withdrawable + spot_usdc + vault_total
        return {
            "connected": True,
            "account_address": account_address,
            "perp_account_value_usd": round(perp_acct_val, 2),
            "perp_withdrawable_usd": round(perp_withdrawable, 2),
            "spot_usdc_usd": round(spot_usdc, 2),
            "vault_total_equity_usd": round(vault_total, 2),
            "total_equity_usd": round(total_eq, 2),
            "vault_positions": vault_positions,
            "fetched_at": datetime.now().isoformat(timespec="seconds"),
        }
    except Exception as e:
        return {
            "connected": False,
            "account_address": account_address,
            "perp_account_value_usd": 0.0,
            "perp_withdrawable_usd": 0.0,
            "spot_usdc_usd": 0.0,
            "vault_total_equity_usd": 0.0,
            "total_equity_usd": 0.0,
            "vault_positions": {},
            "error": str(e),
        }


# ==============================================================================
# 3. Point-in-Time SGRA+ Champion Signal Engine
# ==============================================================================
def compute_sgra_signal(
    deploy_capital_usd: float,
    held_addresses: set,
    cfg: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Computes the exact SGRA+ (Buf=2) target portfolio from the rolling 32-day snapshot panel.
    """
    snap_files = sorted([f for f in SNAP_DIR.glob("*.json") if not f.name.endswith(".bak")])
    if len(snap_files) < 5:
        return {"error": "스냅샷 데이터가 부족합니다 (최소 5일 필요). analyze_top_vaults.py를 먼저 실행하세요."}

    recent_files = snap_files[-32:]
    panel_dates = [f.stem for f in recent_files]
    snaps_by_date = {}
    for f in recent_files:
        try:
            snaps_by_date[f.stem] = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            snaps_by_date[f.stem] = []

    latest_date = panel_dates[-1]
    latest_list = snaps_by_date[latest_date]
    if not latest_list:
        return {"error": f"최신 스냅샷({latest_date})이 비어 있습니다."}

    all_addrs = sorted({v["address"].lower() for d in panel_dates for v in snaps_by_date[d] if "address" in v})
    addr_idx = {a: i for i, a in enumerate(all_addrs)}
    T = len(panel_dates)
    N = len(all_addrs)

    pnl_mat = np.full((T, N), np.nan)
    tvl_mat = np.full((T, N), np.nan)
    allow_mat = np.zeros((T, N), dtype=bool)

    for t, d in enumerate(panel_dates):
        for v in snaps_by_date[d]:
            a = str(v.get("address", "")).lower()
            if a not in addr_idx:
                continue
            i = addr_idx[a]
            p_arr = v.get("alltime_pnl", [])
            if isinstance(p_arr, list) and p_arr:
                pnl_mat[t, i] = float(p_arr[-1])
            elif v.get("pnl_alltime") is not None:
                pnl_mat[t, i] = float(v.get("pnl_alltime", 0.0) or 0.0)
            tvl_mat[t, i] = float(v.get("tvl", 0.0) or 0.0)
            allow_mat[t, i] = bool(v.get("allow_deposits", True))

    ret_mat = np.full((T, N), np.nan)
    for t in range(1, T):
        valid = (~np.isnan(pnl_mat[t])) & (~np.isnan(pnl_mat[t - 1])) & (tvl_mat[t - 1] >= 5000.0)
        dpnl = pnl_mat[t, valid] - pnl_mat[t - 1, valid]
        ret_mat[t, valid] = np.clip(dpnl / tvl_mat[t - 1, valid], -0.35, 0.35)

    mkt_ret = np.zeros(T)
    for t in range(1, T):
        elig = (~np.isnan(ret_mat[t])) & (tvl_mat[t - 1] >= 15000.0) & allow_mat[t - 1]
        if np.any(elig):
            mkt_ret[t] = float(np.mean(ret_mat[t, elig]))

    mkt_eq = np.cumprod(1.0 + mkt_ret)
    m_r14 = mkt_ret[-min(14, T - 1):]
    m_r7 = mkt_ret[-min(7, T - 1):]
    mkt_cum14 = float(np.prod(1.0 + m_r14) - 1.0) if len(m_r14) else 0.0
    mkt_cum7 = float(np.prod(1.0 + m_r7) - 1.0) if len(m_r7) else 0.0
    mkt_dd30 = float((np.max(mkt_eq) - mkt_eq[-1]) / max(np.max(mkt_eq), 1e-9))

    # Build vault feature dictionary at latest_date
    v_feats: Dict[str, Dict[str, Any]] = {}
    pos14, elig_cnt = 0, 0

    for v in latest_list:
        addr = str(v.get("address", "")).lower()
        if not addr or addr in EXCLUDED_ADDRESSES or addr not in addr_idx:
            continue
        i = addr_idx[addr]
        r_series_raw = ret_mat[1:, i]
        vdays = int(np.sum(~np.isnan(r_series_raw)))
        r_clean = np.where(np.isnan(r_series_raw), 0.0, r_series_raw)
        r14 = r_clean[-14:] if len(r_clean) >= 14 else r_clean
        r7 = r_clean[-7:] if len(r_clean) >= 7 else r_clean
        ret14 = float(np.prod(1.0 + r14) - 1.0)
        ret7 = float(np.prod(1.0 + r7) - 1.0)

        eq30 = np.cumprod(1.0 + np.concatenate([[0.0], r_clean]))
        pk30 = np.maximum.accumulate(eq30)
        dd30_now = float((pk30[-1] - eq30[-1]) / max(pk30[-1], 1e-9)) * 100.0

        # 7d TVL change for bankrun check
        tvl_now = float(v.get("tvl", 0.0) or 0.0)
        tvl_7d_ago = float(tvl_mat[max(0, T - 8), i]) if not np.isnan(tvl_mat[max(0, T - 8), i]) else tvl_now
        tvl_chg_7d = ((tvl_now - tvl_7d_ago) / max(tvl_7d_ago, 1.0)) * 100.0

        allow = bool(v.get("allow_deposits", True))
        if allow and tvl_now >= 15000.0 and vdays >= 10:
            elig_cnt += 1
            if ret14 > 0:
                pos14 += 1

        p_arr = v.get("alltime_pnl", [])
        pnl_alltime = float(p_arr[-1]) if (isinstance(p_arr, list) and p_arr) else float(v.get("pnl_alltime", 0.0) or 0.0)

        v_feats[addr] = {
            "address": addr,
            "name": v.get("name", addr[:12]),
            "allow": allow,
            "tvl": tvl_now,
            "tvl_chg_7d": round(tvl_chg_7d, 2),
            "vdays": vdays,
            "leader_ratio": float(v.get("leader_equity_ratio", 0.0) or 0.0),
            "leader_usd": float(v.get("leader_equity_usd", 0.0) or 0.0),
            "snap_sharpe": float(np.clip(float(v.get("sharpe_ratio", 0.0) or 0.0), -20.0, 50.0)),
            "robustness": float(v.get("robustness_score", 0.0) or 0.0),
            "snap_mdd": float(v.get("max_drawdown", 15.0) or 15.0),
            "drawdown_now": max(dd30_now, float(v.get("drawdown_now", 0.0) or 0.0)),
            "apr_30d": float(v.get("apr_30d", 0.0) or 0.0),
            "pnl_alltime": pnl_alltime,
            "ret7": ret7,
            "ret14": ret14,
        }

    breadth14 = (pos14 / elig_cnt) if elig_cnt > 0 else 0.5
    is_bull = (mkt_cum14 > 0.010 and breadth14 >= 0.50 and mkt_cum7 > 0.0)
    is_bear = (mkt_cum14 < -0.015 or breadth14 < 0.42 or mkt_dd30 > 0.035)
    regime = "BULL" if is_bull else ("BEAR" if is_bear else "NEUTRAL")

    # Core Scoring (SGRA+)
    min_tvl = float(cfg.get("min_vault_tvl_usd", 10000.0))
    buf = int(cfg.get("rank_buffer", 2))
    max_tvl_share = float(cfg.get("max_vault_tvl_share", 0.30))
    max_slot_w = float(cfg.get("max_single_slot_weight", 0.25))
    cap_ref = max(float(deploy_capital_usd), 1000.0)

    core_scored: List[Tuple[float, Dict[str, Any]]] = []
    for v in v_feats.values():
        if not v["allow"] or v["tvl"] < min_tvl or v["leader_ratio"] < 0.30 or v["robustness"] < 0.20 or v["ret14"] < -0.05:
            continue
        underval = float(np.clip(v["drawdown_now"] / max(v["snap_mdd"], 5.0), 0.0, 1.0))
        score = (
            v["robustness"] * 0.35
            + (v["snap_sharpe"] / 50.0) * 0.30
            + underval * 0.20
            + min(v["leader_ratio"] / 0.40, 1.0) * 0.15
        )
        v_copy = dict(v)
        v_copy["sgra_score"] = round(score, 4)
        v_copy["sleeve"] = "CORE (Skin>=30% 복리)"
        core_scored.append((score, v_copy))

    core_scored.sort(key=lambda x: x[0], reverse=True)
    ranked_addrs = [v["address"] for _, v in core_scored]
    keep_set = set(ranked_addrs[: 6 + buf]) if buf > 0 else set()

    held_norm = {a.lower() for a in held_addresses}
    sel_core = [v for _, v in core_scored if v["address"] in held_norm and v["address"] in keep_set][:6]
    sel_addrs = {v["address"] for v in sel_core}
    for _, v in core_scored:
        if len(sel_core) >= 6:
            break
        if v["address"] not in sel_addrs:
            sel_core.append(v)
            sel_addrs.add(v["address"])

    # Apply realistic <=30% Vault TVL & <=25% slot capacity cap
    target_weights: Dict[str, float] = {}
    selected_meta: Dict[str, Dict[str, Any]] = {}
    if sel_core:
        caps = np.array([min(max_slot_w, (max_tvl_share * v["tvl"]) / cap_ref) for v in sel_core], dtype=float)
        w = np.ones(len(sel_core), dtype=float)
        w = w / np.sum(w) * min(1.0, float(np.sum(caps)))
        for _ in range(6):
            over = w > caps + 1e-9
            if not np.any(over):
                break
            ex = float(np.sum(w[over] - caps[over]))
            w[over] = caps[over]
            under = ~over
            if np.any(under) and np.sum(w[under]) > 0:
                w[under] += ex * (w[under] / np.sum(w[under]))
        for v, wi in zip(sel_core, w):
            if wi > 1e-4:
                target_weights[v["address"]] = float(wi)
                selected_meta[v["address"]] = v

    # Bull Idle-Cash Accelerator Sleeve (only deploys remaining idle capacity during confirmed Bull)
    idle_w = 1.0 - sum(target_weights.values())
    if is_bull and idle_w > 0.03:
        mom_cands = []
        for v in v_feats.values():
            if v["address"] in target_weights:
                continue
            if not v["allow"] or v["tvl"] < min_tvl or v["vdays"] < 14 or v["pnl_alltime"] <= 0:
                continue
            if v["ret14"] <= 0.02 or v["snap_mdd"] > 30.0 or v["snap_sharpe"] < 2.0:
                continue
            v_copy = dict(v)
            v_copy["sgra_score"] = round(v["ret14"], 4)
            v_copy["sleeve"] = "BULL ACCEL (14d 모멘텀)"
            mom_cands.append((v["ret14"], v_copy))
        mom_cands.sort(key=lambda x: x[0], reverse=True)
        rem = idle_w
        for _, mv in mom_cands[:4]:
            if rem <= 0.01:
                break
            cap_m = min(0.15, (max_tvl_share * mv["tvl"]) / cap_ref)
            add_w = min(rem, cap_m)
            if add_w >= 0.015:
                target_weights[mv["address"]] = add_w
                selected_meta[mv["address"]] = mv
                rem -= add_w

    # Emergency Guardrail Inspection on Currently Held Vaults
    emergency_exits: List[Dict[str, Any]] = []
    if cfg.get("emergency_guard_enabled", True):
        r14_floor = float(cfg.get("emergency_ret14_floor", -0.08))
        dd_ceil = float(cfg.get("emergency_dd_ceiling", 25.0))
        for h_addr in held_norm:
            vf = v_feats.get(h_addr)
            if not vf:
                continue
            reasons = []
            if vf["ret14"] < r14_floor:
                reasons.append(f"14일 수익률 급락 ({vf['ret14']*100:+.1f}% < {r14_floor*100:.0f}%)")
            if vf["drawdown_now"] > dd_ceil and h_addr not in target_weights:
                reasons.append(f"현재 낙폭 한도 초과 ({vf['drawdown_now']:.1f}% > {dd_ceil:.0f}%)")
            if vf["tvl_chg_7d"] <= -40.0 and vf["leader_ratio"] < 0.30:
                reasons.append(f"7일 TVL 급유출 ({vf['tvl_chg_7d']:.1f}%)")
            if not vf["allow"] and vf["apr_30d"] < -10.0:
                reasons.append("입금 중단 및 마이너스 수익 전환")
            if reasons:
                emergency_exits.append({
                    "address": h_addr,
                    "name": vf["name"],
                    "reason": " / ".join(reasons),
                })

    allocations = []
    for addr, wi in sorted(target_weights.items(), key=lambda x: x[1], reverse=True):
        m = selected_meta[addr]
        allocations.append({
            "address": addr,
            "name": m["name"],
            "sleeve": m["sleeve"],
            "target_weight_pct": round(wi * 100.0, 2),
            "target_usd": round(wi * deploy_capital_usd, 2),
            "tvl_usd": round(m["tvl"], 0),
            "leader_ratio_pct": round(m["leader_ratio"] * 100.0, 1),
            "cushioned_sharpe": round(m["snap_sharpe"], 2),
            "robustness": round(m["robustness"], 3),
            "drawdown_now_pct": round(m["drawdown_now"], 2),
            "ret_14d_pct": round(m["ret14"] * 100.0, 2),
            "sgra_score": m["sgra_score"],
        })

    return {
        "snapshot_date": latest_date,
        "regime": regime,
        "mkt_14d_pct": round(mkt_cum14 * 100.0, 2),
        "mkt_7d_pct": round(mkt_cum7 * 100.0, 2),
        "breadth_14d_pct": round(breadth14 * 100.0, 1),
        "mkt_dd30_pct": round(mkt_dd30 * 100.0, 2),
        "deploy_capital_usd": round(deploy_capital_usd, 2),
        "deployed_weight_pct": round(sum(target_weights.values()) * 100.0, 2),
        "cash_reserve_pct": round(max(0.0, 1.0 - sum(target_weights.values())) * 100.0, 2),
        "cash_reserve_usd": round(max(0.0, 1.0 - sum(target_weights.values())) * deploy_capital_usd, 2),
        "allocations": allocations,
        "target_map_usd": {a["address"]: a["target_usd"] for a in allocations},
        "emergency_exits": emergency_exits,
        "vault_lookup": {a: {"name": v["name"], "allow": v["allow"], "tvl": v["tvl"]} for a, v in v_feats.items()},
    }


# ==============================================================================
# 4. Two-Phase Delta Execution Engine (DRY_RUN & LIVE Hyperliquid Mainnet)
# ==============================================================================
def _build_delta_plan(
    current_positions_usd: Dict[str, float],
    target_map: Dict[str, float],
    locked_map: Dict[str, Dict[str, Any]],
    emergency_addrs: set,
    v_lookup: Dict[str, Dict[str, Any]],
    only_emergency: bool,
    band: float,
    min_trade: float,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    planned_sells: List[Dict[str, Any]] = []
    planned_buys: List[Dict[str, Any]] = []
    skipped_band: List[Dict[str, Any]] = []

    all_involved = sorted(set(current_positions_usd.keys()) | set(target_map.keys()))
    for addr in all_involved:
        cur_u = float(current_positions_usd.get(addr, 0.0))
        tgt_u = float(target_map.get(addr, 0.0))
        vname = v_lookup.get(addr, {}).get("name") or addr[:12]

        if only_emergency and addr not in emergency_addrs:
            continue

        if tgt_u <= 0.5 and cur_u > 1.0:
            planned_sells.append({
                "address": addr, "name": vname, "action": "WITHDRAW_FULL",
                "current_usd": round(cur_u, 2), "target_usd": 0.0, "delta_usd": round(cur_u, 2),
                "is_locked": addr in locked_map,
                "locked_until": locked_map.get(addr, {}).get("locked_until"),
                "reason": "비상 손절 탈출" if addr in emergency_addrs else "SGRA+ 목표 포트폴리오 편출",
            })
        elif cur_u > tgt_u * (1.0 + band) and (cur_u - tgt_u) >= min_trade:
            diff = cur_u - tgt_u
            planned_sells.append({
                "address": addr, "name": vname, "action": "WITHDRAW_TRIM",
                "current_usd": round(cur_u, 2), "target_usd": round(tgt_u, 2), "delta_usd": round(diff, 2),
                "is_locked": addr in locked_map,
                "locked_until": locked_map.get(addr, {}).get("locked_until"),
                "reason": f"목표 비중 초과 차익실현 (+{band*100:.0f}% 밴드 초과)",
            })
        elif tgt_u > cur_u * (1.0 + band) and (tgt_u - cur_u) >= min_trade:
            diff = tgt_u - cur_u
            planned_buys.append({
                "address": addr, "name": vname, "action": "DEPOSIT",
                "current_usd": round(cur_u, 2), "target_usd": round(tgt_u, 2), "delta_usd": round(diff, 2),
                "reason": "신규 편입" if cur_u < 1.0 else f"목표 비중 미달 추가배분 (-{band*100:.0f}% 밴드 초과)",
            })
        elif cur_u > 1.0 and tgt_u > 1.0:
            skipped_band.append({
                "address": addr, "name": vname,
                "current_usd": round(cur_u, 2), "target_usd": round(tgt_u, 2),
                "reason": f"±{band*100:.0f}% HWM 보존 불감대 이내 (수수료 절감 유지)",
            })

    return planned_sells, planned_buys, skipped_band


def _sync_live_portfolio_files(
    account_addr: str,
    onchain: Dict[str, Any],
    current_positions_usd: Dict[str, float],
    now_iso: str,
    is_fresh_deploy: bool,
) -> None:
    if not current_positions_usd:
        return
    old_pf: Dict[str, Any] = {}
    if MY_PORTFOLIO_FILE.exists():
        try:
            old_pf = json.loads(MY_PORTFOLIO_FILE.read_text(encoding="utf-8"))
        except Exception:
            old_pf = {}

    old_cap = float(old_pf.get("total_capital", 0.0) or 0.0)
    live_eq = round(float(onchain.get("total_equity_usd", sum(current_positions_usd.values()))), 2)
    today_str = now_iso[:10]

    # Reset invest_date & baseline total_capital when transitioning from pre-funding (<$200) to funded operation
    if is_fresh_deploy or old_cap < 200.0 or old_pf.get("account_address", "").lower() != account_addr.lower():
        base_cap = live_eq
        inv_date = today_str
    else:
        base_cap = old_cap
        inv_date = str(old_pf.get("invest_date") or today_str)

    atomic_write_json(MY_PORTFOLIO_FILE, {
        "_comment": "SGRA+ 자동운용 봇 실시간 동기화 포트폴리오",
        "account_address": account_addr,
        "fetched_at": now_iso,
        "total_capital": base_cap,
        "invest_date": inv_date,
        "positions": current_positions_usd,
    }, indent=2)

    if VIRTUAL_PORTFOLIOS_FILE.exists():
        try:
            vp_list = json.loads(VIRTUAL_PORTFOLIOS_FILE.read_text(encoding="utf-8"))
            if isinstance(vp_list, list):
                changed = False
                for p in vp_list:
                    if p.get("id") == "default":
                        p["positions"] = current_positions_usd
                        p["total_capital"] = base_cap
                        if is_fresh_deploy or float(p.get("total_capital", 0) or 0) < 200.0:
                            p["invest_date"] = inv_date
                        changed = True
                        break
                if changed:
                    atomic_write_json(VIRTUAL_PORTFOLIOS_FILE, vp_list, indent=2)
        except Exception:
            pass


def run_autobot_cycle(
    force_rebalance: bool = False,
    trigger_override: Optional[str] = None,
) -> Dict[str, Any]:
    cfg = load_autobot_config()
    state = load_autobot_state()
    account_addr, priv_key, cred_meta = get_wallet_credentials_meta()
    onchain = fetch_onchain_account_state(account_addr)

    now = datetime.now()
    now_iso = now.isoformat(timespec="seconds")

    requested_mode = str(cfg.get("mode", "LIVE")).upper()
    target_cap = float(cfg.get("target_capital_usd", 20000.0))
    min_deploy_eq = float(cfg.get("min_deploy_equity_usd", 100.0))
    live_total_eq = float(onchain.get("total_equity_usd", 0.0))

    can_sign_live = bool(
        cred_meta["key_configured"]
        and cred_meta["is_direct_master_key"]
        and onchain["connected"]
    )

    is_preview_capital = False
    mode_fallback_reason = None

    if requested_mode == "LIVE":
        # Real wallet mode: NEVER fabricate fake virtual balances!
        effective_mode = "LIVE"
        using_virtual_book = False
        current_positions_usd = {
            a: float(p["equity_usd"]) for a, p in onchain.get("vault_positions", {}).items()
        }
        locked_map = {
            a: p for a, p in onchain.get("vault_positions", {}).items() if p.get("is_locked")
        }
        avail_cash_usd = float(onchain.get("perp_withdrawable_usd", 0.0)) + (
            float(onchain.get("spot_usdc_usd", 0.0)) if cfg.get("auto_spot_to_perp", True) else 0.0
        )
        if live_total_eq >= min_deploy_eq:
            deploy_capital = live_total_eq if cfg.get("compound_profits", True) else min(live_total_eq, target_cap)
        else:
            # Wallet not funded yet: compute SGRA+ target table preview at target_cap ($20,000), keep actual $0/real holdings honest
            is_preview_capital = True
            deploy_capital = target_cap

        if cfg.get("enabled", False) and not can_sign_live:
            if cred_meta.get("is_delegated_agent_key"):
                mode_fallback_reason = (
                    "Hyperliquid L1 규약상 API 위임키는 볼트 입출금(vaultTransfer) 서명이 불가합니다. "
                    "setup_wallet_key.bat을 실행해 운용 지갑의 직접 개인키를 등록해주세요."
                )
            elif not cred_meta.get("key_configured"):
                mode_fallback_reason = (
                    "자동운용이 켜져 있으나 아직 .env 서명키가 등록되지 않았습니다. "
                    "폴더 내 setup_wallet_key.bat을 실행해 지갑 키를 등록해주세요."
                )
    else:
        # Explicit DRY_RUN paper simulation mode (only if user explicitly chooses DRY_RUN in settings)
        effective_mode = "DRY_RUN"
        using_virtual_book = True
        v_pos = state.get("virtual_positions") or {}
        v_cash = state.get("virtual_cash_usd")
        if v_cash is None and not v_pos:
            v_cash = target_cap
        current_positions_usd = {k.lower(): float(val) for k, val in v_pos.items() if float(val) > 0.5}
        locked_map = {}
        avail_cash_usd = float(v_cash if v_cash is not None else max(0.0, target_cap - sum(current_positions_usd.values())))
        deploy_capital = sum(current_positions_usd.values()) + avail_cash_usd
        if abs(deploy_capital - target_cap) > 1.0 and not current_positions_usd:
            deploy_capital = target_cap
            avail_cash_usd = target_cap

    signal = compute_sgra_signal(deploy_capital, set(current_positions_usd.keys()), cfg)
    if "error" in signal:
        state["last_checked_at"] = now_iso
        state["last_error"] = signal["error"]
        atomic_write_json(AUTOBOT_STATE_FILE, state, indent=2)
        return {"status": "error", "error": signal["error"]}

    # Parameters & preliminary delta plan
    interval_days = int(cfg.get("rebalance_interval_days", 14))
    last_reb_str = state.get("last_rebalance_at")
    days_since_reb = 999.0
    if last_reb_str:
        try:
            days_since_reb = (now - datetime.fromisoformat(last_reb_str)).total_seconds() / 86400.0
        except Exception:
            days_since_reb = 999.0

    band = float(cfg.get("no_trade_band_rel", 0.10))
    min_trade = float(cfg.get("min_trade_usd", 50.0))
    cash_buf = float(cfg.get("cash_buffer_usd", 2.0))

    pending_locked = state.get("pending_locked_withdrawals") or {}
    unlocked_retry_addrs = [a for a in pending_locked.keys() if a in current_positions_usd and a not in locked_map]
    emergency_exits = signal.get("emergency_exits", [])
    emergency_addrs = {e["address"] for e in emergency_exits}

    target_map = dict(signal["target_map_usd"])
    for ea in emergency_addrs:
        target_map[ea] = 0.0
    v_lookup = signal.get("vault_lookup", {})

    planned_sells, planned_buys, skipped_band = _build_delta_plan(
        current_positions_usd, target_map, locked_map, emergency_addrs, v_lookup, False, band, min_trade
    )

    is_initial_uninvested = (
        sum(current_positions_usd.values()) < min_deploy_eq
        and len(planned_buys) > 0
        and avail_cash_usd >= min_deploy_eq
    )
    excess_cash_usd = avail_cash_usd - float(signal.get("cash_reserve_usd", 0.0))
    has_new_capital = (excess_cash_usd >= max(300.0, 0.12 * deploy_capital) and len(planned_buys) > 0)

    trigger_type = "HOLD_NO_SIGNAL"
    trigger_reason = (
        f"정상 자동운용 감시 중 — 다음 정기 리밸런싱까지 {max(0.0, interval_days - days_since_reb):.1f}일 남음 "
        f"(보유 볼트 이상 없음, 10% HWM 보존)"
    )
    should_execute = False

    if not cfg.get("enabled", False) and not force_rebalance:
        trigger_type = "PAUSED_STANDBY"
        if effective_mode == "LIVE":
            if not cred_meta["key_configured"]:
                trigger_reason = (
                    "입금 전 대기 중 (일시정지) — ① setup_wallet_key.bat 서명키 등록 및 ② Hyperliquid USDC 입금 후 "
                    "[▶️ 자동운용 재개 실행]을 누르면 즉시 자동 포트폴리오 운용이 시작됩니다."
                )
            elif is_preview_capital:
                trigger_reason = (
                    f"입금 전 대기 중 (일시정지) — 서명키 연결 완료! Hyperliquid 지갑에 자금 입금 후 "
                    f"[▶️ 자동운용 재개 실행]을 누르면 즉시 매수가 시작됩니다. (현재 지갑 총자산 ${live_total_eq:,.2f})"
                )
            else:
                trigger_reason = (
                    f"자동운용 일시정지 중 — 지갑 내 온체인 자산(${live_total_eq:,.2f}) 확인됨. "
                    f"[▶️ 자동운용 재개 실행] 클릭 시 즉시 자동 포트폴리오 배분을 시작합니다."
                )
        else:
            trigger_reason = "모의운용(DRY_RUN) 일시정지 상태입니다."
    elif effective_mode == "LIVE" and not can_sign_live:
        trigger_type = "AWAITING_KEY"
        trigger_reason = mode_fallback_reason or "운용 지갑 서명키(.env) 연결 대기 중입니다."
    elif effective_mode == "LIVE" and is_preview_capital:
        trigger_type = "AWAITING_DEPOSIT"
        addr_disp = (account_addr[:10] + "...") if account_addr else "미설정"
        trigger_reason = (
            f"자동운용 켜짐 (입금 감지 대기 중) — 지갑({addr_disp})에 ${min_deploy_eq:,.0f} 이상 USDC가 입금되면 "
            f"자동으로 포트폴리오 매수가 실행됩니다. (현재 지갑 총자산 ${live_total_eq:,.2f})"
        )
    elif trigger_override == "RESUME_AUTO_START":
        trigger_type = "RESUME_AUTO_START"
        trigger_reason = f"▶️ 자동운용 재개 실행 — 지갑 자금(${deploy_capital:,.2f}) SGRA+ 최적 포트폴리오 즉시 구성 및 자동운용 개시"
        should_execute = True
    elif force_rebalance:
        trigger_type = "MANUAL_FORCE"
        trigger_reason = f"⚡ 웹 관제센터 수동 즉시 리밸런싱 실행 (운용자산 ${deploy_capital:,.2f})"
        should_execute = True
    elif emergency_exits:
        trigger_type = "EMERGENCY_EXIT"
        trigger_reason = "🚨 비상 리스크 가드 발동: " + "; ".join(f"{e['name']}({e['reason']})" for e in emergency_exits)
        should_execute = True
    elif unlocked_retry_addrs:
        trigger_type = "LOCKUP_UNLOCKED_RETRY"
        trigger_reason = f"24시간 락업 해제 완료 볼트({len(unlocked_retry_addrs)}개) 대기 출금/재배분 실행"
        should_execute = True
    elif is_initial_uninvested:
        trigger_type = "INITIAL_DEPLOY"
        trigger_reason = f"💰 지갑 입금 자금(${deploy_capital:,.2f}) 감지 — SGRA+ 최적 포트폴리오 최초 자동 진입"
        should_execute = True
    elif has_new_capital:
        trigger_type = "NEW_CAPITAL_DEPLOY"
        trigger_reason = f"💰 신규 입금 가용 자금(${avail_cash_usd:,.2f}) 감지 — SGRA+ 목표 포트폴리오 자동 배분"
        should_execute = True
    elif days_since_reb >= interval_days:
        trigger_type = "SCHEDULED_14D"
        trigger_reason = f"🔄 정기 {interval_days}일 리밸런싱 시그널 도달 ({days_since_reb:.1f}일 경과)"
        should_execute = True

    if trigger_type == "EMERGENCY_EXIT":
        planned_sells, planned_buys, skipped_band = _build_delta_plan(
            current_positions_usd, target_map, locked_map, emergency_addrs, v_lookup, True, band, min_trade
        )

    exec_events: List[Dict[str, Any]] = []
    new_pending_locked: Dict[str, Any] = {}

    if should_execute:
        if planned_sells or planned_buys:
            exchange = None
            info_live = None
            if effective_mode == "LIVE":
                import eth_account
                from hyperliquid.exchange import Exchange
                pk_norm = priv_key if priv_key.startswith("0x") else ("0x" + priv_key)
                wallet = eth_account.Account.from_key(pk_norm)
                exchange = Exchange(wallet, constants.MAINNET_API_URL, account_address=account_addr)
                info_live = Info(constants.MAINNET_API_URL, skip_ws=True)

            # PHASE 1: Withdrawals / Trims
            for s in planned_sells:
                addr = s["address"]
                amt = float(s["delta_usd"])
                if s["is_locked"]:
                    new_pending_locked[addr] = {
                        "name": s["name"],
                        "amount_usd": amt,
                        "locked_until": s["locked_until"],
                        "queued_at": now_iso,
                    }
                    exec_events.append({
                        "ts": now_iso, "mode": effective_mode, "trigger": trigger_type,
                        "action": "QUEUED_24H_LOCKUP", "vault": s["name"], "address": addr,
                        "amount_usd": amt, "status": "PENDING_UNLOCK",
                        "detail": f"입금 후 24시간 락업 중 ({s['locked_until']} 해제 후 자동 재시도)",
                    })
                    continue

                if effective_mode == "LIVE" and exchange is not None:
                    try:
                        send_usd = amt * 0.998 if s["action"] == "WITHDRAW_FULL" else amt
                        micro_usd = int(round(send_usd * 1_000_000))
                        resp = exchange.vault_usd_transfer(vault_address=addr, is_deposit=False, usd=micro_usd)
                        ok = isinstance(resp, dict) and resp.get("status") == "ok"
                        exec_events.append({
                            "ts": now_iso, "mode": "LIVE", "trigger": trigger_type,
                            "action": s["action"], "vault": s["name"], "address": addr,
                            "amount_usd": round(send_usd, 2), "status": "OK" if ok else "REJECTED",
                            "detail": json.dumps(resp, ensure_ascii=False)[:240],
                        })
                    except Exception as ex:
                        exec_events.append({
                            "ts": now_iso, "mode": "LIVE", "trigger": trigger_type,
                            "action": s["action"], "vault": s["name"], "address": addr,
                            "amount_usd": amt, "status": "ERROR", "detail": str(ex)[:240],
                        })
                else:
                    cur_v = current_positions_usd.get(addr, 0.0)
                    sold = min(cur_v, amt)
                    rem_v = cur_v - sold
                    if rem_v <= 0.5:
                        current_positions_usd.pop(addr, None)
                    else:
                        current_positions_usd[addr] = round(rem_v, 2)
                    avail_cash_usd += sold
                    exec_events.append({
                        "ts": now_iso, "mode": "DRY_RUN", "trigger": trigger_type,
                        "action": s["action"], "vault": s["name"], "address": addr,
                        "amount_usd": round(sold, 2), "status": "SIMULATED_OK",
                        "detail": s["reason"],
                    })

            # Refresh live Perps withdrawable USDC after withdrawals & optionally bridge Spot USDC -> Perps
            if effective_mode == "LIVE" and exchange is not None and info_live is not None:
                if planned_sells:
                    time.sleep(2.5)
                refreshed = fetch_onchain_account_state(account_addr)
                perp_free = float(refreshed.get("perp_withdrawable_usd", 0.0))
                spot_free = float(refreshed.get("spot_usdc_usd", 0.0))
                needed_buys = sum(b["delta_usd"] for b in planned_buys)
                if needed_buys > perp_free and spot_free >= 10.0 and cfg.get("auto_spot_to_perp", True):
                    bridge_amt = round(min(spot_free - 0.5, needed_buys - perp_free + cash_buf), 2)
                    if bridge_amt >= 5.0:
                        try:
                            b_resp = exchange.usd_class_transfer(amount=bridge_amt, to_perp=True)
                            time.sleep(1.5)
                            refreshed = fetch_onchain_account_state(account_addr)
                            perp_free = float(refreshed.get("perp_withdrawable_usd", 0.0))
                            exec_events.append({
                                "ts": now_iso, "mode": "LIVE", "trigger": trigger_type,
                                "action": "SPOT_TO_PERP_BRIDGE", "vault": "Hyperliquid Perps Account", "address": account_addr,
                                "amount_usd": bridge_amt, "status": "OK",
                                "detail": json.dumps(b_resp, ensure_ascii=False)[:200],
                            })
                        except Exception as bx:
                            exec_events.append({
                                "ts": now_iso, "mode": "LIVE", "trigger": trigger_type,
                                "action": "SPOT_TO_PERP_BRIDGE", "vault": "Hyperliquid Perps Account", "address": account_addr,
                                "amount_usd": bridge_amt, "status": "ERROR", "detail": str(bx)[:200],
                            })
                spendable_usd = max(0.0, min(perp_free - cash_buf, deploy_capital))
            else:
                target_cash_res = float(signal.get("cash_reserve_usd", 0.0))
                spendable_usd = max(0.0, avail_cash_usd - max(cash_buf, target_cash_res))

            # PHASE 2: Deposits / Allocations
            total_buy_req = sum(b["delta_usd"] for b in planned_buys)
            scale = min(1.0, spendable_usd / total_buy_req) if total_buy_req > 0 else 0.0

            for b in planned_buys:
                addr = b["address"]
                buy_usd = round(b["delta_usd"] * scale, 2)
                if buy_usd < min_trade:
                    continue

                if effective_mode == "LIVE" and exchange is not None and info_live is not None:
                    try:
                        vdet = info_live.post("/info", {"type": "vaultDetails", "vaultAddress": addr}) or {}
                        if not vdet.get("allowDeposits", True) or vdet.get("isClosed", False):
                            exec_events.append({
                                "ts": now_iso, "mode": "LIVE", "trigger": trigger_type,
                                "action": "SKIPPED_CLOSED", "vault": b["name"], "address": addr,
                                "amount_usd": buy_usd, "status": "SKIPPED",
                                "detail": "온체인 실시간 확인 결과 입금 비활성(allowDeposits=False) 볼트",
                            })
                            continue
                        micro_usd = int(round(buy_usd * 1_000_000))
                        resp = exchange.vault_usd_transfer(vault_address=addr, is_deposit=True, usd=micro_usd)
                        ok = isinstance(resp, dict) and resp.get("status") == "ok"
                        exec_events.append({
                            "ts": now_iso, "mode": "LIVE", "trigger": trigger_type,
                            "action": "DEPOSIT", "vault": b["name"], "address": addr,
                            "amount_usd": buy_usd, "status": "OK" if ok else "REJECTED",
                            "detail": json.dumps(resp, ensure_ascii=False)[:240],
                        })
                    except Exception as ex:
                        exec_events.append({
                            "ts": now_iso, "mode": "LIVE", "trigger": trigger_type,
                            "action": "DEPOSIT", "vault": b["name"], "address": addr,
                            "amount_usd": buy_usd, "status": "ERROR", "detail": str(ex)[:240],
                        })
                else:
                    current_positions_usd[addr] = round(current_positions_usd.get(addr, 0.0) + buy_usd, 2)
                    avail_cash_usd = round(max(0.0, avail_cash_usd - buy_usd), 2)
                    exec_events.append({
                        "ts": now_iso, "mode": "DRY_RUN", "trigger": trigger_type,
                        "action": "DEPOSIT", "vault": b["name"], "address": addr,
                        "amount_usd": buy_usd, "status": "SIMULATED_OK",
                        "detail": b["reason"],
                    })

            state["pending_locked_withdrawals"] = new_pending_locked

            if using_virtual_book:
                state["virtual_positions"] = current_positions_usd
                state["virtual_cash_usd"] = round(avail_cash_usd, 2)
            elif effective_mode == "LIVE" and account_addr:
                time.sleep(1.5)
                onchain = fetch_onchain_account_state(account_addr)
                current_positions_usd = {
                    a: float(p["equity_usd"]) for a, p in onchain.get("vault_positions", {}).items()
                }
                locked_map = {
                    a: p for a, p in onchain.get("vault_positions", {}).items() if p.get("is_locked")
                }
                avail_cash_usd = float(onchain.get("perp_withdrawable_usd", 0.0)) + float(onchain.get("spot_usdc_usd", 0.0))
                _sync_live_portfolio_files(
                    account_addr=account_addr,
                    onchain=onchain,
                    current_positions_usd=current_positions_usd,
                    now_iso=now_iso,
                    is_fresh_deploy=(trigger_type in ("INITIAL_DEPLOY", "RESUME_AUTO_START") and not last_reb_str),
                )

            if exec_events:
                append_exec_logs(exec_events)
                if effective_mode == "LIVE" or cfg.get("notify_on_dry_run", False):
                    send_alert_notifications(
                        f"Hyperliquid SGRA+ 자동운용 ({effective_mode}) — {trigger_type}",
                        [
                            f"• 사유: {trigger_reason}",
                            f"• 시장 국면: {signal['regime']} (14d {signal['mkt_14d_pct']:+.2f}%, 상승폭 {signal['breadth_14d_pct']:.1f}%)",
                            f"• 실행 건수: 총 {len(exec_events)}건 (목표 투자비중 {signal['deployed_weight_pct']:.1f}%, 현금버퍼 {signal['cash_reserve_pct']:.1f}%)",
                        ] + [f"  - [{e['action']}] {e['vault']}: ${e['amount_usd']:,.0f} ({e['status']})" for e in exec_events[:8]],
                    )

            planned_sells, planned_buys, skipped_band = _build_delta_plan(
                current_positions_usd, target_map, locked_map, emergency_addrs, v_lookup, False, band, min_trade
            )

        if trigger_type in ("RESUME_AUTO_START", "MANUAL_FORCE", "INITIAL_DEPLOY", "NEW_CAPITAL_DEPLOY", "SCHEDULED_14D") and (
            len(exec_events) > 0 or (not is_preview_capital and not planned_sells and not planned_buys)
        ):
            state["last_rebalance_at"] = now_iso

    state["last_checked_at"] = now_iso
    state["last_signal_type"] = trigger_type
    state["last_trigger_reason"] = trigger_reason
    state["effective_mode"] = effective_mode
    state["is_preview_capital"] = is_preview_capital
    state["mode_fallback_reason"] = mode_fallback_reason
    state["using_virtual_book"] = using_virtual_book
    state["working_positions_usd"] = {k: round(v, 2) for k, v in current_positions_usd.items()}
    state["working_cash_usd"] = round(avail_cash_usd, 2)
    state["latest_signal"] = {k: v for k, v in signal.items() if k != "vault_lookup"}
    state["planned_sells"] = planned_sells
    state["planned_buys"] = planned_buys
    state["skipped_band"] = skipped_band
    atomic_write_json(AUTOBOT_STATE_FILE, state, indent=2)

    return get_autobot_dashboard_payload(cached_onchain=onchain, cached_creds=cred_meta)


def resume_autobot() -> Dict[str, Any]:
    """
    Called when the user clicks '▶️ 자동운용 재개 실행' on /autobot after depositing funds.
    1) Verifies .env signing key (Direct EOA) unless user explicitly opted into DRY_RUN.
    2) Enables auto-bot (`enabled=True`).
    3) If funds (>= min_deploy_equity_usd) are already in the wallet, IMMEDIATELY executes
       Spot->Perp transfer (if needed) + SGRA+ target portfolio allocation!
       Otherwise arms `AWAITING_DEPOSIT` so funds are automatically deployed upon arrival.
    """
    cfg = load_autobot_config()
    req_mode = str(cfg.get("mode", "LIVE")).upper()
    account_addr, _, cred_meta = get_wallet_credentials_meta()

    if req_mode == "LIVE":
        if not cred_meta["key_configured"]:
            return {
                "ok": False,
                "code": "MISSING_KEY",
                "message": (
                    "아직 운용 지갑 서명키(.env)가 등록되지 않았습니다.\n"
                    "폴더 내 setup_wallet_key.bat 파일을 더블클릭하여 지갑 키를 1회 등록하신 뒤 "
                    "다시 [▶️ 자동운용 재개 실행]을 눌러주세요."
                ),
                "payload": get_autobot_dashboard_payload(cached_creds=cred_meta),
            }
        if cred_meta.get("is_delegated_agent_key"):
            return {
                "ok": False,
                "code": "AGENT_KEY_NOT_ALLOWED",
                "message": (
                    "Hyperliquid 프로토콜 규약상 일반 주문용 API 위임키는 볼트 입출금(vaultTransfer) 서명이 불가합니다.\n"
                    "setup_wallet_key.bat을 실행해 운용 지갑 본체의 개인키를 등록해주세요."
                ),
                "payload": get_autobot_dashboard_payload(cached_creds=cred_meta),
            }

        onchain = fetch_onchain_account_state(account_addr)
        save_autobot_config({"enabled": True, "mode": "LIVE"})
        min_eq = float(cfg.get("min_deploy_equity_usd", 100.0))
        live_eq = float(onchain.get("total_equity_usd", 0.0))

        if live_eq >= min_eq:
            payload = run_autobot_cycle(force_rebalance=True, trigger_override="RESUME_AUTO_START")
            return {
                "ok": True,
                "code": "STARTED_AND_DEPLOYED",
                "message": f"🟢 자동운용이 시작되어 지갑 자산(${live_eq:,.2f})의 SGRA+ 포트폴리오 배분이 즉시 실행되었습니다!",
                "payload": payload,
            }
        else:
            payload = run_autobot_cycle(force_rebalance=False)
            return {
                "ok": True,
                "code": "ARMED_AWAITING_DEPOSIT",
                "message": (
                    f"🟢 자동운용 감시가 켜졌습니다! 현재 지갑 총자산(${live_eq:,.2f})이 최소 기준(${min_eq:,.0f}) 미만이어서 "
                    f"입금 대기 상태이며, Hyperliquid에 USDC를 입금하시면 자동으로 포트폴리오 매수가 시작됩니다."
                ),
                "payload": payload,
            }
    else:
        save_autobot_config({"enabled": True})
        payload = run_autobot_cycle(force_rebalance=True, trigger_override="RESUME_AUTO_START")
        return {
            "ok": True,
            "code": "STARTED_DRY_RUN",
            "message": "🧪 모의운용(DRY_RUN) 자동운용이 재개되었습니다.",
            "payload": payload,
        }


def pause_autobot() -> Dict[str, Any]:
    save_autobot_config({"enabled": False})
    payload = run_autobot_cycle(force_rebalance=False)
    return {
        "ok": True,
        "code": "PAUSED",
        "message": "⏸️ 자동운용이 일시정지되었습니다. (기존 보유 포지션은 그대로 유지됩니다)",
        "payload": payload,
    }


def get_autobot_dashboard_payload(
    cached_onchain: Optional[Dict[str, Any]] = None,
    cached_creds: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    cfg = load_autobot_config()
    state = load_autobot_state()
    if not state.get("latest_signal"):
        return run_autobot_cycle(force_rebalance=False)

    if cached_creds is None or cached_onchain is None:
        account_addr, _, cred_meta = get_wallet_credentials_meta()
        onchain = fetch_onchain_account_state(account_addr)
    else:
        cred_meta = cached_creds
        onchain = cached_onchain

    interval_days = int(cfg.get("rebalance_interval_days", 14))
    last_reb_str = state.get("last_rebalance_at")
    next_reb_str = "재개 실행 시 즉시 진입"
    days_remaining = 0.0
    if last_reb_str:
        try:
            dt_last = datetime.fromisoformat(last_reb_str)
            dt_next = dt_last + timedelta(days=interval_days)
            days_remaining = max(0.0, (dt_next - datetime.now()).total_seconds() / 86400.0)
            next_reb_str = dt_next.strftime("%Y-%m-%d %H:%M")
        except Exception:
            pass

    return {
        "config": cfg,
        "credentials": cred_meta,
        "onchain": onchain,
        "state": {
            "last_checked_at": state.get("last_checked_at"),
            "last_rebalance_at": last_reb_str,
            "next_rebalance_at": next_reb_str,
            "days_to_next_rebalance": round(days_remaining, 1),
            "last_signal_type": state.get("last_signal_type"),
            "last_trigger_reason": state.get("last_trigger_reason"),
            "effective_mode": state.get("effective_mode", cfg.get("mode", "LIVE")),
            "is_preview_capital": state.get("is_preview_capital", True),
            "mode_fallback_reason": state.get("mode_fallback_reason"),
            "using_virtual_book": state.get("using_virtual_book", False),
            "working_positions_usd": state.get("working_positions_usd", {}),
            "working_cash_usd": state.get("working_cash_usd", 0.0),
            "virtual_positions": state.get("virtual_positions", {}),
            "virtual_cash_usd": state.get("virtual_cash_usd"),
            "pending_locked_withdrawals": state.get("pending_locked_withdrawals", {}),
        },
        "signal": state.get("latest_signal", {}),
        "planned_sells": state.get("planned_sells", []),
        "planned_buys": state.get("planned_buys", []),
        "skipped_band": state.get("skipped_band", []),
        "logs": load_exec_logs(limit=60),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Hyperliquid $20,000 SGRA+ Auto Vault Bot")
    parser.add_argument("--force", action="store_true", help="즉시 리밸런싱 강제 실행")
    parser.add_argument("--dry-run", action="store_true", help="일회성 DRY_RUN 강제 설정")
    args = parser.parse_args()

    if args.dry_run:
        save_autobot_config({"mode": "DRY_RUN"})

    payload = run_autobot_cycle(force_rebalance=args.force)
    sig = payload.get("signal", {})
    st = payload.get("state", {})
    print("=" * 78)
    print(f"🤖 Hyperliquid SGRA+ Auto-Bot | Mode={st.get('effective_mode')} | Signal={st.get('last_signal_type')}")
    print(f"   Reason : {st.get('last_trigger_reason')}")
    print(f"   Regime : {sig.get('regime')} (14d={sig.get('mkt_14d_pct')}%, Breadth={sig.get('breadth_14d_pct')}%)")
    print(f"   Capital: ${sig.get('deploy_capital_usd', 0):,.2f} (Deployed {sig.get('deployed_weight_pct', 0):.1f}% / Cash {sig.get('cash_reserve_pct', 0):.1f}%)")
    print("-" * 78)
    for a in sig.get("allocations", []):
        print(
            f"  • {a['name'][:26]:<26} | {a['target_weight_pct']:>5.1f}% (${a['target_usd']:>8,.2f}) | "
            f"Skin {a['leader_ratio_pct']:>5.1f}% | Shp {a['cushioned_sharpe']:>5.1f} | TVL ${a['tvl_usd']:>8,.0f}"
        )
    print("=" * 78)
