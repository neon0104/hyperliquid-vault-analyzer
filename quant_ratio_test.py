import os, sys, json, glob
import numpy as np
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR      = Path(r'c:\Users\USER\.gemini\antigravity\scratch\hyperliquid-vault-analyzer')
DATA_DIR      = BASE_DIR / 'vault_data'
SNAPSHOTS_DIR = DATA_DIR / 'snapshots'

# Snapshots Cache
files = sorted(SNAPSHOTS_DIR.glob('*.json'))
snapshots_cache = {}
for f in files:
    date_str = f.stem
    with open(f, 'r', encoding='utf-8') as fd:
        snapshots_cache[date_str] = json.load(fd)

dates = sorted(snapshots_cache.keys())
start_date = '2026-04-09'
sim_dates = [d for d in dates if d >= start_date]

def get_vault_metrics(v: dict):
    pnl_arr = v.get('alltime_pnl', [])
    if isinstance(pnl_arr, list) and len(pnl_arr) > 0:
        pnl_val = float(pnl_arr[-1])
    else:
        pnl_val = float(v.get('pnl_alltime', 0.0) or v.get('alltime_pnl', 0.0) or 0.0)
    tvl_val = max(float(v.get('tvl', 1.0) or 1.0), 1.0)
    apr_30d = float(v.get('apr_30d', 0.0) or v.get('apr_pct', 0.0) or 0.0)
    sharpe = float(v.get('sharpe_ratio', 0.0) or 0.0)
    rob = float(v.get('robustness_score', 0.0) or 0.0)
    l_usd = float(v.get('leader_equity_usd', 0.0) or 0.0)
    h_mdd = max(float(v.get('max_drawdown', 10.0) or 10.0), 0.5)
    return pnl_val, tvl_val, apr_30d, sharpe, rob, l_usd, h_mdd

def compute_sm_score(v: dict):
    apr = float(v.get('apr_30d', 0.0) or v.get('apr_pct', 0.0) or 0.0)
    robustness = float(v.get('robustness_score', 0.0) or 0.0)
    sharpe = float(v.get('sharpe_ratio', 0.0) or 0.0)
    if apr <= 0: return -100.0
    return (sharpe * 20.0) + (apr * 0.5) + (robustness * 30.0)

def select_vaults(snapshot: list):
    filtered = []
    for v in snapshot:
        allow_dep = bool(v.get('allow_deposits', True))
        robustness = float(v.get('robustness_score', 0) or 0)
        mdd = float(v.get('max_drawdown', 0) or 0)
        apr = float(v.get('apr_30d', 0) or v.get('apr_pct', 0) or 0)
        if allow_dep and (robustness >= 0.15) and (mdd <= 35.0) and apr > 0:
            v_copy = dict(v)
            v_copy['score'] = compute_sm_score(v)
            filtered.append(v_copy)
    if not filtered:
        filtered = [dict(v) for v in snapshot[:4]]
        for v in filtered: v['score'] = compute_sm_score(v)
    filtered.sort(key=lambda x: x['score'], reverse=True)
    return filtered[:2], filtered[2:4]

