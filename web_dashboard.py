#!/usr/bin/env python3
import os, sys, json, glob, threading, urllib.request, sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from flask import Flask, render_template_string, jsonify, request, redirect, make_response
from flask_jwt_extended import (
    JWTManager, jwt_required, get_jwt_identity, 
    set_access_cookies, unset_jwt_cookies, create_access_token
)
from flask_jwt_extended.exceptions import NoAuthorizationError
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

app = Flask(__name__)

# JWT 쿠키 기반 인증 환경설정
app.config["JWT_SECRET_KEY"] = "hyperliquid-vault-analyzer-secret-2026-key"
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_COOKIE_CSRF_PROTECT"] = False  # 모바일 브라우저 편의를 위해 CSRF 비활성화
app.config["JWT_ACCESS_COOKIE_PATH"] = "/"
app.config["JWT_COOKIE_SECURE"] = False  # 로컬 및 프라이빗 터널(HTTP/HTTPS) 호환용

jwt = JWTManager(app)

# 경로 및 환경
BASE_DIR       = Path(__file__).parent
DATA_DIR       = BASE_DIR / "vault_data"
SNAPSHOTS_DIR  = DATA_DIR / "snapshots"
REPORTS_DIR    = DATA_DIR / "reports"
PORTFOLIO_FILE = BASE_DIR / "my_portfolio.json"
DISCORD_CFG    = BASE_DIR / "discord_config.json"

for d in [SNAPSHOTS_DIR, REPORTS_DIR]: os.makedirs(d, exist_ok=True)

# ── auth.py 블루프린트 연동 및 기본 계정 생성 ─────────────────────────────────
from auth import auth_bp, init_db, setup_jwt, DB_PATH, _check_password, _hash_password
app.register_blueprint(auth_bp)
init_db(app)
setup_jwt(jwt)

def create_default_admin():
    """앱 기동 시 어드민 계정이 없을 경우 기본 계정 자동 생성"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM users")
    if cursor.fetchone()[0] == 0:
        pw_hash = _hash_password("admin1234")
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
            ("admin", "admin@hyperliquid.com", pw_hash, "admin")
        )
        conn.commit()
        print("👤 [SECURITY] 기본 관리자 계정이 생성되었습니다. (ID: admin@hyperliquid.com / PW: admin1234)")
    conn.close()

create_default_admin()

# ── 미인증 및 만료 토큰 자동 리다이렉트 핸들러 ────────────────────────────────
@app.errorhandler(NoAuthorizationError)
@app.errorhandler(ExpiredSignatureError)
@app.errorhandler(InvalidTokenError)
def handle_auth_failures(e):
    return redirect("/login")

# ── 로그인 / 로그아웃 라우트 ──────────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login_view():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        user = conn.execute("SELECT id, username, email, password_hash, is_active, role FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()
        
        if not user or not user["is_active"] or not _check_password(password, user["password_hash"]):
            return render_template_string(LOGIN_HTML, error="이메일 또는 비밀번호가 올바르지 않습니다.")
            
        identity = str(user["id"])
        access_token = create_access_token(
            identity=identity,
            additional_claims={"role": user["role"], "username": user["username"]},
            expires_delta=timedelta(hours=24)  # 모바일 편의를 위해 24시간
        )
        
        response = make_response(redirect("/"))
        set_access_cookies(response, access_token)
        return response
        
    return render_template_string(LOGIN_HTML)

@app.route("/logout")
def logout_view():
    response = make_response(redirect("/login"))
    unset_jwt_cookies(response)
    return response


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
@jwt_required()
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
@jwt_required()
def portfolio_page():
    try:
        from portfolio_engine import run_portfolio_analysis
        addr_param = request.args.get("addresses", "")
        addresses = [a.strip() for a in addr_param.split(",") if a.strip()] if addr_param else None
        d = run_portfolio_analysis(top_k=25, max_corr=0.55, addresses=addresses)
        d["user_selected_mode"] = bool(addresses)
        d["user_selected_count"] = len(addresses) if addresses else 0
    except Exception as e:
        return f"<body style='background:#0b0f1a;color:#e74c3c;padding:40px;'><h2>⚠️ 분석 에러</h2><p>{e}</p></body>"
    return render_template_string(PORTFOLIO_HTML, d=d)

@app.route("/api/simulate", methods=["POST"])
@jwt_required()
def api_simulate():
    data = request.json or {}
    start_date = data.get("start_date")
    sim_amount = float(data.get("amount", 100000))
    ptype = data.get("ptype", "max_sharpe")
    custom_vaults = data.get("custom_vaults")

    import portfolio_tracker
    
    if custom_vaults:
        recs = []
        for cv in custom_vaults:
            if float(cv.get("weight", 0)) > 0:
                recs.append({
                    "name": cv.get("name", ""),
                    "address": cv.get("address", ""),
                    "suggested_allocation": float(cv.get("weight", 0))
                })
    else:
        from portfolio_engine import run_portfolio_analysis
        d = run_portfolio_analysis()
        if "error" in d: return jsonify(d)

        # get weights for chosen portfolio
        st = d["portfolios"].get(ptype, {}).get("stats", {})
        weights = st.get("weights", {})
        
        # map names to address
        name_to_addr = {v["name"]: v["address"] for v in d["selected_vaults"]}
        
        recs = []
        for nm, w in weights.items():
            if w > 0:
                recs.append({
                    "name": nm,
                    "address": name_to_addr.get(nm, ""),
                    "suggested_allocation": w
                })
            
    snaps = portfolio_tracker.load_snapshots_all()
    res = portfolio_tracker.simulate_rec_backtest(recs, snaps, start_date, sim_amount)
    
    if not res: return jsonify({"error": "데이터 또는 시뮬레이션 결과가 없습니다."})
    return jsonify(res)

@app.route("/discord")
@jwt_required()
def discord_gui():
    wk = ""
    if os.path.exists(DISCORD_CFG):
        with open(str(DISCORD_CFG), encoding="utf-8") as f: wk = json.load(f).get("webhook_url", "")
    return render_template_string(DISCORD_HTML, wk=wk)

@app.route("/api/discord-setup", methods=["POST"])
@jwt_required()
def api_discord_save():
    data = request.get_json() or {}
    with open(str(DISCORD_CFG), "w", encoding="utf-8") as f: json.dump({"webhook_url": data.get("webhook_url","")}, f)
    send_discord("✅ 연결 성공! Hyperliquid Vault Analyzer와 연동되었습니다.")
    return jsonify({"status": "ok"})

@app.route("/api/portfolio/save", methods=["POST"])
@jwt_required()
def api_portfolio_save():
    data = request.get_json() or {}
    if "positions" not in data or "invest_date" not in data or "total_capital" not in data:
        return jsonify({"error": "Missing required fields: positions, invest_date, total_capital"}), 400
    
    positions = data["positions"]
    invest_date = data["invest_date"]
    total_capital = data["total_capital"]
    
    if not isinstance(positions, dict):
        return jsonify({"error": "positions must be a dictionary mapping vault addresses to numbers"}), 400
    
    cleaned_positions = {}
    for k, v in positions.items():
        k_clean = k.strip().lower()
        if not k_clean.startswith("0x"):
            return jsonify({"error": f"Invalid vault address format: {k}"}), 400
        try:
            cleaned_positions[k_clean] = float(v)
        except (ValueError, TypeError):
            return jsonify({"error": f"Invalid position value for {k}: {v}"}), 400
            
    if not isinstance(invest_date, str):
        return jsonify({"error": "invest_date must be a string YYYY-MM-DD"}), 400
    try:
        datetime.strptime(invest_date, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "invest_date must be in YYYY-MM-DD format"}), 400
        
    try:
        total_capital = float(total_capital)
    except (ValueError, TypeError):
        return jsonify({"error": "total_capital must be numeric"}), 400
        
    existing = {}
    if os.path.exists(PORTFOLIO_FILE):
        try:
            with open(str(PORTFOLIO_FILE), "r", encoding="utf-8") as f:
                existing = json.load(f)
        except:
            pass
            
    existing["positions"] = cleaned_positions
    existing["invest_date"] = invest_date
    existing["total_capital"] = total_capital
    existing["fetched_at"] = datetime.now().isoformat()
    
    try:
        with open(str(PORTFOLIO_FILE), "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
    except Exception as e:
        return jsonify({"error": f"Failed to save portfolio file: {str(e)}"}), 500
        
    return jsonify({"status": "success", "message": "Portfolio saved successfully"})

@app.route("/m")
@app.route("/my-portfolio")
@jwt_required()
def my_portfolio_gui():
    import portfolio_tracker
    p = load_portfolio_config()
    snaps = portfolio_tracker.load_snapshots_all()
    
    port_calc = portfolio_tracker.calc_my_portfolio(p.get("positions", {}), p.get("invest_date"), snaps)
    
    available_vaults = []
    latest_snap, _ = get_latest_snapshot()
    if latest_snap:
        for v in latest_snap:
            if "address" in v and "name" in v:
                available_vaults.append({
                    "address": v["address"],
                    "name": v["name"]
                })
    
    if not port_calc or not port_calc.get("holdings"):
        return render_template_string(MY_HTML, 
                                      holdings=[], 
                                      total=0, 
                                      capital=p.get("total_capital", 100000), 
                                      pnl=0, 
                                      pnl_pct=0, 
                                      net_pnl=0, 
                                      net_pct=0, 
                                      days=0,
                                      available_vaults=available_vaults,
                                      invest_date=p.get("invest_date", "2026-03-12"),
                                      total_capital=p.get("total_capital", 100000))
        
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
                                  days=port_calc["days_held"],
                                  hist_dates=port_calc.get("history_dates", []),
                                  hist_vals=port_calc.get("history_values", []),
                                  available_vaults=available_vaults,
                                  invest_date=p.get("invest_date", "2026-03-12"),
                                  total_capital=p.get("total_capital", 100000))


# ── HTML 템플릿 ───────────────────────────────────────────────────────────────

LOGIN_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HL Vault Analyzer - Login</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
        body { background: #0b0f1a; color: #e8eaf0; font-family: 'Inter', sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
        .login-card { background: #131928; padding: 40px; border-radius: 16px; border: 1px solid #243050; width: 100%; max-width: 400px; box-shadow: 0 8px 32px rgba(0,0,0,0.5); }
        h2 { margin: 0 0 10px 0; color: #fff; text-align: center; }
        p { color: #7b8db0; font-size: 0.85rem; text-align: center; margin-bottom: 30px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; font-size: 0.8rem; color: #7b8db0; margin-bottom: 8px; text-transform: uppercase; }
        input { width: 100%; padding: 12px; background: #0b0f1a; border: 1px solid #243050; border-radius: 8px; color: #fff; font-size: 0.95rem; box-sizing: border-box; }
        .btn { width: 100%; padding: 14px; background: #4f8ef7; border: none; border-radius: 8px; color: #fff; font-weight: bold; font-size: 1rem; cursor: pointer; transition: 0.2s; }
        .btn:hover { background: #3b7ce0; }
        .error { color: #e74c3c; font-size: 0.85rem; text-align: center; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="login-card">
        <h2>🔒 Vault Analyzer Pro</h2>
        <p>비인가자의 접근이 제한된 시스템입니다.</p>
        {% if error %}<div class="error">{{ error }}</div>{% endif %}
        <form method="POST" action="/login">
            <div class="form-group">
                <label>Email Address</label>
                <input type="email" name="email" required placeholder="admin@hyperliquid.com">
            </div>
            <div class="form-group">
                <label>Password</label>
                <input type="password" name="password" required placeholder="••••••••">
            </div>
            <button type="submit" class="btn">안전하게 로그인</button>
        </form>
    </div>
</body>
</html>"""

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

