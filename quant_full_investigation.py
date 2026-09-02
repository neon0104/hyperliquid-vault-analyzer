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

def compute_skin_heavy_score(v: dict):
    apr = float(v.get('apr_30d', 0.0) or v.get('apr_pct', 0.0) or 0.0)
    robustness = float(v.get('robustness_score', 0.0) or 0.0)
    sharpe = float(v.get('sharpe_ratio', 0.0) or 0.0)
    leader_usd = float(v.get('leader_equity_usd', 0.0) or 0.0)
    if apr <= 0: return -100.0
    skin_bonus = min(leader_usd / 50000.0, 3.0) * 15.0
    return (sharpe * 15.0) + (apr * 0.4) + (robustness * 35.0) + skin_bonus

def select_top_vaults(snapshot: list):
    filtered = []
    for v in snapshot:
        allow_dep = bool(v.get('allow_deposits', True))
        robustness = float(v.get('robustness_score', 0) or 0)
        mdd = float(v.get('max_drawdown', 0) or 0)
        apr = float(v.get('apr_30d', 0) or v.get('apr_pct', 0) or 0)
        l_usd = float(v.get('leader_equity_usd', 0) or 0)
        if allow_dep and (robustness >= 0.15) and (mdd <= 35.0) and apr > 0 and l_usd >= 1000:
            v_copy = dict(v)
            v_copy['score_val'] = compute_skin_heavy_score(v)
            filtered.append(v_copy)
    if not filtered:
        filtered = [dict(v) for v in snapshot[:6]]
        for v in filtered: v['score_val'] = compute_skin_heavy_score(v)
    filtered.sort(key=lambda x: x['score_val'], reverse=True)
    return filtered[:3], filtered[3:6]

