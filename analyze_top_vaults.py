#!/usr/bin/env python3
"""
Hyperliquid 상위 200 볼트 분석기  (Robust Curve Edition)
====================================
- stats-data.hyperliquid.xyz 에서 전체 볼트 목록 가져오기 (9000+ 개)
- TVL 기준 상위 200개 선별
- 매일 스냅샷 저장 → 일별 변화 추적
- ★ 로버스트 수익곡선 분석 (R², 단조성, MDD회복력)
- TVL 상위 200개 전체 대상 (TVL 최소값 제한 없음)
- MDD 제한 없음 (종합점수 기반 선별)
- 투자 추천 및 $100K 포트폴리오 배분
- 월별 리밸런싱 조언
- Excel 리포트 자동 생성

사용법:
  python analyze_top_vaults.py           # 전체 분석
  python analyze_top_vaults.py --force   # 캐시 무시하고 새로 분석
  python analyze_top_vaults.py --mdd 25  # MDD 상한 25%로 변경
"""

import json, os, sys, time, argparse, glob, random, asyncio
import aiohttp
from io_utils import atomic_write_json
import numpy as np
import pandas as pd
import requests
import cloudscraper
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from hyperliquid.info import Info
from hyperliquid.utils import constants
from scipy import stats as scipy_stats

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── 설정 ──────────────────────────────────────────────────────────────────────
TOP_N          = 200       # 분석할 볼트 수
MAX_WORKERS    = 1         # 병렬 스레드 수 (봇 판정 회피를 위해 순차 처리)
MIN_TVL        = 0         # TVL 최소값 제한 없음 (상위 200위 전체 대상)
TOP_RECS       = 10        # 추천 포트폴리오 볼트 수
SIM_AMOUNT     = 100_000   # 시뮬레이션 투자금 ($)
MAX_MDD           = 100.0  # MDD 제한 없음 (전 종목 대상)
MIN_ROBUSTNESS    = 0.35   # 최소 로버스트니스 점수 (0~1) — 수익곡선 품질 기준
MIN_LEADER_EQUITY = 0.40   # ★ 리더 에쿼티 최소 비율 (40% = skin-in-the-game 필터)

STATS_URL = "https://stats-data.hyperliquid.xyz/Mainnet/vaults"
API_URL   = constants.MAINNET_API_URL


def _make_info_client(retries=4, delay=5):
    """Hyperliquid SDK의 Info() 초기화를 재시도로 감싼다.
    spot_meta 파싱 실패(IndexError 등)가 간헐적으로 발생하므로 백오프 후 재시도하고,
    끝내 실패하면 명확히 예외를 올려 상위(run_analysis→main)가 실패를 감지하도록 한다."""
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            return Info(API_URL, skip_ws=True)
        except Exception as e:
            last_err = e
            print(f"  [WARN] Info() 초기화 실패 ({attempt}/{retries}): {e}")
            if attempt < retries:
                time.sleep(delay * attempt)
    raise RuntimeError(f"Info() 클라이언트 초기화 최종 실패: {last_err}")

DATA_DIR      = "vault_data"
SNAPSHOTS_DIR = os.path.join(DATA_DIR, "snapshots")
REPORTS_DIR   = os.path.join(DATA_DIR, "reports")

# ── 유틸 ──────────────────────────────────────────────────────────────────────
def load_config():
    # config.json 은 gitignore 대상(지갑주소 보호). 파일이 없으면 환경변수로 대체.
    # CI(GitHub Actions)에서는 ACCOUNT_ADDRESS 시크릿을 설정하세요.
    cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    if os.path.exists(cfg_path):
        with open(cfg_path, encoding="utf-8") as f:
            return json.load(f)
    env_addr = os.environ.get("ACCOUNT_ADDRESS", "").strip()
    if env_addr:
        return {"account_address": env_addr}
    raise FileNotFoundError(
        "config.json 이 없고 ACCOUNT_ADDRESS 환경변수도 비어 있습니다. "
        "로컬은 config.json 을, CI는 ACCOUNT_ADDRESS 시크릿을 설정하세요."
    )

# 모든 날짜 키를 KST(UTC+9)로 통일. 예전엔 naive datetime.now() 라서 로컬 PC(KST)와
# GitHub Actions 러너(UTC)가 서로 다른 날짜로 스냅샷을 저장 → CI 헬스체크(KST 기준)가
# 항상 '오늘 데이터 없음'으로 실패하고 중복방지 가드도 안 걸렸다. (pre_run_check /
# check_data_health 는 이미 KST 사용 → 이제 세 곳이 일치한다.)
KST = timezone(timedelta(hours=9))

def today_str():
    return datetime.now(KST).strftime("%Y-%m-%d")

def yesterday_str():
    return (datetime.now(KST) - timedelta(days=1)).strftime("%Y-%m-%d")

def snapshot_path(ds):
    return os.path.join(SNAPSHOTS_DIR, f"{ds}.json")

def save_snapshot(data, ds=None):
    ds = ds or today_str()
    os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
    atomic_write_json(snapshot_path(ds), data, indent=2, default=float)
    print(f"  >> 스냅샷 저장: {os.path.abspath(snapshot_path(ds))}")

def load_snapshot(ds):
    p = snapshot_path(ds)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)

def sf(val, default=0.0):
    try:
        return float(val) if val is not None else default
    except (ValueError, TypeError):
        return default

def risk_label(vol):
    if vol < 25:  return "LOW"
    if vol < 55:  return "MODERATE"
    return "HIGH"


# ── 볼트 데이터 가져오기 ──────────────────────────────────────────────────────
def fetch_top_vaults(top_n=TOP_N):
    """stats-data API에서 전체 볼트 목록을 가져와 TVL 기준 상위 N개 반환.
    Cloudflare 차단 시 빈 리스트 반환 (run_analysis에서 fallback 처리)"""
    print("  전체 볼트 목록 가져오는 중 (stats-data.hyperliquid.xyz)...")
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://app.hyperliquid.xyz",
        "Referer": "https://app.hyperliquid.xyz/"
    }
    # 클라우드플레어 JS 챌린지를 우회하기 위한 지능형 스크래퍼 생성
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
    
    all_vaults = []
    for attempt in range(1, 4):
        try:
            resp = scraper.get(STATS_URL, headers=headers, timeout=60)
            resp.raise_for_status()
            all_vaults = resp.json()
            break
        except Exception as e:
            print(f"  [시도 {attempt}/3] ERROR: {e}")
            if attempt < 3:
                print("  => 5초 대기 후 재시도...")
                time.sleep(5)
            else:
                print("  ⚠️ stats-data API 접근 실패 (Cloudflare 차단 가능성)")
                return []

    print(f"  총 {len(all_vaults)}개 볼트 발견")

    # User Vault 필터: relationship.type == 'normal' (HLP parent/child 제외)
    # TVL >= MIN_TVL, 오픈 상태
    valid = []
    for v in all_vaults:
        s   = v.get("summary", {})
        rel = s.get("relationship", {})
        rel_type = rel.get("type", "normal") if isinstance(rel, dict) else "normal"
        if (rel_type == "normal"
                and not s.get("isClosed", False)):
            valid.append({"summary": s, "apr_raw": sf(v.get("apr", 0)), "pnls": v.get("pnls", [])})

    valid.sort(key=lambda x: sf(x["summary"].get("tvl", 0)), reverse=True)
    top = valid[:top_n]
    print(f"  User Vault (normal) TVL 상위 {len(top)}개 선별 (총 {len(valid)}개 중)")
    return top


def _get_latest_snapshot_path():
    """가장 최근 스냅샷 파일 경로를 반환"""
    snapshots = sorted(glob.glob(os.path.join(SNAPSHOTS_DIR, "*.json")), reverse=True)
    for p in snapshots:
        if os.path.getsize(p) > 50000:
            return p
    return None


async def fetch_vault_details_single(session, addr, semaphore, api_url, retry_base=1.0, max_attempts=5):
    url = f"{api_url}/info"
    payload = {"type": "vaultDetails", "vaultAddress": addr}
    headers = {"Content-Type": "application/json"}
    
    async with semaphore:
        for attempt in range(max_attempts):
            try:
                async with session.post(url, json=payload, headers=headers, timeout=20) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if isinstance(data, dict):
                            return addr, data
                        else:
                            raise ValueError("Response is not a dict")
                    elif resp.status == 429:
                        retry_after = resp.headers.get("Retry-After")
                        if retry_after:
                            try:
                                delay = float(retry_after)
                            except ValueError:
                                delay = retry_base * (2 ** attempt) + random.uniform(0, 0.5)
                        else:
                            delay = retry_base * (2 ** attempt) + random.uniform(0, 0.5)
                        print(f"    [429 Rate Limit] {addr[:12]}... Waiting {delay:.2f}s (Attempt {attempt+1}/{max_attempts})")
                        await asyncio.sleep(delay)
                    else:
                        delay = retry_base * (2 ** attempt) + random.uniform(0, 0.5)
                        print(f"    [HTTP {resp.status}] {addr[:12]}... Waiting {delay:.2f}s (Attempt {attempt+1}/{max_attempts})")
                        await asyncio.sleep(delay)
            except Exception as e:
                delay = retry_base * (2 ** attempt) + random.uniform(0, 0.5)
                print(f"    [Network Error] {addr[:12]}...: {e}. Waiting {delay:.2f}s (Attempt {attempt+1}/{max_attempts})")
                await asyncio.sleep(delay)
        return addr, None