/* ── 📱 모바일 하단 플로팅 탭바 디자인 ── */
.mobile-tab-bar {
    display: none;
    position: fixed;
    bottom: 16px;
    left: 50%;
    transform: translateX(-50%);
    width: 92%;
    max-width: 480px;
    height: 64px;
    background: rgba(19, 25, 40, 0.85);
    backdrop-filter: blur(15px);
    -webkit-backdrop-filter: blur(15px);
    border: 1px solid rgba(36, 48, 80, 0.8);
    border-radius: 18px;
    box-shadow: 0 12px 36px rgba(0, 0, 0, 0.6);
    z-index: 9999;
    justify-content: space-around;
    align-items: center;
    padding: 0 8px;
}
.tab-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-decoration: none;
    color: var(--muted);
    font-size: 0.72rem;
    font-weight: 600;
    transition: all 0.2s ease;
    flex: 1;
    height: 100%;
}
.tab-item span.icon {
    font-size: 1.25rem;
    margin-bottom: 3px;
    transition: transform 0.2s ease;
}
.tab-item.active {
    color: var(--accent2);
}
.tab-item.active span.icon {
    transform: translateY(-3px);
}
.tab-item:hover {
    color: #fff;
}

/* ── 📱 모바일 극대화 반응형 레이아웃 ── */
@media (max-width: 768px) {
    body { padding-bottom: 95px !important; } /* 하단 탭바 여백 보장 */
    header { padding: 12px 16px; justify-content: center; text-align: center; }
    header h1 { font-size: 1.25rem !important; }
    
    /* 기존 PC용 버튼 목록 및 back 버튼은 가림 */
    header div:last-child { display: none !important; }
    .back-btn { display: none !important; }
    
    /* 모바일 탭바 활성화 */
    .mobile-tab-bar { display: flex; }
    
    main { padding: 12px; }
    .grid { grid-template-columns: 1fr !important; gap: 12px; }
    .card { padding: 16px; margin-bottom: 12px; border-radius: 12px; }
    
    /* 테이블 가로 스크롤 및 콤팩트 패치 */
    table { font-size: 0.78rem; display: block; overflow-x: auto; white-space: nowrap; -webkit-overflow-scrolling: touch; }
    th, td { padding: 8px 6px; }
    .modal-content { width: 96%; padding: 12px; }
    .stat-val { font-size: 1.35rem; }
    
    /* 성능 지표(그리드) 간격 조절 */
    .stat-box { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 12px !important; }
}
"""

EMPTY_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><style>""" + COMMON_STYLE + """</style></head>
<body style="display:flex;align-items:center;justify-content:center;height:100vh;">
<div style="text-align:center;"><h2>📊 데이터가 없습니다.</h2><p>먼저 분석기를 실행해주세요 (python analyze_top_vaults.py)</p></div>
</body></html>"""

MAIN_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Hyperliquid Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>""" + COMMON_STYLE + """</style></head>
<body><header><div><h1 style="background:linear-gradient(90deg, #4f8ef7, #1abc9c);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">HL Vault Analyzer Pro v3.1</h1></div><div>
<a class="btn" href="/m">📱 My Portfolio</a><a class="btn" href="/portfolio">🔬 Analysis</a><a class="btn" href="/discord">🔔 Discord</a><a class="btn" href="/logout" style="color:var(--danger);">🚪 Logout</a>
</div></header><main>
<div class="grid" style="grid-template-columns: repeat(4, 1fr);">
<div class="card stat-box"><div class="stat-label">Analysis Date</div><div class="stat-val" style="color:#fff">{{date}} <small style="font-size:0.8rem;color:var(--muted)">{% if stats.prev_date %}(vs {{stats.prev_date}}){% endif %}</small></div></div>
<div class="card stat-box"><div class="stat-label">Active Vaults</div><div class="stat-val">{{stats.total}}</div></div>
<div class="card stat-box"><div class="stat-label">Avg 30D APR</div><div class="stat-val" style="color:var(--success)">{{stats.avg_apr|round(1)}}%</div></div>
<div class="card stat-box"><div class="stat-label">Avg MDD</div><div class="stat-val" style="color:var(--danger)">{{stats.avg_mdd}}%</div></div>
</div>
<div class="card" style="margin-bottom:15px;">
    <div style="margin-bottom:15px; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
        <h3>Top Vaults (All 200) <span id="matchCount" style="color:var(--accent2); font-size:1rem; margin-left:10px; background:rgba(26,188,156,0.1); padding:4px 10px; border-radius:10px;"></span></h3>
        <div style="display:flex; align-items:center; gap:12px;">
            <span id="selCount" style="color:var(--accent); font-size:0.9rem; font-weight:600;">0/20 selected</span>
            <button id="btnAnalyzeSelected" onclick="goAnalyzeSelected()" class="btn btn-primary" style="margin:0; padding:10px 20px; opacity:0.5; pointer-events:none;" disabled>🔬 선택한 볼트로 분석</button>
        </div>
    </div>
    <div style="display:flex; gap:20px; align-items:center; flex-wrap:wrap; background:rgba(255,255,255,0.03); padding:15px; border-radius:12px; border:1px solid var(--border);">
        <div>
            <label style="font-size:0.8rem; color:var(--muted); margin-right:8px;">Leader Eq Min (%):</label>
            <input type="number" id="leaderFilter" oninput="filterTable()" placeholder="e.g. 10" style="padding:8px; width:100px; background:var(--bg); border:1px solid var(--border); color:#fff; border-radius:8px;">
        </div>
        <div>
            <label style="font-size:0.8rem; color:var(--muted); margin-right:8px;">Max MDD (%):</label>
            <input type="number" id="mddFilter" oninput="filterTable()" placeholder="e.g. 20" style="padding:8px; width:100px; background:var(--bg); border:1px solid var(--border); color:#fff; border-radius:8px;">
        </div>
        <div>
            <label style="font-size:0.8rem; color:var(--muted); margin-right:8px;">Min TVL ($):</label>
            <input type="number" id="tvlFilter" oninput="filterTable()" placeholder="e.g. 10000" style="padding:8px; width:120px; background:var(--bg); border:1px solid var(--border); color:#fff; border-radius:8px;">
        </div>
        <button onclick="selectAllVisible()" class="btn" style="margin:0; padding:8px 14px; font-size:0.8rem;">✅ 보이는 항목 전체선택</button>
        <button onclick="clearSelection()" class="btn" style="margin:0; padding:8px 14px; font-size:0.8rem;">❌ 선택 해제</button>
    </div>
</div>