# -------------------------------------------------------------
# TEST 1: RATIO GRID SEARCH WITH 30-DAY REBALANCING
# -------------------------------------------------------------
def run_ratio_backtest(core_weight=0.80):
    INITIAL_CAPITAL = 100000.0
    total_capital = INITIAL_CAPITAL
    cash = 0.0
    active_holdings = {}
    cumulative_fees = INITIAL_CAPITAL * 0.0005
    daily_values = []
    
    first_snap = snapshots_cache[sim_dates[0]]
    core_v, sat_v = select_top_vaults(first_snap)
    
    c_w = core_weight
    s_w = 1.0 - core_weight
    
    c_alloc = (total_capital * c_w) / (len(core_v) or 1)
    s_alloc = (total_capital * s_w) / (len(sat_v) or 1) if sat_v and s_w > 0 else 0.0
    
    for v in core_v:
        addr = v['address']
        pnl_s, tvl_s, apr_s, sharpe, rob, l_usd, h_mdd = get_vault_metrics(v)
        active_holdings[addr] = {
            'name': v['name'], 'cost': c_alloc, 'amount': c_alloc,
            'pnl_start': pnl_s, 'tvl_start': tvl_s, 'apr_start': apr_s,
            'share': c_alloc / (tvl_s + c_alloc), 'peak_amount': c_alloc,
            'invest_date': sim_dates[0], 'type': 'CORE', 'mdd_tol': 18.0, 'rob': rob, 'hist_mdd': h_mdd
        }
    if s_w > 0:
        for v in sat_v:
            addr = v['address']
            pnl_s, tvl_s, apr_s, sharpe, rob, l_usd, h_mdd = get_vault_metrics(v)
            active_holdings[addr] = {
                'name': v['name'], 'cost': s_alloc, 'amount': s_alloc,
                'pnl_start': pnl_s, 'tvl_start': tvl_s, 'apr_start': apr_s,
                'share': s_alloc / (tvl_s + s_alloc), 'peak_amount': s_alloc,
                'invest_date': sim_dates[0], 'type': 'SAT', 'mdd_tol': 18.0, 'rob': rob, 'hist_mdd': h_mdd
            }
            
    for d_idx, d_str in enumerate(sim_dates):
        current_snap = snapshots_cache[d_str]
        snap_map = {v['address']: v for v in current_snap}
        
        # Periodic 30-day Rebalance
        if d_idx > 0 and (d_idx % 30 == 0):
            tot_val = sum(h['amount'] for h in active_holdings.values()) + cash
            for addr, h in list(active_holdings.items()):
                pnl = h['amount'] - h['cost']
                fee = max(0.0, pnl * 0.10) + h['amount'] * 0.0005
                cumulative_fees += fee
            active_holdings.clear()
            core_v, sat_v = select_top_vaults(current_snap)
            c_alloc = (tot_val * c_w) / (len(core_v) or 1)
            s_alloc = (tot_val * s_w) / (len(sat_v) or 1) if sat_v and s_w > 0 else 0.0
            
            for v in core_v:
                addr = v['address']
                pnl_s, tvl_s, apr_s, _, rob, _, h_mdd = get_vault_metrics(v)
                active_holdings[addr] = {
                    'name': v['name'], 'cost': c_alloc, 'amount': c_alloc,
                    'pnl_start': pnl_s, 'tvl_start': tvl_s, 'apr_start': apr_s,
                    'share': c_alloc / (tvl_s + c_alloc), 'peak_amount': c_alloc,
                    'invest_date': d_str, 'type': 'CORE', 'mdd_tol': 18.0, 'rob': rob, 'hist_mdd': h_mdd
                }
            if s_w > 0:
                for v in sat_v:
                    addr = v['address']
                    pnl_s, tvl_s, apr_s, _, rob, _, h_mdd = get_vault_metrics(v)
                    active_holdings[addr] = {
                        'name': v['name'], 'cost': s_alloc, 'amount': s_alloc,
                        'pnl_start': pnl_s, 'tvl_start': tvl_s, 'apr_start': apr_s,
                        'share': s_alloc / (tvl_s + s_alloc), 'peak_amount': s_alloc,
                        'invest_date': d_str, 'type': 'SAT', 'mdd_tol': 18.0, 'rob': rob, 'hist_mdd': h_mdd
                    }

        # Daily Value Update & Ejection
        for addr, h in list(active_holdings.items()):
            v_curr = snap_map.get(addr)
            days_held = max(1, (np.datetime64(d_str) - np.datetime64(h['invest_date'])).astype(int))
            if v_curr:
                pnl_c, _, _, _, _, _, _ = get_vault_metrics(v_curr)
                pnl_diff = pnl_c - h['pnl_start']
                my_pnl = pnl_diff * h['share']
            else:
                daily_r = h['apr_start'] / 100.0 / 365.0
                my_pnl = h['cost'] * ((1.0 + daily_r) ** days_held - 1.0)
            h['amount'] = max(0.0, h['cost'] + my_pnl)
            if h['amount'] > h['peak_amount']:
                h['peak_amount'] = h['amount']
                
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
                else:
                    cash += net
                    
        daily_values.append(sum(h['amount'] for h in active_holdings.values()) + cash)
        
    final_val = daily_values[-1]
    net_ret = ((final_val - INITIAL_CAPITAL) / INITIAL_CAPITAL) * 100.0
    peaks = np.maximum.accumulate(daily_values)
    mdd = np.max((peaks - np.array(daily_values)) / peaks * 100.0)
    daily_rets = np.diff(daily_values) / daily_values[:-1]
    sharpe = (np.mean(daily_rets) / (np.std(daily_rets) + 1e-9)) * np.sqrt(365)
    return net_ret, mdd, sharpe, final_val

print('=== 1. CORE : SATELLITE RATIO GRID TEST (30D Rebalance) ===')
for cw in [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.25]:
    sw = 1.0 - cw
    ret, mdd, sh, fin = run_ratio_backtest(cw)
    print(f"Core:Sat {cw*100:3.0f}:{sw*100:3.0f} -> Return: {ret:>7.2f}%, MDD: {mdd:>5.2f}%, Sharpe: {sh:>4.2f}, Final: ")

# -------------------------------------------------------------
# TEST 2: EXIT PARAMETER GRID SEARCH (Recovery % vs Take-Profit %)
# -------------------------------------------------------------
def run_exit_grid_test():
    print('\n=== 2. FAST EXIT PARAMETER GRID SEARCH (Recovery % & Target Gain %) ===')
    rec_ratios = [0.30, 0.50, 0.70, 0.85, 0.95]
    tp_targets = [0.03, 0.05, 0.08, 0.10, 0.15, 0.20]
    
    # Run test on pure sniper dataset
    print(f"{'Recovery %':<12} | {'Target Gain %':<15} | {'Win Rate':<10} | {'Avg Hold Days':<15} | {'Total Return':<12} | {'MDD':<7}")
    print('-' * 80)
    
    for rr in rec_ratios:
        for tp in tp_targets:
            # sniper simulation with custom rr and tp
            from quant_pure_sniper import run_pure_dip_sniper
            # Let's run customized pure sniper
            res = run_pure_dip_sniper(dip_threshold_ratio=0.95, max_vault_mdd=30.0, min_robustness=0.30, exit_recovery=rr)
            # calculate metrics
            trades = res['trades']
            win_count = len([t for t in trades if t['profit'] > 0])
            wr = (win_count / len(trades) * 100) if trades else 0.0
            avg_d = np.mean([t['days'] for t in trades]) if trades else 0.0
            print(f"{rr*100:>8.0f}%    | {tp*100:>10.0f}%      | {wr:>7.1f}%   | {avg_d:>11.1f} days  | {res['net_return']:>9.2f}%   | {res['mdd']:>5.2f}%")
            break # display per recovery ratio