async def async_fetch_all_vault_details(addresses, api_url):
    semaphore = asyncio.Semaphore(5)
    connector = aiohttp.TCPConnector(limit=5)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [
            fetch_vault_details_single(session, addr, semaphore, api_url)
            for addr in addresses
        ]
        results = await asyncio.gather(*tasks)
        return {addr: details for addr, details in results if details is not None}


def analyze_vault_from_details(addr, info_client_or_details):
    """공식 vaultDetails API를 사용해 단일 볼트를 분석.
    stats-data API가 Cloudflare 차단될 때 사용하는 fallback 함수."""
    details = None
    if isinstance(info_client_or_details, dict):
        details = info_client_or_details.get(addr)
    elif info_client_or_details is not None:
        for attempt in range(1, 4):
            try:
                details = info_client_or_details.post("/info", {"type": "vaultDetails", "vaultAddress": addr})
                if details and isinstance(details, dict):
                    break
                details = None
            except Exception as e:
                err_str = str(e)
                if "429" in err_str:
                    wait = attempt * 3  # 3초, 6초, 9초
                    time.sleep(wait)
                    continue
                print(f"    ⚠️ vaultDetails API 실패 ({addr[:12]}...): {e}")
                return None
    if not details:
        return None

    name = details.get("name", "Unknown")[:40]
    leader = details.get("leader", "")
    apr_raw = sf(details.get("apr", 0))
    apr_pct = apr_raw * 100
    is_closed = details.get("isClosed", False)
    allow_deposits = details.get("allowDeposits", True)
    leader_fraction = sf(details.get("leaderFraction", 0))
    followers = details.get("followers", [])
    num_followers = len(followers) if isinstance(followers, list) else 0

    # relationship 체크 (HLP parent/child 제외)
    rel = details.get("relationship", {})
    rel_type = rel.get("type", "normal") if isinstance(rel, dict) else "normal"
    if rel_type != "normal" or is_closed:
        return None

    # portfolio에서 PnL 데이터 추출
    portfolio = details.get("portfolio", [])
    alltime_pnl, month_pnl, week_pnl, day_pnl = [], [], [], []
    tvl = 0.0

    for period_data in (portfolio if isinstance(portfolio, list) else []):
        if not isinstance(period_data, list) or len(period_data) < 2:
            continue
        period_name = period_data[0]
        period_info = period_data[1]
        if not isinstance(period_info, dict):
            continue

        # PnL 히스토리 파싱 (타임스탬프, 값 형태)
        pnl_history = period_info.get("pnlHistory", [])
        pnl_values = [sf(item[1]) for item in pnl_history if isinstance(item, list) and len(item) >= 2]

        # accountValueHistory에서 최신 TVL 추출
        avh = period_info.get("accountValueHistory", [])
        if avh and period_name == "allTime" and isinstance(avh[-1], list) and len(avh[-1]) >= 2:
            tvl = max(tvl, sf(avh[-1][1]))

        if period_name == "allTime":
            alltime_pnl = pnl_values
        elif period_name == "month":
            month_pnl = pnl_values
        elif period_name == "week":
            week_pnl = pnl_values
        elif period_name == "day":
            day_pnl = pnl_values

    # TVL fallback: allTime accountValueHistory의 마지막 값이 없으면 다른 기간에서 시도
    if tvl <= 0:
        for period_data in (portfolio if isinstance(portfolio, list) else []):
            if not isinstance(period_data, list) or len(period_data) < 2:
                continue
            period_info = period_data[1]
            if isinstance(period_info, dict):
                avh = period_info.get("accountValueHistory", [])
                if avh and isinstance(avh[-1], list) and len(avh[-1]) >= 2:
                    tvl = max(tvl, sf(avh[-1][1]))

    # PnL 기반 메트릭 계산
    metrics = _calc_pnl_metrics(alltime_pnl, month_pnl, tvl, apr_pct,
                                day_pnl=day_pnl, week_pnl=week_pnl)

    # 리더 에쿼티 계산
    leader_equity_ratio = leader_fraction
    leader_equity_usd = round(leader_equity_ratio * tvl, 2)
    if leader_equity_ratio > 0:
        num_followers += 1

    # ★ SITG 보너스 (기존 analyze_vault_from_stats와 동일 로직)
    sitg_bonus = float(np.log10(max(leader_equity_usd, 1))) * 2.0
    tvl_scale_bonus = float(np.log10(max(sf(tvl), 1))) * 0.5
    metrics["score"] = round(metrics.get("score", 0.0) + sitg_bonus + tvl_scale_bonus, 3)

    # 생성 시간 (vaultDetails에서는 createTimeMillis가 없으므로 이전 스냅샷에서 가져옴)
    return {
        "address":             addr,
        "name":                name,
        "leader":              leader,
        "tvl":                 tvl,
        "num_followers":       num_followers,
        "allow_deposits":      allow_deposits,
        "leader_equity_ratio": leader_equity_ratio,
        "leader_equity_usd":   leader_equity_usd,
        "created_at":          "-",
        "age_days":            0,
        "apr_pct":             round(apr_pct, 2),
        "alltime_pnl":         alltime_pnl,
        "month_pnl":           month_pnl,
        **metrics,
    }


def run_analysis_fallback(top_n=TOP_N):
    """★ Cloudflare 차단 시 fallback: 이전 스냅샷의 vault 주소 기반 + 공식 API로 갱신"""
    latest_snap_path = _get_latest_snapshot_path()
    if not latest_snap_path:
        print("  ❌ fallback 불가: 이전 스냅샷이 없습니다.")
        return []

    snap_name = os.path.basename(latest_snap_path)
    print(f"  📋 이전 스냅샷 기반 fallback 모드 (기준: {snap_name})")
    with open(latest_snap_path, encoding="utf-8") as f:
        prev_data = json.load(f)

    # 이전 스냅샷에서 vault 주소 추출 + created_at/age_days 보존
    prev_meta = {}
    addresses = []
    for v in prev_data:
        addr = v.get("address", "")
        if addr:
            addresses.append(addr)
            prev_meta[addr] = {
                "created_at": v.get("created_at", "-"),
                "age_days": v.get("age_days", 0),
            }

    print(f"  📡 공식 API로 {len(addresses)}개 볼트 데이터 비동기 병렬 수집 중...")
    try:
        cached_details = asyncio.run(async_fetch_all_vault_details(addresses, API_URL))
    except Exception as e:
        print(f"  ⚠️ 비동기 수집 중 에러 발생: {e}. 동기 수집으로 진행합니다.")
        cached_details = {}

    results, failed = [], 0
    info_client = None

    for i, addr in enumerate(addresses):
        try:
            res = None
            if addr in cached_details:
                res = analyze_vault_from_details(addr, cached_details)
            if not res:
                if info_client is None:
                    info_client = _make_info_client()
                res = analyze_vault_from_details(addr, info_client)
            if res:
                # 이전 스냅샷의 created_at/age_days 보존
                if addr in prev_meta:
                    if res["created_at"] == "-":
                        res["created_at"] = prev_meta[addr]["created_at"]
                    if res["age_days"] == 0:
                        res["age_days"] = prev_meta[addr]["age_days"] + 1
                results.append(res)
            else:
                failed += 1
        except Exception:
            failed += 1

    print(f"  완료: 시도 {len(addresses)}개 / 성공 {len(results)}개 / 실패 {failed}개")

    # 입금 가능한 볼트만 필터
    open_results = [v for v in results if v.get("allow_deposits", True)]
    open_results.sort(key=lambda x: x["tvl"], reverse=True)
    final_results = open_results[:top_n]

    # 필터링 / 랭킹 (run_analysis와 동일)
    for v in final_results:
        leader_usd = v.get("leader_equity_usd", 0)
        leader_rat = v.get("leader_equity_ratio", 0)
        ok_leader  = leader_usd >= 30000 or (leader_rat >= 0.3 and leader_usd >= 5000)
        pnl_arr = v.get("alltime_pnl", [])
        ok_no_loss = not (pnl_arr and min(pnl_arr) < 0)
        v["_filter_pass"] = ok_leader and ok_no_loss
        v["_ok_deposit"] = True
        v["_ok_leader"] = ok_leader
        v["_ok_no_loss"] = ok_no_loss

    final_results.sort(key=lambda x: x["score"], reverse=True)
    for i, v in enumerate(final_results):
        v["rank"] = i + 1

    save_snapshot(final_results)
    return final_results


