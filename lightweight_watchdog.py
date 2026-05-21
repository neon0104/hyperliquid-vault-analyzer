#!/usr/bin/env python3
"""
lightweight_watchdog.py — 24/7 Hyperliquid 볼트 3대 규칙 경량화 감시 데몬
=======================================================================
메모리 점유율을 15MB 이하로 최소화하기 위해 numpy, pandas 등의 중형 라이브러리를 배제하고,
순수 파이썬 표준 라이브러리(urllib, json, sqlite3 등)만을 사용하여
매시간 3대 안전 수칙 위반 여부와 슬럼프 탈출 기회 볼트를 탐색하는 초경량 백그라운드 감시 데몬입니다.

3대 안전 수칙:
1. 규칙 1: 과매도 반등 포착 (Satellite Undervalue Snatch)
   - Robustness Score > 0.4 이면서, 30일 이내 단기 슬럼프(undervalue_score > 0.2)를 겪다 최근 3일간 누적 PnL이 양수(+)로 뚜렷하게 전환된 SATELLITE 볼트 감지 및 편입 권고.
2. 규칙 2: 위성 수익 실현 규칙 (Satellite Profit-Taking Guard)
   - 포트폴리오 내 SATELLITE 볼트 누적 수익률이 40% 돌파 시 익절 및 안전 자산(CORE) 리밸런싱 권고.
3. 규칙 3: 포트폴리오 MDD 경보 (Whole-Portfolio Drawdown Breach Alert)
   - 전체 포트폴리오 MDD가 10%를 초과하거나, 보유 개별 SATELLITE 볼트 MDD가 30% 초과 시 긴급 경보 및 100% CORE 전환 리밸런싱 버튼 활성화.
"""

import os
import sys
import json
import glob
import time
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

# UTF-8 출력 보장 (Windows 콘솔 대응)
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# 경로 설정
BASE_DIR        = Path(__file__).parent
DATA_DIR        = BASE_DIR / "vault_data"
SNAPSHOTS_DIR   = DATA_DIR / "snapshots"
STATUS_FILE     = DATA_DIR / "status.json"
PORTFOLIO_FILE  = BASE_DIR / "my_portfolio.json"
CONFIG_FILE     = BASE_DIR / "telegram_config.json"
STOP_FLAG       = BASE_DIR / "emergency_stop.flag"

# 텔레그램 설정 로드
def load_tg_config():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if CONFIG_FILE.exists():
        try:
            cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            token = token or cfg.get("bot_token", "")
            chat_id = chat_id or cfg.get("chat_id", "")
        except Exception:
            pass
    return token.strip(), str(chat_id).strip()

BOT_TOKEN, CHAT_ID = load_tg_config()

def send_telegram_alert(text: str, keyboard: list = None) -> bool:
    """순수 urllib을 사용해 텔레그램 메시지 발송 (메모리 극단적 절약)"""
    if not BOT_TOKEN or not CHAT_ID:
        print("⚠️ 텔레그램 봇 토큰 혹은 챗 ID가 정의되지 않았습니다.")
        return False
    
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    if keyboard:
        payload["reply_markup"] = {"inline_keyboard": keyboard}
        
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url, 
            data=data, 
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            res = json.loads(response.read().decode("utf-8"))
            return res.get("ok", False)
    except Exception as e:
        print(f"❌ 텔레그램 알림 발송 중 오류: {e}")
        return False

# ── 3대 규칙 연동 감시 엔진 ──────────────────────────────────────────────────

def load_all_snapshots():
    """모든 스냅샷 파일을 날짜순으로 로드"""
    snaps = {}
    files = sorted(glob.glob(str(SNAPSHOTS_DIR / "*.json")))
    for f in files:
        dt = os.path.basename(f).replace(".json", "")
        try:
            with open(f, encoding="utf-8") as fd:
                data = json.load(fd)
                if isinstance(data, list):
                    snaps[dt] = {v["address"]: v for v in data if "address" in v}
        except Exception:
            pass
    return snaps

