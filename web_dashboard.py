#!/usr/bin/env python3
import os, sys, json, glob, threading, urllib.request
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template_string, jsonify, request

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

app = Flask(__name__)

# 경로 및 환경
BASE_DIR       = Path(__file__).parent
DATA_DIR       = BASE_DIR / "vault_data"
SNAPSHOTS_DIR  = DATA_DIR / "snapshots"
REPORTS_DIR    = DATA_DIR / "reports"
PORTFOLIO_FILE = BASE_DIR / "my_portfolio.json"
DISCORD_CFG    = BASE_DIR / "discord_config.json"

for d in [SNAPSHOTS_DIR, REPORTS_DIR]: os.makedirs(d, exist_ok=True)

# ── 유틸리티 ──────────────────────────────────────────────────────────────────

def load_portfolio_config():
    if os.path.exists(PORTFOLIO_FILE):
        try:
            with open(str(PORTFOLIO_FILE), encoding="utf-8") as f: return json.load(f)
        except: pass
    return {"positions": {}, "total_capital": 100000}

def get_latest_snapshot():
    files = sorted(glob.glob(os.path.join(SNAPSHOTS_DIR, "*.json")), reverse=True)
    if not files: return [], None
    try:
        with open(str(files[0]), encoding="utf-8") as f:
            return json.load(f), os.path.basename(files[0])[:-5]
    except: return [], None

def send_discord(msg):
    try:
        if not os.path.exists(DISCORD_CFG): return False
        with open(str(DISCORD_CFG), encoding="utf-8") as f: url = json.load(f).get("webhook_url", "")
        if not url: return False
        data = json.dumps({"content": msg, "username": "HyperliquidBot"}).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as r: return r.status in (200, 204)
    except: return False

# ── 라우트 ────────────────────────────────────────────────────────────────────

def get_historical_snapshots():
    files = sorted(glob.glob(os.path.join(SNAPSHOTS_DIR, "*.json")), reverse=True)
    if not files: return [], None, {}, None
    try:
        with open(str(files[0]), encoding="utf-8") as f:
            latest = json.load(f)
            latest_date = os.path.basename(files[0])[:-5]
    except: return [], None, {}, None
    
    prev_vaults = {}
    prev_date = None
    if len(files) > 1:
        try:
            with open(str(files[1]), encoding="utf-8") as f:
                prev_data = json.load(f)
                prev_date = os.path.basename(files[1])[:-5]
                for i, p in enumerate(prev_data):
                    p["rank"] = p.get("rank", i+1)
                    prev_vaults[p["address"]] = p
        except: pass
        
    vault_hist = {}
    for f in reversed(files):
        dt = os.path.basename(f)[:-5]
        try:
            with open(str(f), encoding="utf-8") as fd:
                data = json.load(fd)
                for v in data:
                    addr = v["address"]
                    if addr not in vault_hist:
                        vault_hist[addr] = {"dates": [], "mdd": [], "sharpe": [], "robust": [], "score": []}
                    vault_hist[addr]["dates"].append(dt[5:]) 
                    vault_hist[addr]["mdd"].append(v.get("max_drawdown", 0))
                    vault_hist[addr]["sharpe"].append(v.get("sharpe_ratio", 0))
                    vault_hist[addr]["robust"].append(v.get("robustness_score", 0))
                    vault_hist[addr]["score"].append(v.get("score", 0))
        except: pass
        
    return latest, latest_date, prev_vaults, prev_date, vault_hist

