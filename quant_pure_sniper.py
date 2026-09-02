import os, sys, json, glob
import numpy as np
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR      = Path(r'c:\Users\USER\.gemini\antigravity\scratch\hyperliquid-vault-analyzer')
DATA_DIR      = BASE_DIR / 'vault_data'
SNAPSHOTS_DIR = DATA_DIR / 'snapshots'

files = sorted(SNAPSHOTS_DIR.glob('*.json'))
snapshots_cache = {}
for f in files:
    date_str = f.stem
    with open(f, 'r', encoding='utf-8') as fd:
        snapshots_cache[date_str] = json.load(fd)

dates = sorted(snapshots_cache.keys())
start_date = '2026-04-09'
sim_dates = [d for d in dates if d >= start_date]

def get_vault_pnl_tvl_apr(v: dict):
    pnl_arr = v.get('alltime_pnl', [])
    if isinstance(pnl_arr, list) and len(pnl_arr) > 0:
        pnl_val = float(pnl_arr[-1])
    else:
        pnl_val = float(v.get('pnl_alltime', 0.0) or v.get('alltime_pnl', 0.0) or 0.0)
    tvl_val = float(v.get('tvl', 1.0) or 1.0)
    apr_30d = float(v.get('apr_30d', 0.0) or v.get('apr_pct', 0.0) or 0.0)
    return pnl_val, max(tvl_val, 1.0), apr_30d

def compute_sm_score(v: dict):
    apr = float(v.get('apr_30d', 0.0) or v.get('apr_pct', 0.0) or 0.0)
    robustness = float(v.get('robustness_score', 0.0) or 0.0)
    sharpe = float(v.get('sharpe_ratio', 0.0) or 0.0)
    if apr <= 0: return -100.0
    return (sharpe * 20.0) + (apr * 0.5) + (robustness * 30.0)

def calculate_dynamic_sizing_score(v: dict):
    tvl = float(v.get('tvl', 0.0) or 0.0)
    apr = float(v.get('apr_30d', 0.0) or v.get('apr_pct', 0.0) or 0.0)
    leader_usd = float(v.get('leader_equity_usd', 0.0) or 0.0)
    robustness = float(v.get('robustness_score', 0.0) or 0.0)
    
    # 4대 핵심 지표 정밀 가중 점수 (0 ~ 100)
    tvl_score = min(25.0, (tvl / 50000.0) * 25.0)
    apr_score = min(25.0, max(0.0, (apr / 100.0) * 25.0))
    leader_score = min(25.0, (leader_usd / 50000.0) * 25.0)
    rob_score = min(25.0, (robustness / 0.5) * 25.0)
    
    return tvl_score + apr_score + leader_score + rob_score