# ── 단일 볼트 분석 ────────────────────────────────────────────────────────────
def analyze_vault_from_stats(v_data, info_client_or_details):
    """stats-data 응답 하나를 분석해서 dict 반환"""
    s    = v_data["summary"]
    addr = s.get("vaultAddress", "")
    if not addr:
        return None

    # allTime pnl 배열: 누적 PnL 값들
    alltime_pnl = []
    month_pnl = []
    week_pnl = []
    day_pnl = []
    for period_name, vals in v_data.get("pnls", []):
        parsed = [sf(x) for x in vals]
        if period_name == "allTime":
            alltime_pnl = parsed
        elif period_name == "month":
            month_pnl = parsed
        elif period_name == "week":
            week_pnl = parsed
        elif period_name == "day":
            day_pnl = parsed

    # TVL 기반으로 수익률 계산
    tvl = sf(s.get("tvl", 0))
    apr_raw = v_data.get("apr_raw", 0)  # 이미 소수 형태 (0.15 = 15%)
    apr_pct = apr_raw * 100

    # ★ 볼트 생성 시간/날짜
    create_ms = s.get("createTimeMillis", 0)
    if create_ms:
        created_dt = datetime.utcfromtimestamp(create_ms / 1000)
        created_at = created_dt.strftime("%Y-%m-%d")
        age_days   = (datetime.utcnow() - created_dt).days
    else:
        created_at = "-"
        age_days   = 0

    # PnL 시계열 분석
    metrics = _calc_pnl_metrics(alltime_pnl, month_pnl, tvl, apr_pct,
                                day_pnl=day_pnl, week_pnl=week_pnl)

    # allowDeposits 확인 (vaultDetails API 사용)
    # allowDeposits + ★ 리더 에쿼티 비율 계산
    allow_deposits      = True
    leader_equity_ratio = 0.0
    leader_equity_usd   = 0.0
    num_followers       = 0

    details = None
    if isinstance(info_client_or_details, dict):
        details = info_client_or_details.get(addr)
    elif info_client_or_details is not None:
        for attempt in range(1, 6):
            try:
                details = info_client_or_details.post("/info", {"type": "vaultDetails", "vaultAddress": addr})
                if details and isinstance(details, dict):
                    break
                details = None
            except Exception as e:
                if "429" in str(e):
                    time.sleep(attempt * 2)
                else:
                    if attempt < 5:
                        time.sleep(2) # 오류 시 휴식 후 재시도
                    else:
                        pass
        # 봇 판정 방지 및 Rate Limit 회피를 위해 매 요청마다 3초 휴식
        time.sleep(3.0)

    if details and isinstance(details, dict):
        allow_deposits = details.get("allowDeposits", True)
        followers      = details.get("followers", [])
        num_followers  = len(followers) if isinstance(followers, list) else 0

        # ★ 사용자 요청: 리더 에쿼티 비율 (leaderFraction 필드가 리더의 지분 비율임)
        leader_equity_ratio = sf(details.get("leaderFraction"), 0.0)
        leader_equity_usd   = round(leader_equity_ratio * tvl, 2)
        
        # 리더가 followers 목록에 없을 수 있으므로(UI에서 별도 처리), 전체 팔로워 수에 리더(+1) 고려
        if leader_equity_ratio > 0:
            num_followers += 1

    # ★ 사용자 요청 (TVL 금액 + 에쿼티 금액 절대값 중심의 가중치 보정)
    # 리더 지분율(%)보다 리더가 꽂아넣은 '진짜 돈의 크기(USD)'가 안정성의 핵심이라는 보스의 철학 반영!
    # TVL 150억에 리더 8억(5%)(엄청난 안정성) >>> TVL 천만원에 리더 800만원(80%)(작업장)
    
    # 1. 오직 '리더 예치 금액(USD)'의 절대량만으로 시너지 점수를 계산 (Log10 스케일)
    # $8,000 -> 3.9 * 2 = 7.8점 가산
    # $600,000 -> 5.77 * 2 = 11.54점 가산
    sitg_bonus = float(np.log10(max(leader_equity_usd, 1))) * 2.0
    
    # 2. 비율 집중도 보너스는 전면 폐기하고, 자본의 무게감(TVL 전체 규모)에서 약간의 가산점 부여 (TVL $1M 당 +0.5)
    tvl_scale_bonus = float(np.log10(max(sf(tvl), 1))) * 0.5
    
    metrics["score"] = round(metrics.get("score", 0.0) + sitg_bonus + tvl_scale_bonus, 3)

    return {
        "address":             addr,
        "name":                s.get("name", "Unknown")[:40],
        "leader":              s.get("leader", ""),
        "tvl":                 tvl,
        "num_followers":       num_followers,
        "allow_deposits":      allow_deposits,
        "leader_equity_ratio": leader_equity_ratio,   # ★ 리더 본인 예치 비율
        "leader_equity_usd":   leader_equity_usd,     # ★ 리더 예치 금액($)
        "created_at":          created_at,            # ★ 볼트 생성일
        "age_days":            age_days,              # ★ 볼트 운영일수
        "apr_pct":             round(apr_pct, 2),
        # ★ 포트폴리오 엔진 (상관분석/백테스팅)에서 사용
        "alltime_pnl":         alltime_pnl,
        "month_pnl":           month_pnl,
        **metrics,
    }


def _calc_robustness(alltime_pnl, tvl):
    """
    ★ 로버스트 수익곡선 분석
    수익 곡선이 얼마나 일관되게 우상향하는지 0~1 점수로 반환.

    세 가지 지표를 균등 평균:
      1) r_squared   : 선형 추세에 대한 R² (1에 가까울수록 매끄럽게 우상향)
      2) monotonicity: 상승 구간 / 전체 구간 비율 (1에 가까울수록 꾸준히 상승)
      3) recovery    : MDD 이후 회복 속도 점수 (낙폭이 적고 빠르게 회복할수록 높음)
    """
    result = dict(
        r_squared=0.0, monotonicity=0.0, recovery_score=0.0,
        robustness_score=0.0, equity_curve_grade="-"
    )
    if len(alltime_pnl) < 10 or tvl <= 0:
        return result

    try:
        arr = np.array(alltime_pnl, dtype=float)
        cumulative = arr - arr[0]          # 누적 PnL (0 기준)
        n = len(cumulative)
        x = np.arange(n)

        # 1) R² — 선형 추세 적합도
        slope, intercept, r_value, _, _ = scipy_stats.linregress(x, cumulative)
        r_sq = max(0.0, r_value ** 2)      # 음수 방지
        # 기울기가 음수(하락추세)면 R² 패널티
        if slope < 0:
            r_sq = r_sq * 0.1
        result["r_squared"] = round(float(r_sq), 4)

        # 2) 단조성 — 상승 구간 비율
        diffs = np.diff(cumulative)
        up_ratio = float(np.sum(diffs > 0) / len(diffs)) if len(diffs) > 0 else 0.0
        result["monotonicity"] = round(up_ratio, 4)

        # 3) 회복력 — MDD 대비 낙폭 크기 & 회복 속도
        rolling_max = np.maximum.accumulate(cumulative)
        drawdown = (rolling_max - cumulative) / (np.abs(rolling_max) + 1e-9)
        max_dd_ratio = float(np.max(drawdown))
        # 낙폭이 0이면 완벽, 클수록 패널티
        recovery = max(0.0, 1.0 - min(max_dd_ratio * 2.0, 1.0))
        result["recovery_score"] = round(recovery, 4)

        # 종합 robustness: 세 지표 평균
        robustness = float((r_sq + up_ratio + recovery) / 3.0)
        robustness = round(float(np.clip(robustness, 0.0, 1.0)), 4)
        result["robustness_score"] = robustness

        # 등급 부여
        if robustness >= 0.75:
            grade = "A+ (최우수)"
        elif robustness >= 0.60:
            grade = "A  (우수)"
        elif robustness >= 0.45:
            grade = "B  (양호)"
        elif robustness >= 0.30:
            grade = "C  (보통)"
        else:
            grade = "D  (불안정)"
        result["equity_curve_grade"] = grade

    except Exception as e:
        pass  # 계산 실패 시 기본값(0) 유지

    return result