# ── 라우트 ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    vaults, date, prev_vaults, prev_date, vault_hist = get_historical_snapshots()
    if not vaults:
        return render_template_string(EMPTY_HTML)
        
    for i, v in enumerate(vaults):
        v["rank"] = v.get("rank", i+1)
        v["history"] = vault_hist.get(v["address"], {})

        if prev_vaults and v["address"] in prev_vaults:
            p = prev_vaults[v["address"]]
            cr = p["rank"] - v["rank"]
            cs = round(v.get("score", 0) - p.get("score", 0), 3)
            cm = round(v.get("max_drawdown", 0) - p.get("max_drawdown", 0), 2)
            cp = round(v.get("pnl_alltime", 0) - p.get("pnl_alltime", 0), 2)
            
            cv = round(v.get("tvl", 0) - p.get("tvl", 0), 2)
            ce = round((v.get("leader_equity_ratio", 0) - p.get("leader_equity_ratio", 0)) * 100, 2)
            csh = round(v.get("sharpe_ratio", 0) - p.get("sharpe_ratio", 0), 3)
            
            v["chg"] = {
                "rank_val": abs(cr), "rank_dir": "▲" if cr > 0 else "▼" if cr < 0 else "-", "rank_col": "var(--success)" if cr > 0 else "var(--danger)" if cr < 0 else "var(--muted)",
                "score_val": abs(cs), "score_dir": "▲" if cs > 0 else "▼" if cs < 0 else "-", "score_col": "var(--success)" if cs > 0 else "var(--danger)" if cs < 0 else "var(--muted)",
                "mdd_val": abs(cm), "mdd_dir": "▲" if cm > 0 else "▼" if cm < 0 else "-", "mdd_col": "var(--danger)" if cm > 0 else "var(--success)" if cm < 0 else "var(--muted)",
                "pnl_val": abs(cp), "pnl_dir": "▲" if cp > 0 else "▼" if cp < 0 else "-", "pnl_col": "var(--success)" if cp > 0 else "var(--danger)" if cp < 0 else "var(--muted)",
                "tvl_val": abs(cv), "tvl_dir": "▲" if cv > 0 else "▼" if cv < 0 else "-", "tvl_col": "var(--success)" if cv > 0 else "var(--danger)" if cv < 0 else "var(--muted)",
                "eq_val": abs(ce), "eq_dir": "▲" if ce > 0 else "▼" if ce < 0 else "-", "eq_col": "var(--success)" if ce > 0 else "var(--danger)" if ce < 0 else "var(--muted)",
                "sharpe_val": abs(csh), "sharpe_dir": "▲" if csh > 0 else "▼" if csh < 0 else "-", "sharpe_col": "var(--success)" if csh > 0 else "var(--danger)" if csh < 0 else "var(--muted)"
            }
            def pt(c, pr): return round((c - pr) / abs(pr) * 100, 2) if pr != 0 else 0
            v["chg_pct"] = {
                "tvl": pt(v.get("tvl", 0), p.get("tvl", 0)),
                "eq": pt(v.get("leader_equity_ratio", 0), p.get("leader_equity_ratio", 0)),
                "pnl": pt(v.get("pnl_alltime", 0), p.get("pnl_alltime", 0)),
                "mdd": pt(v.get("max_drawdown", 0), p.get("max_drawdown", 0)),
                "sharpe": pt(v.get("sharpe_ratio", 0), p.get("sharpe_ratio", 0)),
                "score": pt(v.get("score", 0), p.get("score", 0))
            }
            v["has_history"] = True
        else:
            v["has_history"] = False
            
        if v.get("apr_pct") and v.get("age_days"):
            v["alltime_roi_pct"] = round(v.get("apr_pct", 0) * (v.get("age_days", 0) / 365.0), 1)
        else:
            v["alltime_roi_pct"] = 0.0

    
    avg_mdd = sum(v.get("max_drawdown", 0) for v in vaults) / len(vaults) if vaults else 0
    stats = {
        "total": len(vaults),
        "avg_apr": sum(v.get("apr_30d", 0) for v in vaults) / len(vaults) if vaults else 0,
        "avg_mdd": round(avg_mdd, 2),
        "prev_date": prev_date
    }
    return render_template_string(MAIN_HTML, vaults=vaults, date=date, stats=stats)

@app.route("/portfolio")
def portfolio_page():
    try:
        from portfolio_engine import run_portfolio_analysis
        d = run_portfolio_analysis(top_k=25, max_corr=0.55)
    except Exception as e:
        return f"<body style='background:#0b0f1a;color:#e74c3c;padding:40px;'><h2>⚠️ 분석 에러</h2><p>{e}</p></body>"
    return render_template_string(PORTFOLIO_HTML, d=d)

@app.route("/backtest")
def backtest_gui():
    return render_template_string(BACKTEST_HTML)

@app.route("/api/backtest")
def api_backtest():
    # 실제 백테스트 결과는 portfolio_engine에서 가져오는 것이 좋지만, 일단 간단하게
    from portfolio_engine import run_portfolio_analysis
    d = run_portfolio_analysis(top_k=15)
    if "error" in d: return jsonify(d)
    
    # 대표로 'max_sharpe' 결과 반환
    res = d["portfolios"]["max_sharpe"]["backtest"]
    return jsonify(res)

@app.route("/discord")
def discord_gui():
    wk = ""
    if os.path.exists(DISCORD_CFG):
        with open(str(DISCORD_CFG), encoding="utf-8") as f: wk = json.load(f).get("webhook_url", "")
    return render_template_string(DISCORD_HTML, wk=wk)

@app.route("/api/discord-setup", methods=["POST"])
def api_discord_save():
    data = request.get_json() or {}
    with open(str(DISCORD_CFG), "w", encoding="utf-8") as f: json.dump({"webhook_url": data.get("webhook_url","")}, f)
    send_discord("✅ 연결 성공! Hyperliquid Vault Analyzer와 연동되었습니다.")
    return jsonify({"status": "ok"})

@app.route("/m")
@app.route("/my-portfolio")
def my_portfolio_gui():
    import portfolio_tracker
    p = load_portfolio_config()
    snaps = portfolio_tracker.load_snapshots_all()
    
    port_calc = portfolio_tracker.calc_my_portfolio(p.get("positions", {}), p.get("invest_date"), snaps)
    
    if not port_calc or not port_calc.get("holdings"):
        return render_template_string(MY_HTML, holdings=[], total=0, capital=p.get("total_capital", 100000), pnl=0, pnl_pct=0, net_pnl=0, net_pct=0, days=0)
        
    holdings = port_calc["holdings"]
    total_val = port_calc["total_value"]
    total_inv = port_calc["total_invested"]
    total_pnl = port_calc["total_pnl"]
    net_pnl_after_fee = total_pnl * 0.9 if total_pnl > 0 else total_pnl
    total_pct = total_pnl / total_inv * 100 if total_inv > 0 else 0
    net_pct = net_pnl_after_fee / total_inv * 100 if total_inv > 0 else 0
    
    return render_template_string(MY_HTML, 
                                  holdings=holdings, 
                                  total=round(total_val), 
                                  capital=round(total_inv), 
                                  pnl=round(total_pnl), 
                                  pnl_pct=round(total_pct, 2),
                                  net_pnl=round(net_pnl_after_fee), 
                                  net_pct=round(net_pct, 2),
                                  days=port_calc["days_held"])

# ── HTML 템플릿 ───────────────────────────────────────────────────────────────

