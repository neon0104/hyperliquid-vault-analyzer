#!/usr/bin/env python3
"""
resilience_analyzer.py — 역사적 MDD 및 회복탄력성 저점 매수 알림 분석기
========================================================================
- 전체 스냅샷 데이터를 분석하여 역사적 MDD와 과거 드로우다운 복구 이력을 측정합니다.
- 역사적 MDD 지지선 부근에 도달했으나 회복 속도가 검증된 볼트를 발굴하여 알람을 생성합니다.
"""
import os
import sys
import json
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ── 경로 설정 ─────────────────────────────────────────────────────────────────
BASE_DIR        = Path(__file__).parent
DATA_DIR        = BASE_DIR / "vault_data"
SNAPSHOTS_DIR   = DATA_DIR / "snapshots"
STATUS_FILE     = DATA_DIR / "status.json"
ALERTS_LOG      = DATA_DIR / "alerts.jsonl"
RESILIENCE_FILE = DATA_DIR / "resilience_alerts.json"

def get_tvl_change_7d(vault_addr: str, snapshots: dict) -> float:
    dates = sorted(snapshots.keys())
    if len(dates) < 2:
        return 0.0
    latest_date_str = dates[-1]
    latest_date = datetime.strptime(latest_date_str, "%Y-%m-%d")
    target_date = latest_date - timedelta(days=7)
    
    # 7일 전과 가장 가까운 날짜의 스냅샷 찾기
    closest_date_str = min(dates[:-1], key=lambda d: abs(datetime.strptime(d, "%Y-%m-%d") - target_date))
    
    latest_snap = snapshots[latest_date_str]
    old_snap = snapshots[closest_date_str]
    
    if vault_addr not in latest_snap or vault_addr not in old_snap:
        return 0.0
        
    latest_tvl = float(latest_snap[vault_addr].get("tvl", 0.0) or 0.0)
    old_tvl = float(old_snap[vault_addr].get("tvl", 0.0) or 0.0)
    
    if old_tvl <= 0:
        return 0.0
        
    return float((latest_tvl - old_tvl) / old_tvl * 100)


# ── 드로우다운 및 회복 패턴 계산 ────────────────────────────────────────────────
def analyze_vault_resilience(vault_addr: str, snapshots: dict) -> dict:
    dates = sorted(snapshots.keys())
    if len(dates) < 5:
        return None

    equity_curve = []
    valid_dates = []
    
    # 볼트의 최종 정보 확보
    final_tvl = 1.0
    vault_name = vault_addr[:16]
    allow_dep = True
    
    for d in reversed(dates):
        if vault_addr in snapshots[d]:
            final_tvl = float(snapshots[d][vault_addr].get("tvl", 1.0) or 1.0)
            vault_name = snapshots[d][vault_addr].get("name", vault_name)
            allow_dep = snapshots[d][vault_addr].get("allow_deposits", True)
            break
            
    for d in dates:
        if vault_addr in snapshots[d]:
            v = snapshots[d][vault_addr]
            pnl_arr = v.get("alltime_pnl", [])
            if pnl_arr:
                # 스냅샷 내 누적 PnL 및 자산 가치 복원
                cumulative_pnl = pnl_arr[-1]
                equity = final_tvl + cumulative_pnl
                equity_curve.append(equity)
                valid_dates.append(d)
                
    if len(equity_curve) < 10:
        return None
        
    eq = np.array(equity_curve, dtype=float)
    
    # 고점 대비 드로우다운 계산
    running_max = np.maximum.accumulate(eq)
    denom = np.where(running_max > 0, running_max, 1.0)
    drawdowns = (running_max - eq) / denom * 100
    
    historical_max_mdd = float(drawdowns.max())
    current_dd = float(drawdowns[-1])
    
    # 드로우다운 회복 이벤트 추적
    in_drawdown = False
    dd_start_idx = 0
    dd_peak_val = 0.0
    
    drawdown_events = []
    # 역사적 최대 MDD의 40% 이상 하락했을 때 유의미한 드로우다운 이벤트로 정의
    threshold = max(5.0, historical_max_mdd * 0.4)
    
    for i in range(len(drawdowns)):
        dd = drawdowns[i]
        
        if not in_drawdown and dd >= threshold:
            in_drawdown = True
            dd_start_idx = i
            dd_peak_val = dd
        elif in_drawdown:
            if dd > dd_peak_val:
                dd_peak_val = dd
            
            if dd <= 0.1:  # 회복 완료 (0% 근처 도달)
                in_drawdown = False
                recovery_days = (np.datetime64(valid_dates[i]) - np.datetime64(valid_dates[dd_start_idx])).astype(int)
                drawdown_events.append({
                    "start_date": valid_dates[dd_start_idx],
                    "end_date": valid_dates[i],
                    "peak_drawdown": round(dd_peak_val, 2),
                    "recovery_days": int(recovery_days),
                    "status": "Recovered"
                })
                dd_peak_val = 0.0
                
    if in_drawdown:
        ongoing_days = (np.datetime64(valid_dates[-1]) - np.datetime64(valid_dates[dd_start_idx])).astype(int)
        drawdown_events.append({
            "start_date": valid_dates[dd_start_idx],
            "end_date": "Ongoing",
            "peak_drawdown": round(dd_peak_val, 2),
            "recovery_days": int(ongoing_days),
            "status": "Ongoing"
        })
        
    recovered_events = [e for e in drawdown_events if e["status"] == "Recovered"]
    
    # 회복 탄력성 점수 (많이 회복할수록, 빨리 회복할수록 고점)
    # 기본 스코어: 회복 횟수(최대 5회) * 0.2 + (1 - avg_recovery_days / 90) * 0.5 (양수 제한)
    avg_rec_days = np.mean([e["recovery_days"] for e in recovered_events]) if recovered_events else 0.0
    resilience_score = 0.0
    if recovered_events:
        resilience_score = min(5, len(recovered_events)) * 0.1 + max(0, 1.0 - avg_rec_days / 60.0) * 0.5
        
    return {
        "address": vault_addr,
        "name": vault_name,
        "historical_max_mdd": round(historical_max_mdd, 2),
        "current_drawdown": round(current_dd, 2),
        "total_drawdown_events": len(drawdown_events),
        "recovered_count": len(recovered_events),
        "avg_recovery_days": round(float(avg_rec_days), 1),
        "resilience_score": round(float(resilience_score), 3),
        "allow_deposits": allow_dep,
        "events": drawdown_events
    }