<div class="card">
    <table id="vaultTable">
        <thead>
            <tr>
                <th style="width:40px; text-align:center;">✓</th>
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
                <th>AGE</th>
            </tr>
        </thead>
        <tbody>
        {% for v in vaults %}
        <tr data-leader="{{ v.leader_equity_ratio }}" data-deposit="{{ 'open' if v.allow_deposits else 'closed' }}" data-mdd="{{ v.max_drawdown }}" data-tvl="{{ v.tvl }}" data-address="{{v.address}}">
            <td style="text-align:center;"><input type="checkbox" class="vault-cb" data-address="{{v.address}}" onchange="updateSelectionCount()" style="width:18px;height:18px;cursor:pointer;accent-color:var(--accent2);"></td>
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
            <td style="text-align:center; color:var(--muted); font-weight:600;">{{ v.age_days }} D</td>
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
    let leaderMin = parseFloat(document.getElementById('leaderFilter').value);
    if(isNaN(leaderMin)) leaderMin = 0; else leaderMin = leaderMin / 100.0;
    
    let mddMax = parseFloat(document.getElementById('mddFilter').value);
    if(isNaN(mddMax)) mddMax = 999;
    
    let tvlMin = parseFloat(document.getElementById('tvlFilter').value);
    if(isNaN(tvlMin)) tvlMin = 0;
    
    const rows = document.querySelectorAll('#vaultTable tbody tr');
    let count = 0;
    
    rows.forEach(row => {
        const leader = parseFloat(row.getAttribute('data-leader'));
        const mdd = parseFloat(row.getAttribute('data-mdd'));
        const tvl = parseFloat(row.getAttribute('data-tvl'));
        
        const leaderMatch = leader >= leaderMin;
        const mddMatch = mdd <= mddMax;
        const tvlMatch = tvl >= tvlMin;
        
        if (leaderMatch && mddMatch && tvlMatch) {
            row.style.display = '';
            count++;
        } else {
            row.style.display = 'none';
            // 숨겨진 행 체크박스 해제
            const cb = row.querySelector('.vault-cb');
            if(cb) cb.checked = false;
        }
    });
    document.getElementById('matchCount').innerText = `${count} vaults matched`;
    updateSelectionCount();
}

function updateSelectionCount() {
    const checked = document.querySelectorAll('.vault-cb:checked');
    const count = checked.length;
    document.getElementById('selCount').innerText = `${count}/20 selected`;
    const btn = document.getElementById('btnAnalyzeSelected');
    if(count >= 2 && count <= 20) {
        btn.disabled = false;
        btn.style.opacity = '1';
        btn.style.pointerEvents = 'auto';
    } else {
        btn.disabled = true;
        btn.style.opacity = '0.5';
        btn.style.pointerEvents = 'none';
    }
    // 20개 초과 방지
    if(count > 20) {
        alert('최대 20개까지 선택 가능합니다.');
        // 마지막 체크한 것 해제
        const allCbs = document.querySelectorAll('.vault-cb:checked');
        allCbs[allCbs.length - 1].checked = false;
        updateSelectionCount();
    }
}

function selectAllVisible() {
    const rows = document.querySelectorAll('#vaultTable tbody tr');
    let selected = 0;
    // 먼저 모든 체크박스 해제
    document.querySelectorAll('.vault-cb').forEach(cb => cb.checked = false);
    rows.forEach(row => {
        if(row.style.display !== 'none' && selected < 20) {
            const cb = row.querySelector('.vault-cb');
            if(cb) { cb.checked = true; selected++; }
        }
    });
    updateSelectionCount();
}

function clearSelection() {
    document.querySelectorAll('.vault-cb').forEach(cb => cb.checked = false);
    updateSelectionCount();
}

function goAnalyzeSelected() {
    const checked = document.querySelectorAll('.vault-cb:checked');
    if(checked.length < 2) { alert('최소 2개 이상 선택해주세요.'); return; }
    const addresses = Array.from(checked).map(cb => cb.getAttribute('data-address'));
    window.location.href = '/portfolio?addresses=' + addresses.join(',');
}

document.addEventListener('DOMContentLoaded', filterTable);
</script>
<!-- ── 📱 모바일 하단 플로팅 탭바 마크업 ── -->
<div class="mobile-tab-bar">
    <a href="/m" id="tab-portfolio" class="tab-item"><span class="icon">📱</span><span>Portfolio</span></a>
    <a href="/" id="tab-analysis" class="tab-item"><span class="icon">🔬</span><span>Analysis</span></a>
    <a href="/discord" id="tab-discord" class="tab-item"><span class="icon">🔔</span><span>Discord</span></a>
    <a href="/logout" class="tab-item" style="color:var(--danger);"><span class="icon">🚪</span><span>Logout</span></a>
</div>
<script>
    (function() {
        const path = window.location.pathname;
        if(path==='/m'||path==='/my-portfolio') {
            document.getElementById('tab-portfolio').classList.add('active');
        } else if(path==='/discord') {
            document.getElementById('tab-discord').classList.add('active');
        } else if(path==='/'||path.includes('/portfolio')) {
            document.getElementById('tab-analysis').classList.add('active');
        }
    })();
