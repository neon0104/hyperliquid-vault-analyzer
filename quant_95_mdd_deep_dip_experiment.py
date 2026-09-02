import os, sys, json, glob
import numpy as np
from pathlib import Path

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_DIR      = Path(r'c:\Users\USER\.gemini\antigravity\scratch\hyperliquid-vault-analyzer')
DATA_DIR      = BASE_DIR / 'vault_data'
SNAPSHOTS_DIR = DATA_DIR / 'snapshots'

# 1. Load Snapshots Cache
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

def select_core_vaults(snapshot: list):
    filtered = []
    for v in snapshot:
        allow_dep = bool(v.get('allow_deposits', True))
        robustness = float(v.get('robustness_score', 0) or 0)
        mdd = float(v.get('max_drawdown', 0) or 0)
        apr = float(v.get('apr_30d', 0) or v.get('apr_pct', 0) or 0)

        if allow_dep and (robustness >= 0.15) and (mdd <= 35.0) and apr > 0:
            v_copy = dict(v)
            v_copy['sm_score'] = compute_sm_score(v)
            filtered.append(v_copy)

    if not filtered:
        filtered = [dict(v) for v in snapshot[:4]]
        for v in filtered: v['sm_score'] = compute_sm_score(v)

    filtered.sort(key=lambda x: x['sm_score'], reverse=True)
    return filtered[:2], filtered[2:4]

def calculate_dynamic_sizing_score(v: dict):
    tvl = float(v.get('tvl', 0.0) or 0.0)
    apr = float(v.get('apr_30d', 0.0) or v.get('apr_pct', 0.0) or 0.0)
    leader_usd = float(v.get('leader_equity_usd', 0.0) or 0.0)
    robustness = float(v.get('robustness_score', 0.0) or 0.0)
    
    tvl_score = min(25.0, (tvl / 50000.0) * 25.0)
    apr_score = min(25.0, max(0.0, (apr / 100.0) * 25.0))
    leader_score = min(25.0, (leader_usd / 50000.0) * 25.0)
    rob_score = min(25.0, (robustness / 0.5) * 25.0)
    
    return tvl_score + apr_score + leader_score + rob_score