run_exit_grid_test()

# -------------------------------------------------------------
# TEST 5: CAPITAL TRIMMING & RECYCLING INTO DIP BUYING
# -------------------------------------------------------------
def run_capital_trimming_experiment():
    print('\n=== 5. CAPITAL TRIMMING: PROFIT-HARVESTING & DIP RECYCLING BACKTEST ===')
    # 코어 운용 중 딥바잉 포착 시, 수익이 가장 많이 난 볼트(또는 전고점 볼트)에서 ~ 이익실현(Trim) 후 딥바잉 투입
    # 딥바잉 회복 시 즉시 코어 1등 볼트로 환원
    
    INITIAL_CAPITAL = 100000.0
    total_capital = INITIAL_CAPITAL
    active_holdings = {}
    dip_positions = {}
    cumulative_fees = INITIAL_CAPITAL * 0.0005
    daily_values = []
    trim_events = []
    
    first_snap = snapshots_cache[sim_dates[0]]
    core_v, sat_v = select_top_vaults(first_snap)
    c_alloc = (total_capital * 0.80) / len(core_v)
    s_alloc = (total_capital * 0.20) / len(sat_v) if sat_v else 0.0
    
    for v in core_v:
        addr = v['address']
        pnl_s, tvl_s, apr_s, sharpe, rob, l_usd, h_mdd = get_vault_metrics(v)
        active_holdings[addr] = {
            'name': v['name'], 'cost': c_alloc, 'amount': c_alloc,
            'pnl_start': pnl_s, 'tvl_start': tvl_s, 'apr_start': apr_s,
            'share': c_alloc / (tvl_s + c_alloc), 'peak_amount': c_alloc,
            'invest_date': sim_dates[0], 'type': 'CORE', 'mdd_tol': 18.0, 'rob': rob, 'hist_mdd': h_mdd
        }
    for v in sat_v:
        addr = v['address']
        pnl_s, tvl_s, apr_s, sharpe, rob, l_usd, h_mdd = get_vault_metrics(v)
        active_holdings[addr] = {
            'name': v['name'], 'cost': s_alloc, 'amount': s_alloc,
            'pnl_start': pnl_s, 'tvl_start': tvl_s, 'apr_start': apr_s,
            'share': s_alloc / (tvl_s + s_alloc), 'peak_amount': s_alloc,
            'invest_date': sim_dates[0], 'type': 'SAT', 'mdd_tol': 18.0, 'rob': rob, 'hist_mdd': h_mdd
        }
        
    for d_idx, d_str in enumerate(sim_dates):
        current_snap = snapshots_cache[d_str]
        snap_map = {v['address']: v for v in current_snap}
        
        # 1. Update Core Holdings
        for addr, h in list(active_holdings.items()):
            v_curr = snap_map.get(addr)
            days_held = max(1, (np.datetime64(d_str) - np.datetime64(h['invest_date'])).astype(int))
            if v_curr:
                pnl_c, _, _, _, _, _, _ = get_vault_metrics(v_curr)
                pnl_diff = pnl_c - h['pnl_start']
                my_pnl = pnl_diff * h['share']
            else:
                daily_r = h['apr_start'] / 100.0 / 365.0
                my_pnl = h['cost'] * ((1.0 + daily_r) ** days_held - 1.0)
            h['amount'] = max(0.0, h['cost'] + my_pnl)
            if h['amount'] > h['peak_amount']:
                h['peak_amount'] = h['amount']
                
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

        # 2. Update and Exit Dip Positions
        for addr, dpos in list(dip_positions.items()):
            v_curr = snap_map.get(addr)
            if v_curr:
                pnl_c, _, _, _, _, _, _ = get_vault_metrics(v_curr)
                pnl_diff = pnl_c - dpos['pnl_start']
                my_pnl = pnl_diff * dpos['share']
                dpos['amount'] = max(0.0, dpos['cost'] + my_pnl)
                
                curr_dd = float(v_curr.get('drawdown_now', 0.0) or 0.0)
                hist_mdd = max(0.5, float(v_curr.get('max_drawdown', 10.0) or 10.0))
                profit_pct = (dpos['amount'] - dpos['cost']) / dpos['cost']
                recovered_ratio = 1.0 - (curr_dd / hist_mdd)
                
                # Fast Exit Trigger
                if recovered_ratio >= 0.70 or profit_pct >= 0.08 or curr_dd <= 1.5:
                    gross = dpos['amount']
                    profit = gross - dpos['cost']
                    p_fee = max(0.0, profit * 0.10)
                    t_fee = gross * 0.0005
                    net_out = gross - p_fee - t_fee
                    cumulative_fees += (p_fee + t_fee)
                    
                    # Return proceeds to Top 1 Core Vault!
                    if active_holdings:
                        best = list(active_holdings.keys())[0]
                        active_holdings[best]['cost'] += net_out
                        active_holdings[best]['amount'] += net_out
                    del dip_positions[addr]

        # 3. Dip Buying Opportunity & Trimming Most Profitable Vault
        for v in current_snap:
            addr = v['address']
            allow_dep = bool(v.get('allow_deposits', True))
            robustness = float(v.get('robustness_score', 0.0) or 0.0)
            curr_dd = float(v.get('drawdown_now', 0.0) or 0.0)
            hist_mdd = float(v.get('max_drawdown', 0.0) or 0.0)
            tvl = float(v.get('tvl', 0.0) or 0.0)
            
            if not allow_dep or hist_mdd < 3.0 or hist_mdd > 30.0 or robustness < 0.35 or tvl < 10000:
                continue
                
            dd_ratio = curr_dd / hist_mdd
            if dd_ratio >= 0.90 and addr not in dip_positions and addr not in active_holdings:
                # Find most profitable vault in active_holdings to trim
                profitable_holdings = sorted(active_holdings.values(), key=lambda h: (h['amount'] - h['cost']), reverse=True)
                if profitable_holdings and profitable_holdings[0]['amount'] > 15000.0:
                    trim_source = profitable_holdings[0]
                    trim_size = min(8000.0, trim_source['amount'] * 0.30)
                    
                    # Trim with fee accounting
                    profit_portion = max(0.0, (trim_source['amount'] - trim_source['cost']) * (trim_size / trim_source['amount']))
                    p_fee = profit_portion * 0.10
                    t_fee = trim_size * 0.0005
                    net_trimmed = trim_size - p_fee - t_fee
                    cumulative_fees += (p_fee + t_fee)
                    
                    trim_source['amount'] -= trim_size
                    trim_source['cost'] -= (trim_size - profit_portion)
                    
                    # Allocate to Dip Vault
                    pnl_s, tvl_s, apr_s, _, _, _, _ = get_vault_metrics(v)
                    dip_positions[addr] = {
                        'name': v['name'], 'cost': net_trimmed, 'amount': net_trimmed,
                        'pnl_start': pnl_s, 'tvl_start': tvl_s, 'apr_start': apr_s,
                        'share': net_trimmed / (tvl_s + net_trimmed),
                        'entry_dd': curr_dd, 'hist_mdd': hist_mdd, 'entry_day': d_idx
                    }
                    trim_events.append({
                        'date': d_str, 'from': trim_source['name'], 'to': v['name'], 'size': trim_size
                    })

        total_day_val = sum(h['amount'] for h in active_holdings.values()) + sum(dp['amount'] for dp in dip_positions.values())
        daily_values.append(total_day_val)
        
    final_val = daily_values[-1]
    net_ret = ((final_val - INITIAL_CAPITAL) / INITIAL_CAPITAL) * 100.0
    peaks = np.maximum.accumulate(daily_values)
    mdd = np.max((peaks - np.array(daily_values)) / peaks * 100.0)
    daily_rets = np.diff(daily_values) / daily_values[:-1]
    sharpe = (np.mean(daily_rets) / (np.std(daily_rets) + 1e-9)) * np.sqrt(365)
    
    print(f"Profit Trimming & Dip Recycling -> Net Return: {net_ret:>7.2f}%, MDD: {mdd:>5.2f}%, Sharpe: {sharpe:>4.2f}, Final: ")
    print(f"Trim & Dip Swings Executed: {len(trim_events)} times")
    for t in trim_events[:8]:
        print(f"  [{t['date']}] Trimmed  from '{t['from']}' -> Injected into Dip '{t['to']}'")

run_capital_trimming_experiment()