# ── 회복탄력성 매수 기회 검증 ─────────────────────────────────────────────────
def detect_resilience_opportunities(snapshots: dict) -> list:
    latest_date = sorted(snapshots.keys())[-1]
    latest_snap = snapshots[latest_date]
    
    opps = []
    
    for addr in latest_snap.keys():
        res = analyze_vault_resilience(addr, snapshots)
        if not res:
            continue
            
        hist_mdd = res["historical_max_mdd"]
        curr_dd = res["current_drawdown"]
        rec_count = res["recovered_count"]
        avg_rec_days = res["avg_recovery_days"]
        allow_dep = res["allow_deposits"]
        
        if hist_mdd <= 3.0 or not allow_dep:
            continue
            
        # ── 저점 매수 경보 조건 판정 ──
        # 1) 현재 낙폭이 역사상 최대 MDD의 70% 이상 수준으로 지지선 근처 도달
        # 2) 단, 역사상 최대 MDD의 1.15배를 뚫고 신저점을 파괴적으로 흘러내리는 진짜 추세 붕괴는 제외
        # 3) 과거 회복 성공 이력이 최소 1회 이상
        # 4) 평균 회복 일수가 45일 이하인 탄력적 자산
        is_opp = (
            curr_dd >= hist_mdd * 0.70
            and curr_dd <= hist_mdd * 1.15
            and rec_count >= 1
            and avg_rec_days <= 45.0
        )
        
        # 진짜 추세 붕괴 자산 (역사적 MDD 지지선 붕괴)
        is_broken = (
            curr_dd > hist_mdd * 1.15
            and (rec_count == 0 or avg_rec_days > 45.0)
        )
        
        res["is_buy_the_dip_opportunity"] = is_opp
        res["is_broken_trend"] = is_broken
        
        if is_opp:
            opps.append(res)
            
    return opps