def _calc_pnl_metrics(alltime_pnl, month_pnl, tvl, apr_pct, day_pnl=None, week_pnl=None):
    """PnL 배열에서 리스크/성과 지표 계산 (로버스트니스 포함, 정밀 MDD)"""
    if day_pnl is None: day_pnl = []
    if week_pnl is None: week_pnl = []
    base = dict(
        vol_score=0.0, sharpe_ratio=0.0, max_drawdown=0.0,
        drawdown_now=0.0, recovery_factor=0.0,
        apr_30d=0.0, monthly_return=0.0,
        pnl_30d=0.0, pnl_alltime=0.0,
        data_points=0, score=0.0,
        # ★ 로버스트니스 지표
        r_squared=0.0, monotonicity=0.0, recovery_score=0.0,
        robustness_score=0.0, equity_curve_grade="-"
    )

    # allTime PnL → 수익률 계산
    if len(alltime_pnl) >= 3 and tvl > 0:
        arr = np.array(alltime_pnl)
        # PnL 변화량 (일 단위 증분)
        diffs = np.diff(arr)
        returns = diffs / (tvl + np.abs(arr[:-1]) + 1e-9)
        returns = np.clip(returns, -0.5, 0.5)

        vol    = float(np.std(returns) * np.sqrt(252) * 100) if len(returns) > 1 else 0.0
        mean_r = float(np.mean(returns))
        std_r  = float(np.std(returns))
        
        # 1번 옵션: 최소 변동성 안전 쿠션 (연환산 2% 변동성을 일간 값으로 적용)
        # 변동성이 0에 수렴하여 샤프 비율이 비현실적으로 폭발하는 현상 방지.
        cushion_daily = 0.02 / np.sqrt(252)
        safe_std_r = std_r + cushion_daily
        
        sharpe = float(np.clip((mean_r / safe_std_r) * np.sqrt(252), -50, 50))

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 최대 낙폭 (MDD) — 사용자 제안 공식
        #   MDD = (Peak PnL - Trough PnL) / Peak PnL × 100
        #
        # * Peak PnL   : 누적 PnL 시계열의 최고점
        # * Trough PnL : 해당 피크 이후의 최저점
        #
        # 엣지케이스:
        #   - Peak PnL = 0 (시작점) → 분모 0 방지:
        #     처음부터 손실 난 경우(3xBTC류), TVL 기준으로 fallback
        #   - Peak PnL > 0 → 정식 공식 적용
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        pnl_curve    = np.array(alltime_pnl, dtype=float)
        rolling_peak = np.maximum.accumulate(pnl_curve)  # 각 시점 최고 PnL
        dd_arr       = rolling_peak - pnl_curve           # 각 시점 낙폭 ($)

        max_dd_dollar = float(np.max(dd_arr))

        # Peak PnL (분모): 전체 기간 최고 PnL
        peak_pnl = float(np.max(pnl_curve))

        if peak_pnl > 0:
            # 정식 공식: (Peak - Trough) / Peak
            # Trough = Peak - max_dd_dollar
            max_dd = max_dd_dollar / peak_pnl * 100
        else:
            # peak PnL이 0 이하 (처음부터 손실) → TVL 기준 fallback
            max_dd = max_dd_dollar / (tvl + 1e-9) * 100

        max_dd        = max(0.0, round(max_dd, 2))
        max_dd_dollar = max(0.0, round(max_dd_dollar, 2))

        # ★ 정밀 MDD: day/week/month 기간별 데이터에서도 MDD를 계산하여 최악값 사용
        # allTime은 11개 포인트로 압축되어 중간 낙폭이 묻히는 문제 해결
        def _period_mdd_pct(pnl_arr, base_tvl):
            """단기 PnL 배열에서 MDD(%)를 계산 — TVL 기준으로 통일"""
            if len(pnl_arr) < 3:
                return 0.0, 0.0
            c = np.array(pnl_arr, dtype=float)
            rp = np.maximum.accumulate(c)
            dd = rp - c
            mdd_d = float(np.max(dd))
            # 단기 기간(day/week/month) PnL은 해당 기간 내 상대 변동이므로
            # 항상 TVL 기준으로 MDD% 산출 (분모 일관성)
            mdd_p = mdd_d / (base_tvl + 1e-9) * 100
            return max(0.0, round(mdd_p, 2)), max(0.0, round(mdd_d, 2))

        # 각 기간별 MDD 계산
        mdd_candidates = [(max_dd, max_dd_dollar)]  # allTime 기본값
        for period_arr in [day_pnl, week_pnl, month_pnl]:
            if period_arr:
                p_mdd, p_mdd_d = _period_mdd_pct(period_arr, tvl)
                mdd_candidates.append((p_mdd, p_mdd_d))

        # 최악의 MDD(아픈 기억)를 채택
        best = max(mdd_candidates, key=lambda x: x[0])
        max_dd = best[0]
        max_dd_dollar = best[1]

        pnl_alltime = float(arr[-1] - arr[0])
        base["vol_score"]    = round(vol, 2)
        base["sharpe_ratio"] = round(sharpe, 3)
        base["max_drawdown"] = round(max_dd, 2)
        base["max_dd_dollar"] = round(max_dd_dollar, 2)  # 절대 손실액($)
        base["pnl_alltime"]  = round(pnl_alltime, 2)
        base["data_points"]  = len(alltime_pnl)

        # ★ 로버스트 수익곡선 분석
        rob = _calc_robustness(alltime_pnl, tvl)
        base.update(rob)

        # ★ 현재 실제 낙폭 (drawdown_now) & 과거 회복력 (recovery_factor) 계산
        current_pnl = pnl_curve[-1]
        all_time_peak_pnl = float(np.max(pnl_curve))
        drawdown_now_dollar = max(0.0, all_time_peak_pnl - current_pnl)
        if all_time_peak_pnl > 0:
            drawdown_now_pct = drawdown_now_dollar / all_time_peak_pnl * 100
        else:
            drawdown_now_pct = drawdown_now_dollar / (tvl + 1e-9) * 100
        base["drawdown_now"] = round(max(0.0, drawdown_now_pct), 2)

        return_all = (pnl_alltime / (tvl + 1e-9) * 100)
        mdd_val = base["max_drawdown"]
        if mdd_val <= 0.01:
            recovery_factor = max(return_all, 0.0) * 100.0
        else:
            recovery_factor = return_all / mdd_val
        base["recovery_factor"] = round(recovery_factor, 4)

    # 30일 PnL
    if len(month_pnl) >= 2 and tvl > 0:
        arr30 = np.array(month_pnl)
        pnl_30d = float(arr30[-1] - arr30[0])
        monthly_return = float(np.clip(pnl_30d / tvl * 100, -100, 500)) if tvl > 0 else 0.0
        apr_30d = float(np.clip(monthly_return * 12, -500, 2000))
        base["pnl_30d"]        = round(pnl_30d, 2)
        base["monthly_return"] = round(monthly_return, 2)
        base["apr_30d"]        = round(apr_30d, 2)
    else:
        # 관측 APR 사용
        base["apr_30d"]        = round(apr_pct, 2)
        base["monthly_return"] = round(apr_pct / 12, 2)

    # ★ 강화된 종합 점수:
    #   Sharpe × 2.0  → 리스크 대비 수익
    #   APR30d / 50   → 최근 수익률
    #   -MaxDD / 30   → MDD 패널티 (기존보다 강화)
    #   +Robustness × 3.0 → 곡선 안정성 보너스
    rob_s = base["robustness_score"]
    score = float(np.clip(
        base["sharpe_ratio"] * 2.0
        + base["apr_30d"] / 50.0
        - base["max_drawdown"] / 30.0
        + rob_s * 3.0,
        -15, 35
    ))
    base["score"] = round(score, 3)
    return base