def run_watchdog_check():
    """3대 감시 규칙 실행 코어"""
    if STOP_FLAG.exists():
        print("🚨 긴급 중단 플래그(emergency_stop.flag) 감지됨. 감시 활동을 보류합니다.")
        return
        
    print(f"⏰ [WATCHDOG] 감시 시작 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 포트폴리오 설정 로드
    if not PORTFOLIO_FILE.exists():
        print("⚠️ my_portfolio.json 파일이 존재하지 않아 감시를 수행할 수 없습니다.")
        return
        
    try:
        portfolio = json.loads(PORTFOLIO_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"❌ 포트폴리오 로드 실패: {e}")
        return
        
    positions = portfolio.get("positions", {})
    invest_date = portfolio.get("invest_date")
    total_capital = float(portfolio.get("total_capital", 100000.0))
    
    if not positions:
        print("ℹ️ 보유 포지션이 비어있습니다.")
        return
        
    # 2. 스냅샷 전체 로드
    snaps = load_all_snapshots()
    if not snaps:
        print("⚠️ 스냅샷 파일이 없어 비교 분석이 불가능합니다.")
        return
        
    dates = sorted(snaps.keys())
    latest_date = dates[-1]
    latest_snap = snaps[latest_date]
    
    # ── [규칙 3]: 포트폴리오 MDD 경보 & SATELLITE 개별 MDD 감시 ──────────────────
    print("🔍 [RULE 3] 전체 포트폴리오 MDD 및 개별 SATELLITE MDD 검사 시작...")
    
    # 보유 볼트별 최초 스냅샷 및 최신 스냅샷 비교를 통한 에쿼티 계산
    portfolio_equity_series = []
    
    # 보유 볼트 중 SATELLITE 여부 확인
    for d in dates:
        if invest_date and d < invest_date:
            continue
        daily_val = 0.0
        for addr, invested_amt in positions.items():
            invested_amt = float(invested_amt)
            first_snap = None
            
            # 투자 시작일 이후 최초 스냅샷 검색
            for sd in dates:
                if invest_date and sd >= invest_date:
                    if sd in snaps and addr in snaps[sd]:
                        first_snap = snaps[sd][addr]
                        break
            
            curr_snap = snaps[d].get(addr)
            if not curr_snap:
                # 중간에 스냅샷 누락 시 직전 알려진 최고 데이터 탐색
                for prev_d in reversed(dates):
                    if prev_d < d and prev_d in snaps and addr in snaps[prev_d]:
                        curr_snap = snaps[prev_d][addr]
                        break
            
            if first_snap and curr_snap:
                p_first = first_snap.get("alltime_pnl", [0])[-1]
                p_curr = curr_snap.get("alltime_pnl", [0])[-1]
                tvl_first = float(first_snap.get("tvl", 1))
                
                my_share = invested_amt / max(tvl_first, 1.0)
                pnl_vault_diff = p_curr - p_first
                my_real_pnl = pnl_vault_diff * my_share
                
                daily_val += (invested_amt + my_real_pnl)
            else:
                # 스냅샷 부재 시 단순 투자금 유지로 추정
                daily_val += invested_amt
                
        portfolio_equity_series.append(daily_val)
        
    # 포트폴리오 Drawdown 산출
    portfolio_mdd = 0.0
    if portfolio_equity_series:
        peak = portfolio_equity_series[0]
        for val in portfolio_equity_series:
            if val > peak:
                peak = val
            dd = (peak - val) / peak * 100 if peak > 0 else 0
            if dd > portfolio_mdd:
                portfolio_mdd = dd
                
    print(f"📊 현재 포트폴리오 계산된 MDD: {portfolio_mdd:.2f}%")
    
    # 전체 MDD 10% 초과 경보
    if portfolio_mdd > 10.0:
        msg = (
            f"🚨 <b>EMERGENCY: 포트폴리오 낙폭 한계 초과 감지!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"포트폴리오 전체 낙폭(MDD)이 안전 한도(10%)를 초과하여 <b>{portfolio_mdd:.2f}%</b>에 봉착했습니다.\n"
            f"원금 보호를 위해 투기성 SATELLITE 자산을 전량 청산하고 안전한 CORE 자산으로 100% 리포지셔닝하는 리밸런싱을 즉각 권장합니다.\n\n"
            f"🛡️ <b>안전 CORE 100% 전환 대상:</b>\n"
            f"  • Cold Process: 50% ($50,000)\n"
            f"  • 22Cap: 50% ($50,000)\n\n"
            f"⚠️ 아래 [✅ 100% CORE 전환 승인] 버튼 클릭 시 포트폴리오 안전 자산 강제 대피가 즉시 백엔드 반영됩니다."
        )
        keyboard = [
            [
                {"text": "✅ 100% CORE 전환 승인", "callback_data": "apply_rebalance"},
                {"text": "❌ 보류 (수동 제어)", "callback_data": "cancel_rebalance"}
            ]
        ]
        send_telegram_alert(msg, keyboard)
        print("🚨 [RULE 3 ALERT SENT] 전체 MDD 10% 돌파 긴급 푸시 전송!")
        return

    # 개별 SATELLITE 볼트 MDD 30% 감시
    for addr, invested_amt in positions.items():
        v = latest_snap.get(addr)
        if not v:
            continue
            
        is_satellite = v.get("barbell_group") == "SATELLITE"
        mdd = float(v.get("max_drawdown", 0))
        name = v.get("name", "Unknown Vault")
        
        if is_satellite and mdd > 30.0:
            msg = (
                f"🚨 <b>EMERGENCY: 개별 위성 볼트 낙폭 한도(30%) 초과!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"SATELLITE 그룹의 <b>{name}</b> 볼트의 역사적 Drawdown이 위험 한도(30%)를 돌파하여 <b>{mdd:.1f}%</b>를 기록했습니다.\n"
                f"과도한 손실 확산을 방지하기 위해 해당 볼트를 강제 포트폴리오에서 청산하고, 안전한 CORE 볼트로 리밸런싱하는 것을 제안합니다.\n\n"
                f"⚙️ <b>비중 긴급 리밸런싱 제안:</b>\n"
                f"  • {name} 비중 청산 (현금화 및 CORE 이동)\n\n"
                f"⚠️ 아래 [✅ 즉시 리밸런싱 실행] 클릭 시, 포트폴리오 안전 비중 조정을 즉시 시작합니다."
            )
            keyboard = [
                [
                    {"text": "✅ 즉시 리밸런싱 실행", "callback_data": "apply_rebalance"},
                    {"text": "❌ 일단 보류하기", "callback_data": "cancel_rebalance"}
                ]
            ]
            send_telegram_alert(msg, keyboard)
            print(f"🚨 [RULE 3 ALERT SENT] 개별 SATELLITE {name} MDD 30% 돌파 긴급 푸시 전송!")
            return

    # ── [규칙 2]: SATELLITE 40% 익절 기준 검사 ─────────────────────────────────
    print("🔍 [RULE 2] SATELLITE 볼트 40% 익절 기준 검사 시작...")
    for addr, invested_amt in positions.items():
        invested_amt = float(invested_amt)
        v = latest_snap.get(addr)
        if not v:
            continue
            
        is_satellite = v.get("barbell_group") == "SATELLITE"
        if not is_satellite:
            continue
            
        name = v.get("name", "Unknown Vault")
        
        # 실제 누적 수익률 계산
        first_snap = None
        for sd in dates:
            if invest_date and sd >= invest_date:
                if sd in snaps and addr in snaps[sd]:
                    first_snap = snaps[sd][addr]
                    break
                    
        p_first = first_snap.get("alltime_pnl", [0])[-1] if first_snap else 0
        p_curr = v.get("alltime_pnl", [0])[-1]
        tvl_first = float(first_snap.get("tvl", 1)) if first_snap else float(v.get("tvl", 1))
        
        my_share = invested_amt / max(tvl_first, 1.0)
        pnl_vault_diff = p_curr - p_first
        my_real_pnl = pnl_vault_diff * my_share
        
        vault_roi_pct = (my_real_pnl / invested_amt * 100) if invested_amt > 0 else 0
        
        print(f"📈 SATELLITE 볼트 {name} 현재 누적 ROI: {vault_roi_pct:.2f}%")
        
        if vault_roi_pct >= 40.0:
            msg = (
                f"💰 <b>SATELLITE [ {name} ] 목표 수익(40%+) 달성!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"포트폴리오에 편입했던 성장주 <b>{name}</b> 볼트가 누적 수익률 <b>{vault_roi_pct:.1f}%</b>를 돌파하여 목표 익절 기준(40%)을 충족했습니다!\n\n"
                f"기계적인 리스크 분산 수칙에 따라, <b>이익금의 50%를 안전한 CORE 우량주 볼트로 환원하고, 나머지 50%는 현금화(또는 대피)</b>하여 안정적 누적 yield를 실현할 것을 강력히 권장합니다.\n\n"
                f"⚖️ <b>익절 수동 확정 제안 (바벨 최적화 리밸런싱):</b>\n"
                f"  • {name} 초과 이익 확정 및 CORE 자산 전입\n\n"
                f"⚠️ 아래 버튼을 클릭하여 기계적인 이익 보존 리밸런싱을 안전하게 즉시 단행하세요."
            )
            keyboard = [
                [
                    {"text": "✅ 즉시 리밸런싱 실행", "callback_data": "apply_rebalance"},
                    {"text": "❌ 일단 보유하기", "callback_data": "cancel_rebalance"}
                ]
            ]
            send_telegram_alert(msg, keyboard)
            print(f"💰 [RULE 2 ALERT SENT] SATELLITE {name} 익절 40% 달성 알림 전송!")
            return

    # ── [규칙 1]: 과매도 반등 포착 (Satellite Undervalue Snatch) ─────────────────
    print("🔍 [RULE 1] 과매도 SATELLITE 반등 포착 검사 시작...")
    
    # 3일 전 날짜 및 인덱스 획득
    if len(dates) >= 4:
        three_days_ago_date = dates[-4]
        
        for addr, v in latest_snap.items():
            # 포트폴리오에 이미 보유한 볼트는 제외
            if addr in positions:
                continue
                
            is_satellite = v.get("barbell_group") == "SATELLITE"
            if not is_satellite:
                continue
                
            robustness = float(v.get("robustness_score", 0))
            undervalue = float(v.get("undervalue_score", 0))
            name = v.get("name", "Unknown Vault")
            
            # 조건: Robustness > 0.4, 30일 이내 단기 슬럼프(undervalue > 0.20)
            if robustness > 0.40 and undervalue > 0.20:
                # 3일 전 스냅샷과 PnL 비교
                v_3d = snaps[three_days_ago_date].get(addr)
                if v_3d:
                    p_3d = v_3d.get("alltime_pnl", [0])[-1]
                    p_curr = v.get("alltime_pnl", [0])[-1]
                    
                    pnl_diff_3d = p_curr - p_3d
                    # 최근 3일간 누적 PnL이 확실한 양수(+) 즉, 상승세로 전환
                    if pnl_diff_3d > 0:
                        msg = (
                            f"📉 <b>역사적 MDD 근처의 고탄력 회복 볼트 발견!</b>\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"SATELLITE 그룹에서 장기 펀더멘탈(Robustness Score: {robustness:.2f})이 굳건하며, "
                            f"최근 30일간 단기 슬럼프(저평가 지수: {undervalue:.2f})를 겪다가, "
                            f"<b>최근 3일간 뚜렷한 누적 PnL 반등세(+{pnl_diff_3d:,.2f})</b>를 보이며 강력한 모멘텀을 탄 볼트 <b>{name}</b>를 포착했습니다!\n\n"
                            f"현재의 극적인 반등 시그널을 놓치지 않기 위해, 포트폴리오 자산의 <b>20% 비중</b>을 해당 슬럼프 탈출 볼트에 긴급 교체 편입할 것을 권장합니다.\n\n"
                            f"⚖️ <b>추천 비중 갈아타기 구성:</b>\n"
                            f"  • CORE 🛡️: Cold Process (25%), 22Cap (25%)\n"
                            f"  • SATELLITE 🚀: <b>{name} (20% 신규 편입)</b>, SWORM (15%), IKAGI (15%)\n\n"
                            f"⚠️ 아래 [✅ 즉시 리밸런싱 실행] 버튼을 클릭하시면 실제 my_portfolio.json에 {name} 20% 편입을 비롯한 리밸런싱이 실시간 적용됩니다."
                        )
                        keyboard = [
                            [
                                {"text": "✅ 즉시 리밸런싱 실행", "callback_data": "apply_rebalance"},
                                {"text": "❌ 일단 보류하기", "callback_data": "cancel_rebalance"}
                            ]
                        ]
                        send_telegram_alert(msg, keyboard)
                        print(f"📉 [RULE 1 ALERT SENT] {name} 과매도 반등 포착 푸시 전송!")
                        return
                        
    print("✨ [WATCHDOG] 이번 회차의 감시 검사가 이상 없이 완료되었습니다.")

if __name__ == "__main__":
    # 백그라운드 24/7 구동 루프
    print("🚀 [WATCHDOG] Hyperliquid Vault 3대 규칙 경량화 감시 데몬 기동 완료! (RAM < 15MB)")
    print("   매 1시간마다 스냅샷 데이터를 모니터링하여 위험 및 알파 기회를 포착합니다.")
    
    # 기동 시 즉시 1차 체크
    try:
        run_watchdog_check()
    except Exception as e:
        print(f"❌ 감시 중 오류 발생: {e}")
        
    # 24/7 백그라운드 주기 실행 (1시간)
    while True:
        try:
            # 3600초(1시간) 대기
            time.sleep(3600)
            run_watchdog_check()
        except KeyboardInterrupt:
            print("🛑 감시 데몬이 강제 종료되었습니다.")
            break
        except Exception as e:
            print(f"❌ 감시 루프 오류: {e}")
            time.sleep(60)
