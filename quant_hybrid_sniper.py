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

def select_sharpe_momentum_vaults(snapshot: list):
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
    
    # 4대 지표 정밀 가중 점수 (0 ~ 100)
    tvl_score = min(25.0, (tvl / 50000.0) * 25.0)
    apr_score = min(25.0, max(0.0, (apr / 100.0) * 25.0))
    leader_score = min(25.0, (leader_usd / 50000.0) * 25.0)
    rob_score = min(25.0, (robustness / 0.5) * 25.0)
    
    return tvl_score + apr_score + leader_score + rob_score

def run_hybrid_master_simulation(
    dip_threshold_ratio=0.95,
    max_vault_mdd=30.0,
    min_robustness=0.35,
    exit_target=0.70,
    sizing_type='DYNAMIC_SCORE'
):
    INITIAL_CAPITAL = 100000.0
    total_capital = INITIAL_CAPITAL
    active_holdings = {}
    cumulative_fees = INITIAL_CAPITAL * 0.0005
    last_rebalance_date = sim_dates[0]
    daily_values = []
    
    dip_positions = {}
    dip_trades = []
    
    # Initial Rebalance
    first_snap = snapshots_cache[sim_dates[0]]
    core_v, sat_v = select_sharpe_momentum_vaults(first_snap)
    c_alloc = (total_capital * 0.80) / (len(core_v) or 1)
    s_alloc = (total_capital * 0.20) / (len(sat_v) or 1) if sat_v else 0.0
    
    for v in core_v:
        addr = v['address']
        pnl_s, tvl_s, apr_s = get_vault_pnl_tvl_apr(v)
        active_holdings[addr] = {
            'name': v['name'], 'cost': c_alloc, 'amount': c_alloc,
            'pnl_start': pnl_s, 'tvl_start': tvl_s, 'apr_start': apr_s,
            'share': c_alloc / (tvl_s + c_alloc),
            'peak_amount': c_alloc, 'invest_date': sim_dates[0],
            'type': 'CORE', 'mdd_tol': 18.0
        }
    for v in sat_v:
        addr = v['address']
        pnl_s, tvl_s, apr_s = get_vault_pnl_tvl_apr(v)
        active_holdings[addr] = {
            'name': v['name'], 'cost': s_alloc, 'amount': s_alloc,
            'pnl_start': pnl_s, 'tvl_start': tvl_s, 'apr_start': apr_s,
            'share': s_alloc / (tvl_s + s_alloc),
            'peak_amount': s_alloc, 'invest_date': sim_dates[0],
            'type': 'SATELLITE', 'mdd_tol': 15.0
        }
        
    for d_idx, d_str in enumerate(sim_dates):
        current_snap = snapshots_cache[d_str]
        snap_map = {v['address']: v for v in current_snap}
        
        # 1. Update active holdings
        for addr, pos in list(active_holdings.items()):
            if addr in snap_map:
                v = snap_map[addr]
                pnl_now, tvl_now, _ = get_vault_pnl_tvl_apr(v)
                pnl_diff = pnl_now - pos['pnl_start']
                my_pnl = pnl_diff * pos['share']
                pos['amount'] = max(10.0, pos['cost'] + my_pnl)
                if pos['amount'] > pos['peak_amount']:
                    pos['peak_amount'] = pos['amount']
                
                # Check stop-loss
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

        # 2. Check and Exit Dip Positions (Fast Recovery Take-Profit)
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
                
                # Exit trigger: Drawdown recovered 70%+ OR +8% gain OR DD <= 1.5%
                if recovered_ratio >= exit_target or profit_pct >= 0.08 or curr_dd <= 1.5:
                    gross = dpos['amount']
                    profit = gross - dpos['cost']
                    p_fee = max(0.0, profit * 0.10)
                    t_fee = gross * 0.0005
                    net_out = gross - p_fee - t_fee
                    cumulative_fees += (p_fee + t_fee)
                    
                    # Return capital back into Core Top 1 Vault!
                    if active_holdings:
                        best_core = list(active_holdings.keys())[0]
                        active_holdings[best_core]['cost'] += net_out
                        active_holdings[best_core]['amount'] += net_out
                        
                    dip_trades.append({
                        'date': d_str, 'vault': dpos['name'], 'profit': profit,
                        'profit_pct': profit_pct * 100, 'days': d_idx - dpos['entry_day']
                    })
                    del dip_positions[addr]

        # 3. Monthly 30-Day Rebalancing
        d_obj_curr = int(d_str.replace('-', ''))
        d_obj_last = int(last_rebalance_date.replace('-', ''))
        if d_idx > 0 and (d_idx % 30 == 0):
            last_rebalance_date = d_str
            total_cap_rebal = sum(h['amount'] for h in active_holdings.values())
            # liquidate current holdings for rebalance
            for addr, h in list(active_holdings.items()):
                pnl = h['amount'] - h['cost']
                perf_fee = max(0.0, pnl * 0.10)
                turnover_fee = h['amount'] * 0.0005
                cumulative_fees += (perf_fee + turnover_fee)
                
            active_holdings.clear()
            core_v, sat_v = select_sharpe_momentum_vaults(current_snap)
            c_alloc = (total_cap_rebal * 0.80) / (len(core_v) or 1)
            s_alloc = (total_cap_rebal * 0.20) / (len(sat_v) or 1) if sat_v else 0.0
            
            for v in core_v:
                addr = v['address']
                pnl_s, tvl_s, apr_s = get_vault_pnl_tvl_apr(v)
                active_holdings[addr] = {
                    'name': v['name'], 'cost': c_alloc, 'amount': c_alloc,
                    'pnl_start': pnl_s, 'tvl_start': tvl_s, 'apr_start': apr_s,
                    'share': c_alloc / (tvl_s + c_alloc),
                    'peak_amount': c_alloc, 'invest_date': d_str,
                    'type': 'CORE', 'mdd_tol': 18.0
                }
            for v in sat_v:
                addr = v['address']
                pnl_s, tvl_s, apr_s = get_vault_pnl_tvl_apr(v)
                active_holdings[addr] = {
                    'name': v['name'], 'cost': s_alloc, 'amount': s_alloc,
                    'pnl_start': pnl_s, 'tvl_start': tvl_s, 'apr_start': apr_s,
                    'share': s_alloc / (tvl_s + s_alloc),
                    'peak_amount': s_alloc, 'invest_date': d_str,
                    'type': 'SATELLITE', 'mdd_tol': 15.0
                }

        # 4. Check for 95% MDD Extreme Dip Sniper Opportunities
        for v in current_snap:
            addr = v['address']
            allow_dep = bool(v.get('allow_deposits', True))
            robustness = float(v.get('robustness_score', 0.0) or 0.0)
            curr_dd = float(v.get('drawdown_now', 0.0) or 0.0)
            hist_mdd = float(v.get('max_drawdown', 0.0) or 0.0)
            tvl = float(v.get('tvl', 0.0) or 0.0)
            
            # 우량 볼트 필터: 안정적 Max MDD (3%~30%), 회복탄력성, 최소 TVL
            if not allow_dep or hist_mdd < 3.0 or hist_mdd > max_vault_mdd or robustness < min_robustness or tvl < 10000:
                continue
                
            dd_ratio = curr_dd / hist_mdd
            # 사용자 제안: 역사적 최대 낙폭의 95% 수준 진입
            if dd_ratio >= dip_threshold_ratio and addr not in dip_positions and addr not in active_holdings:
                comp_score = calculate_dynamic_sizing_score(v)
                
                # Dynamic Sizing: TVL, APR, Leader Equity, Robustness 복합점수로 사이징
                if sizing_type == 'DYNAMIC_SCORE':
                    dip_size = 3000.0 + (comp_score / 100.0) * 7000.0 #  ~ 
                elif sizing_type == 'FIXED_5K':
                    dip_size = 5000.0
                else:
                    dip_size = 5000.0
                    
                # Core 볼트에서 필요한 만큼만 자금 임시 차출
                total_h_val = sum(h['amount'] for h in active_holdings.values())
                if total_h_val > dip_size * 2: # 충분한 여력이 있을 때만
                    for h in active_holdings.values():
                        cut = dip_size * (h['amount'] / total_h_val)
                        h['amount'] -= cut
                        h['cost'] -= cut
                    
                    pnl_s, tvl_s, apr_s = get_vault_pnl_tvl_apr(v)
                    dip_positions[addr] = {
                        'name': v['name'], 'cost': dip_size, 'amount': dip_size,
                        'pnl_start': pnl_s, 'tvl_start': tvl_s, 'apr_start': apr_s,
                        'share': dip_size / (tvl_s + dip_size),
                        'entry_dd': curr_dd, 'hist_mdd': hist_mdd,
                        'comp_score': comp_score, 'entry_day': d_idx
                    }

        total_day = sum(h['amount'] for h in active_holdings.values()) + sum(dp['amount'] for dp in dip_positions.values())
        daily_values.append(total_day)

    final_val = daily_values[-1]
    net_ret = ((final_val - INITIAL_CAPITAL) / INITIAL_CAPITAL) * 100.0
    peaks = np.maximum.accumulate(daily_values)
    mdd = np.max((peaks - np.array(daily_values)) / peaks * 100.0)
    daily_rets = np.diff(daily_values) / daily_values[:-1]
    sharpe = (np.mean(daily_rets) / (np.std(daily_rets) + 1e-9)) * np.sqrt(365)
    
    return {
        'net_return': net_ret, 'mdd': mdd, 'sharpe': sharpe,
        'final': final_val, 'trades_count': len(dip_trades),
        'win_rate': len([t for t in dip_trades if t['profit'] > 0]) / (len(dip_trades) or 1) * 100,
        'avg_profit_pct': np.mean([t['profit_pct'] for t in dip_trades]) if dip_trades else 0.0,
        'avg_days': np.mean([t['days'] for t in dip_trades]) if dip_trades else 0.0,
        'fees': cumulative_fees,
        'trades': dip_trades
    }

print('=== EXPERIMENT 2: HYBRID MASTER (Sharpe-Momentum 80:20 + 95% Extreme MDD Dip Sniper + Fast Exit) ===')
for thresh in [0.70, 0.80, 0.85, 0.90, 0.95]:
    for stype in ['FIXED_5K', 'DYNAMIC_SCORE']:
        for max_mdd in [20.0, 30.0]:
            res = run_hybrid_master_simulation(
                dip_threshold_ratio=thresh,
                max_vault_mdd=max_mdd,
                min_robustness=0.35,
                exit_target=0.70,
                sizing_type=stype
            )
            print(f"Thresh {thresh*100:2.0f}% | Sizing: {stype:<13} | MaxMDD: <={max_mdd:2.0f}% -> Net Return: {res['net_return']:>7.2f}% | MDD: {res['mdd']:>5.2f}% | Sharpe: {res['sharpe']:>4.2f} | Final:  | Dips: {res['trades_count']} (Win: {res['win_rate']:.1f}%, Hold {res['avg_days']:.1f}d)")