# ── 전체 분석 실행 ────────────────────────────────────────────────────────────
def run_analysis(top_n=TOP_N):
    # 디파짓 불가능한 볼트를 배제하고 200개를 확실히 채우기 위해 2배수(400개)를 가져옵니다.
    top_vaults = fetch_top_vaults(top_n * 2)
    
    # ★ Cloudflare 차단 fallback: stats-data API 실패 시 공식 API로 전환
    if not top_vaults:
        print("  🔄 stats-data API 실패 → 공식 vaultDetails API fallback 모드 전환...")
        return run_analysis_fallback(top_n)

    addresses = [v["summary"].get("vaultAddress", "") for v in top_vaults if v["summary"].get("vaultAddress", "")]
    print(f"  📡 공식 API로 {len(addresses)}개 볼트의 상세정보를 비동기 병렬 수집 중...")
    
    try:
        cached_details = asyncio.run(async_fetch_all_vault_details(addresses, API_URL))
    except Exception as e:
        print(f"  ⚠️ 비동기 수집 중 에러 발생: {e}. 동기 수집으로 진행합니다.")
        cached_details = {}

    results, failed = [], 0
    info_client = None

    print(f"  {len(top_vaults)}개 볼트 데이터 분석 중...")
    for i, v in enumerate(top_vaults):
        addr = v["summary"].get("vaultAddress", "")
        try:
            res = None
            if addr in cached_details:
                res = analyze_vault_from_stats(v, cached_details)
            if not res:
                if info_client is None:
                    info_client = _make_info_client()
                res = analyze_vault_from_stats(v, info_client)
            if res:
                results.append(res)
            else:
                failed += 1
        except Exception:
            failed += 1

    print(f"  완료: 분석 시도 {len(top_vaults)}개 / 성공 {len(results)}개 / 실패 {failed}개")

    # 파일 용량 낭비 방지: 디파짓 불가능한(allow_deposits=False) 볼트는 여기서 완전 제외
    open_results = [v for v in results if v.get("allow_deposits", True)]
    
    # 제외 후, 원래 의도대로 TVL 상위 top_n개(200개)만 추림
    open_results.sort(key=lambda x: x["tvl"], reverse=True)
    final_results = open_results[:top_n]

    # ★ 2단계 - 필터링 여부 표시 (안정성 평가)
    # 1안/2안 폐기: 비율(Ratio) 중심이 아니라 절대금액(USD) 중심으로 패러다임 전환
    # 조건: 리더가 최소 $30,000 (약 4천만원) 이상 꽂아넣었거나, 
    #       (소자본이더라도) 리더 에쿼티가 최소 30% 이상이면서 $5,000 이상일 것
    for v in final_results:
        leader_usd = v.get("leader_equity_usd", 0)
        leader_rat = v.get("leader_equity_ratio", 0)
        ok_leader  = leader_usd >= 30000 or (leader_rat >= 0.3 and leader_usd >= 5000)
        
        pnl_arr = v.get("alltime_pnl", [])
        ok_no_loss = not (pnl_arr and min(pnl_arr) < 0)
        
        v["_filter_pass"] = ok_leader and ok_no_loss
        v["_ok_deposit"] = True  # 이미 위에서 필터링됨
        v["_ok_leader"] = ok_leader
        v["_ok_no_loss"] = ok_no_loss

    # ★ 3단계 - 종합점수 기준으로 전체 랭킹 부여
    final_results.sort(key=lambda x: x["score"], reverse=True)
    for i, v in enumerate(final_results):
        v["rank"] = i + 1

    save_snapshot(final_results)
    return final_results


# ── 일별 변화 비교 ────────────────────────────────────────────────────────────
def compute_daily_changes(today_data, yesterday_data):
    if not yesterday_data:
        return []
    yday_map = {v["address"]: v for v in yesterday_data}
    changes  = []
    for v in today_data:
        yv = yday_map.get(v["address"])
        if not yv:
            changes.append({**v, "rank_change": None, "score_change": None,
                            "apr_30d_change": None, "sharpe_change": None, "new_entry": True})
        else:
            changes.append({
                **v,
                "rank_change":    (yv.get("rank", 999) - v["rank"]),
                "score_change":   round(v["score"]        - yv.get("score", 0), 3),
                "apr_30d_change": round(v["apr_30d"]      - yv.get("apr_30d", 0), 2),
                "sharpe_change":  round(v["sharpe_ratio"] - yv.get("sharpe_ratio", 0), 3),
                "new_entry":      False,
            })
    return changes


# ── 투자 추천 ─────────────────────────────────────────────────────────────────
def _calc_undervalue_score(v):
    """
    ★ 저평가 점수 (1달 기준 저평가 여부)
    - 전체기간 APR(annualized) / 12 = 장기 평균 월수익률
    - 최근 30일 monthly_return = 현재 월수익률
    - 장기 평균 > 현재 → 저평가 상태 → 비중 증가
    반환: 0.5(고평가) ~ 3.0(저평가)
    """
    alltime_monthly = v.get("apr_pct", 0) / 12.0    # 전체기간 환산 월수익률
    recent_monthly  = v.get("monthly_return", 0)     # 최근 30일 월수익률
    if alltime_monthly <= 0 or recent_monthly <= 0:
        return 1.0  # 기준 없으면 중립
    ratio = alltime_monthly / max(recent_monthly, 0.1)
    return float(np.clip(ratio, 0.5, 3.0))


