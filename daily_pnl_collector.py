#!/usr/bin/env python3
"""
일별 PnL 정밀 데이터 수집기 (Daily PnL Collector)
==================================================
매일 자동 실행되어 하이퍼리퀴드 상위 200개 볼트의
day/week/month/allTime PnL 데이터를 SQLite DB에 축적합니다.

시간이 지날수록 데이터가 쌓여 정밀 MDD 계산이 가능해집니다.

사용법:
  python daily_pnl_collector.py          # 수집 실행
  python daily_pnl_collector.py --info   # DB 현황 조회
"""

import json, os, sys, sqlite3, time, argparse
import requests
from datetime import datetime, timezone
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── 설정 ──────────────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
DB_PATH    = BASE_DIR / "vault_data" / "pnl_history.db"
STATS_URL  = "https://stats-data.hyperliquid.xyz/Mainnet/vaults"

def sf(val, default=0.0):
    try:
        return float(val) if val is not None else default
    except (ValueError, TypeError):
        return default


# ── DB 초기화 ─────────────────────────────────────────────────────────────────
def init_db():
    """SQLite DB 및 테이블 생성"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    # 볼트 메타 정보
    c.execute("""
        CREATE TABLE IF NOT EXISTS vaults (
            address TEXT PRIMARY KEY,
            name TEXT,
            first_seen TEXT,
            last_seen TEXT
        )
    """)

    # 일별 PnL 스냅샷 (핵심 테이블)
    c.execute("""
        CREATE TABLE IF NOT EXISTS daily_pnl (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vault_address TEXT NOT NULL,
            collected_at TEXT NOT NULL,
            tvl REAL,
            alltime_pnl REAL,
            day_pnl_max REAL,
            day_pnl_min REAL,
            day_pnl_last REAL,
            week_pnl_max REAL,
            week_pnl_min REAL,
            week_pnl_last REAL,
            month_pnl_max REAL,
            month_pnl_min REAL,
            month_pnl_last REAL,
            day_mdd_pct REAL,
            week_mdd_pct REAL,
            month_mdd_pct REAL,
            day_pnl_raw TEXT,
            week_pnl_raw TEXT,
            month_pnl_raw TEXT,
            alltime_pnl_raw TEXT,
            UNIQUE(vault_address, collected_at)
        )
    """)

    # 인덱스
    c.execute("CREATE INDEX IF NOT EXISTS idx_daily_pnl_vault ON daily_pnl(vault_address)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_daily_pnl_date ON daily_pnl(collected_at)")

    conn.commit()
    return conn


# ── MDD 계산 (단일 배열) ──────────────────────────────────────────────────────
def calc_mdd_from_array(pnl_arr, tvl):
    """PnL 배열에서 MDD(%)를 TVL 기준으로 계산"""
    if len(pnl_arr) < 3 or tvl <= 0:
        return 0.0
    import numpy as np
    c = np.array(pnl_arr, dtype=float)
    rp = np.maximum.accumulate(c)
    dd = rp - c
    mdd_d = float(np.max(dd))
    return round(mdd_d / tvl * 100, 4)


# ── 데이터 수집 ──────────────────────────────────────────────────────────────
def collect_all_vaults():
    """하이퍼리퀴드 API에서 전체 볼트 데이터를 가져와 DB에 저장"""
    print("=" * 60)
    print("  📡 일별 PnL 데이터 수집 시작")
    print("=" * 60)

    # 1) API 호출
    print("  전체 볼트 목록 가져오는 중...")
    try:
        resp = requests.get(STATS_URL, timeout=60)
        resp.raise_for_status()
        all_vaults = resp.json()
    except Exception as e:
        print(f"  ❌ API 오류: {e}")
        return 0

    # 2) Normal 볼트만 필터 + TVL 정렬
    valid = []
    for v in all_vaults:
        s = v.get("summary", {})
        rel = s.get("relationship", {})
        rel_type = rel.get("type", "normal") if isinstance(rel, dict) else "normal"
        if rel_type == "normal" and not s.get("isClosed", False):
            valid.append(v)

    valid.sort(key=lambda x: sf(x.get("summary", {}).get("tvl", 0)), reverse=True)
    top_200 = valid[:200]
    print(f"  총 {len(all_vaults)}개 볼트 중 상위 {len(top_200)}개 선별")

    # 3) DB 연결
    conn = init_db()
    c = conn.cursor()
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    saved = 0
    skipped = 0

    for v in top_200:
        s = v.get("summary", {})
        addr = s.get("vaultAddress", "")
        name = s.get("name", "Unknown")[:60]
        tvl = sf(s.get("tvl", 0))

        if not addr:
            continue

        # PnL 기간별 추출
        pnls_data = {}
        for period_name, vals in v.get("pnls", []):
            pnls_data[period_name] = [sf(x) for x in vals]

        day_pnl = pnls_data.get("day", [])
        week_pnl = pnls_data.get("week", [])
        month_pnl = pnls_data.get("month", [])
        alltime_pnl = pnls_data.get("allTime", [])

        # MDD 계산
        day_mdd = calc_mdd_from_array(day_pnl, tvl)
        week_mdd = calc_mdd_from_array(week_pnl, tvl)
        month_mdd = calc_mdd_from_array(month_pnl, tvl)

        # 볼트 메타 업드이트
        c.execute("""
            INSERT INTO vaults (address, name, first_seen, last_seen)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(address) DO UPDATE SET
                name=excluded.name,
                last_seen=excluded.last_seen
        """, (addr, name, today_str, today_str))

        # 일별 PnL 저장 (중복 방지: 같은 날 같은 볼트는 스킵)
        try:
            c.execute("""
                INSERT INTO daily_pnl (
                    vault_address, collected_at, tvl,
                    alltime_pnl,
                    day_pnl_max, day_pnl_min, day_pnl_last,
                    week_pnl_max, week_pnl_min, week_pnl_last,
                    month_pnl_max, month_pnl_min, month_pnl_last,
                    day_mdd_pct, week_mdd_pct, month_mdd_pct,
                    day_pnl_raw, week_pnl_raw, month_pnl_raw, alltime_pnl_raw
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                addr, today_str, tvl,
                alltime_pnl[-1] if alltime_pnl else 0.0,
                max(day_pnl) if day_pnl else 0.0,
                min(day_pnl) if day_pnl else 0.0,
                day_pnl[-1] if day_pnl else 0.0,
                max(week_pnl) if week_pnl else 0.0,
                min(week_pnl) if week_pnl else 0.0,
                week_pnl[-1] if week_pnl else 0.0,
                max(month_pnl) if month_pnl else 0.0,
                min(month_pnl) if month_pnl else 0.0,
                month_pnl[-1] if month_pnl else 0.0,
                day_mdd, week_mdd, month_mdd,
                json.dumps(day_pnl),
                json.dumps(week_pnl),
                json.dumps(month_pnl),
                json.dumps(alltime_pnl),
            ))
            saved += 1
        except sqlite3.IntegrityError:
            skipped += 1  # 오늘 이미 수집됨

    conn.commit()
    conn.close()

    print(f"\n  ✅ 수집 완료: {saved}개 저장 / {skipped}개 스킵 (이미 존재)")
    print(f"  💾 DB 위치: {DB_PATH}")
    print("=" * 60)
    return saved