def run_dip_experiment(
    dip_threshold_ratio=0.95,
    min_robustness=0.25,
    sizing_mode='DYNAMIC_SCORE',
    exit_recovery_target=0.70,
    exit_mode='REINVEST_CORE'
):
    INITIAL_CAPITAL = 100000.0
    total_capital = INITIAL_CAPITAL
    cash = 0.0
    active_holdings = {}
    cumulative_fees = INITIAL_CAPITAL * 0.0005
    daily_values = []
    
    dip_positions = {}
    dip_events_log = []
    
    first_snap = snapshots_cache[sim_dates[0]]
    core_v, sat_v = select_core_vaults(first_snap)
    
    c_alloc = (total_capital * 0.80) / (len(core_v) or 1)
    s_alloc = (total_capital * 0.20) / (len(sat_v) or 1) if sat_v else 0.0
    
    for v in core_v:
        addr = v['address']
        pnl_s, tvl_s, apr_s = get_vault_pnl_tvl_apr(v)
        hist_mdd = float(v.get('max_drawdown', 15.0) or 15.0)
        active_holdings[addr] = {
            'name': v['name'], 'cost': c_alloc, 'amount': c_alloc,
            'pnl_start': pnl_s, 'tvl_start': tvl_s, 'apr_start': apr_s,
            'share': c_alloc / (tvl_s + c_alloc),
            'peak_amount': c_alloc, 'invest_date': sim_dates[0],
            'type': 'CORE', 'mdd_tol': 18.0, 'hist_mdd': hist_mdd
        }
        
    for v in sat_v:
        addr = v['address']
        pnl_s, tvl_s, apr_s = get_vault_pnl_tvl_apr(v)
        hist_mdd = float(v.get('max_drawdown', 15.0) or 15.0)
        active_holdings[addr] = {
            'name': v['name'], 'cost': s_alloc, 'amount': s_alloc,
            'pnl_start': pnl_s, 'tvl_start': tvl_s, 'apr_start': apr_s,
            'share': s_alloc / (tvl_s + s_alloc),
            'peak_amount': s_alloc, 'invest_date': sim_dates[0],
            'type': 'SATELLITE', 'mdd_tol': 15.0, 'hist_mdd': hist_mdd
        }
        
    for d_idx, d_str in enumerate(sim_dates):
        current_snap = snapshots_cache[d_str]
        snap_map = {v['address']: v for v in current_snap}
        
        # 1. Active holdings update
        for addr, pos in list(active_holdings.items()):
            if addr in snap_map:
                v = snap_map[addr]
                pnl_now, tvl_now, _ = get_vault_pnl_tvl_apr(v)
                pnl_diff = pnl_now - pos['pnl_start']
                my_pnl = pnl_diff * pos['share']
                pos['amount'] = max(10.0, pos['cost'] + my_pnl)
                if pos['amount'] > pos['peak_amount']:
                    pos['peak_amount'] = pos['amount']
                
                dd_from_peak = ((pos['peak_amount'] - pos['amount']) / pos['peak_amount']) * 100.0
                if dd_from_peak >= pos['mdd_tol']:
                    gross = pos['amount']
                    net_profit = gross - pos['cost']
                    perf_fee = max(0.0, net_profit * 0.10)
                    turnover_fee = gross * 0.0005
                    net_proceeds = gross - perf_fee - turnover_fee
                    cumulative_fees += (perf_fee + turnover_fee)
                    
                    del active_holdings[addr]
                    if active_holdings:
                        best_core = list(active_holdings.keys())[0]
                        active_holdings[best_core]['cost'] += net_proceeds
                        active_holdings[best_core]['amount'] += net_proceeds
                    else:
                        cash += net_proceeds

        # 2. Check Dip-Buying Positions for Fast Recovery Exit
        for addr, dpos in list(dip_positions.items()):
            if addr in snap_map:
                v = snap_map[addr]
                pnl_now, tvl_now, _ = get_vault_pnl_tvl_apr(v)
                pnl_diff = pnl_now - dpos['pnl_start']
                my_pnl = pnl_diff * dpos['share']
                dpos['amount'] = max(10.0, dpos['cost'] + my_pnl)
                
                curr_dd = float(v.get('drawdown_now', 0.0) or 0.0)
                hist_mdd = max(0.5, float(v.get('max_drawdown', 10.0) or 10.0))
                
                profit_pct = (dpos['amount'] - dpos['cost']) / dpos['cost']
                recovered_ratio = 1.0 - (curr_dd / hist_mdd)
                
                # Recovery Exit condition: Drawdown reduced significantly OR +10% gain OR DD <= 2%
                if recovered_ratio >= exit_recovery_target or profit_pct >= 0.10 or curr_dd <= 2.0:
                    gross = dpos['amount']
                    profit = gross - dpos['cost']
                    p_fee = max(0.0, profit * 0.10)
                    t_fee = gross * 0.0005
                    net_out = gross - p_fee - t_fee
                    cumulative_fees += (p_fee + t_fee)
                    
                    dip_events_log.append({
                        'date': d_str, 'action': 'EXIT', 'vault': dpos['name'],
                        'profit_usd': profit, 'profit_pct': profit_pct * 100,
                        'days_held': d_idx - dpos['entry_day_idx'],
                        'exit_reason': f'Recovered (DD {curr_dd:.1f}% / Hist {hist_mdd:.1f}%)'
                    })
                    
                    del dip_positions[addr]
                    
                    if exit_mode == 'REINVEST_CORE' and active_holdings:
                        best_core = list(active_holdings.keys())[0]
                        active_holdings[best_core]['cost'] += net_out
                        active_holdings[best_core]['amount'] += net_out
                    else:
                        cash += net_out

        # 3. Search for Dip Opportunities
        for v in current_snap:
            addr = v['address']
            allow_dep = bool(v.get('allow_deposits', True))
            robustness = float(v.get('robustness_score', 0.0) or 0.0)
            curr_dd = float(v.get('drawdown_now', 0.0) or 0.0)
            hist_mdd = float(v.get('max_drawdown', 0.0) or 0.0)
            
            if not allow_dep or hist_mdd < 3.0 or robustness < min_robustness:
                continue
                
            dd_ratio = curr_dd / hist_mdd if hist_mdd > 0 else 0.0
            
            if dd_ratio >= dip_threshold_ratio and addr not in dip_positions:
                comp_score = calculate_dynamic_sizing_score(v)
                
                total_val_curr = sum(h['amount'] for h in active_holdings.values()) + sum(dp['amount'] for dp in dip_positions.values()) + cash
                
                if sizing_mode == 'FIXED_5K':
                    invest_size = 5000.0
                elif sizing_mode == 'DYNAMIC_SCORE':
                    invest_size = 3000.0 + (comp_score / 100.0) * 12000.0
                elif sizing_mode == 'DYNAMIC_PERCENT':
                    invest_size = total_val_curr * (0.03 + (comp_score / 100.0) * 0.12)
                else:
                    invest_size = 5000.0
                    
                invest_size = min(invest_size, total_val_curr * 0.25)
                
                funded = 0.0
                if cash >= invest_size:
                    cash -= invest_size
                    funded = invest_size
                else:
                    funded = cash
                    needed = invest_size - cash
                    cash = 0.0
                    total_h = sum(h['amount'] for h in active_holdings.values())
                    if total_h > needed:
                        for h in active_holdings.values():
                            reduction = needed * (h['amount'] / total_h)
                            h['amount'] -= reduction
                            h['cost'] -= reduction
                        funded += needed
                        
                if funded >= 1000.0:
                    pnl_s, tvl_s, apr_s = get_vault_pnl_tvl_apr(v)
                    dip_positions[addr] = {
                        'name': v['name'], 'cost': funded, 'amount': funded,
                        'pnl_start': pnl_s, 'tvl_start': tvl_s, 'apr_start': apr_s,
                        'share': funded / (tvl_s + funded),
                        'entry_dd': curr_dd, 'hist_mdd': hist_mdd,
                        'comp_score': comp_score, 'entry_day_idx': d_idx,
                        'entry_date': d_str
                    }
                    dip_events_log.append({
                        'date': d_str, 'action': 'BUY_DIP', 'vault': v['name'],
                        'size': funded, 'comp_score': comp_score,
                        'curr_dd': curr_dd, 'hist_mdd': hist_mdd, 'ratio': dd_ratio
                    })

        holdings_val = sum(h['amount'] for h in active_holdings.values())
        dip_val = sum(dp['amount'] for dp in dip_positions.values())
        day_total = holdings_val + dip_val + cash
        daily_values.append(day_total)
        
    final_val = daily_values[-1]
    net_return = ((final_val - INITIAL_CAPITAL) / INITIAL_CAPITAL) * 100.0
    
    peaks = np.maximum.accumulate(daily_values)
    dds = (peaks - np.array(daily_values)) / peaks * 100.0
    max_mdd = np.max(dds)
    
    daily_rets = np.diff(daily_values) / daily_values[:-1]
    sharpe = (np.mean(daily_rets) / (np.std(daily_rets) + 1e-9)) * np.sqrt(365)
    
    return {
        'final_value': final_val,
        'net_return': net_return,
        'max_mdd': max_mdd,
        'sharpe': sharpe,
        'fees': cumulative_fees,
        'num_dips': len([e for e in dip_events_log if e['action'] == 'BUY_DIP']),
        'num_exits': len([e for e in dip_events_log if e['action'] == 'EXIT']),
        'dip_events': dip_events_log
    }