# ── 텔레그램 및 알림 파일 연동 ─────────────────────────────────────────────────
def send_resilience_alerts(opportunities: list):
    if not opportunities:
        return
        
    try:
        from telegram_bot import send_message
    except ImportError:
        print("[Resilience] Warning: telegram_bot module not found, cannot send Telegram alerts.")
        return

    for opp in opportunities:
        msg = (
            f"🚨 <b>[회복탄력성 저점 매수 기회 감지]</b>\n\n"
            f"볼트명: <b>{opp['name']}</b>\n"
            f"주소: <code>{opp['address']}</code>\n"
            f"역사적 최대 MDD: <b>{opp['historical_max_mdd']:.2f}%</b>\n"
            f"현재 드로우다운: <b>{opp['current_drawdown']:.2f}%</b> (바닥 지지선 도달)\n"
            f"과거 복구 성공 횟수: <b>{opp['recovered_count']}회</b>\n"
            f"평균 복구 기간: <b>{opp['avg_recovery_days']:.1f}일</b>\n\n"
            f"👉 <i>과거 신속하게 원복에 성공했던 초우량 볼트가 역사적 지지선 부근까지 하락했습니다. 포트폴리오 편입이나 비중 추가를 적극 고려해 보세요!</i>"
        )
        
        # 텔레그램 전송
        send_message(msg)
        
        # alerts.jsonl에 기록
        alert_log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "RESILIENCE_ALERT",
            "vault_name": opp["name"],
            "vault_address": opp["address"],
            "historical_max_mdd": opp["historical_max_mdd"],
            "current_drawdown": opp["current_drawdown"],
            "message": f"{opp['name']} 볼트 회복탄력성 저점 도달 알림"
        }
        
        try:
            with open(ALERTS_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(alert_log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"[Resilience] Failed to write alert log: {e}")

def check_and_alert_tvl_outflows(snapshots: dict):
    """최근 7일간 TVL이 20% 이상 급감한 볼트를 감지하여 경고 알림 전송 및 기록"""
    latest_date = sorted(snapshots.keys())[-1]
    latest_snap = snapshots[latest_date]
    outflows = []
    
    for addr, v in latest_snap.items():
        change = get_tvl_change_7d(addr, snapshots)
        if change <= -20.0:
            outflows.append({
                "address": addr,
                "name": v.get("name", addr[:16]),
                "tvl_change_7d": round(change, 2),
                "current_tvl": float(v.get("tvl", 0.0) or 0.0)
            })
            
    if not outflows:
        return
        
    print(f"[Resilience] Detected {len(outflows)} vaults with severe TVL outflow.")
    
    # 텔레그램 알림 발송 시도
    try:
        from telegram_bot import send_message
    except ImportError:
        send_message = None
        
    for opp in outflows:
        msg = (
            f"⚠️ <b>[볼트 자금 급격 유출 경고]</b>\n\n"
            f"볼트명: <b>{opp['name']}</b>\n"
            f"주소: <code>{opp['address']}</code>\n"
            f"최근 7일 TVL 변동률: <b>{opp['tvl_change_7d']:.1f}%</b> (자금 급유출)\n"
            f"현재 TVL: <b>${opp['current_tvl']:,.0f}</b>\n\n"
            f"👉 <i>최근 7일간 볼트에서 20% 이상의 자금이 급격히 유출되었습니다. 뱅크런 또는 운용 전략의 신뢰 붕괴 위험이 있으므로 상태를 긴밀히 점검하시길 권장합니다.</i>"
        )
        if send_message:
            send_message(msg)
            
        # alerts.jsonl에 기록
        alert_log_entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "TVL_OUTFLOW_ALERT",
            "vault_name": opp["name"],
            "vault_address": opp["address"],
            "tvl_change_7d": opp["tvl_change_7d"],
            "current_tvl": opp["current_tvl"],
            "message": f"{opp['name']} 볼트 7일 TVL 급감 경고 ({opp['tvl_change_7d']:.1f}%)"
        }
        try:
            with open(ALERTS_LOG, "a", encoding="utf-8") as f:
                f.write(json.dumps(alert_log_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            print(f"[Resilience] Failed to write outflow alert log: {e}")


# ── 메인 분석 실행 ────────────────────────────────────────────────────────────
def run_resilience_analysis():
    import portfolio_tracker
    snapshots = portfolio_tracker.load_snapshots_all()
    if not snapshots:
        print("[Resilience] Error: No snapshots found.")
        return
        
    opps = detect_resilience_opportunities(snapshots)
    print(f"[Resilience] Detected {len(opps)} Buy the Dip opportunities.")
    
    # resilience_alerts.json 에 결과 저장
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(RESILIENCE_FILE, "w", encoding="utf-8") as f:
            json.dump(opps, f, ensure_ascii=False, indent=2)
        print(f"[Resilience] Saved alerts to {RESILIENCE_FILE}")
    except Exception as e:
        print(f"[Resilience] Failed to save resilience alerts: {e}")
        
    # 알림 발송
    send_resilience_alerts(opps)
    
    # TVL 유출 검사 및 알림
    check_and_alert_tvl_outflows(snapshots)
    
    # status.json 에 알림 수 업데이트
    if STATUS_FILE.exists():
        try:
            status = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
            status["resilience_opportunities_count"] = len(opps)
            status["last_resilience_check"] = datetime.now().isoformat()
            STATUS_FILE.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

if __name__ == "__main__":
    run_resilience_analysis()
