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

@app.route("/")
def index():
    vaults, date = get_latest_snapshot()
    if not vaults:
        return render_template_string(EMPTY_HTML)
    
    avg_mdd = sum(v.get("max_drawdown", 0) for v in vaults) / len(vaults) if vaults else 0
    stats = {
        "total": len(vaults),
        "avg_apr": sum(v.get("apr_30d", 0) for v in vaults) / len(vaults) if vaults else 0,
        "avg_mdd": round(avg_mdd, 2)
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
    p = load_portfolio_config()
    vaults, date = get_latest_snapshot()
    v_map = {v["address"]: v for v in vaults} if vaults else {}
    
    holdings = []
    total_val = 0
    for addr, amt in p.get("positions", {}).items():
        v = v_map.get(addr, {"name": "Unknown", "apr_30d": 0, "max_drawdown": 0})
        holdings.append({
            "address": addr,
            "name": v["name"],
            "amount": amt,
            "apr": v.get("apr_30d", 0),
            "mdd": v.get("max_drawdown", 0)
        })
        total_val += amt
        
    return render_template_string(MY_HTML, holdings=holdings, total=total_val, capital=p.get("total_capital", 100000))

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
<div class="card stat-box"><div class="stat-label">Analysis Date</div><div class="stat-val" style="color:#fff">{{date}}</div></div>
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
            <td>#{{v.rank or loop.index}}</td>
            <td><a href="https://app.hyperliquid.xyz/vaults/{{v.address}}" target="_blank"><b>{{v.name}}</b></a><br><small style="color:var(--muted)">{{v.address[:10]}}..</small></td>
            <td>
                <span style="font-weight:600;">${{ "{:,.0f}".format(v.tvl) }}</span><br>
                <small style="color:var(--muted)">≈ {{ "{:,.1f}".format(v.tvl * 1400 / 100000000) }} 억원</small>
            </td>
            <td style="text-align:center;">
                <span class="badge" style="background:rgba(26,188,156,0.1);color:var(--accent2)">{{ (v.leader_equity_ratio * 100)|round(1) }}%</span>
            </td>
            <td>
                <span style="color:{{ 'var(--success)' if v.pnl_alltime >= 0 else 'var(--danger)' }}; font-weight:600;">${{ "{:,.3f}".format(v.pnl_alltime) }}</span><br>
                <small style="color:var(--muted)">({{ "{:,.2f}".format(v.pnl_alltime * 1400 / 100000000) }} 억원)</small>
            </td>
            <td style="color:var(--danger); font-weight:600;">{{ v.max_drawdown }}%</td>
            <td style="color:var(--accent); font-weight:600;">{{ v.sharpe_ratio }}</td>
            <td style="color:var(--success); font-weight:600;">{{ v.apr_30d }}%</td>
            <td><span class="badge" style="background:rgba(79,142,247,0.1);color:var(--accent);font-size:0.9rem;">{{ v.score }}</span></td>
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

<script>
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
<table><thead><tr><th>Vault</th><th>Invested</th><th>Weight</th><th>APR</th><th>MDD</th></tr></thead><tbody>
{% for h in holdings %}<tr><td><a href="https://app.hyperliquid.xyz/vaults/{{h.address}}" target="_blank"><b>{{h.name}}</b></a><br><small style="color:var(--muted)">{{h.address[:12]}}...</small></td><td>${{h.amount|int}}</td><td>{{(h.amount/total*100)|round(1)}}%</td><td style="color:var(--success)">{{h.apr}}%</td><td style="color:var(--danger)">{{h.mdd}}%</td></tr>{% endfor %}
</tbody></table>
{% else %}
<p style="padding:40px;text-align:center;color:var(--muted);">No positions found. Update <code>my_portfolio.json</code> to track your holdings.</p>
{% endif %}
</div>
<div class="card"><h3>Summary</h3>
<div style="margin-bottom:25px;">
<div class="stat-label">Total Invested</div><div class="stat-val">$ {{total|int}}</div>
</div>
<div style="margin-bottom:25px;">
<div class="stat-label">Initial Capital</div><div class="stat-val" style="color:#fff">$ {{capital|int}}</div>
</div>
<div style="margin-bottom:25px;">
<div class="stat-label">All-time PnL</div><div class="stat-val" style="color:{{ 'var(--success)' if total >= capital else 'var(--danger)' }}">{{ (((total/capital)-1)*100)|round(2) }}%</div>
</div>
<a class="btn btn-primary" style="display:block;text-align:center;margin:0;" href="/portfolio">View Rebalancing Advice</a>
</div></div></main></body></html>"""

if __name__ == "__main__":
    print("🚀 Hyperliquid Dashboard Pro v3.1 - Port 5001")
    app.run(host="0.0.0.0", port=5001)