</script>
</main></body></html>"""

PORTFOLIO_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><script src="https://cdn.jsdelivr.net/npm/chart.js"></script><style>""" + COMMON_STYLE + """</style></head><body>
<header><div><h1>🔬 Portfolio Analysis</h1></div><a class="btn back-btn" href="/">← Back</a></header>
<main>
{% if d.user_selected_mode %}
<div style="background:rgba(79,142,247,0.15); padding:15px 20px; border-radius:12px; margin-bottom:20px; border:1px solid var(--accent); display:flex; align-items:center; gap:15px;">
  <span style="font-size:1.5rem;">🎯</span>
  <div>
    <strong style="color:var(--accent);">사용자 선택 모드</strong>
    <span style="color:var(--muted); margin-left:10px;">메인 페이지에서 선택한 <b style="color:#fff;">{{d.user_selected_count}}개</b> 볼트만으로 분석하였습니다.</span>
  </div>
  <a href="/portfolio" class="btn" style="margin-left:auto; padding:8px 16px;">📊 전체 분석 보기</a>
</div>
{% endif %}
<div style="background:rgba(255,255,255,0.05); padding:20px; border-radius:12px; margin-bottom: 25px; border:1px solid var(--accent2); display:flex; align-items:center; gap:20px;">
  <div style="flex-grow:1;">
    <h3 style="margin:0; color:var(--accent2); display:flex; align-items:center; gap:10px;">
      💡 Custom Investment Simulation
    </h3>
    <p style="margin:5px 0 0 0; font-size:0.9rem; color:var(--muted);">Enter your desired investment amount to see exact allocations and profit projections based on our historical analysis.</p>
  </div>
  <div style="display:flex; flex-direction:column; align-items:flex-end; gap:6px;">
    <div style="position: relative; display: flex; align-items: center;">
      <span style="position: absolute; left: 15px; font-weight: bold; color: #fff;">$</span>
      <input type="text" id="simAmount" value="100,000" oninput="formatAmountInput(this); updateSimulation();" style="width: 200px; padding: 12px 12px 12px 30px; font-size: 1.2rem; font-weight: bold; background: #0b0f1a; border: 1px solid var(--border); color: #fff; border-radius: 8px; text-align: right;">
    </div>
    <span id="simAmountKRW" style="font-size:0.85rem; color:var(--accent2); font-weight:600;">≈ ₩140,000,000</span>
  </div>
</div>

{% if d.portfolio_summary %}
<div class="card"><h3>Historical Tracking (Trailing 90 Days Sim)</h3>
<div style="height:350px;"><canvas id="historyChart"></canvas></div>
<div class="grid" style="margin-top:20px;">
<div class="stat-box"><div class="stat-label">Cumulative Return</div><div class="stat-val" style="color:var(--success)">{{d.portfolio_summary.cumulative_pct}}%</div></div>
<div class="stat-box"><div class="stat-label">Max Drawdown</div><div class="stat-val" style="color:var(--danger)">{{d.portfolio_summary.max_mdd_pct}}%</div></div>
<div class="stat-box"><div class="stat-label">Sharpe Ratio</div><div class="stat-val" style="color:var(--accent)">{{d.portfolio_summary.sharpe_ratio}}</div></div>
</div></div>
{% endif %}

<div class="card" style="margin-bottom:25px; border-left:4px solid #f39c12">
  <h3>🎯 Custom Portfolio Builder</h3>
  <p style="margin:-10px 0 20px 0; font-size:0.9rem; color:var(--muted);">선택한 볼트와 비중으로 커스텀 포트폴리오를 구성하고 백테스트를 수행해보세요.</p>
  
  <div style="display:flex; gap:15px; margin-bottom:15px; align-items:center;">
    <select id="customVaultSelect" style="padding:10px; background:#0b0f1a; border:1px solid var(--border); color:#fff; border-radius:8px; flex:1;">
      {% for v in d.filter_details %}
        <option value="{{v.address}}">{{v.name}} (APR: {{v.apr_30d}}%, MDD: {{v.max_drawdown}}%)</option>
      {% endfor %}
    </select>
    <input type="number" id="customVaultWeight" placeholder="비중 (%)" style="padding:10px; width:100px; background:#0b0f1a; border:1px solid var(--border); color:#fff; border-radius:8px;">
    <button onclick="addCustomVault()" class="btn btn-primary" style="margin:0; padding:10px 20px;">+ 추가</button>
  </div>
  
  <div id="customVaultList" style="margin-bottom:20px; background:rgba(0,0,0,0.2); padding:15px; border-radius:8px; min-height:50px;">
    <!-- Selected vaults will appear here -->
  </div>
  
  <div style="display:flex; gap:15px; align-items:center; flex-wrap:wrap;">
    <select id="customSimDate" style="padding:10px; background:#0b0f1a; border:1px solid var(--border); color:#fff; border-radius:8px;">
      {% for dt in d.history_dates | reverse %}
        <option value="{{dt}}">투자 시작일: {{dt}}</option>
      {% endfor %}
    </select>
    <div style="display:flex; flex-direction:column; align-items:flex-end; gap:4px;">
      <div style="position: relative; display: flex; align-items: center;">
        <span style="position: absolute; left: 15px; font-weight: bold; color: #fff;">$</span>
        <input type="text" id="customSimAmount" value="100,000" oninput="formatAmountInput(this); updateCustomKRW();" style="width: 170px; padding: 10px 10px 10px 30px; font-size: 1rem; font-weight: bold; background: #0b0f1a; border: 1px solid var(--border); color: #fff; border-radius: 8px; text-align:right;">
      </div>
      <span id="customSimAmountKRW" style="font-size:0.8rem; color:var(--accent2);">≈ ₩140,000,000</span>
    </div>
    <button onclick="runCustomBacktest()" class="btn" style="background:#f39c12; color:#fff; border-color:#f39c12; margin:0; padding:10px 20px;">▶ 검증 및 시뮬레이션</button>
  </div>
  
  <div id="cbtResult" style="display:none; margin-top:30px; padding-top:20px; border-top:1px solid var(--border);">
    <div class="grid" style="margin-bottom:20px;">
      <div class="stat-box"><div class="stat-label">Simulated PnL</div><div class="stat-val" id="cbtPnl" style="color:var(--success)">-</div></div>
      <div class="stat-box"><div class="stat-label">Net ROI</div><div class="stat-val" id="cbtPct" style="color:var(--success)">-</div></div>
      <div class="stat-box"><div class="stat-label">Final Value</div><div class="stat-val" id="cbtVal" style="color:var(--accent)">-</div></div>
    </div>
    <div style="height:350px;"><canvas id="cbtChart"></canvas></div>
  </div>
</div>

<div class="card" style="margin-bottom:25px; border-left:4px solid var(--accent)">
  <h3>⏳ Time-Travel Simulator</h3>
  <p style="margin:-10px 0 20px 0; font-size:0.9rem; color:var(--muted);">Test the historical performance of any recommended strategy with your chosen starting date and investment amount.</p>
  <div style="display:flex; gap:15px; margin-bottom:20px; align-items:center;">
    <select id="simPtype" style="padding:10px; background:#0b0f1a; border:1px solid var(--border); color:#fff; border-radius:8px;">
      <option value="max_sharpe">Maximum Sharpe Strategy</option>
      <option value="min_variance">Minimum Variance Strategy</option>
      <option value="risk_parity">Risk Parity Strategy</option>
      <option value="min_cvar">CVaR (Capital Protection) Strategy</option>
    </select>
    <select id="simDate" style="padding:10px; background:#0b0f1a; border:1px solid var(--border); color:#fff; border-radius:8px;">
      {% for dt in d.history_dates | reverse %}
        <option value="{{dt}}">Invested on: {{dt}}</option>
      {% endfor %}
    </select>
    <button onclick="runBacktest()" class="btn btn-primary" style="margin:0; padding:10px 20px;">Run Simulation</button>
  </div>
  
  <div id="btResult" style="display:none; margin-top:30px; padding-top:20px; border-top:1px solid var(--border);">
    <div class="grid" style="margin-bottom:20px;">
      <div class="stat-box"><div class="stat-label">Simulated PnL</div><div class="stat-val" id="btPnl" style="color:var(--success)">-</div></div>
      <div class="stat-box"><div class="stat-label">Net ROI</div><div class="stat-val" id="btPct" style="color:var(--success)">-</div></div>
      <div class="stat-box"><div class="stat-label">Final Value</div><div class="stat-val" id="btVal" style="color:var(--accent)">-</div></div>
    </div>
    <div style="height:350px;"><canvas id="btChart"></canvas></div>
  </div>
</div>

<!-- ── 📊 선택된 볼트 상세 비교 ── -->
<div class="card" style="margin-bottom:25px;">
  <h2 style="margin-bottom:5px;">📊 분석 대상 볼트 비교</h2>
  <p style="color:var(--muted); font-size:0.9rem; margin-bottom:15px;">선택된 {{d.n_selected}}개 볼트의 핵심 지표를 비교합니다. 색상은 상대적 우위를 나타냅니다.</p>
  <div style="overflow-x:auto;">
  <table style="min-width:900px;">
    <thead><tr>
      <th>Vault</th>
      <th style="text-align:center;">30d APR</th>
      <th style="text-align:center;">Sharpe</th>
      <th style="text-align:center;">MDD</th>
      <th style="text-align:center;">Robustness</th>
      <th style="text-align:center;">TVL</th>
      <th style="text-align:center;">Score</th>
      <th style="text-align:center;">📈 Max Sharpe</th>
      <th style="text-align:center;">🛡️ Min Var</th>
      <th style="text-align:center;">⚖️ Risk Parity</th>
      <th style="text-align:center;">🔒 CVaR</th>
    </tr></thead>
    <tbody>
    {% for v in d.selected_vaults %}
    <tr>
      <td><a href="https://app.hyperliquid.xyz/vaults/{{v.address}}" target="_blank"><b>{{v.name[:25]}}</b></a></td>
      <td style="text-align:center; color:var(--success); font-weight:600;">{{v.apr_30d}}%</td>
      <td style="text-align:center; color:var(--accent);">{{v.sharpe_ratio}}</td>
      <td style="text-align:center; color:var(--danger);">{{v.max_drawdown}}%</td>
      <td style="text-align:center;"><span style="color:{{'var(--success)' if v.robustness_score >= 0.7 else 'var(--danger)' if v.robustness_score < 0.4 else '#f39c12'}}">{{v.robustness_score}}</span></td>
      <td style="text-align:center;">${{"{:,.0f}".format(v.tvl)}}</td>
      <td style="text-align:center; font-weight:800; color:var(--accent);">{{v.score}}</td>
      <td style="text-align:center;"><span style="background:{{'rgba(26,188,156,0.2)' if v.alloc_sh > 15 else 'rgba(255,255,255,0.03)'}}; padding:3px 8px; border-radius:6px; font-weight:{{'800' if v.alloc_sh > 15 else '400'}}; color:{{'var(--accent2)' if v.alloc_sh > 15 else 'var(--muted)'}};">{{v.alloc_sh}}%</span></td>
      <td style="text-align:center;"><span style="background:{{'rgba(26,188,156,0.2)' if v.alloc_mv > 15 else 'rgba(255,255,255,0.03)'}}; padding:3px 8px; border-radius:6px; font-weight:{{'800' if v.alloc_mv > 15 else '400'}}; color:{{'var(--accent2)' if v.alloc_mv > 15 else 'var(--muted)'}};">{{v.alloc_mv}}%</span></td>
      <td style="text-align:center;"><span style="background:{{'rgba(26,188,156,0.2)' if v.alloc_rp > 15 else 'rgba(255,255,255,0.03)'}}; padding:3px 8px; border-radius:6px; font-weight:{{'800' if v.alloc_rp > 15 else '400'}}; color:{{'var(--accent2)' if v.alloc_rp > 15 else 'var(--muted)'}};">{{v.alloc_rp}}%</span></td>
      <td style="text-align:center;"><span style="background:{{'rgba(26,188,156,0.2)' if v.alloc_cv > 15 else 'rgba(255,255,255,0.03)'}}; padding:3px 8px; border-radius:6px; font-weight:{{'800' if v.alloc_cv > 15 else '400'}}; color:{{'var(--accent2)' if v.alloc_cv > 15 else 'var(--muted)'}};">{{v.alloc_cv}}%</span></td>
    </tr>
    {% endfor %}
    </tbody>
  </table>
  </div>
</div>

<!-- ── 💡 전략 비교 설명 ── -->
<div class="card" style="margin-bottom:25px;">
  <h2 style="margin-bottom:5px;">💡 왜 이렇게 추천했는가?</h2>
  <p style="color:var(--muted); font-size:0.9rem; margin-bottom:20px;">4가지 전략은 각각 다른 투자 철학을 반영합니다. 본인의 성향에 맞는 전략을 선택하세요.</p>
  <div class="grid" style="grid-template-columns: repeat(2, 1fr);">
  {% for k, p in d.portfolios.items() %}
  <div class="card" style="margin-bottom:0; border-left:4px solid {{'var(--accent)' if k == 'max_sharpe' else 'var(--accent2)' if k == 'min_variance' else '#f39c12' if k == 'risk_parity' else '#e74c3c'}};">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
      <h4 style="color:var(--accent);">{{p.emoji}} {{p.label}}</h4>
      <span style="font-size:1.8rem; font-weight:800; color:var(--success);">{{p.stats.annual_return_pct}}%</span>
    </div>

    <!-- 전략 설명 -->
    <div style="background:rgba(255,255,255,0.03); padding:12px; border-radius:8px; margin-bottom:12px; font-size:0.85rem; line-height:1.6;">
    {% if k == 'max_sharpe' %}
      <p style="margin:0; color:var(--text);">📌 <b>핵심 원리:</b> 위험 대비 수익이 가장 높은 조합을 찾습니다.</p>
      <p style="margin:6px 0 0 0; color:var(--muted);">Sharpe가 높은 볼트에 집중 배분합니다. 수익률은 높지만 특정 볼트에 쏠릴 수 있어 하락 시 타격이 클 수 있습니다.</p>
    {% elif k == 'min_variance' %}
      <p style="margin:0; color:var(--text);">📌 <b>핵심 원리:</b> 포트폴리오 전체의 변동성을 최소화합니다.</p>
      <p style="margin:6px 0 0 0; color:var(--muted);">MDD가 낮고 변동성이 작은 볼트에 집중합니다. 수익률은 낮지만 안정적이며, 서로 반대로 움직이는 볼트끼리 조합해 변동을 상쇄합니다.</p>
    {% elif k == 'risk_parity' %}
      <p style="margin:0; color:var(--text);">📌 <b>핵심 원리:</b> 각 볼트가 포트폴리오 위험에 동일하게 기여하도록 배분합니다.</p>
      <p style="margin:6px 0 0 0; color:var(--muted);">변동성이 큰 볼트는 비중을 줄이고, 안정적인 볼트는 비중을 높입니다. 어떤 한 볼트가 전체 위험을 지배하지 않도록 균형을 맞춥니다.</p>
    {% elif k == 'min_cvar' %}
      <p style="margin:0; color:var(--text);">📌 <b>핵심 원리:</b> 최악의 손실 시나리오(하위 5%)를 최소화합니다.</p>
      <p style="margin:6px 0 0 0; color:var(--muted);">원금 보호를 최우선으로 합니다. 꼬리 위험(tail risk)이 적은 볼트를 선호하며, "최악의 날에도 얼마나 덜 잃을 수 있는가"에 집중합니다.</p>
    {% endif %}
    </div>

    <!-- 지표 비교 -->
    <div style="display:grid; grid-template-columns: repeat(4,1fr); gap:8px; text-align:center; margin-bottom:12px;">
      <div style="background:rgba(0,0,0,0.2); padding:8px; border-radius:6px;">
        <div style="font-size:0.7rem; color:var(--muted);">연 수익률</div>
        <div style="font-size:1.1rem; font-weight:800; color:var(--success);">{{p.stats.annual_return_pct}}%</div>
      </div>
      <div style="background:rgba(0,0,0,0.2); padding:8px; border-radius:6px;">
        <div style="font-size:0.7rem; color:var(--muted);">변동성</div>
        <div style="font-size:1.1rem; font-weight:800; color:#f39c12;">{{p.stats.annual_vol_pct}}%</div>
      </div>
      <div style="background:rgba(0,0,0,0.2); padding:8px; border-radius:6px;">
        <div style="font-size:0.7rem; color:var(--muted);">Sharpe</div>
        <div style="font-size:1.1rem; font-weight:800; color:var(--accent);">{{p.stats.sharpe}}</div>
      </div>
      <div style="background:rgba(0,0,0,0.2); padding:8px; border-radius:6px;">
        <div style="font-size:0.7rem; color:var(--muted);">Max MDD</div>
        <div style="font-size:1.1rem; font-weight:800; color:var(--danger);">{{p.backtest.max_drawdown_pct}}%</div>
      </div>
    </div>

    <!-- 비중 배분 -->
    <div style="background:rgba(255,255,255,0.03); padding:10px; border-radius:8px;">
    {% for vname, w in p.stats.weights.items() %}{% if w > 3 %}
    <div style="display:flex; justify-content:space-between; align-items:center; font-size:0.85rem; margin-bottom:4px; padding:4px 0; border-bottom:1px dashed rgba(255,255,255,0.05);">
      <span style="font-weight:600; max-width:55%; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{{vname[:30]}}</span>
      <div style="display:flex; align-items:center; gap:10px;">
        <div style="width:80px; height:6px; background:rgba(255,255,255,0.1); border-radius:3px; overflow:hidden;">
          <div style="width:{{w * 2.86}}%; height:100%; background:var(--accent2); border-radius:3px;"></div>
        </div>
        <span style="color:var(--accent2); font-weight:800; min-width:40px; text-align:right;">{{w}}%</span>
        <span class="alloc-dollar" data-weight="{{w}}" style="color:#fff; min-width:60px; text-align:right;">$0</span>
      </div>
    </div>
    {% endif %}{% endfor %}
    </div>
  </div>
  {% endfor %}
  </div>
</div>

<!-- ── 🔗 상관관계 인사이트 ── -->
{% if d.corr_selected %}
<div class="card" style="margin-bottom:25px;">
  <h2 style="margin-bottom:5px;">🔗 상관관계 분석</h2>
  <p style="color:var(--muted); font-size:0.9rem; margin-bottom:15px;">볼트 간 상관관계가 낮을수록 분산 효과가 큽니다. 빨간색은 같이 움직이는 볼트, 파란색은 반대로 움직이는 볼트입니다.</p>
  <div style="overflow-x:auto;">
  <table style="min-width:600px; font-size:0.75rem;">
    <thead><tr><th></th>
    {% for n in d.corr_selected.names %}<th style="text-align:center; max-width:80px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font-size:0.65rem;" title="{{n}}">{{n[:12]}}</th>{% endfor %}
    </tr></thead>
    <tbody>
    {% for i in range(d.corr_selected.names | length) %}
    <tr>
      <td style="font-weight:600; max-width:80px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font-size:0.7rem;" title="{{d.corr_selected.names[i]}}">{{d.corr_selected.names[i][:12]}}</td>
      {% for j in range(d.corr_selected.names | length) %}
      {% set val = d.corr_selected.matrix[i][j] %}
      <td style="text-align:center; padding:6px; background:{{'rgba(231,76,60,' ~ (val * 0.4) ~ ')' if val > 0.3 else 'rgba(79,142,247,' ~ ((-val) * 0.5) ~ ')' if val < -0.1 else 'rgba(255,255,255,0.02)'}}; font-weight:{{'700' if val|abs > 0.5 else '400'}}; color:{{'var(--danger)' if val > 0.5 else 'var(--accent)' if val < -0.1 else 'var(--muted)'}}; font-size:0.75rem;">
        {% if i == j %}<span style="color:var(--muted);">-</span>{% else %}{{val}}{% endif %}
      </td>
      {% endfor %}
    </tr>
    {% endfor %}
    </tbody>
  </table>
  </div>

  <!-- 상관관계 해석 -->
  <div style="margin-top:15px; background:rgba(255,255,255,0.03); padding:15px; border-radius:8px; font-size:0.85rem; line-height:1.7;">
    <p style="margin:0; color:var(--text);"><b>📖 읽는 법:</b></p>
    <ul style="margin:5px 0 0 0; padding-left:20px; color:var(--muted);">
      <li><span style="color:var(--danger);">빨간 숫자 (0.5 이상)</span> = 두 볼트가 같이 오르고 같이 내림 → 분산 효과 ❌</li>
      <li><span style="color:var(--accent);">파란 숫자 (음수)</span> = 반대로 움직임 → 분산 효과 ✅ (이상적)</li>
      <li><span style="color:var(--muted);">회색 숫자 (0 근처)</span> = 독립적 움직임 → 분산 효과 ✅</li>
    </ul>
    <p style="margin:10px 0 0 0; color:var(--accent2);"><b>💡 포인트:</b> 상관관계 0.5 이상인 볼트 조합은 동시에 투자 시 위험이 겹칩니다. 시스템은 상관 {{d.corr_selected.matrix[0][1] if d.corr_selected.names|length > 1 else 0}} 이하의 저상관 조합을 우선 선택했습니다.</p>
  </div>
</div>
{% endif %}

<!-- ── 📝 종합 분석 가이드 ── -->
<div class="card" style="margin-bottom:25px; border-left:4px solid var(--accent2);">
  <h2 style="margin-bottom:5px;">📝 투자 전략 가이드</h2>
  <div style="font-size:0.9rem; line-height:1.8; color:var(--muted);">
    <div style="display:grid; grid-template-columns: 1fr 1fr; gap:15px; margin-top:10px;">
      <div style="background:rgba(46,204,113,0.05); padding:15px; border-radius:10px; border:1px solid rgba(46,204,113,0.2);">
        <p style="margin:0; color:var(--success); font-weight:600;">✅ 공격적 투자자 (수익 우선)</p>
        <p style="margin:8px 0 0 0;">→ <b>최대 샤프 📈</b> 전략 추천<br>
        높은 Sharpe 볼트에 집중, 수익률 극대화.<br>
        <span style="color:var(--danger);">⚠️ MDD {{d.portfolios.max_sharpe.backtest.max_drawdown_pct}}% 감수 필요</span></p>
      </div>
      <div style="background:rgba(26,188,156,0.05); padding:15px; border-radius:10px; border:1px solid rgba(26,188,156,0.2);">
        <p style="margin:0; color:var(--accent2); font-weight:600;">🛡️ 안정형 투자자 (원금 보호)</p>
        <p style="margin:8px 0 0 0;">→ <b>원금보호 CVaR 🔒</b> 또는 <b>최소분산 🛡️</b> 추천<br>
        최악의 시나리오를 최소화, 변동성 억제.<br>
        <span style="color:var(--success);">MDD {{d.portfolios.min_cvar.backtest.max_drawdown_pct}}%로 제한</span></p>
      </div>
      <div style="background:rgba(243,156,18,0.05); padding:15px; border-radius:10px; border:1px solid rgba(243,156,18,0.2);">
        <p style="margin:0; color:#f39c12; font-weight:600;">⚖️ 균형형 투자자</p>
        <p style="margin:8px 0 0 0;">→ <b>위험 균형 ⚖️</b> 전략 추천<br>
        모든 볼트가 위험에 균등 기여, 특정 볼트 의존도 낮음.<br>
        수익과 안정의 중간 지점.</p>
      </div>
      <div style="background:rgba(79,142,247,0.05); padding:15px; border-radius:10px; border:1px solid rgba(79,142,247,0.2);">
        <p style="margin:0; color:var(--accent); font-weight:600;">🧠 분석 기간</p>
        <p style="margin:8px 0 0 0;">본 분석은 <b>최근 {{d.analysis_days}}일</b> 데이터를 기반으로 합니다.<br>
        {{d.n_selected}}개 볼트가 저상관 기준으로 최종 선택되었으며,<br>
        전체 {{d.n_filtered}}개 필터 통과 중 선별되었습니다.</p>
      </div>
    </div>
  </div>
</div>

</main>
<script>
{% if d.portfolio_summary %}
const ctx = document.getElementById('historyChart').getContext('2d');
const dates = {{ d.portfolio_summary.value_series | map(attribute=0) | list | tojson }};
const baseValues = {{ d.portfolio_summary.value_series | map(attribute=1) | list | tojson }};
const BASE_CAPITAL = 100000; // Simulated originally at 100k

let chartInstance = new Chart(ctx, {
  type: 'line',
  data: {
    labels: dates,
    datasets: [{
      label: 'Portfolio Value ($)',
      data: baseValues,
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
      x: { grid: { display: false }, ticks: { color: '#7b8db0', maxRotation: 0, font: {size: 10} } },
      y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#7b8db0', callback: function(value){ return '$' + value.toLocaleString(); } } }
    }
  }
});

const KRW_RATE = 1400;

function parseAmountValue(el) {
  return parseFloat(el.value.replace(/,/g, '')) || 0;
}

function formatAmountInput(el) {
  const cursor = el.selectionStart;
  const oldLen = el.value.length;
  const raw = el.value.replace(/[^0-9]/g, '');
  const num = parseInt(raw) || 0;
  el.value = num.toLocaleString();
  const newLen = el.value.length;
  const newCursor = cursor + (newLen - oldLen);
  el.setSelectionRange(newCursor, newCursor);
}

function updateKRWDisplay(inputId, krwId) {
  const val = parseAmountValue(document.getElementById(inputId));
  const krw = val * KRW_RATE;
  document.getElementById(krwId).innerText = '≈ ₩' + Math.round(krw).toLocaleString();
}

function updateCustomKRW() {
  updateKRWDisplay('customSimAmount', 'customSimAmountKRW');
}

function updateSimulation() {
  let simAmount = parseAmountValue(document.getElementById('simAmount'));
  if(simAmount <= 0) simAmount = BASE_CAPITAL;
  
  // Update KRW
  updateKRWDisplay('simAmount', 'simAmountKRW');
  
  // Update Chart
  const ratio = simAmount / BASE_CAPITAL;
  const newValues = baseValues.map(v => v * ratio);
  chartInstance.data.datasets[0].data = newValues;
  chartInstance.update();

  // Update Allocation Dollars
  document.querySelectorAll('.alloc-dollar').forEach(el => {
    const weight = parseFloat(el.getAttribute('data-weight')) || 0;
    const alloc = (simAmount * weight / 100).toFixed(0);
    el.innerText = `\$${parseInt(alloc).toLocaleString()}`;
  });
}
updateSimulation(); // init bounds
{% endif %}

let customVaults = [];
let cbtChartInstance = null;

function addCustomVault() {
  const sel = document.getElementById('customVaultSelect');
  const address = sel.value;
  const name = sel.options[sel.selectedIndex].text.split(' (')[0];
  const weight = parseFloat(document.getElementById('customVaultWeight').value);
  
  if(!weight || weight <= 0) { alert('정확한 비중(%)을 입력하세요.'); return; }
  
  customVaults.push({ address, name, weight });
  renderCustomVaultList();
  document.getElementById('customVaultWeight').value = '';
}

function removeCustomVault(idx) {
  customVaults.splice(idx, 1);
  renderCustomVaultList();
}

function renderCustomVaultList() {
  const container = document.getElementById('customVaultList');
  if(customVaults.length === 0) { container.innerHTML = '<span style="color:var(--muted)">추가된 볼트가 없습니다. Total: 0%</span>'; return; }
  
  let html = '';
  let sum = 0;
  customVaults.forEach((v, i) => {
    sum += v.weight;
    html += `<div style="display:flex; justify-content:space-between; padding:5px 0; border-bottom:1px dashed var(--border);">
      <span>${v.name} <small style="color:var(--muted)">- ${v.address.substring(0,8)}...</small></span>
      <span>
        <strong style="color:var(--accent2); margin-right:15px">${v.weight}%</strong>
        <button onclick="removeCustomVault(${i})" style="background:none; border:none; color:var(--danger); cursor:pointer;">❌</button>
      </span>
    </div>`;
  });
  html += `<div style="text-align:right; margin-top:10px; font-weight:bold; color:${Math.abs(sum-100)<0.1?'var(--success)':'var(--danger)'}">총 비중: ${sum}%</div>`;
  container.innerHTML = html;
}
renderCustomVaultList();

function runCustomBacktest() {
  if(customVaults.length === 0) { alert('최소 하나의 볼트를 추가하세요.'); return; }
  const total = customVaults.reduce((a, b) => a + b.weight, 0);
  if(Math.abs(total - 100) > 0.1) { alert('총 비중은 100%가 되어야 합니다. 현재: ' + total + '%'); return; }
  
  const start_date = document.getElementById('customSimDate').value;
  const amount = parseAmountValue(document.getElementById('customSimAmount')) || 100000;
  
  const btn = document.querySelector('button[onclick="runCustomBacktest()"]');
  btn.innerText = "Simulating...";
  
  fetch('/api/simulate', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ custom_vaults: customVaults, start_date, amount })
  })
  .then(r => r.json())
  .then(res => {
    btn.innerText = "▶ 검증 및 시뮬레이션";
    if(res.error) { alert(res.error); return; }
    
    document.getElementById('cbtResult').style.display = 'block';
    
    const pnl = res.total_pnl;
    document.getElementById('cbtPnl').innerHTML = (pnl >= 0 ? '+' : '') + '$' + pnl.toLocaleString();
    document.getElementById('cbtPnl').style.color = pnl >= 0 ? 'var(--success)' : 'var(--danger)';
    
    document.getElementById('cbtPct').innerText = (pnl >= 0 ? '+' : '') + res.total_pnl_pct + '%';
    document.getElementById('cbtPct').style.color = pnl >= 0 ? 'var(--success)' : 'var(--danger)';
    
    document.getElementById('cbtVal').innerText = '$' + res.total_value.toLocaleString();
    
    const ctx = document.getElementById('cbtChart').getContext('2d');
    if(cbtChartInstance) cbtChartInstance.destroy();
    cbtChartInstance = new Chart(ctx, {
      type: 'line',
      data: {
        labels: res.history_dates,
        datasets: [{
          label: 'Custom Portfolio Value ($)',
          data: res.history_values,
          borderColor: '#f39c12',
          backgroundColor: 'rgba(243, 156, 18, 0.15)',
          fill: true, tension: 0.3, borderWidth: 3, pointRadius: 0
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { 
          x: { display: false }, 
          y: { grid: { color: 'rgba(255,255,255,0.05)'}, ticks:{color:'#7b8db0', callback: function(value){ return '$' + value.toLocaleString(); } }}
        }
      }
    });
  })
  .catch(err => {
    btn.innerText = "▶ 검증 및 시뮬레이션";
    alert("시뮬레이션 통신 실패.");
  });
}

let btChartInstance = null;
function runBacktest() {
  const ptype = document.getElementById('simPtype').value;
  const start_date = document.getElementById('simDate').value;
  const amount = parseAmountValue(document.getElementById('simAmount')) || 100000;
  
  const btn = document.querySelector('button[onclick="runBacktest()"]');
  btn.innerText = "Simulating...";
  
  fetch('/api/simulate', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ptype, start_date, amount})
  })
  .then(r => r.json())
  .then(res => {
    btn.innerText = "Run Simulation";
    if(res.error) { alert(res.error); return; }
    
    document.getElementById('btResult').style.display = 'block';
    
    const pnl = res.total_pnl;
    document.getElementById('btPnl').innerHTML = (pnl >= 0 ? '+' : '') + '$' + pnl.toLocaleString();
    document.getElementById('btPnl').style.color = pnl >= 0 ? 'var(--success)' : 'var(--danger)';
    
    document.getElementById('btPct').innerText = (pnl >= 0 ? '+' : '') + res.total_pnl_pct + '%';
    document.getElementById('btPct').style.color = pnl >= 0 ? 'var(--success)' : 'var(--danger)';
    
    document.getElementById('btVal').innerText = '$' + res.total_value.toLocaleString();
    
    const ctx = document.getElementById('btChart').getContext('2d');
    if(btChartInstance) btChartInstance.destroy();
    btChartInstance = new Chart(ctx, {
      type: 'line',
      data: {
        labels: res.history_dates,
        datasets: [{
          label: 'Simulated Value ($)',
          data: res.history_values,
          borderColor: '#4f8ef7',
          backgroundColor: 'rgba(79, 142, 247, 0.15)',
          fill: true, tension: 0.3, borderWidth: 3, pointRadius: 0
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { 
          x: { display: false }, 
          y: { grid: { color: 'rgba(255,255,255,0.05)'}, ticks:{color:'#7b8db0', callback: function(value){ return '$' + value.toLocaleString(); } }}
        }
      }
    });
  })
  .catch(err => {
    btn.innerText = "Run Simulation";
    alert("Simulation failed.");
  });
}
</script>
<!-- ── 📱 모바일 하단 플로팅 탭바 마크업 ── -->
<div class="mobile-tab-bar">
    <a href="/m" id="tab-portfolio" class="tab-item"><span class="icon">📱</span><span>Portfolio</span></a>
    <a href="/" id="tab-analysis" class="tab-item"><span class="icon">🔬</span><span>Analysis</span></a>
    <a href="/discord" id="tab-discord" class="tab-item"><span class="icon">🔔</span><span>Discord</span></a>
    <a href="/logout" class="tab-item" style="color:var(--danger);"><span class="icon">🚪</span><span>Logout</span></a>
</div>
<script>
    (function() {
        const path = window.location.pathname;
        if(path==='/m'||path==='/my-portfolio') {
            document.getElementById('tab-portfolio').classList.add('active');
        } else if(path==='/discord') {
            document.getElementById('tab-discord').classList.add('active');
        } else if(path==='/'||path.includes('/portfolio')) {
            document.getElementById('tab-analysis').classList.add('active');
        }
    })();
</script>
</body></html>"""

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