if __name__ == '__main__':
    thresholds = [0.70, 0.80, 0.85, 0.90, 0.95]
    sizing_modes = ['FIXED_5K', 'DYNAMIC_SCORE', 'DYNAMIC_PERCENT']
    exit_targets = [0.50, 0.70, 0.85]
    exit_modes = ['HOLD_CASH', 'REINVEST_CORE']
    
    results = []
    
    for thresh in thresholds:
        for smode in sizing_modes:
            for etarg in exit_targets:
                for emode in exit_modes:
                    res = run_dip_experiment(
                        dip_threshold_ratio=thresh,
                        min_robustness=0.25,
                        sizing_mode=smode,
                        exit_recovery_target=etarg,
                        exit_mode=emode
                    )
                    results.append({
                        'thresh': thresh,
                        'smode': smode,
                        'etarg': etarg,
                        'emode': emode,
                        'return': res['net_return'],
                        'mdd': res['max_mdd'],
                        'sharpe': res['sharpe'],
                        'final': res['final_value'],
                        'num_dips': res['num_dips'],
                        'num_exits': res['num_exits']
                    })
                    
    results.sort(key=lambda x: x['return'], reverse=True)
    
    print('--- TOP 12 STRATEGY COMBINATIONS ---')
    print(f"{'Thresh':<7} | {'Sizing':<15} | {'ExitTarg':<8} | {'ExitMode':<14} | {'Return':<9} | {'MDD':<7} | {'Sharpe':<6} | {'Dips/Exits'}")
    print('-' * 85)
    for r in results[:12]:
        print(f"{r['thresh']*100:>5.0f}%  | {r['smode']:<15} | {r['etarg']*100:>6.0f}%  | {r['emode']:<14} | {r['return']:>7.2f}% | {r['mdd']:>5.2f}% | {r['sharpe']:>6.2f} | {r['num_dips']}/{r['num_exits']}")
        
    print('\n--- THRESHOLD COMPARISON (DYNAMIC_SCORE, REINVEST_CORE, ExitTarg 70%) ---')
    for t in [0.70, 0.80, 0.85, 0.90, 0.95]:
        matches = [x for x in results if abs(x['thresh'] - t) < 1e-4 and x['smode'] == 'DYNAMIC_SCORE' and x['emode'] == 'REINVEST_CORE' and abs(x['etarg'] - 0.70) < 1e-4]
        if matches:
            r = matches[0]
            print(f"Threshold {t*100:2.0f}% -> Return: {r['return']:>6.2f}%, MDD: {r['mdd']:>5.2f}%, Sharpe: {r['sharpe']:>4.2f}, Final: , Dips: {r['num_dips']}, Exits: {r['num_exits']}")

    print('\n--- DETAILED TRADE EVENTS FOR BEST 95% THRESHOLD ---')
    best_95 = run_dip_experiment(dip_threshold_ratio=0.95, min_robustness=0.25, sizing_mode='DYNAMIC_SCORE', exit_recovery_target=0.70, exit_mode='REINVEST_CORE')
    for e in best_95['dip_events'][:20]:
        print(e)