# ── DB 현황 조회 ─────────────────────────────────────────────────────────────
def show_db_info():
    """DB에 쌓인 데이터 현황 출력"""
    if not DB_PATH.exists():
        print("  ❌ DB 파일이 없습니다. 먼저 수집을 실행하세요.")
        return

    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM vaults")
    vault_count = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM daily_pnl")
    record_count = c.fetchone()[0]

    c.execute("SELECT MIN(collected_at), MAX(collected_at) FROM daily_pnl")
    date_range = c.fetchone()

    c.execute("SELECT COUNT(DISTINCT collected_at) FROM daily_pnl")
    day_count = c.fetchone()[0]

    # DB 파일 크기
    db_size = DB_PATH.stat().st_size / (1024 * 1024)

    print("=" * 60)
    print("  📊 PnL History Database 현황")
    print("=" * 60)
    print(f"  추적 볼트 수:    {vault_count}개")
    print(f"  총 레코드 수:    {record_count:,}개")
    print(f"  수집 일수:       {day_count}일")
    print(f"  데이터 기간:     {date_range[0]} ~ {date_range[1]}")
    print(f"  DB 파일 크기:    {db_size:.1f} MB")
    print(f"  DB 위치:         {DB_PATH}")
    print("=" * 60)

    # 상위 5개 볼트의 데이터 현황
    c.execute("""
        SELECT v.name, COUNT(d.id) as days, MIN(d.collected_at), MAX(d.collected_at)
        FROM daily_pnl d
        JOIN vaults v ON d.vault_address = v.address
        GROUP BY d.vault_address
        ORDER BY days DESC
        LIMIT 5
    """)
    rows = c.fetchall()
    if rows:
        print("\n  [데이터 축적 상위 5개 볼트]")
        for name, days, first, last in rows:
            print(f"    {name[:30]:<30} {days}일 ({first} ~ {last})")

    conn.close()


# ── 정밀 MDD 계산 (축적된 DB 데이터 활용) ────────────────────────────────────
def get_precise_mdd(vault_address):
    """축적된 DB 데이터로 정밀 전체기간 MDD(%) 계산"""
    if not DB_PATH.exists():
        return None

    conn = sqlite3.connect(str(DB_PATH))
    c = conn.cursor()

    # 날짜순 alltime_pnl 조회
    c.execute("""
        SELECT collected_at, alltime_pnl, tvl
        FROM daily_pnl
        WHERE vault_address = ?
        ORDER BY collected_at ASC
    """, (vault_address,))

    rows = c.fetchall()
    conn.close()

    if len(rows) < 3:
        return None

    import numpy as np
    pnl_series = np.array([r[1] for r in rows], dtype=float)
    avg_tvl = np.mean([r[2] for r in rows])

    rolling_peak = np.maximum.accumulate(pnl_series)
    dd = rolling_peak - pnl_series
    max_dd_dollar = float(np.max(dd))

    peak_pnl = float(np.max(pnl_series))
    if peak_pnl > 0:
        mdd_pct = max_dd_dollar / peak_pnl * 100
    else:
        mdd_pct = max_dd_dollar / (avg_tvl + 1e-9) * 100

    return {
        "mdd_pct": round(mdd_pct, 2),
        "mdd_dollar": round(max_dd_dollar, 2),
        "data_days": len(rows),
        "date_range": f"{rows[0][0]} ~ {rows[-1][0]}",
    }


# ── 메인 ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Daily PnL Collector")
    parser.add_argument("--info", action="store_true", help="DB 현황 조회")
    args = parser.parse_args()

    if args.info:
        show_db_info()
    else:
        collect_all_vaults()
        show_db_info()