COMMON_STYLE = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
:root{--bg:#0b0f1a;--card:#131928;--border:#243050;--accent:#4f8ef7;--accent2:#1abc9c;--text:#e8eaf0;--muted:#7b8db0;--danger:#e74c3c;--success:#2ecc71;}
*{box-sizing:border-box;}
body{background:var(--bg);color:var(--text);font-family:'Inter', sans-serif;margin:0;min-height:100vh;overflow-x:hidden;}
header{padding:15px 30px;background:rgba(13, 27, 64, 0.8);backdrop-filter:blur(10px);border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:99;}
h1,h2,h3,h4{margin:0;color:#fff;}
.btn{padding:10px 18px;border-radius:10px;text-decoration:none;font-size:0.85rem;font-weight:600;margin-left:8px;border:1px solid var(--border);color:var(--text);cursor:pointer;transition:all 0.2s;}
.btn:hover{background:var(--border);transform:translateY(-2px);}
.btn-primary{background:var(--accent);border-color:var(--accent);color:#fff;}
.btn-primary:hover{background:#3b7ce0;box-shadow:0 4px 12px rgba(79,142,247,0.3);}
main{padding:30px;max-width:1300px;margin:0 auto;}
.card{background:var(--card);padding:24px;border-radius:16px;border:1px solid var(--border);margin-bottom:24px;box-shadow:0 8px 32px rgba(0,0,0,0.2);}
.grid{display:grid;grid-template-columns:repeat(auto-fit, minmax(300px, 1fr));gap:20px;}
.stat-box{text-align:center;}
.stat-val{font-size:1.8rem;font-weight:800;color:var(--accent2);margin-top:8px;}
.stat-label{font-size:0.8rem;color:var(--muted);text-transform:uppercase;letter-spacing:1px;}
table{width:100%;border-collapse:collapse;background:var(--card);border-radius:12px;overflow:hidden;margin-top:10px;}
th{text-align:left;padding:15px;background:rgba(26, 35, 64, 0.5);font-size:0.75rem;color:var(--muted);text-transform:uppercase;letter-spacing:1px;}
td{padding:15px;border-top:1px solid var(--border);font-size:0.9rem;}
.badge{padding:4px 8px;border-radius:6px;font-size:0.75rem;font-weight:800;}
.bg-success{background:rgba(46,204,113,0.1);color:var(--success);}
.bg-danger{background:rgba(231,76,60,0.1);color:var(--danger);}
canvas{max-height:400px;width:100% !important;}
table a{text-decoration:none; color:inherit; transition: color 0.2s;}
table a:hover{color:var(--accent) !important; text-decoration:underline;}

.modal { display:none; position:fixed; z-index:999; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.8); backdrop-filter:blur(5px); justify-content:center; align-items:center; }
.modal-content { background:var(--card); width:1100px; max-width:95%; border-radius:16px; border:1px solid var(--border); padding:24px; box-shadow:0 8px 32px rgba(0,0,0,0.5); position:relative; animation:slideIn 0.3s forwards; max-height:90vh; overflow-y:auto; }
@keyframes slideIn { from{transform:translateY(20px);opacity:0;} to{transform:translateY(0);opacity:1;} }
.modal-close { position:absolute; top:20px; right:20px; cursor:pointer; font-size:1.5rem; color:var(--muted); transition:0.2s;}
.modal-close:hover { color:#fff; }
.score-breakdown { background:rgba(255,255,255,0.02); padding:15px; border-radius:10px; margin-top:15px; display:grid; gap:10px; }
.score-row { display:flex; justify-content:space-between; font-size:0.9rem; border-bottom:1px dashed var(--border); padding-bottom:5px; }
.history-row { display:flex; justify-content:space-between; font-size:0.95rem; margin-bottom:8px; padding:8px; background:rgba(0,0,0,0.2); border-radius:8px;}
"""

EMPTY_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><style>""" + COMMON_STYLE + """</style></head>
<body style="display:flex;align-items:center;justify-content:center;height:100vh;">
<div style="text-align:center;"><h2>📊 데이터가 없습니다.</h2><p>먼저 분석기를 실행해주세요 (python analyze_top_vaults.py)</p></div>
</body></html>"""

MAIN_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Hyperliquid Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>""" + COMMON_STYLE + """</style></head>
<body><header><div><h1 style="background:linear-gradient(90deg, #4f8ef7, #1abc9c);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">HL Vault Analyzer Pro v3.1</h1></div><div>
<a class="btn" href="/m">📱 My Portfolio</a><a class="btn" href="/portfolio">🔬 Analysis</a><a class="btn" href="/backtest">⏪ Backtest</a><a class="btn" href="/discord">🔔 Discord</a>
</div></header><main>
<div class="grid" style="grid-template-columns: repeat(4, 1fr);">
<div class="card stat-box"><div class="stat-label">Analysis Date</div><div class="stat-val" style="color:#fff">{{date}} <small style="font-size:0.8rem;color:var(--muted)">{% if stats.prev_date %}(vs {{stats.prev_date}}){% endif %}</small></div></div>
<div class="card stat-box"><div class="stat-label">Active Vaults</div><div class="stat-val">{{stats.total}}</div></div>
<div class="card stat-box"><div class="stat-label">Avg 30D APR</div><div class="stat-val" style="color:var(--success)">{{stats.avg_apr|round(1)}}%</div></div>
<div class="card stat-box"><div class="stat-label">Avg MDD</div><div class="stat-val" style="color:var(--danger)">{{stats.avg_mdd}}%</div></div>
</div>
<div class="card" style="margin-bottom:15px;">
    <div style="margin-bottom:15px;">
        <h3>Top Vaults (All 200) <span id="matchCount" style="color:var(--accent2); font-size:1rem; margin-left:10px; background:rgba(26,188,156,0.1); padding:4px 10px; border-radius:10px;"></span></h3>
    </div>
    <div style="display:flex; gap:20px; align-items:center; flex-wrap:wrap; background:rgba(255,255,255,0.03); padding:15px; border-radius:12px; border:1px solid var(--border);">
        <div>
            <label style="font-size:0.8rem; color:var(--muted); margin-right:8px;">Leader Eq Min:</label>
            <select id="leaderFilter" onchange="filterTable()" style="padding:8px; background:var(--bg); border:1px solid var(--border); color:#fff; border-radius:8px;">
                <option value="0">All</option>
                <option value="0.1">10%+</option>
                <option value="0.2">20%+</option>
                <option value="0.3">30%+</option>
                <option value="0.4">40%+</option>
            </select>
        </div>
        <div>
            <label style="font-size:0.8rem; color:var(--muted); margin-right:8px;">Max MDD:</label>
            <select id="mddFilter" onchange="filterTable()" style="padding:8px; background:var(--bg); border:1px solid var(--border); color:#fff; border-radius:8px;">
                <option value="999">All</option>
                <option value="10">Under 10%</option>
                <option value="20">Under 20%</option>
                <option value="30">Under 30%</option>
                <option value="40">Under 40%</option>
                <option value="50">Under 50%</option>
            </select>
        </div>
        <div>
            <label style="font-size:0.8rem; color:var(--muted); margin-right:8px;">Deposits:</label>
            <select id="depositFilter" onchange="filterTable()" style="padding:8px; background:var(--bg); border:1px solid var(--border); color:#fff; border-radius:8px;">
                <option value="all">All</option>
                <option value="open">Open Only</option>
            </select>
        </div>
    </div>
</div>

<div class="card">
    <table id="vaultTable">
        <thead>
            <tr>
                <th>Rank</th>
                <th>Vault Name</th>
                <th>TVL (USD/KRW)</th>
                <th style="text-align:center;">Leader Eq%</th>
                <th>All-time PnL</th>
                <th>All-time MDD</th>
                <th>Sharpe Ratio</th>
                <th>30d APR</th>
                <th>Score</th>
                <th>Deposit</th>
            </tr>
        </thead>
        <tbody>
        {% for v in vaults %}
        <tr data-leader="{{ v.leader_equity_ratio }}" data-deposit="{{ 'open' if v.allow_deposits else 'closed' }}" data-mdd="{{ v.max_drawdown }}">
            <td>
                #{{v.rank}}<br>
                {% if v.has_history and v.chg.rank_val != 0 %}
                    <small style="color:{{ v.chg.rank_col }}; font-weight:bold;">{{ v.chg.rank_dir }} {{ v.chg.rank_val }}</small>
                {% elif v.has_history %}
                    <small style="color:var(--muted)">-</small>
                {% else %}
                    <span class="badge" style="background:rgba(241,196,15,0.1);color:#f1c40f;">NEW</span>
                {% endif %}
            </td>
            <td><a href="https://app.hyperliquid.xyz/vaults/{{v.address}}" target="_blank"><b>{{v.name}}</b></a><br><small style="color:var(--muted)">{{v.address[:10]}}..</small></td>
            <td>
                <span style="font-weight:600;">${{ "{:,.0f}".format(v.tvl) }}</span><br>
                <small style="color:var(--muted)">≈ {{ "{:,.1f}".format(v.tvl * 1400 / 100000000) }} 억원</small>
            </td>
            <td style="text-align:center;">
                <span class="badge" style="background:rgba(26,188,156,0.1);color:var(--accent2)">{{ (v.leader_equity_ratio * 100)|round(1) }}%</span><br>
                <small style="color:var(--muted)">≈ {{ "{:,.1f}".format(v.leader_equity_usd * 1400 / 100000000) }} 억원</small>
            </td>
            <td>
                <span style="color:{{ 'var(--success)' if v.pnl_alltime >= 0 else 'var(--danger)' }}; font-weight:600;">${{ "{:,.0f}".format(v.pnl_alltime) }}</span>
                <span style="font-size:0.8rem; color:var(--accent2); margin-left:4px;">({{ "{:,.1f}".format(v.alltime_roi_pct) }}%)</span><br>
                <small style="color:var(--muted)">({{ "{:,.2f}".format(v.pnl_alltime * 1400 / 100000000) }} 억원)</small>
                {% if v.has_history and v.chg.pnl_val != 0 %}
                    <br><small style="color:{{ v.chg.pnl_col }}">{{ v.chg.pnl_dir }} ${{ "{:,.0f}".format(v.chg.pnl_val) }}</small>
                {% endif %}
            </td>
            <td>
                <span style="color:var(--danger); font-weight:600;">{{ v.max_drawdown }}%</span>
                {% if v.has_history and v.chg.mdd_val != 0 %}
                    <br><small style="color:{{ v.chg.mdd_col }}">{{ v.chg.mdd_dir }} {{ v.chg.mdd_val }}%p</small>
                {% endif %}
            </td>
            <td style="color:var(--accent); font-weight:600;">{{ v.sharpe_ratio }}</td>
            <td style="color:var(--success); font-weight:600;">{{ v.apr_30d }}%</td>
            <td style="cursor:pointer;" onclick="showVaultDetails('{{v.address}}')">
                <span class="badge" style="background:rgba(79,142,247,0.1);color:var(--accent);font-size:0.9rem;border:1px solid rgba(79,142,247,0.3);transition:0.2s;" onmouseover="this.style.background='rgba(79,142,247,0.2)'" onmouseout="this.style.background='rgba(79,142,247,0.1)'">{{ v.score }}</span>
                {% if v.has_history and v.chg.score_val != 0 %}
                    <br><small style="color:{{ v.chg.score_col }}">{{ v.chg.score_dir }} {{ "{:,.3f}".format(v.chg.score_val) }}</small>
                {% endif %}
            </td>
            <td style="text-align:center;">
                {% if v.allow_deposits %}
                <span class="badge bg-success">OPEN</span>
                {% else %}
                <span class="badge bg-danger">CLOSE</span>
                {% endif %}
            </td>
        </tr>
        {% endfor %}
        </tbody>
    </table>
</div>

<!-- Vault Details Modal -->
<div id="vaultModal" class="modal" onclick="if(event.target === this) closeModal()">
    <div class="modal-content">
        <span class="modal-close" onclick="closeModal()">×</span>
        <h2 id="modalTitle" style="color:var(--accent2); margin-bottom:5px;">Vault DETAILS</h2>
        <p style="color:var(--muted); font-size:0.85rem; margin-bottom:20px;">Performance tracking & Score breakdown</p>
        
        <div style="display:flex; gap:20px; align-items:flex-start; margin-bottom:20px;">
            <div style="flex:1;">
                <h4 style="color:var(--text); margin-bottom:10px; border-bottom:1px solid var(--border); padding-bottom:5px;">📈 All-time PnL Curve (USD)</h4>
                <div style="height:250px;"><canvas id="modalPnlChart"></canvas></div>
            </div>
            <div style="flex:1; display:flex; flex-direction:column; gap:20px;">
                <div>
                    <h4 style="color:var(--text); margin-bottom:10px; border-bottom:1px solid var(--border); padding-bottom:5px;">⚖️ Change vs Prev. Snapshot (%)</h4>
                    <div style="height:120px;"><canvas id="modalChgChart"></canvas></div>
                    <div id="modalNewIndicator" style="display:none; color:var(--muted); text-align:center; padding:10px 0;">신규 편입 (과거 데이터 없음)</div>
                </div>
                <div>
                    <h4 style="color:var(--text); margin-bottom:10px; border-bottom:1px solid var(--border); padding-bottom:5px;">🧮 Score Breakdown</h4>
                    <div style="height:120px;"><canvas id="modalScoreChart"></canvas></div>
                    <p style="color:var(--muted); font-size:0.75rem; margin-top:5px; text-align:right;">Score = (+Sharpe×2) (+APR/50) (-MDD/30) (+Rob×3)</p>
                </div>
            </div>
        </div>
        
        <h4 style="color:var(--accent2); margin-top:30px; margin-bottom:10px; border-bottom:1px solid var(--border); padding-bottom:5px;">📊 Historical Trend</h4>
        <div style="display:grid; grid-template-columns:1fr 1fr 1fr 1fr; gap:15px; margin-bottom:10px;">
            <div>
                <div style="text-align:center; font-size:0.85rem; color:var(--muted); margin-bottom:5px;">🏅 Score</div>
                <div style="height:140px;"><canvas id="modalTrendScoreChart"></canvas></div>
            </div>
            <div>
                <div style="text-align:center; font-size:0.85rem; color:var(--muted); margin-bottom:5px;">📉 MDD (%)</div>
                <div style="height:140px;"><canvas id="modalTrendMddChart"></canvas></div>
            </div>
            <div>
                <div style="text-align:center; font-size:0.85rem; color:var(--muted); margin-bottom:5px;">✨ Sharpe Ratio</div>
                <div style="height:140px;"><canvas id="modalTrendSharpeChart"></canvas></div>
            </div>
            <div>
                <div style="text-align:center; font-size:0.85rem; color:var(--muted); margin-bottom:5px;">🛡️ Robustness</div>
                <div style="height:140px;"><canvas id="modalTrendRobustChart"></canvas></div>
            </div>
        </div>
    </div>
</div>

<script>
const vaultConfig = {
    {% for v in vaults %}
    "{{v.address}}": {
        "name": "{{v.name}}",
        "score": {{v.score}},
        "calc_sharpe": {{v.sharpe_ratio}},
        "calc_apr": {{v.apr_30d}},
        "calc_mdd": {{v.max_drawdown}},
        "calc_rob": {{v.robustness_score | default(0)}},
        "has_history": {{ 'true' if v.has_history else 'false' }},
        "alltime_pnl": {{ v.alltime_pnl | default([]) | tojson }},
        "chg_pct": {{ v.chg_pct | default({}) | tojson }},
        "trend_hist": {{ v.history | tojson }}
    }{% if not loop.last %},{% endif %}
    {% endfor %}
};

let modalCharts = {};

function showVaultDetails(address) {
    const data = vaultConfig[address];
    if(!data) return;
    
    document.getElementById('modalTitle').innerText = data.name + " Details";
    
    // Destroy existing charts
    Object.values(modalCharts).forEach(c => c.destroy());
    modalCharts = {};
    
    // 1. PNL Curve
    const pnlCtx = document.getElementById('modalPnlChart').getContext('2d');
    if(data.alltime_pnl && data.alltime_pnl.length > 0) {
        modalCharts.pnl = new Chart(pnlCtx, {
            type: 'line',
            data: {
                labels: data.alltime_pnl.map((_, i) => i+1),
                datasets: [{
                    label: 'Cumulative PnL ($)',
                    data: data.alltime_pnl,
                    borderColor: '#1abc9c',
                    backgroundColor: 'rgba(26,188,156,0.1)',
                    fill: true,
                    tension: 0.1,
                    pointRadius: 0,
                    pointHitRadius: 10
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { x: { display: false } }
            }
        });
    } else {
        modalCharts.pnl = new Chart(pnlCtx, { type: 'line', data: {labels:['No Data'], datasets:[{data:[0]}]}, options:{plugins:{legend:{display:false}}} });
    }
    
    // 2. Daily Change Bar Chart
    const chgCtx = document.getElementById('modalChgChart').getContext('2d');
    if (data.has_history && data.chg_pct && Object.keys(data.chg_pct).length > 0) {
        document.getElementById('modalChgChart').style.display = 'block';
        document.getElementById('modalNewIndicator').style.display = 'none';
        modalCharts.chg = new Chart(chgCtx, {
            type: 'bar',
            data: {
                labels: ['TVL', 'L_Eq', 'PnL', 'MDD', 'Sharpe', 'Score'],
                datasets: [{
                    label: '% Change',
                    data: [data.chg_pct.tvl, data.chg_pct.eq, data.chg_pct.pnl, data.chg_pct.mdd, data.chg_pct.sharpe, data.chg_pct.score],
                    backgroundColor: function(context) {
                        return context.raw >= 0 ? 'rgba(46,204,113,0.8)' : 'rgba(231,76,60,0.8)';
                    },
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { suggestedMin: -5, suggestedMax: 5 } }
            }
        });
    } else {
        document.getElementById('modalChgChart').style.display = 'none';
        document.getElementById('modalNewIndicator').style.display = 'block';
    }

    // 3. Score Breakdown (Horizontal Bar)
    const scoreCtx = document.getElementById('modalScoreChart').getContext('2d');
    let sharpeVal = data.calc_sharpe * 2.0;
    let aprVal = data.calc_apr / 50.0;
    let mddVal = data.calc_mdd / 30.0; // penalty
    let robVal = data.calc_rob * 3.0;

    modalCharts.score = new Chart(scoreCtx, {
        type: 'bar',
        data: {
            labels: ['Sharpe', 'APR', 'MDD Pen.', 'Robust'],
            datasets: [{
                label: 'Points',
                data: [sharpeVal, aprVal, -mddVal, robVal],
                backgroundColor: ['#3498db', '#2ecc71', '#e74c3c', '#9b59b6'],
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true, maintainAspectRatio: false,
            plugins: { legend: { display: false } }
        }
    });

    // 4. Trend Charts (Score, MDD, Sharpe, Robustness)
    function buildTrendChart(ctxId, label, dataArr, datesArr, bgColor, borderColor) {
        const ctx = document.getElementById(ctxId).getContext('2d');
        if(!dataArr || dataArr.length === 0) {
            return new Chart(ctx, { type:'line', data:{labels:['No Data'], datasets:[{data:[0]}]}, options:{plugins:{legend:{display:false}}} });
        }
        return new Chart(ctx, {
            type: 'line',
            data: {
                labels: datesArr,
                datasets: [{
                    label: label,
                    data: dataArr,
                    borderColor: borderColor,
                    backgroundColor: bgColor,
                    fill: true,
                    tension: 0.2,
                    pointRadius: 3,
                    pointBackgroundColor: borderColor
                }]
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { 
                    legend: { display: false },
                    tooltip: { mode: 'index', intersect: false }
                },
                scales: { 
                    x: { display: true, ticks: { font: { size: 9 }, color: 'var(--muted)', maxRotation:45 } },
                    y: { display: true, ticks: { font: { size: 9 }, color: 'var(--muted)' } }
                }
            }
        });
    }

    let tDates = data.trend_hist && data.trend_hist.dates ? data.trend_hist.dates : [];
    
    modalCharts.tScore = buildTrendChart('modalTrendScoreChart', 'Score', data.trend_hist ? data.trend_hist.score : [], tDates, 'rgba(79,142,247,0.1)', '#4f8ef7');
    modalCharts.tMdd = buildTrendChart('modalTrendMddChart', 'MDD', data.trend_hist ? data.trend_hist.mdd : [], tDates, 'rgba(231,76,60,0.1)', '#e74c3c');
    modalCharts.tSharpe = buildTrendChart('modalTrendSharpeChart', 'Sharpe', data.trend_hist ? data.trend_hist.sharpe : [], tDates, 'rgba(52,152,219,0.1)', '#3498db');
    modalCharts.tRobust = buildTrendChart('modalTrendRobustChart', 'Robustness', data.trend_hist ? data.trend_hist.robust : [], tDates, 'rgba(155,89,182,0.1)', '#9b59b6');

    document.getElementById('vaultModal').style.display = 'flex';
}

function closeModal() {
    document.getElementById('vaultModal').style.display = 'none';
}

function filterTable() {
    const leaderMin = parseFloat(document.getElementById('leaderFilter').value);
    const mddMax = parseFloat(document.getElementById('mddFilter').value);
    const depositType = document.getElementById('depositFilter').value;
    const rows = document.querySelectorAll('#vaultTable tbody tr');
    let count = 0;
    
    rows.forEach(row => {
        const leader = parseFloat(row.getAttribute('data-leader'));
        const deposit = row.getAttribute('data-deposit');
        const mdd = parseFloat(row.getAttribute('data-mdd'));
        
        const leaderMatch = leader >= leaderMin;
        const depositMatch = (depositType === 'all') || (deposit === depositType);
        const mddMatch = mdd <= mddMax;
        
        if (leaderMatch && depositMatch && mddMatch) {
            row.style.display = '';
            count++;
        } else {
            row.style.display = 'none';
        }
    });
    document.getElementById('matchCount').innerText = `${count} vaults matched`;
}
document.addEventListener('DOMContentLoaded', filterTable);
</script>
</main></body></html>"""

PORTFOLIO_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><script src="https://cdn.jsdelivr.net/npm/chart.js"></script><style>""" + COMMON_STYLE + """</style></head><body>
<header><div><h1>🔬 Portfolio Analysis</h1></div><a class="btn" href="/">← Back</a></header>
<main>
{% if d.portfolio_summary %}
<div class="card"><h3>Historical Tracking (Simulated)</h3>
<div style="height:350px;"><canvas id="historyChart"></canvas></div>
<div class="grid" style="margin-top:20px;">
<div class="stat-box"><div class="stat-label">Cumulative Return</div><div class="stat-val" style="color:var(--success)">{{d.portfolio_summary.cumulative_pct}}%</div></div>
<div class="stat-box"><div class="stat-label">Max Drawdown</div><div class="stat-val" style="color:var(--danger)">{{d.portfolio_summary.max_mdd_pct}}%</div></div>
<div class="stat-box"><div class="stat-label">Sharpe Ratio</div><div class="stat-val" style="color:var(--accent)">{{d.portfolio_summary.sharpe_ratio}}</div></div>
</div></div>
{% endif %}
<div class="card"><h2>Recommended Portfolios</h2><div class="grid">
{% for k, p in d.portfolios.items() %}<div class="card" style="margin-bottom:0; border-left:4px solid var(--accent2)">
<h4 style="color:var(--accent); text-transform:uppercase;">{{p.label}} {{p.emoji}}</h4><p style="font-size:1.6rem;font-weight:800;margin:15px 0;">{{p.stats.annual_return_pct}}% <small style="font-size:0.8rem;color:var(--muted);font-weight:400;">Expected APR</small></p>
<div style="display:flex;justify-content:space-between;font-size:0.85rem;color:var(--muted);">
<span>Vol: {{p.stats.annual_vol_pct}}%</span><span>Sharpe: {{p.stats.sharpe}}</span><span>MDD: {{p.backtest.max_drawdown_pct}}%</span>
</div><div style="margin-top:15px; background:rgba(255,255,255,0.05); padding:10px; border-radius:8px;">
{% for vname, w in p.stats.weights.items() %}{% if w > 5 %}<div style="display:flex;justify-content:space-between;font-size:0.75rem;margin-bottom:4px;"><span>{{vname[:20]}}</span><span>{{w}}%</span></div>{% endif %}{% endfor %}
</div></div>{% endfor %}</div></div></main>
<script>
{% if d.portfolio_summary %}
const ctx = document.getElementById('historyChart').getContext('2d');
const dates = {{ d.portfolio_summary.value_series | map(attribute=0) | list | tojson }};
const values = {{ d.portfolio_summary.value_series | map(attribute=1) | list | tojson }};
new Chart(ctx, {
  type: 'line',
  data: {
    labels: dates,
    datasets: [{
      label: 'Portfolio Value ($)',
      data: values,
      borderColor: '#1abc9c',
      backgroundColor: 'rgba(26, 188, 156, 0.1)',
      fill: true,
      tension: 0.4,
      borderWidth: 3,
      pointRadius: 0
    }]
  },
  options: {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false } },
    scales: {
      x: { grid: { display: false }, ticks: { color: '#7b8db0', maxRotation: 0 } },
      y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#7b8db0' } }
    }
  }
});
{% endif %}
</script></body></html>"""

BACKTEST_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><script src="https://cdn.jsdelivr.net/npm/chart.js"></script><style>""" + COMMON_STYLE + """</style></head><body>
<header><h1>⏪ Strategy Backtest</h1><a class="btn" href="/">← Back</a></header>
<main><div class="card" id="bt-container">
<div style="text-align:center;padding:50px;">Calculating...</div>
</div></main>
<script>
fetch('/api/backtest').then(r=>r.json()).then(d=>{
  if(d.error) { document.getElementById('bt-container').innerHTML = `<h3>Error: ${d.error}</h3>`; return; }
  document.getElementById('bt-container').innerHTML = `
    <h2 style="color:var(--accent2)">Max Sharpe Equity Curve</h2>
    <h1 style="font-size:3rem;margin:10px 0;">$${d.final_value.toLocaleString()} <small style="font-size:1rem;color:var(--success)">+${d.total_return_pct}%</small></h1>
    <div style="display:flex;gap:30px;margin-bottom:30px;color:var(--muted);">
      <div>Monthly Return: <b>${(d.annual_return_pct/12).toFixed(2)}%</b></div>
      <div>Max Drawdown: <b style="color:var(--danger)">${d.max_drawdown_pct}%</b></div>
      <div>Sharpe: <b>${d.sharpe_ratio}</b></div>
    </div>
    <div style="height:350px;"><canvas id="btChart"></canvas></div>
  `;
  const ctx = document.getElementById('btChart').getContext('2d');
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: Array.from({length: d.equity_curve.length}, (_, i) => i),
      datasets: [{ label: 'Equity', data: d.equity_curve, borderColor: '#4f8ef7', fill: false, tension: 0.4, pointRadius: 0 }]
    },
    options: { responsive: true, maintainAspectRatio: false, scales: { x:{display:false}, y:{grid:{color:'rgba(255,255,255,0.05)'}} } }
  });
});
</script></body></html>"""

DISCORD_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><style>""" + COMMON_STYLE + """</style></head><body>
<header><h1>🔔 Discord Notifications</h1><a class="btn" href="/">← Back</a></header>
<main><div class="card" style="max-width:600px;margin:auto;">
<h3>Webhook Integration</h3>
<p style="color:var(--muted);font-size:0.9rem;margin:15px 0;">Receive daily analysis reports and rebalancing alerts directly on your Discord server.</p>
<input id="url" style="width:100%;padding:14px;background:#0b0f1a;border:1px solid var(--border);color:#fff;border-radius:10px;margin-bottom:20px;" placeholder="https://discord.com/api/webhooks/..." value="{{wk}}">
<button class="btn btn-primary" style="width:100%;padding:14px;margin:0;" onclick="save()">Save & Connect</button>
<p id="msg" style="text-align:center;margin-top:15px;"></p>
</div></main>
<script>
function save(){
  const url = document.getElementById('url').value;
  if(!url.startsWith('http')){ alert('Invalid URL'); return; }
  fetch('/api/discord-setup',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({webhook_url:url})})
  .then(r=>r.json()).then(d=>{
    document.getElementById('msg').innerHTML='<span style="color:var(--success)">✅ Successfully Connected!</span>';
    setTimeout(()=>location.reload(), 2000);
  });
}
</script></body></html>"""

MY_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><style>""" + COMMON_STYLE + """</style></head><body>
<header><h1>📱 My Portfolio</h1><a class="btn" href="/">← Back</a></header>
<main>
<div class="grid" style="grid-template-columns: 2fr 1fr;">
<div class="card"><h3>Current Positions</h3>
{% if holdings %}
<table><thead><tr><th>Vault</th><th>Invested / Weight</th><th>Holding Period</th><th>APR / MDD</th><th>Gross PnL</th><th>Est. Value</th></tr></thead><tbody>
{% for h in holdings %}<tr>
<td><a href="https://app.hyperliquid.xyz/vaults/{{h.address}}" target="_blank"><b>{{h.name}}</b></a><br><small style="color:var(--muted)">{{h.address[:12]}}...</small></td>
<td>${{ "{:,.0f}".format(h.invested_usd) }}<br><small style="color:var(--accent2)">{{ h.weight_pct }}%</small></td>
<td>{{ h.days_held }} Days</td>
<td><span style="color:var(--success)">{{ h.apr_30d }}%</span><br><small style="color:var(--danger)">{{ h.mdd }}%</small></td>
<td><span style="color:{{ 'var(--success)' if h.pnl >= 0 else 'var(--danger)' }}; font-weight:600;">${{ "{:,.0f}".format(h.pnl) }}</span><br><small style="color:{{ 'var(--success)' if h.pnl_pct >= 0 else 'var(--danger)' }}">{{ h.pnl_pct }}%</small></td>
<td style="font-weight:600; color:#fff;">${{ "{:,.0f}".format(h.est_value) }}</td>
</tr>{% endfor %}
</tbody></table>
{% else %}
<p style="padding:40px;text-align:center;color:var(--muted);">No positions found. Update <code>my_portfolio.json</code> to track your holdings.</p>
{% endif %}
</div>
<div class="card"><h3>Performance Summary</h3>
<div style="margin-bottom:20px; padding-bottom:20px; border-bottom:1px solid var(--border);">
<div class="stat-label">Total Invested</div><div class="stat-val" style="color:#fff;">$ {{ "{:,.0f}".format(capital) }}</div>
</div>
<div style="margin-bottom:20px; padding-bottom:20px; border-bottom:1px solid var(--border);">
<div class="stat-label">Holding Period</div><div class="stat-val" style="color:var(--muted);">{{ days }} Days</div>
</div>
<div style="margin-bottom:20px; padding-bottom:20px; border-bottom:1px solid var(--border);">
<div class="stat-label">Gross PnL (Before Fees)</div>
<div class="stat-val" style="color:{{ 'var(--success)' if pnl >= 0 else 'var(--danger)' }}">$ {{ "{:,.0f}".format(pnl) }}</div>
<div style="text-align:center; font-size:0.9rem; color:{{ 'var(--success)' if pnl >= 0 else 'var(--danger)' }};">{{ pnl_pct }}%</div>
</div>
<div style="margin-bottom:25px;">
<div class="stat-label">Net PnL (After 10% Fee)</div>
<div class="stat-val" style="color:{{ 'var(--success)' if net_pnl >= 0 else 'var(--danger)' }}; font-size:2.2rem;">$ {{ "{:,.0f}".format(net_pnl) }}</div>
<div style="text-align:center; font-size:0.95rem; font-weight:600; color:{{ 'var(--success)' if net_pnl >= 0 else 'var(--danger)' }};">{{ net_pct }}%</div>
</div>
<a class="btn btn-primary" style="display:block;text-align:center;margin:0;" href="/portfolio">View Rebalancing Advice</a>
</div></div></main></body></html>"""

if __name__ == "__main__":
    print("🚀 Hyperliquid Dashboard Pro v3.1 - Port 5001")
    app.run(host="0.0.0.0", port=5001)