# -------------------------------------------------------------
# EXPERIMENT 1: Pure Cash Dip-Sniper (현금 100% 대기 -> 95% MDD 딥바잉 -> 고속 익절 후 현금화)
# -------------------------------------------------------------
def run_pure_dip_sniper(dip_threshold_ratio=0.95, max_vault_mdd=25.0, min_robustness=0.35, exit_recovery=0.70):
    INITIAL_CAPITAL = 100000.0
    cash = INITIAL_CAPITAL
    active_dips = {} # addr: {...}
    daily_values = []
    fees = 0.0
    trades = []
    
    for d_idx, d_str in enumerate(sim_dates):
        current_snap = snapshots_cache[d_str]
        snap_map = {v['address']: v for v in current_snap}
        
        # 1. Update and Exit Active Dips
        for addr, pos in list(active_dips.items()):
            if addr in snap_map:
                v = snap_map[addr]
                pnl_now, tvl_now, _ = get_vault_pnl_tvl_apr(v)
                pnl_diff = pnl_now - pos['pnl_start']
                my_pnl = pnl_diff * pos['share']
                pos['amount'] = max(10.0, pos['cost'] + my_pnl)
                
                curr_dd = float(v.get('drawdown_now', 0.0) or 0.0)
                hist_mdd = max(0.5, float(v.get('max_drawdown', 10.0) or 10.0))
                
                profit_pct = (pos['amount'] - pos['cost']) / pos['cost']
                recovered_ratio = 1.0 - (curr_dd / hist_mdd)
                
                # Fast Exit Trigger
                if recovered_ratio >= exit_recovery or profit_pct >= 0.08 or curr_dd <= 1.5:
                    gross = pos['amount']
                    profit = gross - pos['cost']
                    p_fee = max(0.0, profit * 0.10)
                    t_fee = gross * 0.0005
                    net_out = gross - p_fee - t_fee
                    fees += (p_fee + t_fee)
                    cash += net_out
                    
                    trades.append({
                        'date': d_str, 'vault': pos['name'], 'profit': profit,
                        'profit_pct': profit_pct * 100, 'days': d_idx - pos['entry_day']
                    })
                    del active_dips[addr]
                elif (pos['cost'] - pos['amount']) / pos['cost'] >= 0.15: # Stop loss
                    gross = pos['amount']
                    t_fee = gross * 0.0005
                    net_out = gross - t_fee
                    fees += t_fee
                    cash += net_out
                    trades.append({
                        'date': d_str, 'vault': pos['name'], 'profit': pos['amount'] - pos['cost'],
                        'profit_pct': -15.0, 'days': d_idx - pos['entry_day']
                    })
                    del active_dips[addr]

        # 2. Look for Sniper Entry
        for v in current_snap:
            addr = v['address']
            allow_dep = bool(v.get('allow_deposits', True))
            robustness = float(v.get('robustness_score', 0.0) or 0.0)
            curr_dd = float(v.get('drawdown_now', 0.0) or 0.0)
            hist_mdd = float(v.get('max_drawdown', 0.0) or 0.0)
            tvl = float(v.get('tvl', 0.0) or 0.0)
            
            if not allow_dep or hist_mdd < 3.0 or hist_mdd > max_vault_mdd or robustness < min_robustness or tvl < 10000:
                continue
                
            dd_ratio = curr_dd / hist_mdd
            if dd_ratio >= dip_threshold_ratio and addr not in active_dips:
                comp_score = calculate_dynamic_sizing_score(v)
                # Dynamic Sizing based on available cash & score
                target_size = cash * (0.10 + (comp_score / 100.0) * 0.20) # 10% ~ 30% of cash
                target_size = min(target_size, 25000.0)
                
                if cash >= target_size and target_size >= 3000.0:
                    cash -= target_size
                    pnl_s, tvl_s, apr_s = get_vault_pnl_tvl_apr(v)
                    active_dips[addr] = {
                        'name': v['name'], 'cost': target_size, 'amount': target_size,
                        'pnl_start': pnl_s, 'tvl_start': tvl_s, 'apr_start': apr_s,
                        'share': target_size / (tvl_s + target_size),
                        'entry_dd': curr_dd, 'hist_mdd': hist_mdd,
                        'comp_score': comp_score, 'entry_day': d_idx
                    }
                    
        total_day_val = cash + sum(p['amount'] for p in active_dips.values())
        daily_values.append(total_day_val)
        
    final_val = daily_values[-1]
    net_ret = ((final_val - INITIAL_CAPITAL) / INITIAL_CAPITAL) * 100.0
    peaks = np.maximum.accumulate(daily_values)
    mdd = np.max((peaks - np.array(daily_values)) / peaks * 100.0)
    daily_rets = np.diff(daily_values) / daily_values[:-1]
    sharpe = (np.mean(daily_rets) / (np.std(daily_rets) + 1e-9)) * np.sqrt(365)
    
    return {
        'net_return': net_ret, 'mdd': mdd, 'sharpe': sharpe,
        'final': final_val, 'trades_count': len(trades),
        'win_rate': len([t for t in trades if t['profit'] > 0]) / (len(trades) or 1) * 100,
        'avg_profit_pct': np.mean([t['profit_pct'] for t in trades]) if trades else 0.0,
        'avg_days': np.mean([t['days'] for t in trades]) if trades else 0.0,
        'trades': trades
    }

print('=== EXPERIMENT 1: PURE DIP SNIPER (100% Cash -> 95% MDD Dip Entry -> Fast Exit) ===')
for t in [0.70, 0.80, 0.85, 0.90, 0.95]:
    for max_mdd in [20.0, 30.0, 45.0]:
        res = run_pure_dip_sniper(dip_threshold_ratio=t, max_vault_mdd=max_mdd, min_robustness=0.30, exit_recovery=0.70)
        print(f"Thresh: {t*100:2.0f}% | MaxVaultMDD: <={max_mdd:2.0f}% -> Return: {res['net_return']:>6.2f}%, MDD: {res['mdd']:>5.2f}%, Sharpe: {res['sharpe']:>5.2f}, WinRate: {res['win_rate']:>5.1f}% ({res['trades_count']} trades, avg hold {res['avg_days']:.1f}d)")