# -------------------------------------------------------------
# 1. CORE : SATELLITE ALLOCATION RATIO GRID TEST
# -------------------------------------------------------------
def test_allocation_ratios():
    ratios = [
        (1.0, 0.0, '100:0 (All Core Top 2)'),
        (0.9, 0.1, '90:10'),
        (0.8, 0.2, '80:20 (Active Best)'),
        (0.7, 0.3, '70:30'),
        (0.6, 0.4, '60:40'),
        (0.5, 0.5, '50:50 (Equal Core/Sat)'),
        (0.25, 0.75, 'Equal 4-way (25% each)')
    ]
    
    print('=== 1. CORE : SATELLITE ALLOCATION RATIO BACKTEST ===')
    for c_w, s_w, name in ratios:
        INITIAL_CAPITAL = 100000.0
        total_capital = INITIAL_CAPITAL
        active_holdings = {}
        daily_values = []
        cumulative_fees = INITIAL_CAPITAL * 0.0005
        
        first_snap = snapshots_cache[sim_dates[0]]
        core_v, sat_v = select_vaults(first_snap)
        
        c_alloc = (total_capital * c_w) / (len(core_v) or 1)
        s_alloc = (total_capital * s_w) / (len(sat_v) or 1) if sat_v and s_w > 0 else 0.0
        
        for v in core_v:
            addr = v['address']
            pnl_s, tvl_s, apr_s, _, rob, _, h_mdd = get_vault_metrics(v)
            active_holdings[addr] = {
                'name': v['name'], 'cost': c_alloc, 'amount': c_alloc,
                'pnl_start': pnl_s, 'tvl_start': tvl_s, 'apr_start': apr_s,
                'share': c_alloc / (tvl_s + c_alloc), 'peak_amount': c_alloc,
                'invest_date': sim_dates[0], 'type': 'CORE', 'mdd_tol': 18.0, 'rob': rob, 'hist_mdd': h_mdd
            }
        if s_w > 0:
            for v in sat_v:
                addr = v['address']
                pnl_s, tvl_s, apr_s, _, rob, _, h_mdd = get_vault_metrics(v)
                active_holdings[addr] = {
                    'name': v['name'], 'cost': s_alloc, 'amount': s_alloc,
                    'pnl_start': pnl_s, 'tvl_start': tvl_s, 'apr_start': apr_s,
                    'share': s_alloc / (tvl_s + s_alloc), 'peak_amount': s_alloc,
                    'invest_date': sim_dates[0], 'type': 'SAT', 'mdd_tol': 18.0, 'rob': rob, 'hist_mdd': h_mdd
                }
                
        for d_idx, d_str in enumerate(sim_dates):
            current_snap = snapshots_cache[d_str]
            snap_map = {v['address']: v for v in current_snap}
            
            for addr, h in list(active_holdings.items()):
                v_curr = snap_map.get(addr)
                if v_curr:
                    pnl_c, _, _, _, _, _, _ = get_vault_metrics(v_curr)
                    pnl_diff = pnl_c - h['pnl_start']
                    my_pnl = pnl_diff * h['share']
                else:
                    my_pnl = 0.0
                h['amount'] = max(0.0, h['cost'] + my_pnl)
                if h['amount'] > h['peak_amount']:
                    h['peak_amount'] = h['amount']
                    
                # Ejection
                dd = ((h['peak_amount'] - h['amount']) / h['peak_amount']) * 100.0 if h['peak_amount'] > 0 else 0.0
                if dd >= h['mdd_tol']:
                    gross = h['amount']
                    p_fee = max(0.0, gross - h['cost']) * 0.10
                    t_fee = gross * 0.0005
                    net = gross - p_fee - t_fee
                    cumulative_fees += (p_fee + t_fee)
                    del active_holdings[addr]
                    if active_holdings:
                        best = list(active_holdings.keys())[0]
                        active_holdings[best]['cost'] += net
                        active_holdings[best]['amount'] += net
                        
            daily_values.append(sum(h['amount'] for h in active_holdings.values()))
            
        final_val = daily_values[-1]
        net_ret = ((final_val - INITIAL_CAPITAL) / INITIAL_CAPITAL) * 100.0
        peaks = np.maximum.accumulate(daily_values)
        mdd = np.max((peaks - np.array(daily_values)) / peaks * 100.0)
        daily_rets = np.diff(daily_values) / daily_values[:-1]
        sharpe = (np.mean(daily_rets) / (np.std(daily_rets) + 1e-9)) * np.sqrt(365)
        print(f"Ratio: {name:<26} -> Net Return: {net_ret:>7.2f}%, MDD: {mdd:>5.2f}%, Sharpe: {sharpe:>5.2f}, Final: ")

test_allocation_ratios()