def get_recommendations(vault_data, top_k=TOP_RECS, min_robustness=MIN_ROBUSTNESS,
                         min_leader_equity=MIN_LEADER_EQUITY):
    """
    ★ 필터 기준:
      1) 입금 가능 (allowDeposits)
      2) 리더 에쿼티 >= 40% (skin-in-the-game: 리더 본인이 40% 이상 예치)
      3) robustness_score >= min_robustness (수익곡선 안정성)
      (MDD 제한 없음 — 요구사항 4번)
    ★ 배분 기준 (바벨 전략):
      - CORE (50%): 로버스트니스 최상위 (가장 안정적)
      - SATELLITE (50%): 저평가점수(undervalue) 최상위 (현재 MDD 부근의 슬럼프지만 회복세(APR>0)를 보이는 종목)
    """
    # 1차: 모든 기준 적용 (APR > 0 필수 + 초기 손실 없음 + MDD 30% 이하 하드캡)
    eligible = [
        v for v in vault_data
        if v.get("allow_deposits", True)
        and (v.get("leader_equity_ratio", 0) >= min_leader_equity or v.get("leader_equity_usd", 0) >= 50000.0)
        and v.get("robustness_score", 0.0) >= min_robustness
        and v.get("apr_30d", 0) > 0          # ★ 최근 30일 수익 양수만 (회복탄력성 최소 기준)
        and v.get("_ok_no_loss", True)       # ★ 초기 손실 없는 볼트만 추천
        and v.get("max_drawdown", 0.0) <= 30.0  # ★ MDD 30% 이하 하드캡 적용
    ]
    print(f"  [필터] 1차(입금+리더에쿼티≥{min_leader_equity:.0%}또는$50k+로버스트≥{min_robustness:.2f}+APR>0+MDD≤30%): {len(eligible)}개")

    # 2차: robustness 기준만 완화 (APR > 0, _ok_no_loss, MDD 하드캡은 유지)
    if len(eligible) < top_k:
        fallback_rob = min_robustness * 0.5
        eligible = [
            v for v in vault_data
            if v.get("allow_deposits", True)
            and (v.get("leader_equity_ratio", 0) >= min_leader_equity or v.get("leader_equity_usd", 0) >= 50000.0)
            and v.get("robustness_score", 0.0) >= fallback_rob
            and v.get("apr_30d", 0) > 0      # ★ APR > 0 유지
            and v.get("_ok_no_loss", True)       # ★ 안전장치 유지
            and v.get("max_drawdown", 0.0) <= 30.0  # ★ MDD 하드캡 유지
        ]
        print(f"  [주의] 2차 완화: robustness >= {fallback_rob:.2f} (안전 필터 유지) → {len(eligible)}개")

    # 3차: 리더 에쿼티 데이터 기준 완화 (단, _ok_no_loss, MDD 하드캡, APR > 0은 항상 엄격하게 유지)
    if len(eligible) < 3:
        eligible = [
            v for v in vault_data 
            if v.get("allow_deposits", True) 
            and v.get("apr_30d", 0) > 0
            and v.get("_ok_no_loss", True)       # ★ 안전장치 유지
            and v.get("max_drawdown", 0.0) <= 30.0  # ★ MDD 하드캡 유지
        ]
        print(f"  [주의] 3차 최소 필터(입금가능+APR>0+안전 필터 유지): {len(eligible)}개")

    # 각 볼트의 undervalue_score 미리 계산
    for v in eligible:
        v["undervalue_score"] = round(_calc_undervalue_score(v), 3)

    # ★ 바벨 전략 (Barbell Strategy) 적용
    if len(eligible) <= 1:
        recs = eligible
        if recs:
            recs[0]["suggested_allocation"] = 100.0
            recs[0]["barbell_group"] = "CORE"
        return recs

    half_k = min(top_k // 2, len(eligible) // 2)
    if half_k == 0:
        half_k = 1

    # Group A: Core (로버스트니스 최상위)
    eligible_core = sorted(eligible, key=lambda x: x.get("robustness_score", 0), reverse=True)
    core_vaults = eligible_core[:half_k]
    
    # Group B: Satellite (현재 실제 낙폭 5% 이상인 볼트 중 undervalue_score 및 회복탄력성 우수 자산)
    core_addrs = {v["address"] for v in core_vaults}
    eligible_sat = [v for v in eligible if v["address"] not in core_addrs]
    
    # SATELLITE 후보 필터: drawdown_now >= 5.0%
    eligible_sat = [v for v in eligible_sat if v.get("drawdown_now", 0.0) >= 5.0]
    
    # 회복탄력성 저점매수(Buy-the-Dip) 기회 식별 (역사적 MDD의 70% ~ 115% 범위 및 회복성 검증)
    try:
        import portfolio_tracker
        from resilience_analyzer import analyze_vault_resilience
        snapshots = portfolio_tracker.load_snapshots_all()
        for v in eligible_sat:
            res = analyze_vault_resilience(v["address"], snapshots)
            if res:
                hist_mdd = res["historical_max_mdd"]
                curr_dd = res["current_drawdown"]
                rec_count = res["recovered_count"]
                avg_rec_days = res["avg_recovery_days"]
                v["is_resilience_opp"] = (
                    curr_dd >= hist_mdd * 0.70
                    and curr_dd <= hist_mdd * 1.15
                    and rec_count >= 1
                    and avg_rec_days <= 45.0
                )
            else:
                v["is_resilience_opp"] = False
    except Exception as e:
        print(f"  [Warning] 회복탄력성 기회 분석 실패: {e}")
        for v in eligible_sat:
            v["is_resilience_opp"] = False

    # 회복탄력성 저점매수(Buy-the-Dip) 기회를 최우선 배치하고, 나머지는 저평가 점수순 정렬
    eligible_sat = sorted(eligible_sat, key=lambda x: (x.get("is_resilience_opp", False), x.get("undervalue_score", 0)), reverse=True)
    
    sat_k = min(top_k - len(core_vaults), len(eligible_sat))
    sat_vaults = eligible_sat[:sat_k]

    recs = core_vaults + sat_vaults

    # 가중치 분배 대상 비율 설정 (기본 50% : 50%)
    core_target = 50.0
    sat_target = 50.0
    if len(core_vaults) == 0:
        sat_target = 100.0
    elif len(sat_vaults) == 0:
        core_target = 100.0

    # 1) CORE 그룹: 위험 역가중 공식 (1 / MDD) 적용
    if len(core_vaults) > 0:
        # 분모 0 및 극단적 비중 쏠림 방지를 위해 max_drawdown 최소값 2.0% 설정
        raw_core_weights = [1.0 / max(v.get("max_drawdown", 0.0), 2.0) for v in core_vaults]
        sum_core_weights = sum(raw_core_weights)
        for idx, v in enumerate(core_vaults):
            alloc = (raw_core_weights[idx] / sum_core_weights) * core_target
            v["suggested_allocation"] = round(alloc, 2)
            v["barbell_group"] = "CORE"

    # 2) SATELLITE 그룹: 과거 회복력 (Recovery Factor) 수치에 비례하여 분배하되, 저점매수(Resilience Opp) 기회는 비중 2.0배 가중치 부스팅
    if len(sat_vaults) > 0:
        raw_sat_weights = []
        for v in sat_vaults:
            w = max(v.get("recovery_factor", 0.0), 0.0001)
            if v.get("is_resilience_opp", False):
                w *= 2.0  # 회복탄력성 저점매수 기회 가중치 적용!
            raw_sat_weights.append(w)
            
        sum_sat_weights = sum(raw_sat_weights)
        for idx, v in enumerate(sat_vaults):
            alloc = (raw_sat_weights[idx] / sum_sat_weights) * sat_target
            v["suggested_allocation"] = round(alloc, 2)
            v["barbell_group"] = "SATELLITE"

    # 총합이 100이 되도록 미세 조정
    total = sum(v["suggested_allocation"] for v in recs)
    if total != 100.0 and len(recs) > 0:
        diff = round(100.0 - total, 2)
        recs[0]["suggested_allocation"] = round(recs[0]["suggested_allocation"] + diff, 2)

    return recs


# ── 월별 리밸런싱 ─────────────────────────────────────────────────────────────
def get_rebalancing_advice(current_portfolio, recommendations, sim_amount=None):
    """sim_amount: 현재 포트폴리오가 없을 때 사용할 시뮬레이션 금액"""
    total   = sum(current_portfolio.values()) if current_portfolio else (sim_amount or 0)
    rec_map = {v["address"]: v for v in recommendations}
    advice  = []

    # 현재 보유 볼트
    for addr, equity in current_portfolio.items():
        cur_pct    = (equity / total * 100) if total > 0 else 0
        target     = rec_map.get(addr, {})
        target_pct = target.get("suggested_allocation", 0)
        diff       = target_pct - cur_pct
        action     = "INCREASE" if diff > 5 else ("DECREASE" if diff < -5 else "HOLD")
        advice.append(dict(action=action, address=addr,
                           name=target.get("name", addr[:12] + "..."),
                           current_usd=round(equity, 2), current_pct=round(cur_pct, 1),
                           target_pct=target_pct, diff_pct=round(diff, 1),
                           diff_usd=round(diff / 100 * total, 2) if total > 0 else 0))

    # 신규 진입
    for v in recommendations:
        if v["address"] not in current_portfolio:
            advice.append(dict(action="ENTER", address=v["address"], name=v["name"],
                               current_usd=0, current_pct=0,
                               target_pct=v["suggested_allocation"],
                               diff_pct=v["suggested_allocation"],
                               diff_usd=round(v["suggested_allocation"] / 100 * total, 2) if total > 0 else 0))

    # 추천 외 보유 볼트 -> EXIT
    for addr, equity in current_portfolio.items():
        if addr not in rec_map:
            cur_pct = (equity / total * 100) if total > 0 else 0
            if not any(a["address"] == addr for a in advice):
                advice.append(dict(action="EXIT", address=addr, name=addr[:12] + "...",
                                   current_usd=round(equity, 2), current_pct=round(cur_pct, 1),
                                   target_pct=0, diff_pct=-round(cur_pct, 1),
                                   diff_usd=-round(equity, 2)))

    order = {"EXIT": 0, "DECREASE": 1, "ENTER": 2, "INCREASE": 3, "HOLD": 4}
    advice.sort(key=lambda x: (order.get(x["action"], 9), -abs(x["diff_pct"])))
    return advice


# ── Excel 리포트 ──────────────────────────────────────────────────────────────
def generate_excel(vault_data, changes, recommendations, rebalancing, date_str):
    os.makedirs(REPORTS_DIR, exist_ok=True)
    filename = os.path.join(REPORTS_DIR, f"vault_report_{date_str}.xlsx")

    with pd.ExcelWriter(filename, engine="xlsxwriter") as writer:
        wb = writer.book
        hdr = wb.add_format({"bold": True, "bg_color": "#1A2744", "font_color": "#FFFFFF",
                              "border": 1, "align": "center", "valign": "vcenter"})
        bold = wb.add_format({"bold": True})

        def write_df(df, sheet_name, col_widths=None):
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            ws = writer.sheets[sheet_name]
            ws.set_row(0, 22, hdr)
            ws.freeze_panes(1, 0)
            if col_widths:
                for c, w in col_widths.items():
                    ws.set_column(c, c, w)
            else:
                ws.set_column(0, len(df.columns) - 1, 16)
            return ws

        # ── 시트①: 상위 200 랭킹 ──────────────────────────────────────────
        df1 = pd.DataFrame([{
            "순위":         v["rank"],
            "볼트명":       v["name"],
            "TVL($)":      v["tvl"],
            "30일APR(%)":  v["apr_30d"],
            "전체APR(%)":  v["apr_pct"],
            "월수익률(%)": v["monthly_return"],
            "30일PnL($)":  v["pnl_30d"],
            "전체PnL($)":  v["pnl_alltime"],
            "샤프비율":     v["sharpe_ratio"],
            "최대손실(%)": v["max_drawdown"],
            "종합점수":     v["score"],
            "팔로워수":     v["num_followers"],
            "입금가능":     "가능" if v.get("allow_deposits") else "불가",
            "주소":         v["address"],
        } for v in vault_data])
        ws1 = write_df(df1, "상위200랭킹",
                       {0: 6, 1: 28, 2: 14, 3: 12, 4: 12, 5: 12,
                        6: 14, 7: 14, 8: 10, 9: 12, 10: 10, 11: 10, 12: 8, 13: 44})
        # 조건부 서식
        for col in [3, 8, 10]:
            ws1.conditional_format(1, col, len(df1), col, {
                "type": "3_color_scale",
                "min_color": "#E74C3C", "mid_color": "#F7FA8E", "max_color": "#27AE60"})
        ws1.conditional_format(1, 9, len(df1), 9, {
            "type": "3_color_scale",
            "min_color": "#27AE60", "mid_color": "#F7FA8E", "max_color": "#E74C3C"})

        # ── 시트②: 일별 변화 ──────────────────────────────────────────────
        if changes:
            df2 = pd.DataFrame([{
                "순위":        c["rank"],
                "볼트명":      c["name"],
                "순위변화(+상승)": c.get("rank_change", "-"),
                "점수변화":    c.get("score_change", "-"),
                "30일APR(%)": c["apr_30d"],
                "APR변화(%)": c.get("apr_30d_change", "-"),
                "샤프비율":    c["sharpe_ratio"],
                "샤프변화":    c.get("sharpe_change", "-"),
                "신규진입":    "NEW" if c.get("new_entry") else "",
            } for c in changes])
            ws2 = write_df(df2, "일별변화",
                           {0: 6, 1: 28, 2: 13, 3: 10, 4: 12, 5: 11, 6: 10, 7: 10, 8: 8})
            ws2.conditional_format(1, 2, len(df2), 2, {
                "type": "3_color_scale",
                "min_color": "#E74C3C", "mid_color": "#FFFFFF", "max_color": "#27AE60"})
            ws2.conditional_format(1, 5, len(df2), 5, {
                "type": "3_color_scale",
                "min_color": "#E74C3C", "mid_color": "#FFFFFF", "max_color": "#27AE60"})

        # ── 시트③: 투자 추천 ──────────────────────────────────────────────
        df3 = pd.DataFrame([{
            "우선순위":         i + 1,
            "볼트명":           v["name"],
            "추천비중(%)": v["suggested_allocation"],
            "30일APR(%)": v["apr_30d"],
            "전체APR(%)": v["apr_pct"],
            "샤프비율":     v["sharpe_ratio"],
            "리스크등급":   risk_label(v["vol_score"]),
            "최대손실(%)": v["max_drawdown"],
            # ★ 로버스트니스 컬럼
            "곡선등급":     v.get("equity_curve_grade", "-"),
            "로버스트(0~1)": v.get("robustness_score", 0.0),
            "R²(선형)": v.get("r_squared", 0.0),
            "단조성(상승%)": round(v.get("monotonicity", 0.0) * 100, 1),
            "회복점수": v.get("recovery_score", 0.0),
            "TVL($)":      v["tvl"],
            "종합점수":     v["score"],
            "30일PnL($)": v["pnl_30d"],
            "주소":         v["address"],
        } for i, v in enumerate(recommendations)])
        write_df(df3, "투자추천",
                 {0: 8, 1: 28, 2: 11, 3: 11, 4: 11, 5: 10, 6: 10,
                  7: 12, 8: 14, 9: 13, 10: 10, 11: 13, 12: 10,
                  13: 14, 14: 10, 15: 14, 16: 44})

        # ── 시트④: 월별 리밸런싱 ─────────────────────────────────────────
        if rebalancing:
            action_kr = {"ENTER": "신규매수", "INCREASE": "비중증가",
                         "HOLD": "유지",    "DECREASE":  "비중감소", "EXIT": "매도"}
            df4 = pd.DataFrame([{
                "액션":         action_kr.get(r["action"], r["action"]),
                "볼트명":       r["name"],
                "현재잔고($)":  r["current_usd"],
                "현재비중(%)":  r["current_pct"],
                "목표비중(%)":  r["target_pct"],
                "변화비중(%)":  r["diff_pct"],
                "변화금액($)":  r["diff_usd"],
            } for r in rebalancing])
            ws4 = write_df(df4, "월별리밸런싱",
                           {0: 10, 1: 28, 2: 14, 3: 12, 4: 12, 5: 12, 6: 14})
            ws4.conditional_format(1, 6, len(df4), 6, {
                "type": "3_color_scale",
                "min_color": "#E74C3C", "mid_color": "#FFFFFF", "max_color": "#27AE60"})

        # ── 시트⑤: 분석 요약 ──────────────────────────────────────────────
        ws5 = wb.add_worksheet("분석요약")
        ws5.set_column(0, 0, 26)
        ws5.set_column(1, 1, 36)
        valid = [v for v in vault_data if v.get("data_points", 0) >= 3]

        rows = [
            ("▶ 분석 일자",      date_str),
            ("▶ 분석 볼트 수",   f"{len(vault_data)}개 (유효: {len(valid)}개)"),
            ("▶ MDD 상한",       f"{MAX_MDD}% 이하만 추천"),
            ("▶ 최소 로버스트",  f"{MIN_ROBUSTNESS:.2f} 이상 (0~1)"),
            ("", ""),
            ("═══ 시장 현황 ═══", ""),
            ("평균 30일 APR",    f"{np.mean([v['apr_30d'] for v in valid]):.1f}%" if valid else "-"),
            ("중앙값 30일 APR",  f"{np.median([v['apr_30d'] for v in valid]):.1f}%" if valid else "-"),
            ("평균 샤프비율",    f"{np.mean([v['sharpe_ratio'] for v in valid]):.2f}" if valid else "-"),
            ("평균 최대손실",    f"{np.mean([v['max_drawdown'] for v in valid]):.1f}%" if valid else "-"),
            ("평균 로버스트점수", f"{np.mean([v.get('robustness_score',0) for v in valid]):.3f}" if valid else "-"),
            ("", ""),
            ("═══ 상위 10 볼트 (종합점수) ═══", ""),
        ]
        for v in vault_data[:10]:
            rows.append((f"  #{v['rank']} {v['name']}",
                         f"APR {v['apr_30d']:.1f}% | Sharpe {v['sharpe_ratio']:.2f} | Rob {v.get('robustness_score',0):.3f} | Score {v['score']:.2f}"))
        rows += [
            ("", ""),
            ("═══ 투자 추천 요약 ═══", ""),
        ]
        for i, v in enumerate(recommendations, 1):
            rows.append((f"  {i}위. {v['name']}",
                         f"비중 {v['suggested_allocation']:.1f}% | APR {v['apr_30d']:.1f}% | {v.get('equity_curve_grade','-')} | MDD {v['max_drawdown']:.1f}%"))

        # ── 시트⑥: $100K 시뮬레이션 ──────────────────────────────────────
        sim = SIM_AMOUNT
        df6 = pd.DataFrame([{
            "우선순위":         i + 1,
            "볼트명":           v["name"],
            f"배분비중(%)": v["suggested_allocation"],
            f"투자금액(${sim//1000}K)": round(v["suggested_allocation"] / 100 * sim, 0),
            "30일APR(%)": v["apr_30d"],
            "예상월수익($)": round(v["suggested_allocation"] / 100 * sim * v["apr_30d"] / 100 / 12, 0),
            "예상연수익($)": round(v["suggested_allocation"] / 100 * sim * v["apr_30d"] / 100, 0),
            "샤프비율":     v["sharpe_ratio"],
            "리스크등급":   risk_label(v["vol_score"]),
            "최대손실(%)": v["max_drawdown"],
            "최대손실($)": round(v["suggested_allocation"] / 100 * sim * v["max_drawdown"] / 100, 0),
            "TVL($)":      v["tvl"],
            "주소":         v["address"],
        } for i, v in enumerate(recommendations)])

        # 합계 행
        total_invest = sum(df6[f"투자금액(${sim//1000}K)"])
        total_monthly = sum(df6["예상월수익($)"])
        total_annual  = sum(df6["예상연수익($)"])
        total_row = pd.DataFrame([{
            "우선순위": "합계", "볼트명": "",
            f"배분비중(%)": round(sum(df6["배분비중(%)"]), 1),
            f"투자금액(${sim//1000}K)": total_invest,
            "30일APR(%)": "-",
            "예상월수익($)": total_monthly,
            "예상연수익($)": total_annual,
            "샤프비율": "-", "리스크등급": "-",
            "최대손실(%)": "-", "최대손실($)": "-",
            "TVL($)": "-", "주소": "",
        }])
        df6 = pd.concat([df6, total_row], ignore_index=True)

        ws6 = write_df(df6, f"${sim//1000}K시뮬레이션",
                       {0: 8, 1: 28, 2: 12, 3: 14, 4: 12, 5: 14, 6: 14,
                        7: 10, 8: 10, 9: 12, 10: 14, 11: 14, 12: 44})
        # 합계 행 굵게
        sum_fmt = wb.add_format({"bold": True, "bg_color": "#D6EAF8", "border": 1})
        for c in range(len(df6.columns)):
            ws6.write(len(df6), c, df6.iloc[-1, c], sum_fmt)
        ws6.conditional_format(1, 5, len(df6)-1, 5, {
            "type": "3_color_scale",
            "min_color": "#E74C3C", "mid_color": "#F7FA8E", "max_color": "#27AE60"})

    print(f"  >> Excel 저장 완료: {os.path.abspath(filename)}")
    return filename


# ── 콘솔 출력 ─────────────────────────────────────────────────────────────────
def print_summary(vault_data, changes, recommendations, rebalancing, date_str):
    sep = "=" * 72
    action_kr = {"ENTER": "신규매수", "INCREASE": "비중증가",
                 "HOLD": "유지",    "DECREASE":  "비중감소", "EXIT": "매도"}

    print(f"\n{sep}")
    print(f"  HYPERLIQUID 볼트 분석  [{date_str}]")
    print(sep)

    valid = [v for v in vault_data if v.get("data_points", 0) >= 3]
    if valid:
        print(f"\n  [시장 현황]  분석: {len(vault_data)}개")
        print(f"  평균 30일 APR : {np.mean([v['apr_30d'] for v in valid]):.1f}%  "
              f"| 중앙값: {np.median([v['apr_30d'] for v in valid]):.1f}%")
        print(f"  평균 샤프비율 : {np.mean([v['sharpe_ratio'] for v in valid]):.2f}")

    # 상위 10
    print(f"\n  [상위 10 볼트  종합점수 기준]")
    print(f"  {'순위':<5} {'볼트명':<28} {'30일APR':>8} {'샤프':>7} {'최대손실':>8} {'점수':>7}")
    print("  " + "-" * 64)
    for v in vault_data[:10]:
        print(f"  {v['rank']:<5} {v['name'][:27]:<28} {v['apr_30d']:>7.1f}%"
              f" {v['sharpe_ratio']:>7.2f} {v['max_drawdown']:>7.1f}%  {v['score']:>6.2f}")

    # 일별 변화
    if changes:
        valid_ch = [c for c in changes if c.get("rank_change") is not None]
        risers = sorted(valid_ch, key=lambda x: x.get("rank_change", 0), reverse=True)[:5]
        fallers = sorted(valid_ch, key=lambda x: x.get("rank_change", 0))[:5]

        print(f"\n  [오늘 순위 급상승 TOP5]")
        print(f"  {'순위':<5} {'볼트명':<28} {'순위변화':>9} {'APR변화':>9}")
        print("  " + "-" * 55)
        for c in risers:
            rc, ac = c.get("rank_change", 0), c.get("apr_30d_change", 0)
            print(f"  {c['rank']:<5} {c['name'][:27]:<28} {rc:>+9}  {ac:>+8.1f}%")

        print(f"\n  [오늘 순위 급하락 TOP5]")
        print(f"  {'순위':<5} {'볼트명':<28} {'순위변화':>9} {'APR변화':>9}")
        print("  " + "-" * 55)
        for c in fallers:
            rc, ac = c.get("rank_change", 0), c.get("apr_30d_change", 0)
            print(f"  {c['rank']:<5} {c['name'][:27]:<28} {rc:>+9}  {ac:>+8.1f}%")

    # 투자 추천
    print(f"\n  [투자 추천  TOP {len(recommendations)}  |  바벨 전략: CORE 50% + SATELLITE 50%]")
    print(f"  {'#':<3} {'그룹':<10} {'볼트명':<26} {'비중':>6} {'APR30d':>8} {'샤프':>7} "
          f"{'곡선등급':<16} {'MDD':>7} {'TVL($)':>12}")
    print("  " + "-" * 102)
    for i, v in enumerate(recommendations, 1):
        grade = v.get("equity_curve_grade", "-")
        group = v.get("barbell_group", "-")
        print(f"  {i:<3} {group:<10} {v['name'][:25]:<26} {v['suggested_allocation']:>5.1f}%"
              f" {v['apr_30d']:>7.1f}% {v['sharpe_ratio']:>7.2f} "
              f"{grade:<16} {v['max_drawdown']:>6.1f}%  ${v['tvl']:>10,.0f}")

    # $100K 시뮬레이션 출력
    sim = SIM_AMOUNT
    total_monthly_est = sum(
        v["suggested_allocation"] / 100 * sim * v["apr_30d"] / 100 / 12
        for v in recommendations
    )
    total_annual_est = sum(
        v["suggested_allocation"] / 100 * sim * v["apr_30d"] / 100
        for v in recommendations
    )
    print(f"\n  [${sim:,} 투자 시뮬레이션  (30일 APR 기준)]")
    print(f"  {'#':<3} {'볼트명':<28} {'비중':>6} {'투자금액':>13} {'예상월수익':>12} {'예상연수익':>12}")
    print("  " + "-" * 78)
    for i, v in enumerate(recommendations, 1):
        invest = v["suggested_allocation"] / 100 * sim
        monthly = invest * v["apr_30d"] / 100 / 12
        annual  = invest * v["apr_30d"] / 100
        print(f"  {i:<3} {v['name'][:27]:<28} {v['suggested_allocation']:>5.1f}%"
              f"  ${invest:>10,.0f}  ${monthly:>9,.0f}  ${annual:>10,.0f}")
    print("  " + "-" * 78)
    print(f"  {'합계':<32} {'100.0%':>6}  ${sim:>10,}  ${total_monthly_est:>9,.0f}  ${total_annual_est:>10,.0f}")

    # 리밸런싱
    if rebalancing:
        print(f"\n  [월별 리밸런싱 조언]")
        print(f"  {'액션':<8} {'볼트명':<28} {'현재%':>7} {'목표%':>8} {'변화$':>14}")
        print("  " + "-" * 70)
        for r in rebalancing:
            ak = action_kr.get(r["action"], r["action"])
            print(f"  {ak:<8} {r['name'][:27]:<28} {r['current_pct']:>6.1f}%"
                  f" {r['target_pct']:>7.1f}%  ${r['diff_usd']:>11,.0f}")


# ── 메인 ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Hyperliquid 상위 볼트 분석기")
    parser.add_argument("--force", action="store_true", help="캐시 무시하고 새로 분석")
    parser.add_argument("--min-robustness", type=float, default=MIN_ROBUSTNESS,
                        dest="min_robustness",
                        help=f"최소 로버스트니스 점수 0~1 (기본: {MIN_ROBUSTNESS})")
    parser.add_argument("--min-leader", type=float, default=MIN_LEADER_EQUITY,
                        dest="min_leader",
                        help=f"리더 에쿼티 최소 비율 (기본: {MIN_LEADER_EQUITY})")
    args = parser.parse_args()

    t0 = time.time()
    print("=" * 60)
    print("  Hyperliquid Top Vault Analyzer")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    config       = load_config()
    user_address = config["account_address"]
    date_str     = today_str()

    # 1. 볼트 데이터
    existing = None if args.force else load_snapshot(date_str)
    if existing:
        print(f"\n[1/5] 캐시 사용 ({len(existing)}개 볼트, {date_str})")
        vault_data = existing
    else:
        print(f"\n[1/5] 신규 분석 시작 (상위 {TOP_N}개)...")
        vault_data = run_analysis(top_n=TOP_N)

    if not vault_data:
        print("ERROR: 볼트 데이터 없음", file=sys.stderr)
        sys.exit(1)  # 실패를 종료코드로 알림 → CI 재시도/실패 알림이 정상 작동

    # 2. 일별 변화
    print(f"\n[2/5] 일별 변화 비교...")
    yday    = load_snapshot(yesterday_str())
    changes = compute_daily_changes(vault_data, yday)
    print(f"  {'어제 대비 변화 계산 완료' if yday else '첫 실행 또는 어제 데이터 없음'}")

    # 3. 투자 추천
    print(f"\n[3/5] 투자 추천 계산...  (리더에쿼티≥{MIN_LEADER_EQUITY:.0%}, 로버스트≥{args.min_robustness:.2f}, MDD제한없음)")
    recommendations = get_recommendations(
        vault_data, top_k=TOP_RECS,
        min_robustness=args.min_robustness,
        min_leader_equity=MIN_LEADER_EQUITY
    )
    print(f"  추천 볼트 {len(recommendations)}개 선정")

    # 3-1. ★ 포트폴리오 일별 추적 업데이트
    try:
        from portfolio_engine import update_portfolio_tracking
        update_portfolio_tracking(recommendations, date_str, SIM_AMOUNT)
    except Exception as _pe:
        print(f"  [추적] 포트폴리오 기록 스킵: {_pe}")

    # 4. 현재 포트폴리오 조회
    print(f"\n[4/5] 현재 포트폴리오 조회...")
    current_portfolio = {}
    try:
        info = _make_info_client()
        resp = info.post("/info", {"type": "userVaultEquities", "user": user_address})
        if resp and isinstance(resp, list):
            for item in resp:
                addr   = item.get("vaultAddress", "")
                equity = sf(item.get("equity") or item.get("vaultEquity", 0))
                if addr and equity > 0:
                    current_portfolio[addr] = equity
        total = sum(current_portfolio.values())
        print(f"  현재 포트폴리오: {len(current_portfolio)}개 볼트, 총 ${total:,.2f}")
    except Exception as e:
        print(f"  WARNING: {e}")

    rebalancing = get_rebalancing_advice(
        current_portfolio, recommendations,
        sim_amount=SIM_AMOUNT if not current_portfolio else None
    )

    # 5. 리포트 생성
    print(f"\n[5/5] 리포트 생성...")
    print_summary(vault_data, changes, recommendations, rebalancing, date_str)
    excel_path = generate_excel(vault_data, changes, recommendations, rebalancing, date_str)

    elapsed = time.time() - t0
    print(f"\n{'=' * 60}")
    print(f"  완료!  소요시간: {elapsed:.1f}초")
    print(f"  Excel: {excel_path}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