DISCORD_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><style>""" + COMMON_STYLE + """</style></head><body>
<header><h1>🔔 Discord Notifications</h1><a class="btn back-btn" href="/">← Back</a></header>
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
</script>
<!-- ── 📱 모바일 하단 플로팅 탭바 마크업 ── -->
<div class="mobile-tab-bar">
    <a href="/m" id="tab-portfolio" class="tab-item"><span class="icon">📱</span><span>Portfolio</span></a>
    <a href="/" id="tab-analysis" class="tab-item"><span class="icon">🔬</span><span>Analysis</span></a>
    <a href="/discord" id="tab-discord" class="tab-item"><span class="icon">🔔</span><span>Discord</span></a>
    <a href="/logout" class="tab-item" style="color:var(--danger);"><span class="icon">🚪</span><span>Logout</span></a>
</div>
<script>
    (function() {
        const path = window.location.pathname;
        if(path==='/m'||path==='/my-portfolio') {
            document.getElementById('tab-portfolio').classList.add('active');
        } else if(path==='/discord') {
            document.getElementById('tab-discord').classList.add('active');
        } else if(path==='/'||path.includes('/portfolio')) {
            document.getElementById('tab-analysis').classList.add('active');
        }
    })();
</script>
</body></html>"""

MY_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><script src="https://cdn.jsdelivr.net/npm/chart.js"></script><style>""" + COMMON_STYLE + """
#toast {
    visibility: hidden;
    min-width: 250px;
    background-color: var(--accent2);
    color: #fff;
    text-align: center;
    border-radius: 8px;
    padding: 16px;
    position: fixed;
    z-index: 10000;
    left: 50%;
    bottom: 30px;
    transform: translateX(-50%);
    font-weight: bold;
    box-shadow: 0 4px 12px rgba(0,0,0,0.5);
}
#toast.show {
    visibility: visible;
    -webkit-animation: fadein 0.5s, fadeout 0.5s 2.5s;
    animation: fadein 0.5s, fadeout 0.5s 2.5s;
}
@-webkit-keyframes fadein {
    from {bottom: 0; opacity: 0;} 
    to {bottom: 30px; opacity: 1;}
}
@keyframes fadein {
    from {bottom: 0; opacity: 0;}
    to {bottom: 30px; opacity: 1;}
}
@-webkit-keyframes fadeout {
    from {bottom: 30px; opacity: 1;} 
    to {bottom: 0; opacity: 0;}
}
@keyframes fadeout {
    from {bottom: 30px; opacity: 1;}
    to {bottom: 0; opacity: 0;}
}
</style></head><body>
<header><h1>📱 My Portfolio</h1><div><button class="btn btn-primary" onclick="openEditModal()">✏️ Edit Portfolio</button><a class="btn back-btn" href="/">← Back</a></div></header>
<main>
<div style="display: flex; flex-direction: column; gap: 20px;">
<div class="card"><h3>Performance Summary</h3>
<div style="height:250px; margin-bottom:20px; border-bottom:1px solid var(--border); padding-bottom:15px;"><canvas id="histChart"></canvas></div>
<div class="grid" style="grid-template-columns: repeat(3, 1fr); text-align: center; gap: 15px;">
  <div style="padding:15px; background:rgba(255,255,255,0.02); border-radius:10px;">
    <div class="stat-label">Total Invested (Holding Period)</div>
    <div class="stat-val" style="color:#fff; font-size:1.6rem;">$ {{ "{:,.0f}".format(capital) }} <small style="font-size:0.9rem; color:var(--muted); font-weight:400;">({{ days }} Days)</small></div>
  </div>
  <div style="padding:15px; background:rgba(255,255,255,0.02); border-radius:10px;">
    <div class="stat-label">Gross PnL (Before Fees)</div>
    <div class="stat-val" style="color:{{ 'var(--success)' if pnl >= 0 else 'var(--danger)' }}; font-size:1.6rem;">$ {{ "{:,.0f}".format(pnl) }}</div>
    <div style="font-size:0.9rem; margin-top:5px; color:{{ 'var(--success)' if pnl >= 0 else 'var(--danger)' }};">{{ pnl_pct }}%</div>
  </div>
  <div style="padding:15px; background:rgba(255,255,255,0.02); border-radius:10px; border: 1px solid var(--accent2);">
    <div class="stat-label" style="color:var(--accent2);">Net Return / Final Payout</div>
    <div class="stat-val" style="color:{{ 'var(--success)' if net_pnl >= 0 else 'var(--danger)' }}; font-size:2rem;">$ {{ "{:,.0f}".format(capital + net_pnl) }}</div>
    <div style="font-size:1rem; font-weight:600; margin-top:5px; color:{{ 'var(--success)' if net_pnl >= 0 else 'var(--danger)' }};">Net PnL: $ {{ "{:,.0f}".format(net_pnl) }} ({{ net_pct }}%)</div>
  </div>
</div>
</div>
<div class="card"><h3>Current Positions</h3>
{% if holdings %}
<table><thead><tr><th>Vault</th><th>Invested / Weight</th><th>Holding Period</th><th>APR / MDD</th><th>Gross PnL</th><th>Net Final Payout<br><small>(After 10% Fee)</small></th></tr></thead><tbody>
{% for h in holdings %}
{% set h_net_pnl = h.pnl * 0.9 if h.pnl > 0 else h.pnl %}
{% set h_net_pct = h_net_pnl / h.invested_usd * 100 if h.invested_usd > 0 else 0 %}
{% set h_final_val = h.invested_usd + h_net_pnl %}
<tr>
<td><a href="https://app.hyperliquid.xyz/vaults/{{h.address}}" target="_blank"><b>{{h.name}}</b></a><br><small style="color:var(--muted)">{{h.address[:12]}}...</small></td>
<td>${{ "{:,.0f}".format(h.invested_usd) }}<br><small style="color:var(--accent2)">{{ h.weight_pct }}%</small></td>
<td>{{ h.days_held }} Days</td>
<td><span style="color:var(--success)">{{ h.apr_30d }}%</span><br><small style="color:var(--danger)">{{ h.mdd }}%</small></td>
<td><span style="color:{{ 'var(--success)' if h.pnl >= 0 else 'var(--danger)' }}; font-weight:600;">${{ "{:,.0f}".format(h.pnl) }}</span><br><small style="color:{{ 'var(--success)' if h.pnl_pct >= 0 else 'var(--danger)' }}">{{ h.pnl_pct }}%</small></td>
<td style="font-weight:600; color:#fff;">${{ "{:,.0f}".format(h_final_val) }}<br><small style="color:{{ 'var(--success)' if h_net_pct >= 0 else 'var(--danger)' }}">{{ h_net_pct | round(2) }}%</small></td>
</tr>{% endfor %}
</tbody></table>
{% else %}
<p style="padding:40px;text-align:center;color:var(--muted);">No positions found. Update <code>my_portfolio.json</code> to track your holdings.</p>
{% endif %}
</div>
</div></main>

<div id="toast"></div>

<!-- Edit Portfolio Modal -->
<div id="editModal" class="modal" onclick="if(event.target === this) closeEditModal()">
    <div class="modal-content" style="max-width: 500px;">
        <span class="modal-close" onclick="closeEditModal()">×</span>
        <h2 style="color:var(--accent2); margin-bottom:15px;">✏️ Edit Portfolio</h2>
        
        <div style="margin-bottom:12px;">
            <label style="display:block; font-size:0.8rem; color:var(--muted); margin-bottom:4px;">Total Capital (USD)</label>
            <input type="number" id="editTotalCapital" value="{{ total_capital }}" style="width:100%; padding:10px; background:#0b0f1a; border:1px solid var(--border); color:#fff; border-radius:8px;">
        </div>
        <div style="margin-bottom:12px;">
            <label style="display:block; font-size:0.8rem; color:var(--muted); margin-bottom:4px;">Investment Start Date</label>
            <input type="date" id="editInvestDate" value="{{ invest_date }}" style="width:100%; padding:10px; background:#0b0f1a; border:1px solid var(--border); color:#fff; border-radius:8px;">
        </div>
        
        <h3 style="margin-top:16px; margin-bottom:8px; font-size:0.95rem; border-bottom:1px solid var(--border); padding-bottom:4px;">Current Positions</h3>
        <div id="editPositionsList" style="margin-bottom:16px; max-height: 150px; overflow-y: auto; background:rgba(0,0,0,0.2); padding:10px; border-radius:8px;">
        </div>
        
        <h3 style="margin-top:16px; margin-bottom:8px; font-size:0.95rem; border-bottom:1px solid var(--border); padding-bottom:4px;">➕ Add Position</h3>
        <div style="background:rgba(255,255,255,0.02); padding:10px; border-radius:8px; display:flex; flex-direction:column; gap:8px; margin-bottom:16px;">
            <div>
                <label style="display:block; font-size:0.75rem; color:var(--muted); margin-bottom:2px;">Select Vault</label>
                <select id="editAddVaultSelect" onchange="onVaultSelectChange()" style="width:100%; padding:8px; background:#0b0f1a; border:1px solid var(--border); color:#fff; border-radius:8px;">
                    <option value="">-- Choose Vault --</option>
                    {% for av in available_vaults %}
                    <option value="{{ av.address }}">{{ av.name }}</option>
                    {% endfor %}
                    <option value="custom">-- Custom Address --</option>
                </select>
            </div>
            
            <div id="customVaultAddressContainer" style="display:none;">
                <label style="display:block; font-size:0.75rem; color:var(--muted); margin-bottom:2px;">Custom Vault Address</label>
                <input type="text" id="editCustomVaultAddress" placeholder="0x..." style="width:100%; padding:8px; background:#0b0f1a; border:1px solid var(--border); color:#fff; border-radius:8px;">
            </div>
            
            <div>
                <label style="display:block; font-size:0.75rem; color:var(--muted); margin-bottom:2px;">Invested Amount (USD)</label>
                <input type="number" id="editAddAmount" placeholder="e.g. 5000" style="width:100%; padding:8px; background:#0b0f1a; border:1px solid var(--border); color:#fff; border-radius:8px;">
            </div>
            
            <button onclick="addPositionToEditList()" class="btn btn-primary" style="margin:0; padding:8px; width:100%;">Add Position</button>
        </div>
        
        <button onclick="savePortfolioChanges()" class="btn btn-primary" style="margin:0; padding:10px; width:100%; background:var(--accent2); border-color:var(--accent2); font-weight:bold; font-size:0.95rem;">Save Changes</button>
    </div>
</div>

<script>
{% if hist_dates and hist_vals %}
const ctx = document.getElementById('histChart').getContext('2d');
new Chart(ctx, {
    type: 'line',
    data: {
        labels: {{ hist_dates | tojson }},
        datasets: [{
            label: 'Est. Portfolio Value ($)',
            data: {{ hist_vals | tojson }},
            borderColor: '#1abc9c',
            backgroundColor: 'rgba(26, 188, 156, 0.1)',
            fill: true,
            tension: 0.3,
            borderWidth: 2,
            pointRadius: 2
        }]
    },
    options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
            x: { display: false },
            y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: 'var(--muted)', font: { size: 9 } } }
        }
    }
});
{% endif %}

// Portfolio Edit Logic
let editPositions = {
    {% for h in holdings %}
    "{{ h.address }}": {{ h.invested_usd }}{% if not loop.last %},{% endif %}
    {% endfor %}
};

const vaultNames = {
    {% for av in available_vaults %}
    "{{ av.address }}": "{{ av.name }}",
    {% endfor %}
    {% for h in holdings %}
    "{{ h.address }}": "{{ h.name }}"{% if not loop.last %},{% endif %}
    {% endfor %}
};

function openEditModal() {
    document.getElementById('editModal').style.display = 'flex';
    renderEditPositions();
}

function closeEditModal() {
    document.getElementById('editModal').style.display = 'none';
}

function renderEditPositions() {
    const container = document.getElementById('editPositionsList');
    const keys = Object.keys(editPositions);
    if (keys.length === 0) {
        container.innerHTML = '<span style="color:var(--muted)">No positions in portfolio.</span>';
        return;
    }
    
    let html = '';
    keys.forEach(addr => {
        const amt = editPositions[addr];
        const name = vaultNames[addr] || (addr.substring(0, 10) + '...');
        html += `<div style="display:flex; justify-content:space-between; align-items:center; padding:6px 0; border-bottom:1px dashed var(--border);">
            <div style="flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; padding-right:10px;">
                <b>${name}</b><br>
                <small style="color:var(--muted); font-size:0.75rem;">${addr.substring(0, 12)}...</small>
            </div>
            <div style="display:flex; align-items:center; gap:8px;">
                <span style="font-weight:600; font-size:0.85rem;">$${amt.toLocaleString()}</span>
                <button onclick="deletePositionFromEditList('${addr}')" style="background:none; border:none; color:var(--danger); cursor:pointer; font-size:1rem; padding: 2px;">❌</button>
            </div>
        </div>`;
    });
    container.innerHTML = html;
}

function deletePositionFromEditList(addr) {
    delete editPositions[addr];
    renderEditPositions();
}

function onVaultSelectChange() {
    const sel = document.getElementById('editAddVaultSelect');
    const customContainer = document.getElementById('customVaultAddressContainer');
    if (sel.value === 'custom') {
        customContainer.style.display = 'block';
    } else {
        customContainer.style.display = 'none';
    }
}

function addPositionToEditList() {
    const sel = document.getElementById('editAddVaultSelect');
    let address = sel.value;
    const amountVal = parseFloat(document.getElementById('editAddAmount').value);
    
    if (address === 'custom') {
        address = document.getElementById('editCustomVaultAddress').value.trim().toLowerCase();
        if (!address.startsWith('0x') || address.length < 40) {
            alert('올바른 볼트 주소(0x...)를 입력해주세요.');
            return;
        }
    }
    
    if (!address) {
        alert('볼트를 선택하거나 주소를 입력해주세요.');
        return;
    }
    
    if (isNaN(amountVal) || amountVal <= 0) {
        alert('올바른 투자 금액을 입력해주세요.');
        return;
    }
    
    const opt = sel.options[sel.selectedIndex];
    if (sel.value !== 'custom' && opt) {
        vaultNames[address] = opt.text;
    } else if (!vaultNames[address]) {
        vaultNames[address] = address;
    }
    
    editPositions[address] = amountVal;
    renderEditPositions();
    
    document.getElementById('editAddAmount').value = '';
    document.getElementById('editCustomVaultAddress').value = '';
    sel.value = '';
    onVaultSelectChange();
}

function savePortfolioChanges() {
    const total_capital = parseFloat(document.getElementById('editTotalCapital').value);
    const invest_date = document.getElementById('editInvestDate').value;
    
    if (isNaN(total_capital) || total_capital <= 0) {
        alert('올바른 Total Capital을 입력해주세요.');
        return;
    }
    
    if (!invest_date) {
        alert('투자 시작일을 입력해주세요.');
        return;
    }
    
    const payload = {
        positions: editPositions,
        invest_date: invest_date,
        total_capital: total_capital
    };
    
    const saveBtn = document.querySelector('button[onclick="savePortfolioChanges()"]');
    const oldText = saveBtn.innerText;
    saveBtn.innerText = 'Saving...';
    saveBtn.disabled = true;
    
    fetch('/api/portfolio/save', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    })
    .then(res => {
        if (!res.ok) {
            return res.json().then(data => { throw new Error(data.error || 'Server error'); });
        }
        return res.json();
    })
    .then(data => {
        showToast('✅ 포트폴리오가 성공적으로 저장되었습니다!');
        setTimeout(() => {
            location.reload();
        }, 1500);
    })
    .catch(err => {
        alert('저장 실패: ' + err.message);
        saveBtn.innerText = oldText;
        saveBtn.disabled = false;
    });
}

function showToast(message) {
    const toast = document.getElementById("toast");
    toast.innerText = message;
    toast.className = "show";
    setTimeout(function(){ toast.className = toast.className.replace("show", ""); }, 3000);
}
</script>
<!-- ── 📱 모바일 하단 플로팅 탭바 마크업 ── -->
<div class="mobile-tab-bar">
    <a href="/m" id="tab-portfolio" class="tab-item"><span class="icon">📱</span><span>Portfolio</span></a>
    <a href="/" id="tab-analysis" class="tab-item"><span class="icon">🔬</span><span>Analysis</span></a>
    <a href="/discord" id="tab-discord" class="tab-item"><span class="icon">🔔</span><span>Discord</span></a>
    <a href="/logout" class="tab-item" style="color:var(--danger);"><span class="icon">🚪</span><span>Logout</span></a>
</div>
<script>
    (function() {
        const path = window.location.pathname;
        if(path==='/m'||path==='/my-portfolio') {
            document.getElementById('tab-portfolio').classList.add('active');
        } else if(path==='/discord') {
            document.getElementById('tab-discord').classList.add('active');
        } else if(path==='/'||path.includes('/portfolio')) {
            document.getElementById('tab-analysis').classList.add('active');
        }
    })();
</script>
</body></html>"""

if __name__ == "__main__":
    print("🚀 Hyperliquid Dashboard Pro v3.1 - Port 5001")
    app.run(host="0.0.0.0", port=5001)

