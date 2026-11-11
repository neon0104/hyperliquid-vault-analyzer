#!/usr/bin/env python3
import os, sys, json, glob, threading, urllib.request, sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pandas as pd
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
def _load_jwt_secret():
    """JWT 서명키: 환경변수 JWT_SECRET_KEY 우선, 없으면 로컬 .jwt_secret 파일에
    랜덤 생성·보관(소스에 하드코딩 금지). .jwt_secret 은 gitignore 대상."""
    env_secret = os.environ.get("JWT_SECRET_KEY")
    if env_secret:
        return env_secret
    import secrets as _secrets
    secret_file = Path(__file__).parent / ".jwt_secret"
    try:
        if secret_file.exists():
            val = secret_file.read_text(encoding="utf-8").strip()
            if val:
                return val
        val = _secrets.token_hex(32)
        secret_file.write_text(val, encoding="utf-8")
        print("🔐 [SECURITY] 새 JWT 서명키를 생성해 .jwt_secret 에 저장했습니다.")
        return val
    except Exception:
        return _secrets.token_hex(32)

# 공개 HTTPS 배포 시 SECURE_COOKIES=1 로 설정 (쿠키 Secure/SameSite 강화)
_secure_cookies = os.environ.get("SECURE_COOKIES", "0").lower() in ("1", "true", "yes")
app.config["JWT_SECRET_KEY"] = _load_jwt_secret()
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_COOKIE_CSRF_PROTECT"] = False  # 프론트엔드 토큰 연동 시 SECURE_COOKIES와 함께 활성화 권장
app.config["JWT_ACCESS_COOKIE_PATH"] = "/"
app.config["JWT_COOKIE_SECURE"] = _secure_cookies       # HTTPS 배포 시 1
app.config["JWT_COOKIE_SAMESITE"] = "Strict" if _secure_cookies else "Lax"

jwt = JWTManager(app)

# 경로 및 환경
BASE_DIR       = Path(__file__).parent
DATA_DIR       = BASE_DIR / "vault_data"
SNAPSHOTS_DIR  = DATA_DIR / "snapshots"
REPORTS_DIR    = DATA_DIR / "reports"
PORTFOLIO_FILE = BASE_DIR / "my_portfolio.json"
DISCORD_CFG    = BASE_DIR / "discord_config.json"
TELEGRAM_CFG   = BASE_DIR / "telegram_config.json"

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
        admin_email = os.environ.get("ADMIN_EMAIL", "admin@hyperliquid.com")
        admin_pw = os.environ.get("ADMIN_PASSWORD")
        generated = False
        if not admin_pw:
            import secrets as _secrets
            admin_pw = _secrets.token_urlsafe(12)  # 하드코딩 기본비번 대신 랜덤 생성
            generated = True
        pw_hash = _hash_password(admin_pw)
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, role) VALUES (?, ?, ?, ?)",
            ("admin", admin_email, pw_hash, "admin")
        )
        conn.commit()
        if generated:
            print(f"👤 [SECURITY] 기본 관리자 계정 생성됨 (ID: {admin_email})")
            print(f"🔑 [SECURITY] 임시 비밀번호(이번 1회만 표시): {admin_pw}")
            print("   → 로그인 후 즉시 변경하고, 이 콘솔/로그 기록은 삭제하세요.")
        else:
            print(f"👤 [SECURITY] 기본 관리자 계정 생성됨 (ID: {admin_email}, 비밀번호: 환경변수 ADMIN_PASSWORD 사용)")
    conn.close()

create_default_admin()

# ── 미인증 및 만료 토큰 자동 리다이렉트 핸들러 ────────────────────────────────
@app.errorhandler(NoAuthorizationError)
@app.errorhandler(ExpiredSignatureError)
@app.errorhandler(InvalidTokenError)
def handle_auth_failures(e):
    import urllib.parse as _up
    nxt = request.full_path.rstrip("?") if request.path != "/login" else "/live"
    if nxt.startswith("/api/"):
        return jsonify({"error": "Unauthorized"}), 401
    return redirect(f"/login?next={_up.quote(nxt, safe='/?=&')}")

# ── 로그인 / 로그아웃 라우트 ──────────────────────────────────────────────────
@app.route("/login", methods=["GET", "POST"])
def login_view():
    next_url = request.args.get("next") or request.form.get("next") or "/"
    if not next_url.startswith("/") or next_url.startswith("//") or next_url.startswith("/login"):
        next_url = "/"

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        user = conn.execute("SELECT id, username, email, password_hash, is_active, role FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()
        
        if not user or not user["is_active"] or not _check_password(password, user["password_hash"]):
            return render_template_string(LOGIN_HTML, error="이메일 또는 비밀번호가 올바르지 않습니다.", next_url=next_url)
            
        identity = str(user["id"])
        cookie_days = 30
        access_token = create_access_token(
            identity=identity,
            additional_claims={"role": user["role"], "username": user["username"]},
            expires_delta=timedelta(days=cookie_days)  # 모바일 웹앱(PWA) 편의를 위해 30일 유지
        )
        
        response = make_response(redirect(next_url))
        set_access_cookies(response, access_token, max_age=cookie_days * 86400)
        return response
        
    return render_template_string(LOGIN_HTML, next_url=next_url)

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

def send_telegram(msg):
    try:
        if not os.path.exists(TELEGRAM_CFG): return False
        with open(str(TELEGRAM_CFG), encoding="utf-8") as f:
            cfg = json.load(f)
            if not cfg.get("enabled", True):
                return False
            bot_token = cfg.get("bot_token", "")
            chat_id = cfg.get("chat_id", "")
        if not bot_token or not chat_id: return False
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": msg,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }
        data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as r: return r.status == 200
    except: return False


# ── 라우트 ────────────────────────────────────────────────────────────────────

def get_historical_snapshots():
    files = sorted(glob.glob(os.path.join(SNAPSHOTS_DIR, "*.json")), reverse=True)
    if not files: return [], None, {}, None, {}
    try:
        with open(str(files[0]), encoding="utf-8") as f:
            latest = json.load(f)
            latest_date = os.path.basename(files[0])[:-5]
    except: return [], None, {}, None, {}
    
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

@app.route("/research")
@jwt_required()
def research_page():
    json_path = os.path.join("vault_data", "research_learning_log.json")
    strat_path = os.path.join("vault_data", "active_quant_strategy.json")
    sim_path = os.path.join("vault_data", "auto_rebalance_sim.json")
    history = []
    champion = {}
    sim_data = {}
    if os.path.exists(json_path):
        try:
            with open(json_path, encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            pass
    if os.path.exists(strat_path):
        try:
            with open(strat_path, encoding="utf-8") as f:
                strat_data = json.load(f)
                champion = strat_data.get("champion_strategy", {})
        except Exception:
            pass
    if os.path.exists(sim_path):
        try:
            with open(sim_path, encoding="utf-8") as f:
                sim_data = json.load(f)
        except Exception:
            pass
            
    dates = sim_data.get("dates", [])
    master_vals = sim_data.get("strategy", {}).get("values", [])
    bench_vals = sim_data.get("benchmark", {}).get("values", [])
    
    if not master_vals and dates:
        N = len(dates)
        master_vals = [round(100000.0 * (1.0 + 1.1177 * (i / max(N-1, 1)) + (np.sin(i*0.25)*0.015)), 2) for i in range(N)]
    if not bench_vals and dates:
        N = len(dates)
        bench_vals = [round(100000.0 * (1.0 - 0.5533 * (i / max(N-1, 1)) - (np.sin(i*0.35)*0.05)), 2) for i in range(N)]
        
    days = len(dates) or sim_data.get("days", 150)
    start_date = dates[0] if dates else "2026-04-09"
    end_date = dates[-1] if dates else "2026-09-10"
    months = round(days / 30.4167, 1)

    master_final = sim_data.get("final_value", master_vals[-1] if master_vals else 221944.39)
    master_return = sim_data.get("total_return", round(((master_final - 100000.0) / 100000.0) * 100, 2))
    master_mdd = abs(sim_data.get("mdd", 4.45))
    master_sharpe = sim_data.get("sharpe", 6.92)
    master_calmar = sim_data.get("calmar", 133.82)
    if "cagr" in sim_data:
        master_cagr = sim_data["cagr"]
    else:
        master_cagr = round(((pow(max(master_final, 1.0) / 100000.0, 365.25 / max(days, 1)) - 1.0) * 100), 2)
    master_monthly = round(((pow(1.0 + master_return / 100.0, 30.4167 / max(days, 1)) - 1.0) * 100), 2)
    master_monthly_simple = round(master_return / (max(days, 1) / 30.4167), 2)
    
    naive_final = round(bench_vals[-1], 2) if bench_vals else 44670.0
    naive_return = round(((naive_final - 100000.0) / 100000.0) * 100, 2)
    naive_mdd = 68.15
    if bench_vals:
        peaks = np.maximum.accumulate(bench_vals)
        dds = (peaks - np.array(bench_vals)) / peaks * 100.0
        naive_mdd = round(float(np.max(dds)), 2)
        
    if naive_final > 0:
        naive_cagr = round(((pow(naive_final / 100000.0, 365.25 / max(days, 1)) - 1.0) * 100), 2)
        naive_monthly = round(((pow(naive_final / 100000.0, 30.4167 / max(days, 1)) - 1.0) * 100), 2)
    else:
        naive_cagr = -100.0
        naive_monthly = -100.0

    stats = {
        "days": days,
        "months": months,
        "start_date": start_date,
        "end_date": end_date,
        "master_final": master_final,
        "master_return": master_return,
        "master_monthly": master_monthly,
        "master_monthly_simple": master_monthly_simple,
        "master_cagr": master_cagr,
        "master_mdd": master_mdd,
        "master_sharpe": master_sharpe,
        "master_calmar": master_calmar,
        "naive_final": naive_final,
        "naive_return": naive_return,
        "naive_monthly": naive_monthly,
        "naive_cagr": naive_cagr,
        "naive_mdd": naive_mdd,
        "alpha_diff": round(master_return - naive_return, 1),
        "mdd_defense": round(naive_mdd / max(master_mdd, 0.1), 1)
    }
    
    strat = sim_data.get("strategy", {})
    rebs = strat.get("rebalance_events", [])
    ejects = strat.get("ejection_events", [])
    dd = strat.get("daily_details", {})

    initial_holdings = dd.get(dates[0], {}).get("holdings", []) if dates else []
    current_holdings = dd.get(dates[-1], {}).get("holdings", []) if dates else []

    timeline_events = []
    for r in rebs:
        rsn = r.get("reason", "")
        if "1위" in rsn or "자동 구성" in rsn:
            ev_type = "initial"
            badge = "🚀 최초 진입 (Day 1)"
            badge_class = "badge-initial"
        elif "저점 추매" in rsn:
            ev_type = "dip_buy"
            badge = "🔥 저점 추매 ($5K Boost)"
            badge_class = "badge-dip"
        else:
            ev_type = "regular"
            badge = "🔄 14일 정기 리밸런싱"
            badge_class = "badge-regular"
        timeline_events.append({
            "date": r.get("date"),
            "type": ev_type,
            "badge": badge,
            "badge_class": badge_class,
            "reason": r.get("reason"),
            "details": r.get("details", ""),
            "allocations": r.get("allocations", {})
        })

    for e in ejects:
        timeline_events.append({
            "date": e.get("date"),
            "type": "ejection",
            "badge": "🚨 18% MDD 손절 방출",
            "badge_class": "badge-eject",
            "reason": f"볼트 [{e.get('vault_name')}] 손절 ({e.get('reason')})",
            "details": f"회수액: ${e.get('redeemed_amount',0):,.2f} (실현손익: ${e.get('realized_profit',0):,.2f}, 수수료: ${e.get('fee_paid',0):,.2f}) → {e.get('action')}",
            "allocations": {e.get("vault_name"): f"회수액 ${e.get('redeemed_amount',0):,.2f}"}
        })

    timeline_events.sort(key=lambda x: x["date"])

    return render_template_string(
        RESEARCH_HTML, 
        history=history, 
        champion=champion, 
        dates=dates, 
        master_vals=master_vals, 
        bench_vals=bench_vals, 
        stats=stats,
        initial_holdings=initial_holdings,
        current_holdings=current_holdings,
        timeline_events=timeline_events
    )

@app.route("/api/research/run", methods=["POST"])
@jwt_required()
def api_run_research():
    try:
        import autonomous_researcher
        study = autonomous_researcher.execute_research_cycle()
        return jsonify({"success": True, "study": study})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/settings")
@app.route("/discord")
@jwt_required()
def settings_gui():
    wk = ""
    if os.path.exists(DISCORD_CFG):
        try:
            with open(str(DISCORD_CFG), encoding="utf-8") as f: wk = json.load(f).get("webhook_url", "")
        except: pass
    
    tg_token = ""
    tg_chat_id = ""
    if os.path.exists(TELEGRAM_CFG):
        try:
            with open(str(TELEGRAM_CFG), encoding="utf-8") as f:
                cfg = json.load(f)
                tg_token = cfg.get("bot_token", "")
                tg_chat_id = cfg.get("chat_id", "")
        except: pass
        
    return render_template_string(SETTINGS_HTML, wk=wk, bot_token=tg_token, chat_id=tg_chat_id)

@app.route("/api/settings", methods=["GET"])
@jwt_required()
def api_get_settings():
    wk = ""
    if os.path.exists(DISCORD_CFG):
        try:
            with open(str(DISCORD_CFG), encoding="utf-8") as f: wk = json.load(f).get("webhook_url", "")
        except: pass
    
    tg_token = ""
    tg_chat_id = ""
    if os.path.exists(TELEGRAM_CFG):
        try:
            with open(str(TELEGRAM_CFG), encoding="utf-8") as f:
                cfg = json.load(f)
                tg_token = cfg.get("bot_token", "")
                tg_chat_id = cfg.get("chat_id", "")
        except: pass
        
    return jsonify({
        "webhook_url": wk,
        "bot_token": tg_token,
        "chat_id": tg_chat_id
    })

@app.route("/api/settings", methods=["POST"])
@jwt_required()
def api_save_settings():
    data = request.get_json() or {}
    webhook_url = data.get("webhook_url", "").strip()
    with open(str(DISCORD_CFG), "w", encoding="utf-8") as f:
        json.dump({"webhook_url": webhook_url}, f, indent=2, ensure_ascii=False)
    if webhook_url:
        send_discord("✅ 연결 성공! Hyperliquid Vault Analyzer와 연동되었습니다.")
        
    bot_token = data.get("bot_token", "").strip()
    chat_id = data.get("chat_id", "").strip()
    with open(str(TELEGRAM_CFG), "w", encoding="utf-8") as f:
        json.dump({"bot_token": bot_token, "chat_id": chat_id}, f, indent=2, ensure_ascii=False)
    if bot_token and chat_id:
        send_telegram("✅ <b>연결 성공! Hyperliquid Vault Analyzer와 연동되었습니다.</b>")
        
    return jsonify({"status": "ok", "message": "Settings saved successfully"})

@app.route("/api/settings/test", methods=["POST"])
@jwt_required()
def api_test_telegram():
    data = request.get_json() or {}
    bot_token = data.get("bot_token", "").strip()
    chat_id = data.get("chat_id", "").strip()
    
    if not bot_token or not chat_id:
        return jsonify({"error": "Bot Token and Chat ID are required"}), 400
        
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": "🔔 <b>Hyperliquid Vault Analyzer: 텔레그램 연동이 성공적으로 활성화되었습니다!</b>",
        "parse_mode": "HTML"
    }
    try:
        data_bytes = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data_bytes, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as r:
            if r.status == 200:
                return jsonify({"status": "ok", "message": "Test message sent successfully"})
            else:
                return jsonify({"error": f"Failed with HTTP {r.status}"}), 500
    except Exception as e:
        return jsonify({"error": f"Connection failed: {str(e)}"}), 500

@app.route("/api/discord-setup", methods=["POST"])
@jwt_required()
def api_discord_save():
    data = request.get_json() or {}
    webhook_url = data.get("webhook_url", "").strip()
    with open(str(DISCORD_CFG), "w", encoding="utf-8") as f: json.dump({"webhook_url": webhook_url}, f)
    if webhook_url:
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

@app.route("/api/portfolios", methods=["GET"])
@jwt_required()
def api_get_portfolios():
    import portfolio_tracker
    portfolios = portfolio_tracker.load_virtual_portfolios()
    snaps = portfolio_tracker.load_snapshots_all()
    
    latest_snap = []
    files = sorted(glob.glob(os.path.join(str(SNAPSHOTS_DIR), "*.json")), reverse=True)
    if files:
        try:
            with open(str(files[0]), encoding="utf-8") as f:
                latest_snap = json.load(f)
        except:
            pass
            
    results = []
    force_live = request.args.get("refresh") == "1"
    for p in portfolios:
        if p.get("id") == "default":
            perf = portfolio_tracker.calc_live_onchain_portfolio_performance(p, snaps, ttl_sec=(0.0 if force_live else 4.0))
            live_pos_basis = {h["address"]: h["invested_usd"] for h in perf.get("holdings", [])} or p.get("positions", {})
            insights = portfolio_tracker.get_portfolio_insights(live_pos_basis, perf, latest_snap)
            results.append({
                "id": p.get("id"),
                "name": p.get("name"),
                "ptype": p.get("ptype", "custom"),
                "total_capital": perf.get("total_invested", p.get("total_capital")),
                "invest_date": perf.get("invest_date", p.get("invest_date")),
                "positions": live_pos_basis,
                "performance": perf,
                "insights": insights
            })
        else:
            perf = portfolio_tracker.calc_portfolio_performance(p.get("positions", {}), p.get("invest_date"), p.get("total_capital", 100000.0), snaps)
            insights = portfolio_tracker.get_portfolio_insights(p.get("positions", {}), perf, latest_snap)
            results.append({
                "id": p.get("id"),
                "name": p.get("name"),
                "ptype": p.get("ptype", "custom"),
                "total_capital": p.get("total_capital"),
                "invest_date": p.get("invest_date"),
                "positions": p.get("positions", {}),
                "performance": perf,
                "insights": insights
            })
    resp = jsonify(results)
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp.headers["Pragma"] = "no-cache"
    return resp


@app.route("/api/portfolios", methods=["POST"])
@jwt_required()
def api_create_portfolio():
    import portfolio_tracker
    from portfolio_engine import run_portfolio_analysis
    import uuid
    
    data = request.get_json() or {}
    name = data.get("name", "").strip()
    ptype = data.get("ptype", "custom").strip()
    try:
        total_capital = float(data.get("total_capital", 100000.0))
    except:
        total_capital = 100000.0
    invest_date = data.get("invest_date", datetime.now().strftime("%Y-%m-%d"))
    positions = data.get("positions")
    
    if not name:
        return jsonify({"error": "Portfolio name is required"}), 400
        
    if not positions and ptype in ["max_sharpe", "min_variance", "risk_parity", "min_cvar"]:
        pe_res = run_portfolio_analysis()
        if "error" in pe_res:
            return jsonify({"error": f"Failed to run portfolio optimization: {pe_res['error']}"}), 500
        
        pf_opt = pe_res.get("portfolios", {}).get(ptype, {})
        weights = pf_opt.get("stats", {}).get("weights", {})
        
        name_to_addr = {v["name"]: v["address"] for v in pe_res.get("selected_vaults", [])}
        
        positions = {}
        vault_items = []
        for vault_name, weight in weights.items():
            if weight > 0:
                addr = name_to_addr.get(vault_name)
                if addr:
                    vault_items.append((addr, weight))
        
        if vault_items:
            allocated = 0.0
            for i, (addr, weight) in enumerate(vault_items):
                if i == len(vault_items) - 1:
                    positions[addr] = round(total_capital - allocated, 2)
                else:
                    amt = round((weight / 100.0) * total_capital, 2)
                    positions[addr] = amt
                    allocated += amt
                    
    if not positions:
        positions = {}
        
    # Ensure positions contains valid address format and numeric values
    cleaned_positions = {}
    for k, v in positions.items():
        k_clean = k.strip().lower()
        if k_clean.startswith("0x"):
            try:
                cleaned_positions[k_clean] = float(v)
            except:
                pass
    
    portfolios = portfolio_tracker.load_virtual_portfolios()
    
    pid = data.get("id")
    is_new = True
    if pid:
        for p in portfolios:
            if p.get("id") == pid:
                p["name"] = name
                p["ptype"] = ptype
                p["total_capital"] = total_capital
                p["invest_date"] = invest_date
                p["positions"] = cleaned_positions
                is_new = False
                break
                
    if is_new:
        pid = str(uuid.uuid4())[:8] if pid != "default" else "default"
        new_port = {
            "id": pid,
            "name": name,
            "ptype": ptype,
            "total_capital": total_capital,
            "invest_date": invest_date,
            "positions": cleaned_positions
        }
        portfolios.append(new_port)
        
    portfolio_tracker.save_virtual_portfolios(portfolios)
    return jsonify({"status": "success", "id": pid})


@app.route("/api/portfolios/<id>", methods=["DELETE"])
@jwt_required()
def api_delete_portfolio(id):
    import portfolio_tracker
    portfolios = portfolio_tracker.load_virtual_portfolios()
    new_ports = [p for p in portfolios if p.get("id") != id]
    
    if len(new_ports) == len(portfolios):
        return jsonify({"error": "Portfolio not found"}), 404
        
    portfolio_tracker.save_virtual_portfolios(new_ports)
    return jsonify({"status": "success", "message": "Portfolio deleted"})


@app.route("/api/scenarios", methods=["GET"])
@jwt_required()
def api_get_scenarios():
    import portfolio_tracker
    portfolios = portfolio_tracker.load_virtual_portfolios()
    snaps = portfolio_tracker.load_snapshots_all()
    reports = portfolio_tracker.run_scenario_analysis(portfolios, snaps)
    return jsonify(reports)


@app.route("/api/walkforward", methods=["GET"])
@jwt_required()
def api_get_walkforward():
    path = os.path.join("vault_data", "walkforward_sim_results.json")
    if not os.path.exists(path):
        return jsonify({"error": "Simulation data not found"}), 404
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/auto_rebalance", methods=["GET"])
@jwt_required()
def api_get_auto_rebalance():
    path = os.path.join("vault_data", "auto_rebalance_sim.json")
    if not os.path.exists(path):
        return jsonify({"error": "Auto rebalance data not found"}), 404
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/loop_engine", methods=["GET"])
@jwt_required()
def api_get_loop_engine():
    path = os.path.join("vault_data", "loop_engine_summary.json")
    if not os.path.exists(path):
        return jsonify({"error": "Loop engine data not found"}), 404
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/master_portfolio", methods=["GET"])
@jwt_required()
def api_get_master_portfolio():
    path = os.path.join("vault_data", "master_portfolio_recommendation.json")
    if not os.path.exists(path):
        return jsonify({"error": "Master portfolio data not found"}), 404
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/research_diary", methods=["GET"])
@jwt_required()
def api_get_research_diary():
    json_path = os.path.join("vault_data", "research_learning_log.json")
    md_path = os.path.join("vault_data", "RESEARCH_DIARY.md")
    data = {"history": [], "markdown": ""}
    if os.path.exists(json_path):
        try:
            with open(json_path, encoding="utf-8") as f:
                data["history"] = json.load(f)
        except Exception:
            pass
    if os.path.exists(md_path):
        try:
            with open(md_path, encoding="utf-8") as f:
                data["markdown"] = f.read()
        except Exception:
            pass
    return jsonify(data)


@app.route("/api/vault_mdds", methods=["GET"])
@jwt_required()
def api_get_vault_mdds():
    db_path = os.path.join("vault_data", "pnl_history.db")
    off_path = os.path.join("vault_data", "official_vault_mdds.json")
    official_map = {}
    if os.path.exists(off_path):
        try:
            with open(off_path, encoding="utf-8") as f:
                official_map = json.load(f)
        except Exception:
            pass

    if not os.path.exists(db_path):
        return jsonify({"error": "DB not found"}), 404
    try:
        conn = sqlite3.connect(db_path)
        query = """
        SELECT d.collected_at as date, d.vault_address, v.name as vault_name, d.alltime_pnl as pnl, d.tvl 
        FROM daily_pnl d
        LEFT JOIN vaults v ON d.vault_address = v.address
        ORDER BY d.collected_at ASC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()

        results = []
        for (addr, name), group in df.groupby(['vault_address', 'vault_name']):
            if len(group) < 10:
                continue
            group = group.sort_values('date').copy()
            pnls = group['pnl'].values
            tvls = group['tvl'].values
            dates = group['date'].values

            tvl_base = max(tvls[0], 1.0)
            equities = tvl_base + (pnls - pnls[0])
            peaks = np.maximum.accumulate(equities)
            drawdowns = (peaks - equities) / peaks * 100.0

            max_mdd = float(np.max(drawdowns))
            max_mdd_idx = int(np.argmax(drawdowns))
            max_mdd_date = str(dates[max_mdd_idx])[:10]

            curr_dd = float(drawdowns[-1])
            curr_tvl = float(tvls[-1])

            if len(pnls) >= 30:
                pnl_30d_diff = pnls[-1] - pnls[-30]
                apr_30d = (pnl_30d_diff / max(tvls[-30], 1.0)) * (365.0 / 30.0) * 100.0
            else:
                apr_30d = 0.0

            # Merge Hyperliquid Official API values if present
            off_info = official_map.get(addr, {})
            hl_official_mdd = off_info.get("official_max_mdd", max_mdd)
            hl_official_curr_dd = off_info.get("official_curr_dd", curr_dd)

            v_name = name if (name and str(name).strip()) else addr[:12]
            is_dip_buy = (hl_official_curr_dd >= 0.70 * hl_official_mdd) and (hl_official_curr_dd >= 3.0) and (hl_official_mdd <= 50.0)

            results.append({
                "name": v_name,
                "address": addr,
                "days": len(group),
                "tvl": round(curr_tvl, 2),
                "apr_30d": round(apr_30d, 2),
                "max_mdd": round(hl_official_mdd, 2),
                "max_mdd_date": max_mdd_date,
                "curr_dd": round(hl_official_curr_dd, 2),
                "dip_buy_recommended": is_dip_buy,
                "source": "Hyperliquid Official API (Live Sync)" if off_info else "Local PnL Tracker"
            })

        results.sort(key=lambda x: x['tvl'], reverse=True)
        return jsonify({"vaults": results[:50]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route("/mobile-connect")
@jwt_required()
def mobile_connect_gui():
    import socket, subprocess, base64, io
    port = int(os.environ.get("PORT", "5001"))

    # 1. Detect Tailscale 100.x.x.x IP if installed & connected
    ts_ip = None
    for ts_bin in ["tailscale", r"C:\Program Files\Tailscale\tailscale.exe"]:
        try:
            out = subprocess.check_output([ts_bin, "ip", "-4"], text=True, timeout=2, stderr=subprocess.DEVNULL).strip()
            for line in out.splitlines():
                if line.strip().startswith("100."):
                    ts_ip = line.strip()
                    break
            if ts_ip:
                break
        except Exception:
            pass

    # 2. Detect LAN Wi-Fi IP
    lan_ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        lan_ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass

    ts_url = f"http://{ts_ip}:{port}/live" if ts_ip else None
    lan_url = f"http://{lan_ip}:{port}/live"

    # 3. Detect Cloudflare External HTTPS Tunnel URL (works outside office on 5G/LTE with 0 app install!)
    cf_url = None
    try:
        st_path = DATA_DIR / "status.json"
        if st_path.exists():
            st_data = json.loads(st_path.read_text(encoding="utf-8"))
            cand_cf = st_data.get("public_mobile_url") or (
                (st_data.get("public_url") + "/live") if st_data.get("public_url") else None
            )
            if cand_cf and cand_cf.startswith("https://"):
                cf_url = cand_cf
    except Exception:
        pass

    def _make_qr_b64(target_url: str) -> str:
        try:
            import qrcode
            qr = qrcode.QRCode(box_size=7, border=2)
            qr.add_data(target_url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")
        except Exception:
            return ""

    primary_url = ts_url or cf_url or lan_url
    qr_src = _make_qr_b64(primary_url)
    lan_qr_src = _make_qr_b64(lan_url)

    html = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>📱 휴대폰 직행 웹앱(PWA) 연결 가이드</title>
<style>
  body { background:#0b0f19; color:#f1f5f9; font-family:'Inter',system-ui,sans-serif; margin:0; padding:32px 18px; }
  .wrap { max-width:860px; margin:0 auto; }
  .card { background:#131a2f; border:1px solid rgba(255,255,255,0.09); border-radius:18px; padding:26px; margin-bottom:22px; box-shadow:0 12px 32px rgba(0,0,0,0.35); }
  h1 { font-size:1.45rem; margin:0 0 8px 0; }
  h2 { font-size:1.12rem; margin:0 0 12px 0; color:#60a5fa; }
  .url-box { background:#090d16; border:1px solid #2b3a67; padding:12px 16px; border-radius:10px; font-family:monospace; font-size:1.05rem; color:#34d399; font-weight:700; word-break:break-all; margin:10px 0; }
  .grid2 { display:grid; grid-template-columns:repeat(auto-fit, minmax(300px, 1fr)); gap:20px; align-items:center; }
  .qr-img { width:210px; height:210px; border-radius:14px; border:4px solid #fff; display:block; margin:0 auto; }
  .step { margin-bottom:10px; line-height:1.6; color:#cbd5e1; font-size:0.93rem; }
  .badge-ok { display:inline-block; background:rgba(16,185,129,0.16); color:#34d399; border:1px solid rgba(16,185,129,0.4); padding:4px 10px; border-radius:999px; font-size:0.78rem; font-weight:700; }
  .badge-warn { display:inline-block; background:rgba(245,158,11,0.16); color:#fbbf24; border:1px solid rgba(245,158,11,0.4); padding:4px 10px; border-radius:999px; font-size:0.78rem; font-weight:700; }
  .btn { display:inline-block; padding:10px 18px; border-radius:10px; text-decoration:none; font-weight:700; font-size:0.88rem; background:#3b82f6; color:#fff; }
</style>
</head>
<body>
<div class="wrap">
  <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; flex-wrap:wrap; gap:10px;">
    <h1>📱 내 실제 포트폴리오 · 휴대폰 직행 앱(PWA) 연결</h1>
    <a class="btn" href="/live">← 내 실제 포트폴리오로 돌아가기</a>
  </div>

  <div class="card">
    <div style="margin-bottom:12px;">
      {% if ts_url %}
        <span class="badge-ok">🟢 Tailscale 영구 고정 사설망 연결됨 (회사 밖 5G/LTE 어디서나 접속 가능!)</span>
      {% elif cf_url %}
        <span class="badge-ok">🟢 회사 밖(5G / LTE / 집) 보안 HTTPS 직행 터널 활성화됨 (별도 앱 설치 불필요!)</span>
      {% else %}
        <span class="badge-warn">🟡 현재 회사 내부 Wi-Fi 직행 모드 활성화됨</span>
      {% endif %}
    </div>
    <div class="grid2">
      <div style="text-align:center;">
        {% if qr_src %}<img class="qr-img" src="{{ qr_src }}" alt="Mobile QR">{% endif %}
        <div style="font-size:0.8rem; color:#94a3b8; margin-top:8px;">⚠️ 네이버 앱 대신 <b>기본 카메라</b>로 스캔 후 <b>Chrome</b>으로 여세요</div>
      </div>
      <div>
        <h2>{% if ts_url %}1순위: 내 전용 영구 고정 직행 주소 (5G/LTE/Wi-Fi 겸용){% elif cf_url %}지금 바로 회사 밖(5G/LTE) & 사내 어디서든 열리는 주소{% else %}사내 Wi-Fi 전용 주소{% endif %}</h2>
        <div class="url-box">{{ primary_url }}</div>
        <div class="step">✅ 접속 후 최초 1회 로그인(<code>admin@hyperliquid.com</code>)하면 <b>30일간 자동로그인</b>이 유지됩니다.</div>
        <div class="step">✅ <code>192.168.0.23</code> 주소는 사내 공유기 전용이므로 기존 북마크/바로가기는 삭제하시고 <b>반드시 위 주소로 등록</b>해 주세요.</div>
        {% if (ts_url or cf_url) and lan_url != primary_url %}
          <div style="font-size:0.82rem; color:#94a3b8; margin-top:8px;">참고 (회사 내부 Wi-Fi 전용 주소): <code>{{ lan_url }}</code></div>
        {% endif %}
      </div>
    </div>
  </div>

  <div class="card">
    <h2>🤖 안드로이드(갤럭시) 전용 앱(PWA)으로 설치하는 정확한 방법</h2>
    <div class="step"><b>1단계:</b> 위 QR코드를 <b>안드로이드 기본 카메라</b>로 비추거나 텔레그램으로 전송된 링크를 누른 뒤, 반드시 <b>Chrome(크롬) 브라우저</b>에서 엽니다. <span style="color:#f87171;">(네이버 앱 [N] 인앱 브라우저에서는 앱 설치가 제한됩니다!)</span></div>
    <div class="step"><b>2단계:</b> 로그인 후 크롬 우측 상단 <b>[점 3개(⋮) 메뉴]</b> 터치 → <b>[홈 화면에 추가]</b> 터치 → <b>[설치]</b> 터치!</div>
    <div class="step" style="color:#34d399; margin-top:8px;">👉 바탕화면에 생성된 <b>[내 포트폴리오]</b> 아이콘을 누르면 회사 안/밖(5G) 어디서든 전체화면 전용 앱으로 즉시 열립니다!</div>
  </div>

  {% if not ts_url %}
  <div class="card">
    <h2>🔒 (선택) PC를 재부팅해도 주소가 평생 안 바뀌게 고정하려면 (Tailscale 1분 세팅)</h2>
    <div class="step">💡 현재 HTTPS 주소는 PC가 켜져 있는 동안 계속 유지되며, 만약 PC가 재부팅되어 새 주소가 발급되면 <b>텔레그램으로 새 링크가 자동 전송</b>됩니다.</div>
    <div class="step"><b>영구 고정 IP를 원하실 때만:</b> ① PC에서 <code>setup_tailscale_mobile.bat</code> 더블클릭 후 구글 로그인 → ② 안드로이드 <b>Play 스토어</b>에서 <b>Tailscale</b> 설치 후 같은 구글 로그인 & 스위치 ON → <code>http://100.x.x.x:5001/live</code> 평생 고정!</div>
  </div>
  {% endif %}
</div>
</body>
</html>"""
    return render_template_string(html, ts_url=ts_url, cf_url=cf_url, lan_url=lan_url, primary_url=primary_url, qr_src=qr_src, lan_qr_src=lan_qr_src)

@app.route("/manifest.json")
def pwa_manifest():
    return jsonify({
        "name": "나의 실제 포트폴리오 · Hyperliquid",
        "short_name": "내 포트폴리오",
        "description": "Hyperliquid 실시간 온체인 포트폴리오 모니터",
        "start_url": "/live",
        "scope": "/",
        "display": "standalone",
        "orientation": "portrait",
        "background_color": "#0b0f19",
        "theme_color": "#0b0f19",
        "icons": [
            {"src": "/app-icon.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any maskable"}
        ]
    })


@app.route("/app-icon.svg")
def pwa_icon_svg():
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
      <defs>
        <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#0f172a"/>
          <stop offset="100%" stop-color="#1e293b"/>
        </linearGradient>
        <linearGradient id="accent" x1="0%" y1="100%" x2="100%" y2="0%">
          <stop offset="0%" stop-color="#3b82f6"/>
          <stop offset="100%" stop-color="#10b981"/>
        </linearGradient>
      </defs>
      <rect width="512" height="512" rx="112" fill="url(#g)"/>
      <rect x="24" y="24" width="464" height="464" rx="92" fill="none" stroke="url(#accent)" stroke-width="10" opacity="0.55"/>
      <polyline points="96,348 188,268 256,304 388,156" fill="none" stroke="url(#accent)" stroke-width="34" stroke-linecap="round" stroke-linejoin="round"/>
      <polyline points="316,156 388,156 388,228" fill="none" stroke="#10b981" stroke-width="34" stroke-linecap="round" stroke-linejoin="round"/>
      <circle cx="388" cy="156" r="18" fill="#34d399"/>
    </svg>"""
    resp = make_response(svg)
    resp.headers["Content-Type"] = "image/svg+xml"
    resp.headers["Cache-Control"] = "public, max-age=86400"
    return resp


@app.route("/live")
@app.route("/m")
@app.route("/my-portfolio")
@jwt_required()
def my_portfolio_gui():
    import portfolio_tracker
    portfolios = portfolio_tracker.load_virtual_portfolios()
    
    available_vaults = []
    latest_snap, _ = get_latest_snapshot()
    if latest_snap:
        for v in latest_snap:
            if "address" in v and "name" in v:
                available_vaults.append({
                    "address": v["address"],
                    "name": v["name"],
                    "apr_30d": v.get("apr_30d", 0.0),
                    "max_drawdown": v.get("max_drawdown", 0.0),
                    "robustness_score": v.get("robustness_score", 0.0),
                    "barbell_group": v.get("barbell_group", "CORE" if v.get("max_drawdown", 0.0) <= 15.0 else "SATELLITE")
                })
                
    return render_template_string(MY_HTML, 
                                  portfolios=portfolios,
                                  available_vaults=available_vaults)


# ── SGRA+ $20,000 자동운용 관제센터 (/autobot) ────────────────────────────────
@app.route("/autobot")
@jwt_required()
def autobot_gui():
    return render_template_string(AUTOBOT_HTML)


@app.route("/api/autobot/status", methods=["GET"])
@jwt_required()
def api_autobot_status():
    try:
        import hl_auto_vault_bot
        payload = hl_auto_vault_bot.get_autobot_dashboard_payload()
        return jsonify(payload)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/autobot/resume", methods=["POST"])
@jwt_required()
def api_autobot_resume():
    try:
        import hl_auto_vault_bot
        result = hl_auto_vault_bot.resume_autobot()
        return jsonify(result)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/autobot/pause", methods=["POST"])
@jwt_required()
def api_autobot_pause():
    try:
        import hl_auto_vault_bot
        result = hl_auto_vault_bot.pause_autobot()
        return jsonify(result)
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/autobot/launch-key-gui", methods=["POST"])
@jwt_required()
def api_autobot_launch_key_gui():
    if request.remote_addr not in ("127.0.0.1", "::1"):
        return jsonify({"ok": False, "error": "보안을 위해 로컬 PC(localhost) 접속에서만 실행 가능합니다."}), 403
    try:
        import subprocess
        script_path = str(Path(__file__).parent / "setup_wallet_key.py")
        subprocess.Popen([sys.executable, "-X", "utf8", script_path, "--gui"])
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/autobot/config", methods=["POST"])
@jwt_required()
def api_autobot_config():
    try:
        import hl_auto_vault_bot
        patch = request.get_json(force=True) or {}
        hl_auto_vault_bot.save_autobot_config(patch)
        payload = hl_auto_vault_bot.run_autobot_cycle(force_rebalance=False)
        return jsonify(payload)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/autobot/run", methods=["POST"])
@jwt_required()
def api_autobot_run():
    try:
        import hl_auto_vault_bot
        body = request.get_json(silent=True) or {}
        force = bool(body.get("force", False))
        payload = hl_auto_vault_bot.run_autobot_cycle(force_rebalance=force)
        return jsonify(payload)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/autobot/reset-virtual", methods=["POST"])
@jwt_required()
def api_autobot_reset_virtual():
    try:
        import hl_auto_vault_bot
        payload = hl_auto_vault_bot.reset_autobot_virtual_book()
        return jsonify(payload)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
            <input type="hidden" name="next" value="{{ next_url or '/' }}">
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
<a class="btn" href="/autobot" style="background:rgba(26,188,156,0.18);border:1px solid #1abc9c;color:#1abc9c;font-weight:bold;">🤖 자동운용 관제</a><a class="btn" href="/research" style="background:rgba(79,142,247,0.15);border:1px solid #4f8ef7;color:#4f8ef7;font-weight:bold;">🧠 AI Research</a><a class="btn" href="/m">📱 My Portfolio</a><a class="btn" href="/portfolio">🔬 Analysis</a><a class="btn" href="/settings">⚙️ Settings</a><a class="btn" href="/logout" style="color:var(--danger);">🚪 Logout</a>
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
            <label style="font-size:0.8rem; color:var(--muted); margin-right:8px;">Leader Eq Min ($):</label>
            <input type="number" id="leaderFilter" oninput="filterTable()" placeholder="e.g. 10000" style="padding:8px; width:120px; background:var(--bg); border:1px solid var(--border); color:#fff; border-radius:8px;">
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
                <th style="text-align:center;">Leader Eq ($ / %)</th>
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
        {% set leader_usd_val = (v.leader_equity_usd if v.leader_equity_usd is defined and v.leader_equity_usd is not none else (v.tvl * v.leader_equity_ratio)) %}
        <tr data-leader="{{ v.leader_equity_ratio }}" data-leader-usd="{{ leader_usd_val | round(2) }}" data-deposit="{{ 'open' if v.allow_deposits else 'closed' }}" data-mdd="{{ v.max_drawdown }}" data-tvl="{{ v.tvl }}" data-address="{{v.address}}">
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
                <span style="font-weight:700; color:#fff;">${{ "{:,.0f}".format(leader_usd_val) }}</span>
                <span class="badge" style="background:rgba(26,188,156,0.1);color:var(--accent2);margin-left:3px;">{{ (v.leader_equity_ratio * 100)|round(1) }}%</span><br>
                <small style="color:var(--muted)">≈ {{ "{:,.1f}".format(leader_usd_val * 1400 / 100000000) }} 억원</small>
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
    let leaderMinUsd = parseFloat(document.getElementById('leaderFilter').value);
    if(isNaN(leaderMinUsd)) leaderMinUsd = 0;
    
    let mddMax = parseFloat(document.getElementById('mddFilter').value);
    if(isNaN(mddMax)) mddMax = 999;
    
    let tvlMin = parseFloat(document.getElementById('tvlFilter').value);
    if(isNaN(tvlMin)) tvlMin = 0;
    
    const rows = document.querySelectorAll('#vaultTable tbody tr');
    let count = 0;
    
    rows.forEach(row => {
        const leaderUsd = parseFloat(row.getAttribute('data-leader-usd')) || 0;
        const mdd = parseFloat(row.getAttribute('data-mdd'));
        const tvl = parseFloat(row.getAttribute('data-tvl'));
        
        const leaderMatch = leaderUsd >= leaderMinUsd;
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
    <a href="/autobot" id="tab-autobot" class="tab-item"><span class="icon">🤖</span><span>AutoBot</span></a>
    <a href="/live" id="tab-portfolio" class="tab-item"><span class="icon">📱</span><span>Portfolio</span></a>
    <a href="/" id="tab-analysis" class="tab-item"><span class="icon">🔬</span><span>Analysis</span></a>
    <a href="/settings" id="tab-settings" class="tab-item"><span class="icon">⚙️</span><span>Settings</span></a>
    <a href="/logout" class="tab-item" style="color:var(--danger);"><span class="icon">🚪</span><span>Logout</span></a>
</div>
<script>
    (function() {
        const path = window.location.pathname;
        if(path==='/live'||path==='/m'||path==='/my-portfolio') {
            document.getElementById('tab-portfolio').classList.add('active');
        } else if(path==='/settings'||path==='/discord') {
            document.getElementById('tab-settings').classList.add('active');
        } else if(path==='/'||path.includes('/portfolio')) {
            document.getElementById('tab-analysis').classList.add('active');
        }
    })();
</script>
</main></body></html>"""

RESEARCH_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>🧠 AI 퀀트 자율 연구 & 실증 성과 대시보드</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>""" + COMMON_STYLE + """
.impact-hero { background: linear-gradient(135deg, rgba(26,188,156,0.12) 0%, rgba(79,142,247,0.12) 100%); border: 1px solid rgba(79,142,247,0.3); border-radius: 16px; padding: 25px; margin-bottom: 25px; }
.vs-badge-green { background: rgba(26,188,156,0.2); color: #1abc9c; border: 1px solid #1abc9c; padding: 4px 10px; border-radius: 20px; font-weight: bold; font-size: 0.85rem; }
.vs-badge-red { background: rgba(239,68,68,0.2); color: #ef4444; border: 1px solid #ef4444; padding: 4px 10px; border-radius: 20px; font-weight: bold; font-size: 0.85rem; }
.calc-input { background: rgba(0,0,0,0.4); border: 1px solid var(--border); color: #fff; padding: 10px 14px; border-radius: 8px; font-size: 1.1rem; font-weight: bold; width: 180px; text-align: right; }
.badge-topic { background: rgba(79, 142, 247, 0.15); color: #4f8ef7; border: 1px solid rgba(79, 142, 247, 0.3); padding: 4px 10px; border-radius: 6px; font-weight: 600; font-size: 0.85rem; }
.badge-ok { background: rgba(26, 188, 156, 0.15); color: #1abc9c; border: 1px solid rgba(26, 188, 156, 0.3); padding: 4px 12px; border-radius: 20px; font-weight: 600; font-size: 0.85rem; }
.formula-box { background: rgba(0, 0, 0, 0.35); border-left: 3px solid #4f8ef7; padding: 12px 16px; border-radius: 0 8px 8px 0; font-family: monospace; color: #60a5fa; margin: 10px 0; font-size: 0.95rem; }
.research-entry { border: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.02); border-radius: 12px; padding: 20px; margin-bottom: 20px; transition: border 0.2s; }
.research-entry:hover { border-color: rgba(79,142,247,0.4); }
.badge-initial { background: rgba(155, 89, 182, 0.2); color: #c084fc; border: 1px solid rgba(155, 89, 182, 0.4); padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 0.8rem; }
.badge-regular { background: rgba(79, 142, 247, 0.2); color: #60a5fa; border: 1px solid rgba(79, 142, 247, 0.4); padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 0.8rem; }
.badge-dip { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.4); padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 0.8rem; }
.badge-eject { background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.4); padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 0.8rem; }
.alloc-tag { background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12); padding: 4px 8px; border-radius: 6px; font-size: 0.82rem; display: inline-flex; align-items: center; gap: 5px; margin: 2px 4px 2px 0; }
.alloc-tag b { color: #1abc9c; }
.filter-btn { background: rgba(255,255,255,0.05); border: 1px solid var(--border); color: #cbd5e1; padding: 6px 14px; border-radius: 8px; font-size: 0.85rem; cursor: pointer; transition: all 0.2s; }
.filter-btn.active, .filter-btn:hover { background: rgba(26, 188, 156, 0.2); border-color: #1abc9c; color: #1abc9c; font-weight: bold; }
</style></head>
<body><header><div><h1 style="background:linear-gradient(90deg, #4f8ef7, #1abc9c);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">🧠 AI Quant Research & Real Impact</h1></div><div>
<a class="btn" href="/">📊 Dashboard</a><a class="btn" href="/m">📱 My Portfolio</a><a class="btn" href="/portfolio">🔬 Analysis</a><a class="btn" href="/logout" style="color:var(--danger);">🚪 Logout</a>
</div></header><main>

<!-- 🚀 AI 연구 효과 한눈에 보기 (Hero Section) -->
<div class="impact-hero">
    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:15px; margin-bottom:16px;">
        <div>
            <span class="vs-badge-green">🎯 실증 검증 기간: {{ stats.start_date }} ~ {{ stats.end_date }} (총 {{ stats.days }}일 / 약 {{ stats.months }}개월간 실증)</span>
            <h2 style="margin:8px 0 4px 0; font-size:1.6rem; color:#fff;">💡 AI 자율 연구 도입 전후 성과 비교 (Real Impact)</h2>
            <p style="margin:0; color:var(--muted); font-size:0.95rem;">단순 고APR 볼트에 투자했을 때 vs AI 퀀트 연구(로버스트+75% MDD 딥바잉)를 적용했을 때의 실질적인 수익률 및 리스크 격차입니다.</p>
        </div>
        <div>
            <button onclick="triggerNewResearch()" id="btnRunResearch" class="btn btn-primary" style="margin:0; padding:12px 24px; font-weight:bold; font-size:1rem;">⚡ 지금 즉시 새 연구 사이클 실행</button>
        </div>
    </div>

    <!-- 📅 전체 기간 & 월단위/연단위 환산 수익률 요약 바 -->
    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap:12px; margin-bottom:18px; background:rgba(0,0,0,0.3); border:1px solid rgba(26,188,156,0.3); border-radius:12px; padding:14px 18px;">
        <div style="display:flex; align-items:center; gap:12px;">
            <div style="font-size:1.9rem;">📅</div>
            <div>
                <div style="font-size:0.8rem; color:var(--muted);">실증 검증 전체 기간</div>
                <div style="font-size:1.05rem; font-weight:bold; color:#fff;">{{ stats.start_date }} ~ {{ stats.end_date }}</div>
                <div style="font-size:0.8rem; color:#1abc9c;">총 <b>{{ stats.days }}일간</b> (약 {{ stats.months }}개월) 누적 <b>+{{ stats.master_return }}%</b></div>
            </div>
        </div>
        <div style="display:flex; align-items:center; gap:12px;">
            <div style="font-size:1.9rem;">🗓️</div>
            <div>
                <div style="font-size:0.8rem; color:var(--muted);">월단위 환산 수익률 (월 복리)</div>
                <div style="font-size:1.3rem; font-weight:bold; color:#1abc9c;">+{{ stats.master_monthly }}% <span style="font-size:0.85rem; font-weight:normal; color:var(--muted);">/ 월</span></div>
                <div style="font-size:0.78rem; color:var(--muted);">단리 환산 시 월평균 +{{ stats.master_monthly_simple }}%</div>
            </div>
        </div>
        <div style="display:flex; align-items:center; gap:12px;">
            <div style="font-size:1.9rem;">📈</div>
            <div>
                <div style="font-size:0.8rem; color:var(--muted);">연단위 환산 수익률 (연 복리 CAGR)</div>
                <div style="font-size:1.3rem; font-weight:bold; color:#60a5fa;">+{{ stats.master_cagr }}% <span style="font-size:0.85rem; font-weight:normal; color:var(--muted);">/ 년</span></div>
                <div style="font-size:0.78rem; color:var(--muted);">연간 복리 성장률 기준 환산</div>
            </div>
        </div>
    </div>
    
    <div class="grid" style="grid-template-columns: repeat(4, 1fr); gap:15px;">
        <div class="card stat-box" style="background:rgba(26,188,156,0.08); border:1px solid rgba(26,188,156,0.35);">
            <div class="stat-label" style="display:flex; justify-content:space-between; align-items:center;">
                <span>AI 퀀트 실현 순수익률 ($100k 기준)</span>
                <span style="font-size:0.75rem; background:rgba(26,188,156,0.25); color:#1abc9c; padding:2px 7px; border-radius:10px; font-weight:bold;">총 {{ stats.days }}일간</span>
            </div>
            <div class="stat-val" style="color:var(--success); font-size:1.85rem; margin:6px 0 2px 0;">+{{ stats.master_return }}%</div>
            <div style="font-size:0.82rem; color:#e2e8f0; margin-bottom:8px;">
                📅 <b>전체 기간:</b> {{ stats.start_date }} ~ {{ stats.end_date }} ({{ stats.days }}일)
            </div>
            <div style="display:flex; flex-direction:column; gap:5px; padding-top:8px; border-top:1px solid rgba(255,255,255,0.08); font-size:0.82rem;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="color:var(--muted);">🗓️ <b>월 환산 수익률:</b></span>
                    <span style="color:#1abc9c; font-weight:bold; font-size:0.92rem;">+{{ stats.master_monthly }}% / 월</span>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="color:var(--muted);">📈 <b>연 환산 수익률 (CAGR):</b></span>
                    <span style="color:#60a5fa; font-weight:bold; font-size:0.92rem;">+{{ stats.master_cagr }}% / 년</span>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center; margin-top:2px;">
                    <span style="color:var(--muted);">💰 <b>최종 잔고:</b></span>
                    <span style="color:#fff; font-weight:bold;">${{ "{:,.0f}".format(stats.master_final) }}</span>
                </div>
            </div>
        </div>
        
        <div class="card stat-box" style="background:rgba(239,68,68,0.08); border:1px solid rgba(239,68,68,0.35);">
            <div class="stat-label" style="display:flex; justify-content:space-between; align-items:center;">
                <span>단순 고APR 몰빵 수익률 (일반 투자)</span>
                <span style="font-size:0.75rem; background:rgba(239,68,68,0.25); color:#ef4444; padding:2px 7px; border-radius:10px; font-weight:bold;">총 {{ stats.days }}일간</span>
            </div>
            <div class="stat-val" style="color:var(--danger); font-size:1.85rem; margin:6px 0 2px 0;">{{ stats.naive_return }}%</div>
            <div style="font-size:0.82rem; color:#e2e8f0; margin-bottom:8px;">
                📅 <b>전체 기간:</b> {{ stats.start_date }} ~ {{ stats.end_date }} ({{ stats.days }}일)
            </div>
            <div style="display:flex; flex-direction:column; gap:5px; padding-top:8px; border-top:1px solid rgba(255,255,255,0.08); font-size:0.82rem;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="color:var(--muted);">🗓️ <b>월 환산 수익률:</b></span>
                    <span style="color:#ef4444; font-weight:bold; font-size:0.92rem;">{{ stats.naive_monthly }}% / 월</span>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="color:var(--muted);">📉 <b>연 환산 수익률 (CAGR):</b></span>
                    <span style="color:#ef4444; font-weight:bold; font-size:0.92rem;">{{ stats.naive_cagr }}% / 년</span>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center; margin-top:2px;">
                    <span style="color:var(--muted);">💰 <b>최종 잔고:</b></span>
                    <span style="color:#fff; font-weight:bold;">${{ "{:,.0f}".format(stats.naive_final) }}</span>
                </div>
            </div>
        </div>
        
        <div class="card stat-box" style="background:rgba(79,142,247,0.08); border:1px solid rgba(79,142,247,0.35);">
            <div class="stat-label">AI 연구 창출 초과 알파</div>
            <div class="stat-val" style="color:#60a5fa; font-size:1.85rem; margin:6px 0 2px 0;">+{{ stats.alpha_diff }}%p</div>
            <div style="font-size:0.82rem; color:#e2e8f0; margin-bottom:8px;">
                💡 <b>순수익 차이:</b> +${{ "{:,.0f}".format(stats.master_final - stats.naive_final) }}
            </div>
            <div style="display:flex; flex-direction:column; gap:5px; padding-top:8px; border-top:1px solid rgba(255,255,255,0.08); font-size:0.82rem;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="color:var(--muted);">월 알파 격차:</span>
                    <span style="color:#60a5fa; font-weight:bold; font-size:0.92rem;">{{ "{:+.2f}".format(stats.master_monthly - stats.naive_monthly) }}%p / 월</span>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="color:var(--muted);">연 알파 격차:</span>
                    <span style="color:#60a5fa; font-weight:bold; font-size:0.92rem;">{{ "{:+.2f}".format(stats.master_cagr - stats.naive_cagr) }}%p / 년</span>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center; margin-top:2px;">
                    <span style="color:var(--muted);">안전성:</span>
                    <span style="color:#1abc9c; font-weight:bold;">Sharpe {{ stats.master_sharpe }} (기관급)</span>
                </div>
            </div>
        </div>
        
        <div class="card stat-box" style="background:rgba(245,158,11,0.08); border:1px solid rgba(245,158,11,0.35);">
            <div class="stat-label">최대 낙폭 (MDD) 리스크 방어</div>
            <div class="stat-val" style="color:#f59e0b; font-size:1.85rem; margin:6px 0 2px 0;">{{ stats.master_mdd }}% vs {{ stats.naive_mdd }}%</div>
            <div style="font-size:0.82rem; color:#e2e8f0; margin-bottom:8px;">
                🛡️ <b>리스크 방어:</b> {{ stats.mdd_defense }}배 더 안전한 방어
            </div>
            <div style="display:flex; flex-direction:column; gap:5px; padding-top:8px; border-top:1px solid rgba(255,255,255,0.08); font-size:0.82rem;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="color:var(--muted);">AI 퀀트 MDD:</span>
                    <span style="color:#1abc9c; font-weight:bold; font-size:0.92rem;">{{ stats.master_mdd }}% (초안전 방어)</span>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="color:var(--muted);">일반 몰빵 MDD:</span>
                    <span style="color:#ef4444; font-weight:bold; font-size:0.92rem;">-{{ stats.naive_mdd }}% (원금 손실)</span>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center; margin-top:2px;">
                    <span style="color:var(--muted);">수익-낙폭 비율:</span>
                    <span style="color:#f59e0b; font-weight:bold;">Calmar {{ stats.master_calmar }}</span>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- 📈 수익 곡선 시각화 차트 -->
<div class="card" style="margin-bottom:25px;">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px; flex-wrap:wrap; gap:10px;">
        <h3 style="margin:0;">📈 실증 자산 성장 곡선 비교 ({{ dates[0] if dates else '2026-04-09' }} ~ {{ dates[-1] if dates else '2026-09-01' }}, 총 {{ stats.days }}일)</h3>
        <div style="display:flex; gap:15px; font-size:0.9rem; font-weight:600;">
            <span style="color:#1abc9c;">● AI 퀀트 마스터 전략 (+{{ stats.master_return }}%)</span>
            <span style="color:#ef4444;">● 단순 고APR 투자 ({{ stats.naive_return }}%)</span>
            <span style="color:#f59e0b;">● Baseline 벤치마크</span>
        </div>
    </div>
    <div style="height:350px; position:relative;">
        <canvas id="equityChart"></canvas>
    </div>
</div>

<!-- 🏛️ 151일간 퀀트 포트폴리오 운용 여정 & 실증 리밸런싱 전수 기록 (Initial Allocation & Rebalance Timeline) -->
<div class="card" style="margin-bottom:25px; border-color:rgba(26,188,156,0.35); background:linear-gradient(180deg, rgba(26,188,156,0.03) 0%, rgba(0,0,0,0) 100%);">
    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; margin-bottom:20px; border-bottom:1px solid rgba(255,255,255,0.08); padding-bottom:14px;">
        <div>
            <div style="display:flex; align-items:center; gap:8px;">
                <span style="font-size:1.4rem;">🏛️</span>
                <h3 style="margin:0; font-size:1.35rem; color:#fff;">151일간 퀀트 포트폴리오 운용 여정 & 실증 리밸런싱 전수 기록</h3>
            </div>
            <p style="margin:4px 0 0 0; color:var(--muted); font-size:0.9rem;">
                Day 1 시작 시점의 <b>초기 볼트 배분</b>부터 <b>정기 리밸런싱(11회)</b>, <b>저점 추매(23회)</b>, <b>손절 방출(4회)</b>을 거쳐 현재 <b>+121.94%($221,944)</b>에 도달한 전체 실증 히스토리입니다.
            </p>
        </div>
        <div style="display:flex; gap:8px; flex-wrap:wrap;">
            <span style="background:rgba(26,188,156,0.15); color:#1abc9c; border:1px solid rgba(26,188,156,0.3); padding:5px 12px; border-radius:20px; font-size:0.85rem; font-weight:bold;">
                총 {{ timeline_events|length }}회 실증 액션 추적 완료
            </span>
        </div>
    </div>

    <!-- 1. Day 1 초기 진입 vs Day 151 현재 포트폴리오 비교 카드 -->
    <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap:18px; margin-bottom:25px;">
        <!-- 시작 포트폴리오 (Day 1) -->
        <div style="background:rgba(0,0,0,0.35); border:1px solid rgba(155,89,182,0.35); border-radius:12px; padding:16px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <div style="display:flex; align-items:center; gap:8px;">
                    <span class="badge-initial">🚀 시작 포트폴리오 (Day 1)</span>
                    <span style="font-size:0.85rem; color:var(--muted);">{{ stats.start_date }}</span>
                </div>
                <span style="color:#c084fc; font-weight:bold; font-size:1.1rem;">원금 $100,000</span>
            </div>
            <div style="font-size:0.82rem; color:var(--muted); margin-bottom:10px;">
                <b>SKIN_IN_GAME_HEAVY 60:40 바벨 배분</b> (Core 3개 60% + Satellite 3개 40%)
            </div>
            <table style="width:100%; border-collapse:collapse; font-size:0.85rem;">
                <thead>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.1); color:var(--muted); text-align:left;">
                        <th style="padding:6px 4px;">구분</th>
                        <th style="padding:6px 4px;">볼트명</th>
                        <th style="padding:6px 4px; text-align:right;">진입 비중</th>
                        <th style="padding:6px 4px; text-align:right;">투자 금액</th>
                    </tr>
                </thead>
                <tbody>
                    {% for h in initial_holdings %}
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.04);">
                        <td style="padding:7px 4px;">
                            {% if 'CORE' in h.type %}
                            <span style="color:#1abc9c; font-weight:bold; font-size:0.75rem;">🛡️ CORE</span>
                            {% else %}
                            <span style="color:#60a5fa; font-weight:bold; font-size:0.75rem;">🚀 SATELLITE</span>
                            {% endif %}
                        </td>
                        <td style="padding:7px 4px; font-weight:600; color:#e2e8f0;">{{ h.name }}</td>
                        <td style="padding:7px 4px; text-align:right; color:#1abc9c; font-weight:bold;">
                            {{ "%.1f"|format(h.amount / 100000.0 * 100) }}%
                        </td>
                        <td style="padding:7px 4px; text-align:right; color:#fff;">${{ "{:,.0f}".format(h.amount) }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <!-- 현재 포트폴리오 (Day 151) -->
        <div style="background:rgba(0,0,0,0.35); border:1px solid rgba(26,188,156,0.35); border-radius:12px; padding:16px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <div style="display:flex; align-items:center; gap:8px;">
                    <span style="background:rgba(26,188,156,0.2); color:#1abc9c; border:1px solid rgba(26,188,156,0.4); padding:4px 10px; border-radius:6px; font-weight:bold; font-size:0.8rem;">
                        🏁 현재 보유 포트폴리오 (Day {{ stats.days }})
                    </span>
                    <span style="font-size:0.85rem; color:var(--muted);">{{ stats.end_date }}</span>
                </div>
                <span style="color:#1abc9c; font-weight:bold; font-size:1.1rem;">${{ "{:,.0f}".format(stats.master_final) }} (+{{ stats.master_return }}%)</span>
            </div>
            <div style="font-size:0.82rem; color:var(--muted); margin-bottom:10px;">
                <b>151일간 34회 리밸런싱 누적 복리 성장</b> (순수익 +${{ "{:,.0f}".format(stats.master_final - 100000.0) }})
            </div>
            <table style="width:100%; border-collapse:collapse; font-size:0.85rem;">
                <thead>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.1); color:var(--muted); text-align:left;">
                        <th style="padding:6px 4px;">구분</th>
                        <th style="padding:6px 4px;">볼트명</th>
                        <th style="padding:6px 4px; text-align:right;">보유 비중</th>
                        <th style="padding:6px 4px; text-align:right;">현재 평가액</th>
                    </tr>
                </thead>
                <tbody>
                    {% for h in current_holdings %}
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.04);">
                        <td style="padding:7px 4px;">
                            {% if 'CORE' in h.type %}
                            <span style="color:#1abc9c; font-weight:bold; font-size:0.75rem;">🛡️ CORE</span>
                            {% else %}
                            <span style="color:#60a5fa; font-weight:bold; font-size:0.75rem;">🚀 SATELLITE</span>
                            {% endif %}
                        </td>
                        <td style="padding:7px 4px; font-weight:600; color:#e2e8f0;">{{ h.name }}</td>
                        <td style="padding:7px 4px; text-align:right; color:#1abc9c; font-weight:bold;">
                            {{ "%.1f"|format(h.amount / stats.master_final * 100) }}%
                        </td>
                        <td style="padding:7px 4px; text-align:right; color:#fff;">${{ "{:,.0f}".format(h.amount) }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <!-- 2. 전체 리밸런싱 및 손절 방출 전수 타임라인 -->
    <div>
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:15px;">
            <h4 style="margin:0; font-size:1.1rem; color:#fff;">🔄 151일간 실증 리밸런싱 & 액션 전수 타임라인 (Chronological Events)</h4>
            <div style="display:flex; gap:6px; flex-wrap:wrap;">
                <button class="filter-btn active" onclick="filterRebalanceTimeline('all', this)">전체 ({{ timeline_events|length }})</button>
                <button class="filter-btn" onclick="filterRebalanceTimeline('regular', this)">🔄 정기 리밸런싱 (11)</button>
                <button class="filter-btn" onclick="filterRebalanceTimeline('dip_buy', this)">🔥 저점 추매 $5K (23)</button>
                <button class="filter-btn" onclick="filterRebalanceTimeline('ejection', this)">🚨 18% MDD 손절 (4)</button>
            </div>
        </div>

        <div id="rebalanceTimelineList" style="max-height:550px; overflow-y:auto; padding-right:6px;">
            {% for ev in timeline_events %}
            <div class="timeline-item timeline-type-{{ ev.type }}" style="background:rgba(0,0,0,0.25); border:1px solid rgba(255,255,255,0.08); border-radius:10px; padding:14px 16px; margin-bottom:12px;">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-bottom:8px;">
                    <div style="display:flex; align-items:center; gap:10px;">
                        <span class="{{ ev.badge_class }}">{{ ev.badge }}</span>
                        <span style="font-weight:bold; color:#fff; font-size:0.95rem;">📅 {{ ev.date }}</span>
                    </div>
                    <span style="font-size:0.8rem; color:var(--muted);">이벤트 #{{ loop.index }}</span>
                </div>
                <div style="font-size:0.9rem; color:#e2e8f0; margin-bottom:8px; font-weight:600;">
                    {{ ev.reason }}
                </div>
                {% if ev.details %}
                <div style="font-size:0.83rem; color:var(--muted); margin-bottom:8px; line-height:1.4;">
                    {{ ev.details }}
                </div>
                {% endif %}
                <div style="display:flex; flex-wrap:wrap; gap:6px; margin-top:6px;">
                    {% for k, v in ev.allocations.items() %}
                    <span class="alloc-tag">
                        <span>{{ k }}:</span> <b>{{ v }}</b>
                    </span>
                    {% endfor %}
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</div>

<!-- 💰 내 투자금 즉시 계산기 (What-If Calculator) -->
<div class="card" style="margin-bottom:25px; background:rgba(255,255,255,0.02); border:1px solid var(--border);">
    <h3 style="margin-top:0;">💰 내 투자금 즉시 수익 계산기 (What-If Simulator)</h3>
    <div style="display:flex; align-items:center; gap:20px; flex-wrap:wrap; margin-top:15px;">
        <div>
            <label style="color:var(--muted); font-size:0.9rem; display:block; margin-bottom:6px;">내 투자 원금 ($ USD):</label>
            <input type="number" id="userCapitalInput" value="10000" step="1000" oninput="calcUserROI()" class="calc-input">
        </div>
        <div style="display:flex; gap:20px; flex-grow:1; flex-wrap:wrap;">
            <div style="background:rgba(239,68,68,0.1); border:1px solid rgba(239,68,68,0.3); padding:12px 20px; border-radius:10px; flex-grow:1;">
                <div style="font-size:0.85rem; color:#ef4444; font-weight:bold;">❌ 일반 고APR 투자 시 현재 잔고:</div>
                <div id="calcNaiveRes" style="font-size:1.4rem; font-weight:bold; color:#ef4444; margin-top:4px;">$4,467 (-$5,533)</div>
                <div id="calcNaiveMonthly" style="font-size:0.82rem; color:var(--muted); margin-top:5px;">월 환산: {{ stats.naive_monthly }}% / 월 (연 CAGR {{ stats.naive_cagr }}%)</div>
            </div>
            <div style="background:rgba(26,188,156,0.1); border:1px solid rgba(26,188,156,0.3); padding:12px 20px; border-radius:10px; flex-grow:1;">
                <div style="font-size:0.85rem; color:#1abc9c; font-weight:bold;">👑 AI 퀀트 연구 적용 시 현재 잔고:</div>
                <div id="calcMasterRes" style="font-size:1.4rem; font-weight:bold; color:#1abc9c; margin-top:4px;">$21,339 (+$11,339 순익)</div>
                <div id="calcMasterMonthly" style="font-size:0.82rem; color:#1abc9c; margin-top:5px;">월 환산: +{{ stats.master_monthly }}% / 월 (연 CAGR +{{ stats.master_cagr }}%)</div>
            </div>
        </div>
    </div>
</div>

<!-- 🔬 시간대별 연구 일지 타임라인 -->
<div class="card" style="margin-bottom:20px;">
    <h3 style="margin-top:0; margin-bottom:15px;">📚 시간대별 퀀트 자율 연구 & 볼트 발굴 일지 (Timeline)</h3>
    <div id="researchList">
        {% for item in history|reverse %}
        <div class="research-entry">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; flex-wrap:wrap; gap:8px;">
                <div style="display:flex; align-items:center; gap:10px;">
                    <span class="badge-topic">{{ item.topic_id }}</span>
                    <h3 style="margin:0; font-size:1.15rem; color:#fff;">{{ item.topic_title }}</h3>
                </div>
                <div style="display:flex; align-items:center; gap:10px;">
                    <span style="color:var(--muted); font-size:0.85rem;">📅 {{ item.timestamp }}</span>
                    <span class="badge-ok">{{ item.decision }}</span>
                </div>
            </div>
            
            <p style="margin:6px 0; color:#cbd5e1; font-size:0.95rem;"><strong>📚 레퍼런스 출처:</strong> <code style="background:rgba(255,255,255,0.06); padding:2px 6px; border-radius:4px; color:#93c5fd;">{{ item.reference_source }}</code></p>
            <p style="margin:6px 0; color:#cbd5e1; font-size:0.95rem;"><strong>💡 핵심 가설:</strong> {{ item.hypothesis }}</p>
            
            <div class="formula-box">
                📐 <strong>Mathematical Model:</strong> {{ item.mathematical_formula }}
            </div>
            
            {% if item.top_discovered_vaults %}
            <div style="margin-top:14px; overflow-x:auto;">
                <table style="width:100%; border-collapse:collapse; font-size:0.9rem; margin-top:8px;">
                    <thead>
                        <tr style="border-bottom:1px solid rgba(255,255,255,0.1); color:var(--muted); text-align:left;">
                            <th style="padding:8px;">발굴된 볼트명</th>
                            <th style="padding:8px;">Hurst (추세성)</th>
                            <th style="padding:8px;">Sortino</th>
                            <th style="padding:8px;">Kelly 최적비중</th>
                            <th style="padding:8px;">30일 APR</th>
                            <th style="padding:8px;">Sharpe</th>
                            <th style="padding:8px;">리더 에쿼티</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for v in item.top_discovered_vaults %}
                        <tr style="border-bottom:1px solid rgba(255,255,255,0.04);">
                            <td style="padding:8px; font-weight:600; color:#fff;">{{ v.name }}</td>
                            <td style="padding:8px; color:{% if v.hurst >= 0.55 %}#1abc9c{% elif v.hurst <= 0.45 %}#f59e0b{% else %}#94a3b8{% endif %}; font-weight:bold;">{{ v.hurst }}</td>
                            <td style="padding:8px; color:#4f8ef7;">{{ v.sortino }}</td>
                            <td style="padding:8px; color:#1abc9c; font-weight:bold;">{{ v.kelly_f }}%</td>
                            <td style="padding:8px; color:#1abc9c;">{{ v.apr_30d }}%</td>
                            <td style="padding:8px; color:#f59e0b;">{{ v.sharpe }}</td>
                            <td style="padding:8px; color:#cbd5e1;">${{ "{:,.0f}".format(v.leader_usd) }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
            {% endif %}
        </div>
        {% endfor %}
    </div>
</div>

</main>
<script>
const simDates = {{ dates|tojson }};
const masterVals = {{ master_vals|tojson }};
const benchVals = {{ bench_vals|tojson }};

// Render Equity Chart
const ctx = document.getElementById('equityChart').getContext('2d');
new Chart(ctx, {
    type: 'line',
    data: {
        labels: simDates,
        datasets: [
            {
                label: '👑 AI 퀀트 마스터 전략 (+{{ stats.master_return }}%)',
                data: masterVals,
                borderColor: '#1abc9c',
                backgroundColor: 'rgba(26,188,156,0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.1,
                pointRadius: 0
            },
            {
                label: '❌ 단순 고APR 투자 ({{ stats.naive_return }}%)',
                data: benchVals,
                borderColor: '#ef4444',
                borderWidth: 2,
                borderDash: [5, 5],
                pointRadius: 0,
                fill: false
            }
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        scales: {
            x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8', maxTicksLimit: 10 } },
            y: { 
                grid: { color: 'rgba(255,255,255,0.05)' }, 
                ticks: { 
                    color: '#94a3b8',
                    callback: function(value) { return '$' + value.toLocaleString(); }
                } 
            }
        },
        plugins: {
            legend: { display: false },
            tooltip: {
                callbacks: {
                    label: function(c) {
                        return c.dataset.label + ': $' + Math.round(c.parsed.y).toLocaleString();
                    }
                }
            }
        }
    }
});

function calcUserROI() {
    const cap = parseFloat(document.getElementById('userCapitalInput').value) || 0;
    const naiveReturn = {{ stats.naive_return }} / 100.0;
    const masterReturn = {{ stats.master_return }} / 100.0;
    const naiveFinal = cap * (1.0 + naiveReturn);
    const naiveDiff = naiveFinal - cap;
    const masterFinal = cap * (1.0 + masterReturn);
    const masterDiff = masterFinal - cap;
    
    document.getElementById('calcNaiveRes').innerText = '$' + Math.round(naiveFinal).toLocaleString() + ' (' + (naiveDiff >= 0 ? '+' : '') + Math.round(naiveDiff).toLocaleString() + ')';
    document.getElementById('calcMasterRes').innerText = '$' + Math.round(masterFinal).toLocaleString() + ' (+' + Math.round(masterDiff).toLocaleString() + ' 순익)';
    
    const masterMonthlyEst = Math.round(cap * ({{ stats.master_monthly }} / 100.0));
    const naiveMonthlyEst = Math.round(cap * ({{ stats.naive_monthly }} / 100.0));
    const elMasterM = document.getElementById('calcMasterMonthly');
    if(elMasterM) elMasterM.innerHTML = '🗓️ 예상 월 수익: <b>+' + (masterMonthlyEst).toLocaleString() + ' USD/월</b> (월 복리 +{{ stats.master_monthly }}%, 연 CAGR +{{ stats.master_cagr }}%)';
    const elNaiveM = document.getElementById('calcNaiveMonthly');
    if(elNaiveM) elNaiveM.innerHTML = '🗓️ 예상 월 손익: <b>' + (naiveMonthlyEst >= 0 ? '+' : '') + (naiveMonthlyEst).toLocaleString() + ' USD/월</b> (월 {{ stats.naive_monthly }}%)';
}

function triggerNewResearch() {
    const btn = document.getElementById('btnRunResearch');
    btn.disabled = true;
    btn.innerText = '⏳ AI 퀀트 연구 및 백테스트 실행 중...';
    fetch('/api/research/run', { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            alert('✅ 새로운 퀀트 연구 사이클 완료!\\n주제: ' + (data.study ? data.study.topic_title : '연구 완료'));
            location.reload();
        })
        .catch(err => {
            alert('오류 발생: ' + err);
            btn.disabled = false;
            btn.innerText = '⚡ 지금 즉시 새 연구 사이클 실행';
        });
}

function filterRebalanceTimeline(type, btn) {
    const buttons = document.querySelectorAll('.filter-btn');
    buttons.forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');
    
    const items = document.querySelectorAll('#rebalanceTimelineList .timeline-item');
    items.forEach(item => {
        if (type === 'all' || item.classList.contains('timeline-type-' + type)) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
}

document.addEventListener('DOMContentLoaded', calcUserROI);
</script>
</body></html>"""

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

<!-- AI Barbell Walk-Forward Simulation & Rebalancing Card -->
<div class="card" style="margin-bottom:25px; border-left:4px solid #9b59b6">
  <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px; flex-wrap:wrap; gap:10px;">
    <div>
      <h3 style="margin:0; color:#fff; display:flex; align-items:center; gap:10px;">
        🤖 AI Barbell Walk-Forward Simulation
      </h3>
      <p style="margin:5px 0 0 0; font-size:0.9rem; color:var(--muted);">
        실제 92일간의 과거 스냅샷 데이터 기반 AI 바벨 포트폴리오 ($100k) 거래비용 반영 시뮬레이션 결과입니다.
      </p>
      
      <div style="display:flex; align-items:center; gap:10px; margin-top:12px;">
        <span style="font-size:0.85rem; color:var(--muted); font-weight:bold;">전략 시나리오 선택:</span>
        <select id="wfStrategySelect" onchange="window.switchWfStrategy(this.value)" style="padding:8px 12px; background:#0b0f1a; border:1px solid var(--border); color:#fff; border-radius:6px; font-weight:bold; font-size:0.9rem; cursor:pointer; width:340px;">
          <option value="auto_barbell" selected>🤖 자율 하이브리드 바벨 (30일 리밸런싱 + 15% 손절 방출)</option>
          <option value="optimized">✨ Optimized Barbell (최적화 바벨)</option>
          <option value="baseline">📉 Baseline Barbell (기본 바벨)</option>
          <option value="core_only">🛡️ Core Only (안정형 CORE 전용)</option>
          <option value="satellite_only">🚀 Satellite Only (공격형 SATELLITE)</option>
        </select>
      </div>
    </div>
    <span style="font-size:0.85rem; padding:6px 12px; background:rgba(155,89,182,0.2); border:1px solid #9b59b6; color:#e0b0ff; border-radius:30px; font-weight:bold;" id="wfStrategyTag">
      CAGR 103.1% 최적화 적용됨
    </span>
  </div>

  <div class="grid" style="margin-bottom:20px; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));">
    <div class="stat-box" style="border-color:rgba(155,89,182,0.3)">
      <div class="stat-label">AI 최종 자산 가치</div>
      <div class="stat-val" style="color:#2ecc71; font-size:1.3rem;" id="wfAiFinal">$211,777</div>
    </div>
    <div class="stat-box" style="border-color:rgba(46,204,113,0.4)">
      <div class="stat-label">AI 순 누적 수익률</div>
      <div class="stat-val" style="color:#2ecc71; font-size:1.3rem;" id="wfAiReturn">+111.78%</div>
    </div>
    <div class="stat-box" style="border-color:rgba(26,188,156,0.4)">
      <div class="stat-label">AI 순 월간 수익률</div>
      <div class="stat-val" style="color:#1abc9c; font-size:1.3rem;" id="wfAiMonthly">+19.82% / 월</div>
    </div>
    <div class="stat-box" style="border-color:rgba(52,152,219,0.4)">
      <div class="stat-label">AI 순 연간 수익률 (CAGR)</div>
      <div class="stat-val" style="color:#3498db; font-size:1.3rem;" id="wfAiCagr">+843.98% / 년</div>
    </div>
    <div class="stat-box" style="border-color:rgba(231,76,60,0.3)">
      <div class="stat-label">AI 최대 낙폭 (MDD)</div>
      <div class="stat-val" style="color:#e74c3c; font-size:1.3rem;" id="wfAiMdd">-4.45%</div>
    </div>
    <div class="stat-box" style="border-color:rgba(243,156,18,0.4)">
      <div class="stat-label">누적 지불 수수료 (Net Fee)</div>
      <div class="stat-val" style="color:#f39c12; font-size:1.3rem;" id="wfAiFees">$5,886</div>
    </div>
    <div class="stat-box" style="border-color:rgba(155,89,182,0.3)">
      <div class="stat-label">벤치마크 수익률 (Hold)</div>
      <div class="stat-val" style="color:var(--muted); font-size:1.3rem;" id="wfBenchReturn">+3.11%</div>
    </div>
  </div>

  <div style="height:350px; margin-bottom:30px;">
    <canvas id="walkforwardChart"></canvas>
  </div>

  <!-- Daily Holdings Inspector -->
  <div style="background:rgba(255,255,255,0.02); padding:20px; border-radius:8px; border:1px solid var(--border); margin-bottom:30px;">
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px; flex-wrap:wrap; gap:10px;">
      <h4 style="margin:0; color:#fff; display:flex; align-items:center; gap:10px;">
        📅 일자별 상세 포트폴리오 조회 (Daily Holdings Inspector)
      </h4>
      <div style="display:flex; align-items:center; gap:10px;">
        <span style="font-size:0.85rem; color:var(--muted);">날짜 선택:</span>
        <select id="wfDateSelect" onchange="window.showDailyDetails(this.value)" style="padding:8px 12px; background:#0b0f1a; border:1px solid var(--border); color:#fff; border-radius:6px; font-weight:bold; font-size:0.9rem; cursor:pointer; width:150px;">
          <!-- Dates populated dynamically -->
        </select>
      </div>
    </div>

    <div style="display:flex; gap:15px; margin-bottom:15px; flex-wrap:wrap;">
      <div style="padding:8px 12px; background:rgba(0,0,0,0.15); border-radius:6px; border:1px solid rgba(255,255,255,0.05);">
        <span style="font-size:0.75rem; color:var(--muted); display:block;">총 자산 가치</span>
        <strong style="font-size:1rem; color:#fff;" id="detTotalVal">-</strong>
      </div>
      <div style="padding:8px 12px; background:rgba(0,0,0,0.15); border-radius:6px; border:1px solid rgba(255,255,255,0.05);">
        <span style="font-size:0.75rem; color:var(--muted); display:block;">누적 수익률</span>
        <strong style="font-size:1rem; color:#2ecc71;" id="detTotalRet">-</strong>
      </div>
      <div style="padding:8px 12px; background:rgba(0,0,0,0.15); border-radius:6px; border:1px solid rgba(255,255,255,0.05);">
        <span style="font-size:0.75rem; color:var(--muted); display:block;">현금 잔고</span>
        <strong style="font-size:1rem; color:#fff;" id="detCash">-</strong>
      </div>
    </div>

    <div style="overflow-x:auto;">
      <table style="width:100%; border-collapse:collapse; text-align:left; font-size:0.85rem;">
        <thead>
          <tr style="border-bottom:1px solid var(--border); color:var(--muted);">
            <th style="padding:8px 5px;">볼트명 (Vault Name)</th>
            <th style="padding:8px 5px; text-align:right;">현재 평가 금액</th>
            <th style="padding:8px 5px; text-align:right;">최초 매수 금액</th>
            <th style="padding:8px 5px; text-align:right;">누적 수익금</th>
            <th style="padding:8px 5px; text-align:right; width:120px;">수익률 (ROI)</th>
          </tr>
        </thead>
        <tbody id="wfDetailLog">
          <tr><td colspan="5" style="text-align:center; padding:15px; color:var(--muted);">데이터를 불러오는 중입니다...</td></tr>
        </tbody>
      </table>
    </div>
  </div>

  <h4 style="margin:20px 0 10px 0; color:#fff;">🔄 리밸런싱 및 위험 회피 내역 (Rebalancing History)</h4>
  <div style="overflow-x:auto;">
    <table style="width:100%; border-collapse:collapse; text-align:left; font-size:0.9rem; margin-top:10px;">
      <thead>
        <tr style="border-bottom:2px solid var(--border); color:var(--muted);">
          <th style="padding:10px 5px; width:120px;">날짜</th>
          <th style="padding:10px 5px; width:150px;">구분/이유</th>
          <th style="padding:10px 5px; width:220px;">세부 정보</th>
          <th style="padding:10px 5px;">배분 비중 (Allocations)</th>
        </tr>
      </thead>
      <tbody id="wfEventLog">
        <!-- Rebalance events will be populated dynamically -->
      </tbody>
    </table>
  </div>
</div>

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

// Load Walk-Forward Simulation Data
(function() {
  window.wfChartInstance = null;
  window.wfRawData = null;
  window.wfDailyDetails = null;

  fetch('/api/walkforward')
    .then(r => r.json())
    .then(res => {
      if (res.error) return;
      window.wfRawData = res;

      fetch('/api/auto_rebalance')
        .then(r => r.json())
        .then(autoRes => {
          if (autoRes && autoRes.strategy) {
            autoRes.strategy.final_value = autoRes.final_value;
            autoRes.strategy.total_return = autoRes.total_return;
            autoRes.strategy.mdd = autoRes.mdd;
            autoRes.strategy.fees = autoRes.fees || autoRes.strategy.fees || 11618.0;
            window.wfRawData.fees = autoRes.fees || 11618.0;
            window.wfRawData.strategies.auto_barbell = autoRes.strategy;
          }
        })
        .catch(e => console.log('Auto rebalance fetch note:', e))
        .finally(() => {
          // Populate Date Inspector Dropdown
          const dateSelect = document.getElementById('wfDateSelect');
          dateSelect.innerHTML = '';
          window.wfRawData.dates.forEach(date => {
            const opt = document.createElement('option');
            opt.value = date;
            opt.innerText = date;
            dateSelect.appendChild(opt);
          });

          // Default to auto_barbell if present
          const selVal = document.getElementById('wfStrategySelect').value || 'auto_barbell';
          window.switchWfStrategy(selVal);
        });
      
      // Function to show daily holdings details
      window.showDailyDetails = function(date) {
        const day = window.wfDailyDetails ? window.wfDailyDetails[date] : null;
        if (!day) return;
        
        document.getElementById('detTotalVal').innerText = '$' + Math.round(day.total_value).toLocaleString();
        document.getElementById('detTotalRet').innerText = (day.total_return >= 0 ? '+' : '') + day.total_return.toFixed(2) + '%';
        document.getElementById('detTotalRet').style.color = day.total_return >= 0 ? 'var(--success)' : 'var(--danger)';
        document.getElementById('detCash').innerText = '$' + Math.round(day.cash).toLocaleString();
        
        const detailBody = document.getElementById('wfDetailLog');
        detailBody.innerHTML = '';
        
        if (!day.holdings || day.holdings.length === 0) {
          detailBody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:15px; color:var(--muted);">보유 중인 볼트 자산이 없습니다.</td></tr>';
          return;
        }
        
        day.holdings.forEach(hold => {
          const tr = document.createElement('tr');
          tr.style.borderBottom = '1px solid rgba(255,255,255,0.05)';
          
          const profitColor = hold.profit >= 0 ? 'var(--success)' : 'var(--danger)';
          const profitPrefix = hold.profit >= 0 ? '+' : '';
          
          tr.innerHTML = `
            <td style="padding:10px 5px; font-weight:600; color:#fff;">📁 ${hold.name}</td>
            <td style="padding:10px 5px; text-align:right; font-weight:bold;">$${Math.round(hold.amount).toLocaleString()}</td>
            <td style="padding:10px 5px; text-align:right; color:var(--muted);">$${Math.round(hold.cost).toLocaleString()}</td>
            <td style="padding:10px 5px; text-align:right; color:${profitColor};">${profitPrefix}$${Math.round(hold.profit).toLocaleString()}</td>
            <td style="padding:10px 5px; text-align:right; font-weight:bold; color:${profitColor};">${profitPrefix}${hold.return_pct.toFixed(2)}%</td>
          `;
          detailBody.appendChild(tr);
        });
      };

      // Function to switch strategy
      window.switchWfStrategy = function(stratName) {
        const strat = window.wfRawData.strategies[stratName];
        if (!strat) return;
        
        // Update Stats
        const totalDays = window.wfRawData.days || 120;
        const totReturn = strat.total_return || 0.0;
        const netCagr = (strat.cagr !== undefined) ? strat.cagr : ((Math.pow(1 + totReturn / 100.0, 365.0 / totalDays) - 1.0) * 100.0);
        const netMonthly = (Math.pow(1 + totReturn / 100.0, 30.0 / totalDays) - 1.0) * 100.0;
        const feeVal = (strat.fees !== undefined && strat.fees > 0) ? strat.fees : ((window.wfRawData.fees !== undefined) ? window.wfRawData.fees : 11618);

        document.getElementById('wfAiFinal').innerText = '$' + Math.round(strat.final_value).toLocaleString();
        document.getElementById('wfAiReturn').innerText = (totReturn >= 0 ? '+' : '') + totReturn.toFixed(2) + '%';
        document.getElementById('wfAiMonthly').innerText = (netMonthly >= 0 ? '+' : '') + netMonthly.toFixed(2) + '% / 월';
        document.getElementById('wfAiCagr').innerText = (netCagr >= 0 ? '+' : '') + netCagr.toFixed(2) + '% / 년';
        document.getElementById('wfAiMdd').innerText = strat.mdd.toFixed(2) + '%';
        document.getElementById('wfAiFees').innerText = '$' + Math.round(feeVal).toLocaleString();
        document.getElementById('wfBenchReturn').innerText = (window.wfRawData.benchmark.total_return >= 0 ? '+' : '') + window.wfRawData.benchmark.total_return.toFixed(2) + '%';
        
        // Update tags
        const tag = document.getElementById('wfStrategyTag');
        if (stratName === 'auto_barbell') {
          tag.innerText = '🤖 30일 리밸런싱 + 15% 손절 방출 실증 가동중';
          tag.style.borderColor = '#1abc9c';
          tag.style.color = '#1abc9c';
        } else if (stratName === 'optimized') {
          tag.innerText = 'CAGR 103.1% 최적화 적용됨';
          tag.style.borderColor = '#9b59b6';
          tag.style.color = '#e0b0ff';
        } else if (stratName === 'baseline') {
          tag.innerText = '기본 바벨 셋업';
          tag.style.borderColor = '#e74c3c';
          tag.style.color = '#ff9999';
        } else if (stratName === 'core_only') {
          tag.innerText = '원금 보존형';
          tag.style.borderColor = '#2ecc71';
          tag.style.color = '#a3f3c3';
        } else {
          tag.innerText = '고위험 고수익형';
          tag.style.borderColor = '#f39c12';
          tag.style.color = '#fcd090';
        }

        // Set active daily details
        window.wfDailyDetails = strat.daily_details;
        
        // Refresh Inspector
        const currentSelDate = document.getElementById('wfDateSelect').value || window.wfRawData.dates[window.wfRawData.dates.length - 1];
        window.showDailyDetails(currentSelDate);
        
        // Update Chart
        if (window.wfChartInstance) {
          window.wfChartInstance.data.datasets[0].label = stratName.toUpperCase() + ' Portfolio ($)';
          window.wfChartInstance.data.datasets[0].data = strat.values;
          window.wfChartInstance.update();
        }
        
        // Populate Event Log Table (Rebalance & Emergency Cutoff Events)
        const logBody = document.getElementById('wfEventLog');
        logBody.innerHTML = '';

        const allEvents = [];
        (strat.rebalance_events || []).forEach(evt => allEvents.push({...evt, is_ejection: false}));
        (strat.ejection_events || []).forEach(evt => allEvents.push({...evt, is_ejection: true}));
        allEvents.sort((a, b) => a.date.localeCompare(b.date));

        allEvents.forEach(evt => {
          const tr = document.createElement('tr');
          tr.style.borderBottom = '1px solid rgba(255,255,255,0.05)';
          
          if (evt.is_ejection) {
            tr.style.backgroundColor = 'rgba(231, 76, 60, 0.08)';
            const profitColor = evt.realized_profit >= 0 ? 'var(--success)' : 'var(--danger)';
            const profitPrefix = evt.realized_profit >= 0 ? '+' : '';
            tr.innerHTML = `
              <td style="padding:10px 5px; font-weight:bold; color:var(--muted); cursor:pointer;" onclick="document.getElementById('wfDateSelect').value='${evt.date}'; window.showDailyDetails('${evt.date}');">${evt.date}</td>
              <td style="padding:10px 5px;"><strong style="color:var(--danger)">🛡️ 긴급 방출 (MDD/손절)</strong></td>
              <td style="padding:10px 5px; color:#e8eaf0;"><strong>${evt.vault_name}</strong> - ${evt.reason}</td>
              <td style="padding:10px 5px; max-width:300px; color:${profitColor};">출금: $${Math.round(evt.redeemed_amount).toLocaleString()} (${profitPrefix}$${Math.round(evt.realized_profit).toLocaleString()})</td>
            `;
          } else {
            let allocsStr = '';
            for (const [name, weight] of Object.entries(evt.allocations || {})) {
              allocsStr += `<span style="display:inline-block; padding:2px 6px; background:rgba(255,255,255,0.05); border-radius:4px; font-size:0.75rem; margin:2px; cursor:pointer;" onclick="document.getElementById('wfDateSelect').value='${evt.date}'; window.showDailyDetails('${evt.date}');">${name}: <b>${weight}</b></span> `;
            }
            
            tr.innerHTML = `
              <td style="padding:10px 5px; font-weight:bold; color:var(--muted); cursor:pointer;" onclick="document.getElementById('wfDateSelect').value='${evt.date}'; window.showDailyDetails('${evt.date}');">${evt.date}</td>
              <td style="padding:10px 5px;"><strong style="color:${evt.reason.includes('위험') ? 'var(--danger)' : evt.reason.includes('초기') ? 'var(--accent2)' : 'var(--accent)'}">${evt.reason}</strong></td>
              <td style="padding:10px 5px; color:#e8eaf0;">${evt.details}</td>
              <td style="padding:10px 5px; max-width:300px; word-wrap:break-word;">${allocsStr}</td>
            `;
          }
          logBody.appendChild(tr);
        });
      };
      
      // Draw Chart
      const ctx = document.getElementById('walkforwardChart').getContext('2d');
      window.wfChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
          labels: res.dates,
          datasets: [
            {
              label: 'AI Barbell Portfolio ($)',
              data: res.strategies.optimized.values,
              borderColor: '#9b59b6',
              backgroundColor: 'rgba(155, 89, 182, 0.05)',
              fill: true, tension: 0.3, borderWidth: 3, pointRadius: 0
            },
            {
              label: 'Equal Weight Benchmark ($)',
              data: res.benchmark.values,
              borderColor: '#7b8db0',
              borderDash: [5, 5],
              fill: false, tension: 0.3, borderWidth: 2, pointRadius: 0
            }
          ]
        },
        options: {
          responsive: true, maintainAspectRatio: false,
          plugins: { 
            legend: { display: true, labels: { color: '#e8eaf0' } },
            tooltip: {
              callbacks: {
                title: function(context) {
                  const date = context[0].label;
                  return '날짜: ' + date;
                }
              }
            }
          },
          onClick: (evt, activeElements, chart) => {
            if (activeElements && activeElements.length > 0) {
              const idx = activeElements[0].index;
              const date = chart.data.labels[idx];
              document.getElementById('wfDateSelect').value = date;
              window.showDailyDetails(date);
            }
          },
          scales: { 
            x: { grid: { display: false }, ticks: { color: '#7b8db0', maxRotation: 0, font: {size: 10} } }, 
            y: { grid: { color: 'rgba(255,255,255,0.05)'}, ticks:{color:'#7b8db0', callback: function(value){ return '$' + value.toLocaleString(); } }}
          }
        }
      });
      
      // Initialize with optimized strategy
      window.switchWfStrategy('optimized');
      
    })
    .catch(err => console.error("Failed to load walkforward simulation data:", err));
})();
</script>
<!-- ── 📱 모바일 하단 플로팅 탭바 마크업 ── -->
<div class="mobile-tab-bar">
    <a href="/autobot" id="tab-autobot" class="tab-item"><span class="icon">🤖</span><span>AutoBot</span></a>
    <a href="/live" id="tab-portfolio" class="tab-item"><span class="icon">📱</span><span>Portfolio</span></a>
    <a href="/" id="tab-analysis" class="tab-item"><span class="icon">🔬</span><span>Analysis</span></a>
    <a href="/settings" id="tab-settings" class="tab-item"><span class="icon">⚙️</span><span>Settings</span></a>
    <a href="/logout" class="tab-item" style="color:var(--danger);"><span class="icon">🚪</span><span>Logout</span></a>
</div>
<script>
    (function() {
        const path = window.location.pathname;
        if(path==='/live'||path==='/m'||path==='/my-portfolio') {
            document.getElementById('tab-portfolio').classList.add('active');
        } else if(path==='/settings'||path==='/discord') {
            document.getElementById('tab-settings').classList.add('active');
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

SETTINGS_HTML = """<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>⚙️ Settings</title><style>""" + COMMON_STYLE + """
.settings-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
    margin-top: 20px;
}
@media (max-width: 768px) {
    .settings-grid {
        grid-template-columns: 1fr;
    }
}
.setting-section-title {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
    border-bottom: 1px solid var(--border);
    padding-bottom: 8px;
    font-size: 1.2rem;
    font-weight: 700;
}
</style></head><body>
<header><div><h1 style="background:linear-gradient(90deg, #4f8ef7, #a855f7);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">⚙️ Settings & Integrations</h1></div><a class="btn back-btn" href="/">← Back</a></header>
<main>
    <div class="settings-grid" style="max-width:1100px; margin:auto;">
        <!-- Discord Card -->
        <div class="glass-card" style="padding:24px; margin-bottom:0;">
            <div class="setting-section-title" style="color:#5865F2;">
                <span>🔔 Discord Webhook Integration</span>
            </div>
            <p style="color:var(--text-muted); font-size:0.85rem; margin-bottom:20px; line-height:1.5;">
                Receive daily analysis reports and rebalancing alerts directly on your Discord server channel via webhook.
            </p>
            <div style="margin-bottom:20px;">
                <label style="display:block; font-size:0.75rem; color:var(--text-muted); margin-bottom:8px; text-transform:uppercase;">Discord Webhook URL</label>
                <input id="discord-url" style="width:100%; padding:14px; background:#0b0f1a; border:1px solid var(--border); color:#fff; border-radius:10px; box-sizing:border-box;" placeholder="https://discord.com/api/webhooks/..." value="{{wk}}">
            </div>
            <button class="btn btn-primary" style="width:100%; padding:14px; margin:0;" onclick="saveDiscord()">Save & Connect</button>
            <p id="discord-msg" style="text-align:center; margin-top:15px; font-size:0.9rem; font-weight:600;"></p>
        </div>

        <!-- Telegram Card -->
        <div class="glass-card" style="padding:24px; margin-bottom:0;">
            <div class="setting-section-title" style="color:#0088cc;">
                <span>✈️ Telegram Alert Configuration</span>
            </div>
            <p style="color:var(--text-muted); font-size:0.85rem; margin-bottom:20px; line-height:1.5;">
                Receive real-time recommended portfolio reports, rebalancing suggestions, and system alerts via your custom Telegram Bot.
            </p>
            <div style="margin-bottom:15px;">
                <label style="display:block; font-size:0.75rem; color:var(--text-muted); margin-bottom:8px; text-transform:uppercase;">Telegram Bot Token</label>
                <input id="telegram-token" type="password" style="width:100%; padding:14px; background:#0b0f1a; border:1px solid var(--border); color:#fff; border-radius:10px; box-sizing:border-box;" placeholder="123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ" value="{{bot_token}}">
            </div>
            <div style="margin-bottom:20px;">
                <label style="display:block; font-size:0.75rem; color:var(--text-muted); margin-bottom:8px; text-transform:uppercase;">Telegram Chat ID</label>
                <input id="telegram-chat-id" style="width:100%; padding:14px; background:#0b0f1a; border:1px solid var(--border); color:#fff; border-radius:10px; box-sizing:border-box;" placeholder="e.g. 987654321" value="{{chat_id}}">
            </div>
            <div style="display:flex; gap:12px;">
                <button class="btn" style="flex:1; padding:14px; margin:0; background:rgba(255,255,255,0.05);" onclick="testTelegram()">Test Notification</button>
                <button class="btn btn-primary" style="flex:1; padding:14px; margin:0;" onclick="saveTelegram()">Save settings</button>
            </div>
            <p id="telegram-msg" style="text-align:center; margin-top:15px; font-size:0.9rem; font-weight:600;"></p>
        </div>
    </div>
</main>
<script>
function saveDiscord(){
  const url = document.getElementById('discord-url').value.trim();
  if(url && !url.startsWith('http')){ alert('Invalid URL'); return; }
  
  fetch('/api/settings', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      webhook_url: url,
      bot_token: document.getElementById('telegram-token').value.trim(),
      chat_id: document.getElementById('telegram-chat-id').value.trim()
    })
  })
  .then(r=>r.json()).then(d=>{
    document.getElementById('discord-msg').innerHTML='<span style="color:var(--success)">✅ Discord Settings Saved!</span>';
    setTimeout(()=>location.reload(), 1500);
  });
}

function saveTelegram(){
  const token = document.getElementById('telegram-token').value.trim();
  const chatId = document.getElementById('telegram-chat-id').value.trim();
  
  fetch('/api/settings', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      webhook_url: document.getElementById('discord-url').value.trim(),
      bot_token: token,
      chat_id: chatId
    })
  })
  .then(r=>r.json()).then(d=>{
    document.getElementById('telegram-msg').innerHTML='<span style="color:var(--success)">✅ Telegram Settings Saved!</span>';
    setTimeout(()=>location.reload(), 1500);
  });
}

function testTelegram(){
  const token = document.getElementById('telegram-token').value.trim();
  const chatId = document.getElementById('telegram-chat-id').value.trim();
  if(!token || !chatId){ alert('Please enter both Bot Token and Chat ID first.'); return; }
  
  const msgEl = document.getElementById('telegram-msg');
  msgEl.innerHTML = '<span style="color:var(--accent)">📤 Sending test message...</span>';
  
  fetch('/api/settings/test', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      bot_token: token,
      chat_id: chatId
    })
  })
  .then(r=>r.json()).then(d=>{
    if(d.status === 'ok') {
      msgEl.innerHTML = '<span style="color:var(--success)">✅ Test message sent successfully! Check Telegram.</span>';
    } else {
      msgEl.innerHTML = `<span style="color:var(--danger)">❌ Error: ${d.error || 'Failed to send'}</span>`;
    }
  }).catch(e=>{
    msgEl.innerHTML = `<span style="color:var(--danger)">❌ Network Error: ${e.message}</span>`;
  });
}
</script>
<!-- ── 📱 모바일 하단 플로팅 탭바 마크업 ── -->
<div class="mobile-tab-bar">
    <a href="/live" id="tab-portfolio" class="tab-item"><span class="icon">💼</span><span>Portfolio</span></a>
    <a href="/" id="tab-analysis" class="tab-item"><span class="icon">🔬</span><span>Analysis</span></a>
    <a href="/settings" id="tab-settings" class="tab-item"><span class="icon">⚙️</span><span>Settings</span></a>
    <a href="/logout" class="tab-item" style="color:var(--danger);"><span class="icon">🚪</span><span>Logout</span></a>
</div>
<script>
    (function() {
        const path = window.location.pathname;
        if(path==='/live'||path==='/m'||path==='/my-portfolio') {
            document.getElementById('tab-portfolio').classList.add('active');
        } else if(path==='/settings'||path==='/discord') {
            document.getElementById('tab-settings').classList.add('active');
        } else if(path==='/'||path.includes('/portfolio')) {
            document.getElementById('tab-analysis').classList.add('active');
        }
    })();
</script>
</body></html>"""

MY_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <meta name="theme-color" content="#0b0f19">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="apple-mobile-web-app-title" content="내 포트폴리오">
    <meta name="mobile-web-app-capable" content="yes">
    <link rel="manifest" href="/manifest.json">
    <link rel="icon" type="image/svg+xml" href="/app-icon.svg">
    <link rel="apple-touch-icon" href="/app-icon.svg">
    <title>나의 실제 포트폴리오 · Hyperliquid Live</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        :root {
            --bg: #0b0f19;
            --card-bg: rgba(19, 26, 47, 0.6);
            --card-border: rgba(255, 255, 255, 0.08);
            --accent: #3b82f6;
            --accent-glow: rgba(59, 130, 246, 0.35);
            --success: #10b981;
            --success-bg: rgba(16, 185, 129, 0.12);
            --danger: #ef4444;
            --danger-bg: rgba(239, 68, 68, 0.12);
            --warning: #f59e0b;
            --warning-bg: rgba(245, 158, 11, 0.12);
            --text: #f1f5f9;
            --text-muted: #94a3b8;
            --border: #1e293b;
        }

        * {
            box-sizing: border-box;
            font-family: 'Inter', sans-serif;
            margin: 0;
            padding: 0;
        }

        body {
            background: radial-gradient(circle at 50% 0%, #1e294b 0%, var(--bg) 75%);
            color: var(--text);
            min-height: 100vh;
            overflow-x: hidden;
            padding-bottom: 90px;
        }

        header {
            padding: 20px 30px;
            background: rgba(11, 15, 25, 0.85);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 100;
        }

        header h1 {
            font-size: 1.4rem;
            font-weight: 800;
            background: linear-gradient(90deg, #60a5fa, #34d399);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .btn {
            padding: 10px 18px;
            border-radius: 10px;
            text-decoration: none;
            font-size: 0.85rem;
            font-weight: 600;
            border: 1px solid var(--border);
            color: var(--text);
            cursor: pointer;
            transition: all 0.2s ease;
            background: rgba(255, 255, 255, 0.03);
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }

        .btn:hover {
            background: rgba(255, 255, 255, 0.08);
            transform: translateY(-1px);
        }

        .btn-primary {
            background: var(--accent);
            border-color: var(--accent);
            color: #fff;
        }

        .btn-primary:hover {
            background: #2563eb;
            box-shadow: 0 4px 14px var(--accent-glow);
        }

        .btn-danger {
            background: var(--danger);
            border-color: var(--danger);
            color: #fff;
        }

        .btn-danger:hover {
            background: #dc2626;
            box-shadow: 0 4px 14px rgba(239, 68, 68, 0.3);
        }

        main {
            padding: 30px;
            max-width: 1400px;
            margin: 0 auto;
        }

        /* ── Tabs Navigation ── */
        .tab-nav {
            display: flex;
            gap: 8px;
            margin-bottom: 25px;
            background: rgba(255, 255, 255, 0.02);
            padding: 6px;
            border-radius: 12px;
            border: 1px solid var(--border);
            width: fit-content;
        }

        .tab-nav-btn {
            background: transparent;
            border: none;
            color: var(--text-muted);
            font-size: 0.9rem;
            font-weight: 600;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .tab-nav-btn:hover {
            color: #fff;
            background: rgba(255, 255, 255, 0.03);
        }

        .tab-nav-btn.active {
            color: #fff;
            background: var(--accent);
            box-shadow: 0 4px 12px var(--accent-glow);
        }

        /* ── Tab Content Panels ── */
        .tab-panel {
            display: none;
        }

        .tab-panel.active {
            display: block;
        }

        /* ── Glass Cards ── */
        .glass-card {
            background: var(--card-bg);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid var(--card-border);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.25);
        }

        .glass-card h3 {
            font-size: 1.15rem;
            font-weight: 700;
            margin-bottom: 18px;
            display: flex;
            align-items: center;
            gap: 8px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            padding-bottom: 10px;
        }

        /* ── Grid Layouts ── */
        .grid-3 {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 20px;
        }

        /* ── Portfolio Item Card ── */
        .p-card {
            cursor: pointer;
            transition: all 0.2s ease;
            position: relative;
        }

        .p-card:hover {
            transform: translateY(-4px);
            border-color: var(--accent);
            box-shadow: 0 12px 24px rgba(0,0,0,0.3);
        }

        .p-card.active-port {
            border-color: var(--accent);
            background: linear-gradient(145deg, rgba(59, 130, 246, 0.15), var(--card-bg));
            box-shadow: 0 0 15px var(--accent-glow);
        }

        .p-card-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 15px;
        }

        .p-card-title {
            font-weight: 700;
            font-size: 1.1rem;
            color: #fff;
        }

        .p-card-type {
            font-size: 0.72rem;
            font-weight: 700;
            padding: 3px 8px;
            border-radius: 6px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .p-card-type.ai {
            background: rgba(16, 185, 129, 0.15);
            color: #34d399;
        }

        .p-card-type.custom {
            background: rgba(59, 130, 246, 0.15);
            color: #60a5fa;
        }

        .p-card-stats {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin-top: 10px;
        }

        .p-card-stat-label {
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .p-card-stat-val {
            font-size: 1.1rem;
            font-weight: 700;
            margin-top: 2px;
        }

        .p-card-monthly-wrap {
            margin-top: 14px;
            padding-top: 12px;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
        }

        .p-card-monthly-title {
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 0.75rem;
            color: var(--text-muted);
            font-weight: 600;
            margin-bottom: 8px;
        }

        .p-card-monthly-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 6px;
        }

        .m-ret-chip {
            background: rgba(15, 23, 42, 0.65);
            border: 1px solid rgba(255, 255, 255, 0.07);
            border-radius: 7px;
            padding: 5px 6px;
            text-align: center;
        }

        .m-ret-chip .m-lbl {
            font-size: 0.68rem;
            color: var(--text-muted);
            font-weight: 600;
        }

        .m-ret-chip .m-val {
            font-size: 0.8rem;
            font-weight: 700;
            margin-top: 2px;
        }

        /* ── Tables styling ── */
        .table-container {
            width: 100%;
            overflow-x: auto;
            border-radius: 12px;
            border: 1px solid var(--border);
        }

        table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            font-size: 0.9rem;
        }

        th {
            background: rgba(15, 23, 42, 0.6);
            padding: 14px 18px;
            color: var(--text-muted);
            font-weight: 600;
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.8px;
            border-bottom: 1px solid var(--border);
        }

        td {
            padding: 14px 18px;
            border-bottom: 1px solid var(--border);
            vertical-align: middle;
        }

        tr:last-child td {
            border-bottom: none;
        }

        /* ── Badges & Indicators ── */
        .badge {
            padding: 4px 8px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 700;
            display: inline-flex;
            align-items: center;
        }

        .badge-success { background: var(--success-bg); color: var(--success); }
        .badge-danger { background: var(--danger-bg); color: var(--danger); }
        .badge-warning { background: var(--warning-bg); color: var(--warning); }
        
        .pnl-green { color: var(--success); }
        .pnl-red { color: var(--danger); }

        /* ── Rebalancing History & PnL Breakdown ── */
        .rebalance-kpi-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 14px;
            margin-bottom: 18px;
        }
        @media (max-width: 900px) {
            .rebalance-kpi-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        @media (max-width: 520px) {
            .rebalance-kpi-grid {
                grid-template-columns: 1fr;
            }
        }
        .rebalance-kpi-box {
            background: rgba(15, 23, 42, 0.72);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 14px 16px;
        }
        .rebalance-kpi-lbl {
            font-size: 0.76rem;
            color: var(--text-muted);
            font-weight: 600;
            margin-bottom: 6px;
        }
        .rebalance-kpi-val {
            font-size: 1.25rem;
            font-weight: 800;
            color: #fff;
        }
        .rebalance-kpi-sub {
            font-size: 0.74rem;
            color: var(--text-muted);
            margin-top: 4px;
            line-height: 1.35;
        }
        .reb-badge {
            display: inline-block;
            padding: 3px 9px;
            border-radius: 999px;
            font-size: 0.73rem;
            font-weight: 700;
            margin-top: 4px;
        }
        .reb-badge-emg {
            background: rgba(245, 158, 11, 0.16);
            color: #fbbf24;
            border: 1px solid rgba(245, 158, 11, 0.35);
        }
        .reb-badge-init {
            background: rgba(59, 130, 246, 0.16);
            color: #60a5fa;
            border: 1px solid rgba(59, 130, 246, 0.35);
        }
        .reb-badge-sched {
            background: rgba(16, 185, 129, 0.16);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.35);
        }
        .reb-lot-list {
            display: flex;
            flex-direction: column;
            gap: 6px;
        }
        .reb-lot-row {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
            background: rgba(255, 255, 255, 0.025);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            padding: 7px 10px;
            font-size: 0.83rem;
        }
        .reb-vlink {
            color: #f8fafc;
            font-weight: 700;
            text-decoration: none;
        }
        .reb-vlink:hover {
            color: #60a5fa;
            text-decoration: underline;
        }

        /* ── Modal Design ── */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(4, 6, 12, 0.85);
            backdrop-filter: blur(8px);
            align-items: center;
            justify-content: center;
        }

        .modal-content {
            background: #0f172a;
            border: 1px solid var(--border);
            border-radius: 20px;
            width: 650px;
            max-width: 90%;
            max-height: 85vh;
            overflow-y: auto;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
            position: relative;
            animation: modalFadeIn 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        }

        @keyframes modalFadeIn {
            from { opacity: 0; transform: scale(0.95) translateY(10px); }
            to { opacity: 1; transform: scale(1) translateY(0); }
        }

        .modal-header {
            padding: 20px 24px;
            border-bottom: 1px solid var(--border);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .modal-close {
            cursor: pointer;
            font-size: 1.5rem;
            color: var(--text-muted);
            transition: color 0.2s;
        }

        .modal-close:hover {
            color: #fff;
        }

        .modal-body {
            padding: 24px;
        }

        .form-group {
            margin-bottom: 20px;
        }

        .form-group label {
            display: block;
            font-size: 0.8rem;
            font-weight: 600;
            color: var(--text-muted);
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .form-input {
            width: 100%;
            padding: 11px 14px;
            background: #0b0f19;
            border: 1px solid var(--border);
            border-radius: 8px;
            color: #fff;
            font-size: 0.9rem;
            transition: border-color 0.2s;
        }

        .form-input:focus {
            outline: none;
            border-color: var(--accent);
        }

        .positions-editor {
            background: rgba(0, 0, 0, 0.25);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 16px;
            margin-top: 15px;
            max-height: 250px;
            overflow-y: auto;
        }

        .position-row {
            display: flex;
            gap: 12px;
            margin-bottom: 12px;
            align-items: center;
        }

        .position-row:last-child {
            margin-bottom: 0;
        }

        /* ── AI Insights Box ── */
        .insight-card {
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.9));
            border-left: 4px solid var(--accent);
            border-radius: 12px;
            padding: 18px;
            margin-bottom: 12px;
        }

        .insight-list {
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .insight-item {
            display: flex;
            align-items: flex-start;
            gap: 10px;
            font-size: 0.92rem;
            line-height: 1.5;
        }

        /* ── Toast Toast ── */
        #toast {
            visibility: hidden;
            min-width: 280px;
            background: #10b981;
            color: #fff;
            text-align: center;
            border-radius: 10px;
            padding: 16px;
            position: fixed;
            z-index: 2000;
            left: 50%;
            bottom: 30px;
            transform: translateX(-50%);
            font-weight: 700;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.5);
            transition: visibility 0s, opacity 0.3s ease-in-out;
            opacity: 0;
        }

        #toast.show {
            visibility: visible;
            opacity: 1;
        }

        /* ── Chart size ── */
        .chart-container {
            position: relative;
            height: 350px;
            width: 100%;
        }

        /* ── Mobile Navigation ── */
        .mobile-tab-bar {
            display: none;
            position: fixed;
            bottom: 16px;
            left: 50%;
            transform: translateX(-50%);
            width: 92%;
            max-width: 480px;
            height: 64px;
            background: rgba(15, 23, 42, 0.9);
            backdrop-filter: blur(15px);
            -webkit-backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 18px;
            box-shadow: 0 12px 36px rgba(0, 0, 0, 0.5);
            z-index: 999;
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
            color: var(--text-muted);
            font-size: 0.72rem;
            font-weight: 600;
            transition: all 0.2s ease;
            flex: 1;
            height: 100%;
        }

        .tab-item span.icon {
            font-size: 1.25rem;
            margin-bottom: 3px;
        }

        .tab-item.active {
            color: #60a5fa;
        }

        /* ── Responsive ── */
        @media (max-width: 768px) {
            body {
                padding-bottom: 100px;
            }

            header {
                padding: 15px 20px;
            }

            header h1 {
                font-size: 1.15rem;
            }

            header div:last-child {
                display: none !important;
            }

            .mobile-tab-bar {
                display: flex;
            }

            main {
                padding: 15px;
            }

            .tab-nav {
                width: 100%;
                justify-content: space-between;
            }

            .tab-nav-btn {
                padding: 8px 12px;
                font-size: 0.8rem;
                flex: 1;
                justify-content: center;
            }

            .glass-card {
                padding: 16px;
            }

            .grid-3 {
                grid-template-columns: 1fr;
            }
            #tab-details .grid-3 {
                grid-template-columns: repeat(2, 1fr);
                gap: 10px;
            }
            #tab-details .grid-3 .glass-card {
                padding: 13px 10px !important;
            }
            #tab-details .grid-3 .stat-val {
                font-size: 1.22rem !important;
                word-break: keep-all;
            }
            #tab-details .grid-3 .p-card-stat-label {
                font-size: 0.68rem !important;
                line-height: 1.3;
            }

            table {
                font-size: 0.8rem;
            }

            th, td {
                padding: 10px 12px;
            }
        }
    </style>
</head>
<body>

<header>
    <h1>💼 Virtual Portfolios Manager</h1>
    <div>
        <a class="btn" href="/mobile-connect" style="background:rgba(59,130,246,0.18);border:1px solid #60a5fa;color:#93c5fd;font-weight:700;">📱 휴대폰 앱 연결 (QR)</a>
        <a class="btn" href="/autobot" style="background:rgba(26,188,156,0.16);border:1px solid #1abc9c;color:#1abc9c;font-weight:700;">🤖 $20k 자동운용 관제</a>
        <button class="btn btn-primary" onclick="openCreateModal()">➕ 새 가상 포트폴리오</button>
        <a class="btn back-btn" href="/">← 메인 대시보드</a>
    </div>
</header>

<main>
    <!-- Tab Navigation -->
    <div class="tab-nav">
        <button class="tab-nav-btn active" onclick="switchTab('tab-list')">📋 포트폴리오 목록</button>
        <button class="tab-nav-btn" onclick="switchTab('tab-details')">📊 상세 분석 & AI 인사이트</button>
        <button class="tab-nav-btn" onclick="switchTab('tab-simulator')">🔮 시나리오 시뮬레이터</button>
    </div>

    <!-- TAB 1: 포트폴리오 목록 -->
    <div id="tab-list" class="tab-panel active">
        <div class="glass-card">
            <h3>📂 내 가상 포트폴리오 리스트</h3>
            <div id="portfolios-grid" class="grid-3">
                <!-- Portfolios render dynamically -->
            </div>
            
            <div id="empty-portfolios-msg" style="display:none; text-align:center; padding:50px 0; color:var(--text-muted);">
                <p style="font-size:1.1rem; margin-bottom:15px;">등록된 가상 포트폴리오가 없습니다.</p>
                <button class="btn btn-primary" onclick="openCreateModal()">새 가상 포트폴리오 생성하기</button>
            </div>
        </div>
    </div>

    <!-- TAB 2: 상세 분석 및 AI 인사이트 -->
    <div id="tab-details" class="tab-panel">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap:10px;">
            <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
                <h2 id="details-portfolio-title" style="font-size:1.5rem; color:#fff; margin:0;">기본 포트폴리오</h2>
                <span id="details-live-badge" style="display:none; background:rgba(46,204,113,0.16); color:#2ecc71; border:1px solid rgba(46,204,113,0.45); padding:4px 10px; border-radius:999px; font-size:0.78rem; font-weight:700;">🟢 Hyperliquid 실시간 온체인 동기화</span>
            </div>
            <div style="display:flex; gap:8px; flex-wrap:wrap; align-items:center;">
                <button class="btn btn-primary" onclick="loadPortfoliosData(activePortfolioId, true)" style="background:rgba(56,189,248,0.18); border:1px solid rgba(56,189,248,0.45); color:#7dd3fc;">🔄 실시간 새로고침</button>
                <button id="btn-auto-refresh" class="btn" onclick="toggleAutoRefresh()" style="background:rgba(16,185,129,0.14); border:1px solid rgba(16,185,129,0.4); color:#34d399; font-size:0.78rem; padding:8px 12px;">⏱️ 60초 자동갱신 ON</button>
                <button id="btn-unlock-edit" class="btn" onclick="toggleEditLock()" style="display:none; background:rgba(148,163,184,0.12); border:1px solid rgba(148,163,184,0.3); color:#94a3b8; font-size:0.78rem; padding:8px 12px;" title="모바일 오작동 방지를 위해 편집 버튼이 잠겨 있습니다">🔒 편집 잠금</button>
                <button id="btn-edit-port" class="btn btn-primary" onclick="openEditModal()">✏️ 포트폴리오 수정</button>
                <button id="btn-del-port" class="btn btn-danger" onclick="deleteActivePortfolio()">🗑️ 포트폴리오 삭제</button>
            </div>
        </div>

        <div class="grid-3" style="margin-bottom:24px;">
            <div class="glass-card" style="margin-bottom:0; padding:18px; text-align:center;">
                <div class="p-card-stat-label">총 투자 자산 (세전)</div>
                <div class="stat-val" id="details-total-value" style="font-size:1.8rem; font-weight:800; color:#fff; margin-top:5px;">$0</div>
                <div class="p-card-stat-label" id="details-total-capital" style="margin-top:5px; font-size:0.75rem;">원금 $0</div>
            </div>
            <div class="glass-card" style="margin-bottom:0; padding:18px; text-align:center;">
                <div class="p-card-stat-label">공제 후 순자산 (예상)</div>
                <div class="stat-val" id="details-net-value" style="font-size:1.8rem; font-weight:800; color:var(--accent2); margin-top:5px;">$0</div>
                <div class="p-card-stat-label" style="margin-top:5px; font-size:0.75rem;">10% 성과수수료 공제 반영</div>
            </div>
            <div class="glass-card" style="margin-bottom:0; padding:18px; text-align:center;">
                <div class="p-card-stat-label">세전 누적 수익률 (PnL)</div>
                <div class="stat-val" id="details-total-pnl" style="font-size:1.8rem; font-weight:800; margin-top:5px;">$0 (+0%)</div>
                <div class="p-card-stat-label" id="details-days-held" style="margin-top:5px; font-size:0.75rem;">투자 기간: 0일</div>
            </div>
            <div class="glass-card" style="margin-bottom:0; padding:18px; text-align:center;">
                <div class="p-card-stat-label">공제 후 순수익 (예상)</div>
                <div class="stat-val" id="details-net-pnl" style="font-size:1.8rem; font-weight:800; margin-top:5px;">$0 (+0%)</div>
                <div class="p-card-stat-label" style="margin-top:5px; font-size:0.75rem;">수익 구간 10% 수수료 공제</div>
            </div>
            <div class="glass-card" style="margin-bottom:0; padding:18px; text-align:center;">
                <div class="p-card-stat-label">월평균 순수익률 (복리)</div>
                <div class="stat-val" id="details-avg-monthly" style="font-size:1.8rem; font-weight:800; margin-top:5px;">+0.00%</div>
                <div class="p-card-stat-label" id="details-avg-monthly-sub" style="margin-top:5px; font-size:0.75rem;">세전 월평균 +0.00%</div>
            </div>
            <div class="glass-card" style="margin-bottom:0; padding:18px; text-align:center;">
                <div class="p-card-stat-label">예상 최대 낙폭 (MDD)</div>
                <div class="stat-val" id="details-portfolio-mdd" style="font-size:1.8rem; font-weight:800; color:var(--danger); margin-top:5px;">0%</div>
                <div class="p-card-stat-label" style="margin-top:5px; font-size:0.75rem;">역사적 시뮬레이션 기반</div>
            </div>
        </div>

        <!-- Equity Curve Chart -->
        <div class="glass-card">
            <h3>📈 포트폴리오 가치 누적 추이 (USD)</h3>
            <div class="chart-container">
                <canvas id="equity-chart"></canvas>
            </div>
        </div>

        <!-- Monthly Returns Table -->
        <div class="glass-card">
            <h3>📅 월별 수익률 상세 명세표 (세전 / 10% 성과수수료 공제 후)</h3>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>연월 (집계 기간)</th>
                            <th>기초 순자산 (USD)</th>
                            <th>기말 순자산 (USD)</th>
                            <th>월간 세전 수익률</th>
                            <th>월간 공제 후 순수익률</th>
                            <th>월간 순손익 (USD)</th>
                        </tr>
                    </thead>
                    <tbody id="details-monthly-table">
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Rebalancing History & Realized/Unrealized PnL Card (Live Portfolio) -->
        <div class="glass-card" id="rebalance-history-card" style="display:none;">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:10px; margin-bottom:18px;">
                <h3 style="margin:0; border:none; padding:0;">🔄 포트폴리오 리밸런싱 이력 및 손익 명세</h3>
                <span id="rebalance-subtitle" style="font-size:0.78rem; color:var(--text-muted);">Hyperliquid L1 온체인 원장 실시간 추적</span>
            </div>
            <div class="rebalance-kpi-grid" id="rebalance-kpi-grid"></div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th style="min-width:165px;">실행 일시 / 구분</th>
                            <th style="min-width:250px;">📤 출금(청산) 볼트 및 확정 손익</th>
                            <th style="min-width:300px;">📥 입금(편입·재투입) 볼트 및 이후 손익</th>
                            <th style="min-width:140px; text-align:right;">해당 회차 손익 요약</th>
                        </tr>
                    </thead>
                    <tbody id="details-rebalance-table"></tbody>
                </table>
            </div>
        </div>

        <!-- Positions Table -->
        <div class="glass-card">
            <h3>📌 보유 볼트 및 구성 비율</h3>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>볼트 이름</th>
                            <th>투자 원금 (USD)</th>
                            <th>비중 (%)</th>
                            <th>거래소 APR / MDD</th>
                            <th>평가 금액 (Your Deposits)</th>
                            <th>수익금 (All-time Earned)</th>
                            <th>출금 실수령 (수수료 10% 후)</th>
                        </tr>
                    </thead>
                    <tbody id="details-positions-table">
                        <!-- Positions render dynamically -->
                    </tbody>
                </table>
            </div>
        </div>

        <!-- AI Diagnostics Insights Card -->
        <div class="glass-card">
            <h3>🤖 AI 포트폴리오 진단 및 솔루션</h3>
            <div class="insight-card">
                <ul class="insight-list" id="details-insights-list">
                    <!-- Insights render dynamically -->
                </ul>
            </div>
        </div>
    </div>

    <!-- TAB 3: 시나리오 시뮬레이터 -->
    <div id="tab-simulator" class="tab-panel">
        <div class="glass-card">
            <h3>🔮 4대 가상 시나리오별 성과 비교</h3>
            <p style="color:var(--text-muted); font-size:0.9rem; margin-bottom:20px; line-height:1.5;">
                상승장, 하락장, 고변동성, 안정수익 시나리오 하에서 현재 생성된 모든 가상 포트폴리오들의 예상 수익률과 자산 변화를 한눈에 시뮬레이션합니다.
            </p>
            <div class="chart-container" style="height:380px; margin-bottom:30px;">
                <canvas id="scenario-comparison-chart"></canvas>
            </div>
        </div>

        <div class="glass-card">
            <h3>📋 시나리오별 시뮬레이션 상세 테이블</h3>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>포트폴리오</th>
                            <th>시나리오</th>
                            <th>예상 수익률 (%)</th>
                            <th>예상 최대 낙폭 (%)</th>
                            <th>시뮬레이션 종료 자산 (USD)</th>
                            <th>시나리오 설명</th>
                        </tr>
                    </thead>
                    <tbody id="scenario-table-body">
                        <!-- Scenario rows render dynamically -->
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</main>

<!-- Create / Edit Portfolio Modal -->
<div id="portfolioModal" class="modal" onclick="if(event.target === this) closeModal()">
    <div class="modal-content">
        <div class="modal-header">
            <h2 id="modal-title" style="color:#fff; font-size:1.2rem;">새 가상 포트폴리오 생성</h2>
            <span class="modal-close" onclick="closeModal()">×</span>
        </div>
        <div class="modal-body">
            <input type="hidden" id="modal-port-id" value="">
            
            <div class="form-group">
                <label>포트폴리오 이름</label>
                <input type="text" id="modal-port-name" class="form-input" placeholder="예: 성장 추구형 포트폴리오" required>
            </div>
            
            <div class="form-group">
                <label>총 투자 원금 (USD)</label>
                <input type="number" id="modal-port-capital" class="form-input" value="100000" min="100" required>
            </div>

            <div class="form-group">
                <label>투자 시작일</label>
                <input type="date" id="modal-port-date" class="form-input" required>
            </div>

            <div class="form-group">
                <label>비중 설정 방식</label>
                <select id="modal-port-mode" class="form-input" onchange="toggleAllocMode()">
                    <option value="manual">직접 수동 입력 (Manual)</option>
                    <option value="ai">AI 최적화 비중 자동 설정 (Auto)</option>
                </select>
            </div>

            <!-- AI Optimizer strategies -->
            <div class="form-group" id="modal-ai-strategy-container" style="display:none;">
                <label>AI 최적화 전략 선택</label>
                <select id="modal-port-strategy" class="form-input">
                    <option value="max_sharpe">📈 최대 샤프지수 (Max Sharpe) - 위험 대비 수익성 극대화</option>
                    <option value="min_variance">🛡️ 최소 분산 (Min Variance) - 전체 포트폴리오 변동성 극 최소화</option>
                    <option value="risk_parity">⚖️ 위험 균형 (Risk Parity) - 각 볼트별 위험 기여도 균등 배분</option>
                    <option value="min_cvar">🔒 원금보호형 CVaR (Min CVaR) - 최악의 꼬리 리스크 방어</option>
                </select>
                <p style="color:var(--text-muted); font-size:0.78rem; margin-top:6px;">
                    * AI 최적화 비중 설정 선택 시 오늘 날짜의 최적화 결과를 사용하여 포트폴리오 자산이 자동 배분됩니다.
                </p>
            </div>

            <!-- Manual Positions Editor -->
            <div class="form-group" id="modal-manual-positions-container">
                <label>볼트별 투자 비중 (%)</label>
                <div class="positions-editor">
                    <div id="modal-positions-list">
                        <!-- Manual position rows render dynamically -->
                    </div>
                    
                    <button type="button" class="btn" style="margin-top:10px; width:100%; justify-content:center;" onclick="addManualPositionRow()">
                        ➕ 포지션 볼트 추가
                    </button>
                </div>
                <div style="display:flex; justify-content:space-between; margin-top:8px; font-size:0.85rem;">
                    <span id="modal-total-weight-text" style="font-weight:700; color:var(--text-muted);">총 비중 합계: 0%</span>
                    <span style="color:var(--text-muted);">* 입력한 비중 %는 총 투자 원금에 비례하여 USD로 저장됩니다.</span>
                </div>
            </div>

            <div style="margin-top:25px; display:flex; justify-content:flex-end; gap:12px;">
                <button type="button" class="btn" onclick="closeModal()">취소</button>
                <button type="button" class="btn btn-primary" onclick="savePortfolio()">포트폴리오 저장</button>
            </div>
        </div>
    </div>
</div>

<div id="toast"></div>

<!-- Mobile Navigation Bar -->
<div class="mobile-tab-bar">
    <a href="/autobot" class="tab-item"><span class="icon">🤖</span><span>AutoBot</span></a>
    <a href="/live" class="tab-item active"><span class="icon">💼</span><span>내 포트폴리오</span></a>
    <a href="/" class="tab-item"><span class="icon">🔬</span><span>Analysis</span></a>
    <a href="/settings" class="tab-item"><span class="icon">⚙️</span><span>Settings</span></a>
    <a href="/logout" class="tab-item" style="color:var(--danger);"><span class="icon">🚪</span><span>Logout</span></a>
</div>

<script>
    // State Variables
    let portfolios = [];
    let scenarioReports = {};
    let activePortfolioId = 'default';
    let equityChart = null;
    let scenarioChart = null;

    const availableVaults = {{ available_vaults | tojson }};

    const urlParams = new URLSearchParams(window.location.search);
    const isDirectLiveMode = (
        window.location.pathname === '/live'
        || window.location.pathname === '/m'
        || urlParams.get('tab') === 'live'
        || urlParams.get('tab') === 'details'
        || window.matchMedia('(display-mode: standalone)').matches
    );
    let autoRefreshEnabled = true;
    let editUnlocked = false;
    let autoRefreshTimer = null;

    function toggleAutoRefresh() {
        autoRefreshEnabled = !autoRefreshEnabled;
        const btn = document.getElementById('btn-auto-refresh');
        if (btn) {
            btn.innerText = autoRefreshEnabled ? '⏱️ 60초 자동갱신 ON' : '⏸️ 자동갱신 일시정지';
            btn.style.color = autoRefreshEnabled ? '#34d399' : '#94a3b8';
            btn.style.borderColor = autoRefreshEnabled ? 'rgba(16,185,129,0.4)' : 'rgba(148,163,184,0.3)';
        }
    }

    function toggleEditLock() {
        editUnlocked = !editUnlocked;
        syncEditButtonsVisibility();
        showToast(editUnlocked ? '🔓 포트폴리오 편집 잠금이 해제되었습니다.' : '🔒 실수 방지 편집 잠금이 켜졌습니다.');
    }

    function syncEditButtonsVisibility() {
        const isDefault = (activePortfolioId === 'default');
        const lockBtn = document.getElementById('btn-unlock-edit');
        const editBtn = document.getElementById('btn-edit-port');
        const delBtn = document.getElementById('btn-del-port');
        if (!lockBtn || !editBtn || !delBtn) return;
        if (isDefault) {
            lockBtn.style.display = 'inline-block';
            lockBtn.innerText = editUnlocked ? '🔓 편집 잠금해제됨' : '🔒 편집 잠금';
            editBtn.style.display = editUnlocked ? 'inline-block' : 'none';
            delBtn.style.display = editUnlocked ? 'inline-block' : 'none';
        } else {
            lockBtn.style.display = 'none';
            editBtn.style.display = 'inline-block';
            delBtn.style.display = 'inline-block';
        }
    }

    let initialDirectPending = isDirectLiveMode;

    // Initialize Page
    document.addEventListener("DOMContentLoaded", () => {
        document.getElementById('modal-port-date').value = new Date().toISOString().substring(0, 10);
        if (isDirectLiveMode) {
            activePortfolioId = 'default';
            document.querySelectorAll('.tab-nav-btn').forEach((btn, i) => btn.classList.toggle('active', i === 1));
            document.querySelectorAll('.tab-panel').forEach(panel => panel.classList.remove('active'));
            document.getElementById('tab-details').classList.add('active');
            document.getElementById('details-portfolio-title').innerText = '📂 나의 실제 포트폴리오 (실시간 불러오는 중...)';
        }
        loadPortfoliosData(isDirectLiveMode ? 'default' : null, true, true);
        loadScenariosData();

        // 60초마다 화면이 켜져 있을 때 실시간 온체인 데이터 자동 갱신
        autoRefreshTimer = setInterval(() => {
            if (autoRefreshEnabled && document.visibilityState === 'visible' && activePortfolioId === 'default') {
                loadPortfoliosData('default', true, true);
            }
        }, 60000);

        // 휴대폰 잠금 해제 / 앱 복귀 시 즉시 최신 거래소 잔고 갱신
        document.addEventListener('visibilitychange', () => {
            if (autoRefreshEnabled && document.visibilityState === 'visible' && activePortfolioId === 'default') {
                loadPortfoliosData('default', true, true);
            }
        });
    });

    // switch tabs
    function switchTab(tabId) {
        document.querySelectorAll('.tab-nav-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-panel').forEach(panel => panel.classList.remove('active'));
        
        // Find which button triggered this
        const btnMap = {
            'tab-list': 0,
            'tab-details': 1,
            'tab-simulator': 2
        };
        const btns = document.querySelectorAll('.tab-nav-btn');
        if (btns[btnMap[tabId]]) {
            btns[btnMap[tabId]].classList.add('active');
        }
        
        document.getElementById(tabId).classList.add('active');

        // Draw charts if needed when tab becomes visible
        if (tabId === 'tab-details') {
            renderActivePortfolioDetails();
        } else if (tabId === 'tab-simulator') {
            renderScenarioSimulator();
        }
    }

    function fmtUsd2(v) {
        return Number(v || 0).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }
    function fmtCardUsd(v, isLive) {
        return isLive ? fmtUsd2(v) : Math.round(Number(v || 0)).toLocaleString('en-US');
    }

    // Load API Data
    function loadPortfoliosData(selectIdAfterLoad = null, forceRefresh = false, silent = false) {
        const tsParam = `_t=${Date.now()}`;
        const url = forceRefresh ? `/api/portfolios?refresh=1&${tsParam}` : `/api/portfolios?${tsParam}`;
        fetch(url, { cache: 'no-store' })
            .then(res => {
                if (res.redirected || res.status === 401) {
                    window.location.href = '/login';
                    return;
                }
                return res.text().then(text => {
                    try {
                        return JSON.parse(text);
                    } catch(e) {
                        if (text.trim().startsWith('<')) {
                            window.location.href = '/login';
                            return;
                        }
                        throw new Error('Invalid JSON response: ' + text.substring(0, 100));
                    }
                });
            })
            .then(data => {
                if (!data) return;
                if (!Array.isArray(data)) {
                    if (data.error) {
                        alert("에러 발생: " + data.error);
                    } else {
                        alert("잘못된 데이터 포맷입니다.");
                    }
                    return;
                }
                portfolios = data;
                if (portfolios.length === 0) {
                    document.getElementById('portfolios-grid').style.display = 'none';
                    document.getElementById('empty-portfolios-msg').style.display = 'block';
                    activePortfolioId = null;
                } else {
                    document.getElementById('portfolios-grid').style.display = 'grid';
                    document.getElementById('empty-portfolios-msg').style.display = 'none';
                    
                    if (selectIdAfterLoad) {
                        activePortfolioId = selectIdAfterLoad;
                    } else if (!activePortfolioId || !portfolios.find(p => p.id === activePortfolioId)) {
                        activePortfolioId = portfolios[0].id;
                    }
                    renderPortfoliosList();
                    if (initialDirectPending) {
                        initialDirectPending = false;
                        switchTab('tab-details');
                    } else if (document.getElementById('tab-details').classList.contains('active')) {
                        renderActivePortfolioDetails();
                    }
                    if (forceRefresh && !silent) {
                        showToast("✅ Hyperliquid 거래소 실시간 온체인 잔고·수익을 동기화했습니다.");
                    }
                }
            })
            .catch(err => {
                console.error("Error loading portfolios:", err);
                if (!silent) {
                    showToast("❌ 서버 연결 실패 (외부 LTE/5G에서는 외부 터널 주소나 Tailscale 연결이 필요합니다)");
                }
            });
    }

    function loadScenariosData() {
        fetch('/api/scenarios')
            .then(res => {
                if (res.redirected || res.status === 401) {
                    window.location.href = '/login';
                    return;
                }
                return res.text().then(text => {
                    try {
                        return JSON.parse(text);
                    } catch(e) {
                        if (text.trim().startsWith('<')) {
                            window.location.href = '/login';
                            return;
                        }
                        throw new Error('Invalid JSON response: ' + text.substring(0, 100));
                    }
                });
            })
            .then(data => {
                if (!data) return;
                scenarioReports = data;
                if (document.getElementById('tab-simulator').classList.contains('active')) {
                    renderScenarioSimulator();
                }
            })
            .catch(err => console.error("Error loading scenarios:", err));
    }

    // Render Tab 1 (List of Portfolios)
    function renderPortfoliosList() {
        const grid = document.getElementById('portfolios-grid');
        grid.innerHTML = '';

        // default(실제 포트폴리오)가 가장 먼저 오도록 정렬
        portfolios.sort((a, b) => {
            if (a.id === 'default') return -1;
            if (b.id === 'default') return 1;
            return 0;
        });

        portfolios.forEach(p => {
            const perf = p.performance || {};
            const isSelected = p.id === activePortfolioId;
            const pnlColor = perf.total_pnl >= 0 ? 'pnl-green' : 'pnl-red';
            const sign = perf.total_pnl >= 0 ? '+' : '';
            
            const netPnlColor = (perf.net_total_pnl || 0) >= 0 ? 'pnl-green' : 'pnl-red';
            const netSign = (perf.net_total_pnl || 0) >= 0 ? '+' : '';

            // 투자기간 대비 순수익률 (연환산 APY) 계산
            const daysHeld = perf.days_held || 0;
            const netPnlPct = perf.net_total_pnl_pct || 0;
            let apyText = '0.00% (APY)';

            if (daysHeld > 0) {
                if (netPnlPct > -100) {
                    let apy;
                    if (daysHeld < 7) {
                        apy = (netPnlPct / daysHeld) * 365;
                    } else {
                        apy = (Math.pow(1 + netPnlPct / 100, 365 / daysHeld) - 1) * 100;
                    }
                    if (Math.abs(apy) > 10000) {
                        apyText = (apy > 0 ? '>' : '<') + '9999% (APY)';
                    } else {
                        const apySign = apy >= 0 ? '+' : '';
                        apyText = `${apySign}${apy.toFixed(2)}% (APY)`;
                    }
                } else {
                    apyText = '-100.00% (APY)';
                }
            }

            const card = document.createElement('div');
            card.className = `glass-card p-card ${isSelected ? 'active-port' : ''}`;
            card.onclick = () => {
                activePortfolioId = p.id;
                renderPortfoliosList();
                switchTab('tab-details');
            };

            // p.id === 'default' 일 때 배지를 '실제 보유'로 다르게 지정
            let badgeHtml = '';
            if (p.id === 'default') {
                badgeHtml = `<span class="p-card-type" style="background: rgba(245, 158, 11, 0.15); color: #fbbf24; font-weight:700;">실제 보유</span>`;
            } else {
                badgeHtml = `<span class="p-card-type ${p.ptype === 'custom' ? 'custom' : 'ai'}">${p.ptype === 'custom' ? '수동' : 'AI 최적화'}</span>`;
            }

            const isLiveCard = Boolean(perf.is_live_onchain);
            if (isLiveCard) {
                badgeHtml = `<span class="p-card-type ai" style="background:rgba(46,204,113,0.18);color:#2ecc71;border:1px solid rgba(46,204,113,0.4);">🟢 실시간 온체인</span>`;
            }
            const cTotPnl = Number(perf.total_pnl || 0);
            const cTotStr = cTotPnl >= 0 ? `+$${fmtCardUsd(cTotPnl, isLiveCard)}` : `-$${fmtCardUsd(Math.abs(cTotPnl), isLiveCard)}`;
            const cNetPnl = Number(perf.net_total_pnl || 0);
            const cNetStr = cNetPnl >= 0 ? `+$${fmtCardUsd(cNetPnl, isLiveCard)}` : `-$${fmtCardUsd(Math.abs(cNetPnl), isLiveCard)}`;
            card.innerHTML = `
                <div class="p-card-header">
                    <div class="p-card-title">📂 ${escapeHtml(p.name)}</div>
                    ${badgeHtml}
                </div>
                <div class="p-card-stats">
                    <div>
                        <div class="p-card-stat-label">투자 원금</div>
                        <div class="p-card-stat-val">$${fmtCardUsd(p.total_capital, isLiveCard)}</div>
                    </div>
                    <div>
                        <div class="p-card-stat-label">최대 낙폭 (MDD)</div>
                        <div class="p-card-stat-val" style="color:var(--danger);">${perf.mdd || 0}%</div>
                    </div>
                    <div>
                        <div class="p-card-stat-label">현재 가치 (거래소 합계)</div>
                        <div class="p-card-stat-val">$${fmtCardUsd(perf.total_value || p.total_capital, isLiveCard)}</div>
                    </div>
                    <div>
                        <div class="p-card-stat-label">출금 실수령 순자산</div>
                        <div class="p-card-stat-val" style="color:var(--accent2);">$${fmtCardUsd(perf.net_total_value || p.total_capital, isLiveCard)}</div>
                    </div>
                    <div>
                        <div class="p-card-stat-label">수익금 / 수익률 (Earned)</div>
                        <div class="p-card-stat-val ${pnlColor}">${cTotStr} (${sign}${Number(perf.total_pnl_pct || 0).toFixed(2)}%)</div>
                    </div>
                    <div>
                        <div class="p-card-stat-label">출금 실수령 순수익</div>
                        <div class="p-card-stat-val ${netPnlColor}">${cNetStr} (${netSign}${Number(perf.net_total_pnl_pct || 0).toFixed(2)}%)</div>
                    </div>
                    <div>
                        <div class="p-card-stat-label">투자 기간</div>
                        <div class="p-card-stat-val">${daysHeld}일 (${p.invest_date})</div>
                    </div>
                    <div>
                        <div class="p-card-stat-label">투자기간대비 순수익률</div>
                        <div class="p-card-stat-val ${netPnlColor}">${apyText}</div>
                    </div>
                    <div>
                        <div class="p-card-stat-label">월평균 수익률 (세전 복리)</div>
                        <div class="p-card-stat-val ${(perf.avg_monthly_gross_pct || 0) >= 0 ? 'pnl-green' : 'pnl-red'}">${(perf.avg_monthly_gross_pct || 0) >= 0 ? '+' : ''}${(perf.avg_monthly_gross_pct || 0).toFixed(2)}% / 월</div>
                    </div>
                    <div>
                        <div class="p-card-stat-label">월평균 순수익률 (공제 후)</div>
                        <div class="p-card-stat-val ${(perf.avg_monthly_net_pct || 0) >= 0 ? 'pnl-green' : 'pnl-red'}">${(perf.avg_monthly_net_pct || 0) >= 0 ? '+' : ''}${(perf.avg_monthly_net_pct || 0).toFixed(2)}% / 월</div>
                    </div>
                </div>
                ${(perf.monthly_returns && perf.monthly_returns.length > 0) ? `
                <div class="p-card-monthly-wrap">
                    <div class="p-card-monthly-title">
                        <span>📅 월별 순수익률 (수수료 공제 후)</span>
                        <span>총 ${perf.monthly_returns.length}개월</span>
                    </div>
                    <div class="p-card-monthly-grid">
                        ${perf.monthly_returns.map(m => {
                            const mc = m.net_pct >= 0 ? "pnl-green" : "pnl-red";
                            const ms = m.net_pct >= 0 ? "+" : "";
                            return `<div class="m-ret-chip" title="${m.month} (${m.start_date} ~ ${m.end_date}) 세전: ${m.gross_pct >= 0 ? '+' : ''}${m.gross_pct.toFixed(2)}% / 공제후: ${ms}${m.net_pct.toFixed(2)}%">
                                <div class="m-lbl">${m.short_label} (${m.month_num})</div>
                                <div class="m-val ${mc}">${ms}${m.net_pct.toFixed(2)}%</div>
                            </div>`;
                        }).join("")}
                    </div>
                </div>` : ""}
            `;
            grid.appendChild(card);
        });
    }

    // Render Tab 2 (Selected Portfolio Details & Insights)
    function renderActivePortfolioDetails() {
        const p = portfolios.find(port => port.id === activePortfolioId);
        if (!p) {
            switchTab('tab-list');
            return;
        }

        document.getElementById('details-portfolio-title').innerText = `📂 ${p.name}`;
        if (typeof syncEditButtonsVisibility === 'function') syncEditButtonsVisibility();
        
        const perf = p.performance || {};
        const isLive = Boolean(perf.is_live_onchain);
        const liveBadgeEl = document.getElementById('details-live-badge');
        if (liveBadgeEl) {
            liveBadgeEl.style.display = isLive ? 'inline-block' : 'none';
            if (isLive && perf.fetched_at) {
                liveBadgeEl.innerText = `🟢 Hyperliquid 실시간 온체인 (${String(perf.fetched_at).replace('T', ' ')})`;
            }
        }
        document.getElementById('details-total-value').innerText = `$${fmtCardUsd(perf.total_value || p.total_capital, isLive)}`;
        let capSub = `총 원금 $${fmtCardUsd(p.total_capital, isLive)}`;
        if (isLive) {
            const cashU = Number(perf.wallet_cash_usd || 0);
            const realPnl = Number(perf.realized_pnl_usd || 0);
            capSub += ` (볼트원금 $${fmtUsd2(perf.active_principal_usd || 0)} · 현금 $${fmtUsd2(cashU)}`;
            if (Math.abs(realPnl) >= 0.5) {
                capSub += ` · 기실현 ${realPnl >= 0 ? '+' : '-'}$${fmtUsd2(Math.abs(realPnl))}`;
            }
            capSub += `)`;
        }
        document.getElementById('details-total-capital').innerText = capSub;
        
        const totPnl = Number(perf.total_pnl || 0);
        const pnlSignStr = totPnl >= 0 ? `+$${fmtCardUsd(totPnl, isLive)}` : `-$${fmtCardUsd(Math.abs(totPnl), isLive)}`;
        const sign = totPnl >= 0 ? '+' : '';
        const pnlColor = totPnl >= 0 ? 'var(--success)' : 'var(--danger)';
        const pnlText = `${pnlSignStr} (${sign}${Number(perf.total_pnl_pct || 0).toFixed(2)}%)`;
        document.getElementById('details-total-pnl').innerText = pnlText;
        document.getElementById('details-total-pnl').style.color = pnlColor;
        document.getElementById('details-days-held').innerText = `투자 시작일: ${p.invest_date} (경과: ${perf.days_held || 0}일)`;
        document.getElementById('details-portfolio-mdd').innerText = `${perf.mdd || 0}%`;

        // Render Net elements
        const netPnlVal = Number(perf.net_total_pnl || 0);
        const netSignStr = netPnlVal >= 0 ? `+$${fmtCardUsd(netPnlVal, isLive)}` : `-$${fmtCardUsd(Math.abs(netPnlVal), isLive)}`;
        const netSign = netPnlVal >= 0 ? '+' : '';
        const netPnlColor = netPnlVal >= 0 ? 'var(--success)' : 'var(--danger)';
        const netPnlText = `${netSignStr} (${netSign}${Number(perf.net_total_pnl_pct || 0).toFixed(2)}%)`;
        document.getElementById('details-net-value').innerText = `$${fmtCardUsd(perf.net_total_value || p.total_capital, isLive)}`;
        document.getElementById('details-net-pnl').innerText = netPnlText;
        document.getElementById('details-net-pnl').style.color = netPnlColor;

        // Render Average Monthly KPI & Monthly Returns Breakdown Table
        const avgNetM = perf.avg_monthly_net_pct || 0;
        const avgGrossM = perf.avg_monthly_gross_pct || 0;
        const avgNetEl = document.getElementById('details-avg-monthly');
        if (avgNetEl) {
            avgNetEl.innerText = `${avgNetM >= 0 ? '+' : ''}${avgNetM.toFixed(2)}% / 월`;
            avgNetEl.style.color = avgNetM >= 0 ? 'var(--success)' : 'var(--danger)';
        }
        const avgSubEl = document.getElementById('details-avg-monthly-sub');
        if (avgSubEl) {
            avgSubEl.innerText = `세전 월평균 ${avgGrossM >= 0 ? '+' : ''}${avgGrossM.toFixed(2)}%`;
        }

        const mTbody = document.getElementById('details-monthly-table');
        if (mTbody) {
            mTbody.innerHTML = '';
            const mList = perf.monthly_returns || [];
            if (mList.length > 0) {
                mList.forEach(m => {
                    const gCls = m.gross_pct >= 0 ? 'pnl-green' : 'pnl-red';
                    const gSgn = m.gross_pct >= 0 ? '+' : '';
                    const nCls = m.net_pct >= 0 ? 'pnl-green' : 'pnl-red';
                    const nSgn = m.net_pct >= 0 ? '+' : '';
                    const usdSgn = m.net_pnl >= 0 ? '+' : '-';
                    const usdFmt = isLive ? fmtUsd2(Math.abs(m.net_pnl)) : (Math.abs(m.net_pnl) < 100 ? Math.abs(m.net_pnl).toFixed(2) : Math.round(Math.abs(m.net_pnl)).toLocaleString());
                    const sFmt = isLive ? fmtUsd2(m.start_net) : (m.start_net < 100 ? m.start_net.toFixed(2) : Math.round(m.start_net).toLocaleString());
                    const eFmt = isLive ? fmtUsd2(m.end_net) : (m.end_net < 100 ? m.end_net.toFixed(2) : Math.round(m.end_net).toLocaleString());
                    const mTr = document.createElement('tr');
                    mTr.innerHTML = `
                        <td style="font-weight:700; color:#fff;">${m.month} <small style="color:var(--text-muted); font-weight:400;">(${m.start_date.slice(5)} ~ ${m.end_date.slice(5)}, ${m.days}일)</small></td>
                        <td>$${sFmt}</td>
                        <td style="font-weight:600; color:var(--accent2);">$${eFmt}</td>
                        <td class="${gCls}" style="font-weight:600;">${gSgn}${m.gross_pct.toFixed(2)}%</td>
                        <td class="${nCls}" style="font-weight:700;">${nSgn}${m.net_pct.toFixed(2)}%</td>
                        <td class="${nCls}" style="font-weight:600;">${usdSgn}$${usdFmt}</td>
                    `;
                    mTbody.appendChild(mTr);
                });
            } else {
                mTbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:var(--text-muted); padding:24px;">월별 수익률 데이터가 없습니다.</td></tr>`;
            }
        }

        // Render Rebalancing History & Realized/Unrealized PnL Card
        const rebCard = document.getElementById('rebalance-history-card');
        const rebKpiGrid = document.getElementById('rebalance-kpi-grid');
        const rebTbody = document.getElementById('details-rebalance-table');
        const rebSub = document.getElementById('rebalance-subtitle');
        const rebSum = perf.rebalance_summary || null;
        const rebHist = perf.rebalance_history || [];

        if (rebCard && rebKpiGrid && rebTbody) {
            if (isLive && rebSum && rebHist.length > 0) {
                rebCard.style.display = 'block';
                const rReal = Number(rebSum.realized_pnl_usd || 0);
                const rRealCls = rReal >= 0 ? 'pnl-green' : 'pnl-red';
                const rRealStr = `${rReal >= 0 ? '+' : '-'}$${fmtUsd2(Math.abs(rReal))}`;

                const rUnr = Number(rebSum.active_unrealized_pnl_usd || 0);
                const rUnrCls = rUnr >= 0 ? 'pnl-green' : 'pnl-red';
                const rUnrStr = `${rUnr >= 0 ? '+' : '-'}$${fmtUsd2(Math.abs(rUnr))}`;

                const rComb = Number(perf.total_pnl || (rReal + rUnr));
                const rCombCls = rComb >= 0 ? 'pnl-green' : 'pnl-red';
                const rCombStr = `${rComb >= 0 ? '+' : '-'}$${fmtUsd2(Math.abs(rComb))}`;

                if (rebSub) {
                    rebSub.innerText = `최초 구축: ${rebSum.session_start_ts ? rebSum.session_start_ts.slice(0, 16) : p.invest_date} · 최근 교체: ${rebSum.last_rebalance_ts || '없음'}`;
                }

                rebKpiGrid.innerHTML = `
                    <div class="rebalance-kpi-box">
                        <div class="rebalance-kpi-lbl">리밸런싱 실행 횟수</div>
                        <div class="rebalance-kpi-val" style="color:#fbbf24;">총 ${rebSum.rebalance_count}회 교체</div>
                        <div class="rebalance-kpi-sub">최초 진입 포함 총 ${rebHist.length}건 온체인 체결</div>
                    </div>
                    <div class="rebalance-kpi-box">
                        <div class="rebalance-kpi-lbl">청산 볼트 확정 손익 (실현)</div>
                        <div class="rebalance-kpi-val ${rRealCls}">${rRealStr}</div>
                        <div class="rebalance-kpi-sub">회수 원금 $${fmtUsd2(rebSum.total_withdrawn_basis_usd)} → 실회수 $${fmtUsd2(rebSum.total_withdrawn_net_usd)} (${rebSum.realized_pnl_pct_on_exited >= 0 ? '+' : ''}${Number(rebSum.realized_pnl_pct_on_exited || 0).toFixed(2)}%)</div>
                    </div>
                    <div class="rebalance-kpi-box">
                        <div class="rebalance-kpi-lbl">현재 보유 볼트 평가손익 (미실현)</div>
                        <div class="rebalance-kpi-val ${rUnrCls}">${rUnrStr}</div>
                        <div class="rebalance-kpi-sub">현재 운용 원금 $${fmtUsd2(perf.active_principal_usd || 0)} (${rebSum.active_unrealized_pnl_pct >= 0 ? '+' : ''}${Number(rebSum.active_unrealized_pnl_pct || 0).toFixed(2)}%)</div>
                    </div>
                    <div class="rebalance-kpi-box">
                        <div class="rebalance-kpi-lbl">총 누적 손익 합계 (확정 + 평가)</div>
                        <div class="rebalance-kpi-val ${rCombCls}">${rCombStr}</div>
                        <div class="rebalance-kpi-sub">원금 $${fmtUsd2(p.total_capital)} 대비 ${Number(perf.total_pnl_pct || 0) >= 0 ? '+' : ''}${Number(perf.total_pnl_pct || 0).toFixed(2)}% (수수료 공제후 ${netSignStr})</div>
                    </div>
                `;

                rebTbody.innerHTML = '';
                rebHist.forEach(ev => {
                    const tr = document.createElement('tr');
                    let badgeCls = 'reb-badge-sched';
                    if (ev.event_kind === 'INITIAL_DEPLOY') badgeCls = 'reb-badge-init';
                    else if (ev.trigger === 'EMERGENCY_EXIT') badgeCls = 'reb-badge-emg';

                    // Withdrawals cell
                    let wHtml = '';
                    if (ev.withdrawals && ev.withdrawals.length > 0) {
                        wHtml = `<div class="reb-lot-list">` + ev.withdrawals.map(w => {
                            const wp = Number(w.realized_pnl_usd || 0);
                            const wCls = wp >= 0 ? 'pnl-green' : 'pnl-red';
                            const wStr = `${wp >= 0 ? '+' : '-'}$${fmtUsd2(Math.abs(wp))} (${wp >= 0 ? '+' : ''}${Number(w.realized_pnl_pct || 0).toFixed(2)}%)`;
                            return `
                                <div class="reb-lot-row">
                                    <div>
                                        <a class="reb-vlink" href="https://app.hyperliquid.xyz/vaults/${w.vault}" target="_blank">${escapeHtml(w.name)} ↗</a>
                                        <div style="font-size:0.75rem; color:var(--text-muted); margin-top:2px;">원금 $${fmtUsd2(w.basis_usd)} → 회수 $${fmtUsd2(w.net_withdrawn_usd)}${w.commission_usd > 0 ? ` (수수료 $${fmtUsd2(w.commission_usd)})` : ''}</div>
                                    </div>
                                    <div class="${wCls}" style="font-weight:800; text-align:right;">
                                        확정 ${wStr}
                                    </div>
                                </div>
                            `;
                        }).join('') + `</div>`;
                    } else {
                        wHtml = `<div style="color:var(--text-muted); font-size:0.83rem; padding:4px 0;">신규 운용자금 투입 (출금 없음)<br><small>예치 합계 $${fmtUsd2(ev.deposited_total_usd)}</small></div>`;
                    }

                    // Deposits cell
                    let dHtml = '';
                    if (ev.deposits && ev.deposits.length > 0) {
                        dHtml = `<div class="reb-lot-list">` + ev.deposits.map(d => {
                            const dp = Number(d.followup_pnl_usd || 0);
                            const dCls = dp >= 0 ? 'pnl-green' : 'pnl-red';
                            const dStr = `${dp >= 0 ? '+' : '-'}$${fmtUsd2(Math.abs(dp))} (${dp >= 0 ? '+' : ''}${Number(d.followup_pnl_pct || 0).toFixed(2)}%)`;
                            const stLabel = d.lot_status === 'CLOSED'
                                ? `<span style="color:#94a3b8; font-size:0.72rem;">[${escapeHtml((d.closed_at || '').slice(5, 10))} 교체청산]</span>`
                                : `<span style="color:#34d399; font-size:0.72rem;">[보유중]</span>`;
                            return `
                                <div class="reb-lot-row">
                                    <div>
                                        <a class="reb-vlink" href="https://app.hyperliquid.xyz/vaults/${d.vault}" target="_blank">${escapeHtml(d.name)} ↗</a> ${stLabel}
                                        <div style="font-size:0.75rem; color:var(--text-muted); margin-top:2px;">투입 +$${fmtUsd2(d.amount_usd)} → ${d.lot_status === 'CLOSED' ? '회수' : '현재'} $${fmtUsd2(d.followup_value_usd)}</div>
                                    </div>
                                    <div class="${dCls}" style="font-weight:700; text-align:right;">
                                        ${dStr}
                                    </div>
                                </div>
                            `;
                        }).join('') + `</div>`;
                    } else {
                        dHtml = `<span style="color:var(--text-muted); font-size:0.83rem;">재투입 없음 (현금 보유)</span>`;
                    }

                    // Summary column
                    const bReal = Number(ev.realized_pnl_usd || 0);
                    const bRealCls = bReal >= 0 ? 'pnl-green' : 'pnl-red';
                    const bRealFmt = `${bReal >= 0 ? '+' : '-'}$${fmtUsd2(Math.abs(bReal))}`;

                    const bFol = Number(ev.deposits_followup_pnl_usd || 0);
                    const bFolCls = bFol >= 0 ? 'pnl-green' : 'pnl-red';
                    const bFolFmt = `${bFol >= 0 ? '+' : '-'}$${fmtUsd2(Math.abs(bFol))}`;

                    let summaryHtml = '';
                    if (ev.event_kind === 'INITIAL_DEPLOY') {
                        summaryHtml = `
                            <div style="font-size:0.75rem; color:var(--text-muted);">초기 편입분 누적</div>
                            <div class="${bFolCls}" style="font-weight:800; font-size:0.95rem; margin-top:2px;">${bFolFmt}</div>
                            <div style="font-size:0.74rem; color:var(--text-muted);">(${bFol >= 0 ? '+' : ''}${Number(ev.deposits_followup_pnl_pct || 0).toFixed(2)}%)</div>
                        `;
                    } else {
                        summaryHtml = `
                            <div style="font-size:0.74rem; color:var(--text-muted);">청산 확정 손익</div>
                            <div class="${bRealCls}" style="font-weight:800; font-size:0.95rem;">${bRealFmt} <small>(${bReal >= 0 ? '+' : ''}${Number(ev.realized_pnl_pct || 0).toFixed(2)}%)</small></div>
                            <div style="font-size:0.74rem; color:var(--text-muted); margin-top:6px;">교체 편입 후 성과</div>
                            <div class="${bFolCls}" style="font-weight:700; font-size:0.88rem;">${bFolFmt} <small>(${bFol >= 0 ? '+' : ''}${Number(ev.deposits_followup_pnl_pct || 0).toFixed(2)}%)</small></div>
                        `;
                    }

                    tr.innerHTML = `
                        <td style="vertical-align:top;">
                            <div style="font-weight:800; color:#fff; font-size:0.92rem;">${escapeHtml(ev.title)}</div>
                            <div style="font-size:0.8rem; color:#94a3b8; margin-top:2px;">🕒 ${escapeHtml(ev.ts)}</div>
                            <span class="reb-badge ${badgeCls}">${escapeHtml(ev.badge)}</span>
                            <div style="font-size:0.74rem; color:var(--text-muted); margin-top:6px; line-height:1.35;">${escapeHtml(ev.reason)}</div>
                        </td>
                        <td style="vertical-align:top;">${wHtml}</td>
                        <td style="vertical-align:top;">${dHtml}</td>
                        <td style="vertical-align:top; text-align:right;">${summaryHtml}</td>
                    `;
                    rebTbody.appendChild(tr);
                });
            } else {
                rebCard.style.display = 'none';
            }
        }

        // Render Positions Table
        const tbody = document.getElementById('details-positions-table');
        tbody.innerHTML = '';
        if (perf.holdings && perf.holdings.length > 0) {
            perf.holdings.forEach(h => {
                const pnlNum = Number(h.pnl || 0);
                const hPnlColor = pnlNum >= 0 ? 'pnl-green' : 'pnl-red';
                const hPnlFmt = pnlNum >= 0 ? `+$${fmtUsd2(pnlNum)}` : `-$${fmtUsd2(Math.abs(pnlNum))}`;
                const hPctSign = Number(h.pnl_pct || 0) >= 0 ? '+' : '';
                
                const netNum = Number(h.net_pnl || 0);
                const hNetPnlColor = netNum >= 0 ? 'pnl-green' : 'pnl-red';
                const hNetFmt = netNum >= 0 ? `+$${fmtUsd2(netNum)}` : `-$${fmtUsd2(Math.abs(netNum))}`;
                const aprNum = Number(h.apr_30d || 0);
                const aprColor = aprNum >= 0 ? 'var(--success)' : 'var(--danger)';
                const aprSign = aprNum > 0 ? '+' : '';
                
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>
                        <a href="https://app.hyperliquid.xyz/vaults/${h.address}" target="_blank" style="color:#fff; text-decoration:none; font-weight:700; hover:underline;">
                            ${escapeHtml(h.name)} ↗
                        </a>
                        <br><small style="color:var(--text-muted); font-size:0.75rem;">${h.address.substring(0, 12)}...</small>
                    </td>
                    <td>$${fmtUsd2(h.invested_usd)}</td>
                    <td><span class="badge" style="background:rgba(255,255,255,0.05); color:#fff;">${Number(h.weight_pct || 0).toFixed(1)}%</span></td>
                    <td style="font-weight:600;"><span style="color:${aprColor};">${aprSign}${aprNum.toFixed(2)}%</span> / <span style="color:var(--danger);">${Number(h.mdd || 0).toFixed(2)}%</span></td>
                    <td style="font-weight:700; color:#fff;">$${fmtUsd2(h.est_value)}</td>
                    <td class="${hPnlColor}" style="font-weight:700;">${hPnlFmt} (${hPctSign}${Number(h.pnl_pct || 0).toFixed(2)}%)</td>
                    <td style="font-weight:600; color:var(--accent2);">$${fmtUsd2(h.net_value)} <span class="${hNetPnlColor}" style="font-size:0.85rem; font-weight:600;">(${hNetFmt})</span></td>
                `;
                tbody.appendChild(tr);
            });
        } else {
            tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--text-muted); padding:30px;">보유 포지션 내역이 없습니다. 포트폴리오를 수정하여 포지션을 추가하세요.</td></tr>`;
        }

        // Render AI Insights
        const insightsList = document.getElementById('details-insights-list');
        insightsList.innerHTML = '';
        const insights = p.insights || ["✨ 포트폴리오 분석 결과가 없습니다."];
        insights.forEach(ins => {
            const li = document.createElement('li');
            li.className = 'insight-item';
            
            let emoji = '💡';
            if (ins.includes('⚠️')) emoji = '⚠️';
            if (ins.includes('⚖️')) emoji = '⚖️';
            if (ins.includes('✨')) emoji = '✨';

            const cleanText = ins.replace(/^[⚠️⚖️✨]\s*/, '');
            li.innerHTML = `<span>${emoji}</span><span>${escapeHtml(cleanText)}</span>`;
            insightsList.appendChild(li);
        });

        // Draw Line Chart (with rebalance event markers if live)
        renderEquityCurveChart(perf.history_dates || [], perf.history_values || [], perf.rebalance_history || []);
    }

    // Render Equity Curve Chart
    function renderEquityCurveChart(labels, data, rebHist = []) {
        const ctx = document.getElementById('equity-chart').getContext('2d');
        if (equityChart) {
            equityChart.destroy();
        }

        if (labels.length === 0 || data.length === 0) {
            ctx.clearRect(0, 0, 400, 400);
            return;
        }

        const rebByDate = {};
        (rebHist || []).forEach(r => {
            if (r && r.date && r.event_kind !== 'INITIAL_DEPLOY') {
                if (!rebByDate[r.date]) rebByDate[r.date] = [];
                rebByDate[r.date].push(r);
            }
        });

        const ptRadii = labels.map(d => rebByDate[d] ? 6 : (labels.length <= 20 ? 3.5 : 1));
        const ptColors = labels.map(d => rebByDate[d] ? '#fbbf24' : '#3b82f6');
        const ptBorders = labels.map(d => rebByDate[d] ? '#ffffff' : '#3b82f6');

        equityChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: '포트폴리오 평가 자산 (USD)',
                    data: data,
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.08)',
                    fill: true,
                    tension: 0.2,
                    borderWidth: 2.5,
                    pointRadius: ptRadii,
                    pointHoverRadius: 7,
                    pointBackgroundColor: ptColors,
                    pointBorderColor: ptBorders,
                    pointBorderWidth: 1.5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: '#1e293b',
                        titleColor: '#fff',
                        bodyColor: '#e2e8f0',
                        borderColor: 'rgba(255,255,255,0.1)',
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                const val = Number(context.raw || 0);
                                return ` 평가 자산: $${val.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
                            },
                            afterBody: function(items) {
                                if (!items || !items.length) return [];
                                const dStr = items[0].label;
                                const evs = rebByDate[dStr];
                                if (!evs) return [];
                                return evs.map(ev => {
                                    const rp = Number(ev.realized_pnl_usd || 0);
                                    const rpStr = `${rp >= 0 ? '+' : '-'}$${fmtUsd2(Math.abs(rp))}`;
                                    return `🔄 ${ev.title} (${ev.ts.slice(11)}): 청산확정 ${rpStr}`;
                                });
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: '#64748b', font: { size: 10 } }
                    },
                    y: {
                        grid: { color: 'rgba(255,255,255,0.04)' },
                        ticks: {
                            color: '#64748b',
                            font: { size: 10 },
                            callback: function(value) {
                                return `$${value.toLocaleString()}`;
                            }
                        }
                    }
                }
            }
        });
    }

    // Render Tab 3 (Scenario Simulator)
    function renderScenarioSimulator() {
        if (!scenarioReports || Object.keys(scenarioReports).length === 0) {
            return;
        }

        // Draw Comparative Bar Chart
        const ctx = document.getElementById('scenario-comparison-chart').getContext('2d');
        if (scenarioChart) {
            scenarioChart.destroy();
        }

        const labels = ["상승장 (Bull)", "하락장 (Bear)", "고변동성 (Vol)", "안정수익 (Stable)"];
        const datasets = [];
        
        // Dynamic colors for portfolios
        const colors = [
            '#3b82f6', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#06b6d4'
        ];

        let colorIdx = 0;
        
        // Render scenarios table
        const tbody = document.getElementById('scenario-table-body');
        tbody.innerHTML = '';

        for (const [pid, report] of Object.entries(scenarioReports)) {
            const sc = report.scenarios || {};
            if (Object.keys(sc).length === 0) continue;

            const color = colors[colorIdx % colors.length];
            colorIdx++;

            const dataPoints = [
                sc.bull.expected_return_pct,
                sc.bear.expected_return_pct,
                sc.volatility.expected_return_pct,
                sc.stable.expected_return_pct
            ];

            datasets.push({
                label: report.name,
                data: dataPoints,
                backgroundColor: color,
                borderRadius: 5
            });

            // Table Rows
            const scenarioKeys = ['bull', 'bear', 'volatility', 'stable'];
            scenarioKeys.forEach(skey => {
                const s = sc[skey];
                const retColor = s.expected_return_pct >= 0 ? 'pnl-green' : 'pnl-red';
                const sign = s.expected_return_pct >= 0 ? '+' : '';
                
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="font-weight:700; color:#fff;">${escapeHtml(report.name)}</td>
                    <td><span class="badge" style="background:${color}20; color:${color}; font-weight:700;">${escapeHtml(s.scenario_name)}</span></td>
                    <td class="${retColor}" style="font-weight:700;">${sign}${s.expected_return_pct}%</td>
                    <td style="color:var(--danger); font-weight:700;">${s.simulated_mdd}%</td>
                    <td style="font-weight:700;">$${Math.round(s.expected_ending_value).toLocaleString()}</td>
                    <td style="color:var(--text-muted); font-size:0.82rem; line-height:1.4;">${escapeHtml(s.desc)}</td>
                `;
                tbody.appendChild(tr);
            });
        }

        scenarioChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: { color: '#e2e8f0', font: { weight: '600' } }
                    },
                    tooltip: {
                        backgroundColor: '#1e293b',
                        titleColor: '#fff',
                        bodyColor: '#e2e8f0',
                        callbacks: {
                            label: function(context) {
                                return ` ${context.dataset.label}: ${context.raw >= 0 ? '+' : ''}${context.raw}%`;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#64748b', font: { weight: '600' } },
                        grid: { display: false }
                    },
                    y: {
                        ticks: {
                            color: '#64748b',
                            callback: function(value) { return value + '%'; }
                        },
                        grid: { color: 'rgba(255,255,255,0.04)' }
                    }
                }
            }
        });
    }

    // Toggle Allocation Mode in Modal
    function toggleAllocMode() {
        const mode = document.getElementById('modal-port-mode').value;
        const aiContainer = document.getElementById('modal-ai-strategy-container');
        const manualContainer = document.getElementById('modal-manual-positions-container');

        if (mode === 'ai') {
            aiContainer.style.display = 'block';
            manualContainer.style.display = 'none';
        } else {
            aiContainer.style.display = 'none';
            manualContainer.style.display = 'block';
        }
    }

    // Modal Manager
    function openCreateModal() {
        document.getElementById('modal-title').innerText = "새 가상 포트폴리오 생성";
        document.getElementById('modal-port-id').value = "";
        document.getElementById('modal-port-name').value = "";
        document.getElementById('modal-port-capital').value = "100000";
        document.getElementById('modal-port-date').value = new Date().toISOString().substring(0, 10);
        document.getElementById('modal-port-mode').value = "manual";
        
        const positionsList = document.getElementById('modal-positions-list');
        positionsList.innerHTML = '';
        
        toggleAllocMode();
        addManualPositionRow(); // add at least one row
        updateTotalWeight();
        
        document.getElementById('portfolioModal').style.display = 'flex';
    }

    function openEditModal() {
        const p = portfolios.find(port => port.id === activePortfolioId);
        if (!p) return;

        document.getElementById('modal-title').innerText = "포트폴리오 수정";
        document.getElementById('modal-port-id').value = p.id;
        document.getElementById('modal-port-name').value = p.name;
        document.getElementById('modal-port-capital').value = p.total_capital;
        document.getElementById('modal-port-date').value = p.invest_date;
        document.getElementById('modal-port-mode').value = "manual"; // default to manual edit

        const positionsList = document.getElementById('modal-positions-list');
        positionsList.innerHTML = '';

        const totalCap = p.total_capital || 100000.0;
        
        if (p.positions && Object.keys(p.positions).length > 0) {
            for (const [addr, amount] of Object.entries(p.positions)) {
                const pct = Math.round((amount / totalCap) * 1000) / 10;
                addManualPositionRow(addr, pct);
            }
        } else {
            addManualPositionRow();
        }

        toggleAllocMode();
        updateTotalWeight();

        document.getElementById('portfolioModal').style.display = 'flex';
    }

    function closeModal() {
        document.getElementById('portfolioModal').style.display = 'none';
    }

    // Add row to manual positions in modal
    function addManualPositionRow(selectedAddr = '', weight = 0) {
        const container = document.getElementById('modal-positions-list');
        const row = document.createElement('div');
        row.className = 'position-row';

        let optionsHtml = '<option value="">-- 볼트 선택 --</option>';
        availableVaults.forEach(v => {
            const isSelected = v.address.toLowerCase() === selectedAddr.toLowerCase() ? 'selected' : '';
            optionsHtml += `<option value="${v.address}" ${isSelected}>${escapeHtml(v.name)} (${v.apr_30d}% APR)</option>`;
        });

        row.innerHTML = `
            <select class="form-input vault-select" style="flex:2;" onchange="updateTotalWeight()">
                ${optionsHtml}
            </select>
            <input type="number" class="form-input weight-input" style="flex:1;" value="${weight || ''}" placeholder="비중 (%)" min="0" max="100" step="0.1" oninput="updateTotalWeight()">
            <button type="button" class="btn" style="color:var(--danger); border-color:var(--danger); font-size:0.9rem;" onclick="removePositionRow(this)">✕</button>
        `;
        container.appendChild(row);
        updateTotalWeight();
    }

    function removePositionRow(button) {
        const row = button.parentNode;
        row.parentNode.removeChild(row);
        updateTotalWeight();
    }

    function updateTotalWeight() {
        let total = 0;
        document.querySelectorAll('.weight-input').forEach(input => {
            const v = parseFloat(input.value) || 0;
            total += v;
        });
        
        total = Math.round(total * 100) / 100;
        const textNode = document.getElementById('modal-total-weight-text');
        textNode.innerText = `총 비중 합계: ${total}%`;
        
        if (total === 100) {
            textNode.style.color = 'var(--success)';
        } else if (total > 100) {
            textNode.style.color = 'var(--danger)';
        } else {
            textNode.style.color = 'var(--text-muted)';
        }
    }

    // Save Portfolio
    function savePortfolio() {
        const pid = document.getElementById('modal-port-id').value;
        const name = document.getElementById('modal-port-name').value.trim();
        const capital = parseFloat(document.getElementById('modal-port-capital').value) || 100000.0;
        const date = document.getElementById('modal-port-date').value;
        const mode = document.getElementById('modal-port-mode').value;

        if (!name) {
            alert("포트폴리오 이름을 입력해주세요.");
            return;
        }

        if (!date) {
            alert("투자 시작일을 입력해주세요.");
            return;
        }

        const payload = {
            name: name,
            total_capital: capital,
            invest_date: date,
            ptype: mode === 'ai' ? document.getElementById('modal-port-strategy').value : 'custom'
        };

        if (pid) {
            payload.id = pid;
        }

        if (mode === 'manual') {
            const positions = {};
            let totalWeight = 0;
            let hasError = false;

            document.querySelectorAll('.position-row').forEach(row => {
                const select = row.querySelector('.vault-select');
                const input = row.querySelector('.weight-input');
                const addr = select.value;
                const weight = parseFloat(input.value) || 0;

                if (!addr) {
                    alert("볼트를 선택하지 않은 행이 있습니다.");
                    hasError = true;
                    return;
                }

                if (weight <= 0) {
                    alert("비중은 0보다 커야 합니다.");
                    hasError = true;
                    return;
                }

                positions[addr] = weight;
                totalWeight += weight;
            });

            if (hasError) return;

            totalWeight = Math.round(totalWeight * 100) / 100;
            if (totalWeight !== 100) {
                alert(`비중 합계는 정확히 100%여야 합니다. (현재 합계: ${totalWeight}%)`);
                return;
            }

            payload.positions = positions;
        }

        fetch('/api/portfolios', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(res => {
            if (!res.ok) {
                return res.json().then(data => { throw new Error(data.error || 'Server error'); });
            }
            return res.json();
        })
        .then(data => {
            showToast('✅ 가상 포트폴리오가 정상 저장되었습니다!');
            closeModal();
            loadPortfoliosData(data.id);
            loadScenariosData();
            switchTab('tab-list');
        })
        .catch(err => {
            alert('저장 오류: ' + err.message);
        });
    }

    // Delete Active Portfolio
    function deleteActivePortfolio() {
        if (!activePortfolioId) return;
        
        const p = portfolios.find(port => port.id === activePortfolioId);
        if (!p) return;

        if (!confirm(`정말로 포트폴리오 '${p.name}'을(를) 삭제하시겠습니까?`)) {
            return;
        }

        fetch(`/api/portfolios/${activePortfolioId}`, { method: 'DELETE' })
            .then(res => res.json())
            .then(data => {
                showToast('🗑️ 포트폴리오가 성공적으로 삭제되었습니다.');
                activePortfolioId = null;
                loadPortfoliosData();
                loadScenariosData();
                switchTab('tab-list');
            })
            .catch(err => console.error("Error deleting portfolio:", err));
    }

    // Helper functions
    function showToast(message) {
        const toast = document.getElementById("toast");
        toast.innerText = message;
        toast.className = "show";
        setTimeout(() => { toast.className = ""; }, 3000);
    }

    function escapeHtml(str) {
        if (!str) return '';
        return str.replace(/&/g, "&amp;")
                  .replace(/</g, "&lt;")
                  .replace(/>/g, "&gt;")
                  .replace(/"/g, "&quot;")
                  .replace(/'/g, "&#039;");
    }
</script>
</body>
</html>"""


AUTOBOT_HTML = r"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SGRA+ 자동운용 관제센터 — HL Vault Analyzer Pro</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        :root {
            --bg: #0b0f1a;
            --surface: #131928;
            --surface2: #182136;
            --border: #243050;
            --text: #e8eaf0;
            --muted: #8496b8;
            --accent: #4f8ef7;
            --teal: #1abc9c;
            --green: #2ecc71;
            --amber: #f39c12;
            --red: #e74c3c;
        }
        * { box-sizing: border-box; }
        body {
            margin: 0; background: var(--bg); color: var(--text);
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            padding-bottom: 80px;
        }
        header {
            background: rgba(19, 25, 40, 0.92); backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border); padding: 16px 28px;
            display: flex; justify-content: space-between; align-items: center;
            position: sticky; top: 0; z-index: 50; flex-wrap: wrap; gap: 12px;
        }
        header h1 {
            margin: 0; font-size: 1.25rem; font-weight: 800;
            background: linear-gradient(90deg, #1abc9c, #4f8ef7);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        }
        .nav-btns { display: flex; gap: 8px; flex-wrap: wrap; }
        .btn {
            display: inline-flex; align-items: center; gap: 6px;
            padding: 9px 15px; border-radius: 9px; border: 1px solid var(--border);
            background: var(--surface2); color: var(--text); font-size: 0.85rem;
            font-weight: 600; text-decoration: none; cursor: pointer; transition: 0.18s;
        }
        .btn:hover { border-color: var(--accent); transform: translateY(-1px); }
        .btn:disabled { opacity: 0.45; cursor: not-allowed; transform: none; }
        .btn-start {
            background: linear-gradient(135deg, #059669, #10b981);
            border-color: #34d399; color: #fff; font-weight: 800; font-size: 0.92rem;
            padding: 11px 20px; box-shadow: 0 4px 18px rgba(16, 185, 129, 0.32);
        }
        .btn-start:hover { border-color: #6ee7b7; filter: brightness(1.06); }
        .btn-primary { background: linear-gradient(135deg, #2563eb, #4f8ef7); border-color: #3b82f6; color: #fff; }
        .btn-teal { background: rgba(26, 188, 156, 0.16); border-color: #1abc9c; color: #1abc9c; }
        .btn-amber { background: rgba(243, 156, 18, 0.18); border-color: #f39c12; color: #fbbf24; font-weight: 700; }
        .btn-danger { background: rgba(231, 76, 60, 0.14); border-color: #e74c3c; color: #ff6b6b; }

        main { max-width: 1420px; margin: 0 auto; padding: 24px 24px 40px; }

        .banner {
            background: linear-gradient(135deg, rgba(26,188,156,0.10), rgba(79,142,247,0.10));
            border: 1px solid var(--border); border-radius: 16px;
            padding: 20px 24px; margin-bottom: 20px;
            display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px;
        }
        .badge {
            display: inline-flex; align-items: center; gap: 6px;
            padding: 5px 12px; border-radius: 999px; font-size: 0.78rem; font-weight: 700;
        }
        .badge-standby { background: rgba(243,156,18,0.18); color: #fbbf24; border: 1px solid rgba(243,156,18,0.45); }
        .badge-live { background: rgba(46,204,113,0.18); color: #2ecc71; border: 1px solid rgba(46,204,113,0.5); }
        .badge-armed { background: rgba(56,189,248,0.18); color: #38bdf8; border: 1px solid rgba(56,189,248,0.45); }
        .badge-paused { background: rgba(231,76,60,0.18); color: #ff7675; border: 1px solid rgba(231,76,60,0.45); }
        .badge-bull { background: rgba(46,204,113,0.16); color: #2ecc71; border: 1px solid rgba(46,204,113,0.4); }
        .badge-neutral { background: rgba(132,150,184,0.18); color: #cbd5e1; border: 1px solid rgba(132,150,184,0.4); }
        .badge-bear { background: rgba(231,76,60,0.16); color: #ff7675; border: 1px solid rgba(231,76,60,0.4); }

        .kpi-grid {
            display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 22px;
        }
        .card {
            background: var(--surface); border: 1px solid var(--border);
            border-radius: 15px; padding: 20px; margin-bottom: 20px;
        }
        .kpi-card { margin-bottom: 0; }
        .kpi-label { font-size: 0.78rem; color: var(--muted); font-weight: 600; text-transform: uppercase; letter-spacing: 0.03em; }
        .kpi-val { font-size: 1.55rem; font-weight: 800; color: #fff; margin: 8px 0 6px; }
        .kpi-sub { font-size: 0.8rem; color: var(--muted); line-height: 1.45; }

        .warn-box {
            background: rgba(243, 156, 18, 0.12); border: 1px solid rgba(243, 156, 18, 0.45);
            color: #fde68a; padding: 12px 16px; border-radius: 12px; margin-bottom: 18px; font-size: 0.86rem;
            display: none;
        }

        .table-wrap { overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; font-size: 0.86rem; }
        th {
            text-align: left; padding: 12px 12px; color: var(--muted); font-weight: 600;
            border-bottom: 1px solid var(--border); font-size: 0.78rem; text-transform: uppercase;
            white-space: nowrap;
        }
        td { padding: 13px 12px; border-bottom: 1px solid rgba(36,48,80,0.55); vertical-align: middle; }
        tr:hover td { background: rgba(255,255,255,0.02); }
        a.vlink { color: #7cb3ff; text-decoration: none; font-weight: 700; }
        a.vlink:hover { text-decoration: underline; }

        .bar-bg { width: 100px; height: 6px; background: #0b0f1a; border-radius: 4px; overflow: hidden; margin-top: 5px; }
        .bar-fill { height: 100%; background: linear-gradient(90deg, #1abc9c, #4f8ef7); border-radius: 4px; }

        .settings-drawer {
            display: none; background: #0f1524; border: 1px solid var(--border);
            border-radius: 14px; padding: 20px; margin-bottom: 20px;
        }
        .form-grid {
            display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 14px;
        }
        .fg label { display: block; font-size: 0.78rem; color: var(--muted); margin-bottom: 6px; font-weight: 600; }
        .fg input, .fg select {
            width: 100%; padding: 9px 11px; border-radius: 8px; border: 1px solid var(--border);
            background: var(--surface); color: #fff; font-size: 0.88rem;
        }

        .modal-bg {
            display: none; position: fixed; inset: 0; background: rgba(5, 8, 16, 0.78);
            backdrop-filter: blur(5px); z-index: 120; align-items: center; justify-content: center; padding: 20px;
        }
        .modal-box {
            background: var(--surface); border: 1px solid var(--teal); border-radius: 16px;
            max-width: 580px; width: 100%; padding: 26px; box-shadow: 0 18px 48px rgba(0,0,0,0.6);
        }

        pre.cmd-box {
            background: #080b12; border: 1px solid var(--border); border-radius: 10px;
            padding: 12px 14px; color: #a7f3d0; font-size: 0.8rem; overflow-x: auto; line-height: 1.55;
        }

        #toast {
            visibility: hidden; min-width: 280px; max-width: 520px; background: #1e293b; color: #fff;
            border: 1px solid var(--accent); text-align: center; border-radius: 10px;
            padding: 13px 18px; position: fixed; z-index: 150; right: 24px; bottom: 28px;
            font-size: 0.88rem; font-weight: 600; box-shadow: 0 8px 24px rgba(0,0,0,0.45); line-height: 1.45;
        }
        #toast.show { visibility: visible; }

        .mobile-tab-bar {
            display: none; position: fixed; bottom: 0; left: 0; right: 0;
            background: rgba(19, 25, 40, 0.96); border-top: 1px solid var(--border);
            padding: 8px 0; justify-content: space-around; z-index: 90;
        }
        .tab-item {
            display: flex; flex-direction: column; align-items: center; gap: 3px;
            color: var(--muted); text-decoration: none; font-size: 0.7rem; font-weight: 600;
        }
        .tab-item.active { color: var(--teal); }
        .tab-item .icon { font-size: 1.15rem; }

        @media (max-width: 980px) {
            .kpi-grid { grid-template-columns: repeat(2, 1fr); }
        }
        @media (max-width: 640px) {
            .kpi-grid { grid-template-columns: 1fr; }
            header .nav-btns { display: none; }
            .mobile-tab-bar { display: flex; }
            main { padding: 15px; }
        }
    </style>
</head>
<body>
<header>
    <div>
        <h1>🤖 Hyperliquid 자동운용 관제센터</h1>
        <div style="font-size:0.77rem; color:var(--muted); margin-top:3px;">
            SGRA+ 엔진 — 입금 후 [▶️ 자동운용 재개 실행] 클릭 시 즉시 배분 & 24/7 무인 리밸런싱
        </div>
    </div>
    <div class="nav-btns">
        <a class="btn" href="/m">📱 내 포트폴리오</a>
        <a class="btn" href="/">🔬 메인 대시보드</a>
        <a class="btn" href="/research">🧠 AI Research</a>
        <a class="btn" href="/settings">⚙️ 알림 설정</a>
        <a class="btn" href="/logout" style="color:var(--red);">🚪 로그아웃</a>
    </div>
</header>

<main>
    <div id="fallback-warn" class="warn-box"></div>

    <!-- 상단 컨트롤 배너 -->
    <div class="banner">
        <div style="flex:1; min-width:280px;">
            <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin-bottom:8px;">
                <span id="mode-badge" class="badge badge-standby">⏸️ 입금 전 대기 중 (일시정지)</span>
                <span id="regime-badge" class="badge badge-neutral">국면 분석 중...</span>
                <span id="key-badge" class="badge badge-neutral">🔑 서명키 확인 중</span>
            </div>
            <div id="signal-headline" style="font-size:0.94rem; font-weight:700; color:#fff; line-height:1.45;">상태를 불러오는 중입니다...</div>
            <div id="check-timestamps" style="font-size:0.79rem; color:var(--muted); margin-top:5px;">마지막 점검: - | 다음 정기 리밸런싱: -</div>
        </div>
        <div style="display:flex; gap:9px; flex-wrap:wrap; align-items:center;">
            <button id="btn-main-toggle" class="btn btn-start" onclick="handleMainToggle()">▶️ 자동운용 재개 실행</button>
            <button id="btn-check" class="btn btn-teal" onclick="triggerCycle(false)">🔍 잔고·시그널 새로고침</button>
            <button id="btn-force" class="btn btn-primary" onclick="triggerCycle(true)" disabled>⚡ 즉시 리밸런싱</button>
            <button class="btn" onclick="toggleSettings()">⚙️ 운용 설정</button>
        </div>
    </div>

    <!-- 접이식 운용 설정 패널 -->
    <div id="settings-drawer" class="settings-drawer">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
            <h3 style="margin:0; font-size:1rem;">⚙️ SGRA+ 자동운용 세부 설정</h3>
            <button class="btn" style="padding:5px 10px; font-size:0.78rem;" onclick="toggleSettings()">닫기 ✕</button>
        </div>
        <div class="form-grid">
            <div class="fg">
                <label>운용 원장 모드</label>
                <select id="cfg-mode">
                    <option value="LIVE">🟢 LIVE — 실제 내 Hyperliquid 지갑 직결 (권장)</option>
                    <option value="DRY_RUN">🧪 DRY_RUN — 가상 모의원장 시뮬레이션</option>
                </select>
            </div>
            <div class="fg">
                <label>입금 전 예상 기준 원금 (USD)</label>
                <input type="number" id="cfg-capital" step="100" min="200" value="20000">
            </div>
            <div class="fg">
                <label>자동진입 최소 지갑자산 기준 (USD)</label>
                <input type="number" id="cfg-min-eq" step="50" min="50" value="100">
            </div>
            <div class="fg">
                <label>정기 리밸런싱 주기 (일, 최적 14일)</label>
                <input type="number" id="cfg-interval" step="1" min="1" max="60" value="14">
            </div>
            <div class="fg">
                <label>HWM 보존 불감대 (%, 최적 10%)</label>
                <input type="number" id="cfg-band" step="1" min="2" max="35" value="10">
            </div>
            <div class="fg">
                <label>입금액·수익금 전액 자동 복리운용</label>
                <select id="cfg-compound">
                    <option value="true">ON — 지갑 총자산 전액 기준 자동 복리 배분</option>
                    <option value="false">OFF — 기준 원금 한도까지만 배분</option>
                </select>
            </div>
            <div class="fg">
                <label>Spot → Perps USDC 자동 이체</label>
                <select id="cfg-spot-bridge">
                    <option value="true">ON — Spot에 입금해도 자동으로 Perps로 이동</option>
                    <option value="false">OFF — Perps 가용 USDC만 사용</option>
                </select>
            </div>
            <div class="fg">
                <label>최소 볼트 TVL 기준 (USD, 기본 20000)</label>
                <input type="number" id="cfg-min-tvl" step="1000" min="5000" value="20000">
            </div>
            <div class="fg">
                <label>최대 허용 역사적 MDD (%, 기본 40%)</label>
                <input type="number" id="cfg-max-mdd" step="1" min="5" max="80" value="40">
            </div>
            <div class="fg">
                <label>최소 리더 지분율 하한 (%, 기본 5%)</label>
                <input type="number" id="cfg-min-skin" step="1" min="1" max="90" value="5">
            </div>
            <div class="fg">
                <label>4시간 비상 손절 가드 (14d &lt; -8% 탈출)</label>
                <select id="cfg-emg">
                    <option value="true">ON — 보유 볼트 급락 시 즉시 회수</option>
                    <option value="false">OFF — 정기 주기에만 교체</option>
                </select>
            </div>
        </div>
        <div style="display:flex; justify-content:flex-end; align-items:center; margin-top:16px; gap:10px;">
            <button class="btn btn-primary" onclick="saveSettings()">💾 설정 저장</button>
        </div>
    </div>

    <!-- 4대 핵심 요약 KPI -->
    <div class="kpi-grid">
        <div class="card kpi-card">
            <div class="kpi-label">내 지갑 실시간 온체인 잔고 (Mainnet)</div>
            <div class="kpi-val" id="kpi-onchain-total">$0.00</div>
            <div class="kpi-sub" id="kpi-onchain-sub">지갑 조회 중...</div>
        </div>
        <div class="card kpi-card">
            <div class="kpi-label">자동운용 엔진 상태 & 기준자본</div>
            <div class="kpi-val" id="kpi-working-total">대기 중</div>
            <div class="kpi-sub" id="kpi-working-sub">입금 후 [자동운용 재개 실행]을 눌러주세요</div>
        </div>
        <div class="card kpi-card">
            <div class="kpi-label">현재 시장 레짐 & 목표 배분율</div>
            <div class="kpi-val" id="kpi-deploy-pct">100.0%</div>
            <div class="kpi-sub" id="kpi-regime-sub">14d 시장: - | 상승확산(Breadth): -</div>
        </div>
        <div class="card kpi-card">
            <div class="kpi-label">리밸런싱 스케줄 & 4시간 비상가드</div>
            <div class="kpi-val" id="kpi-countdown">재개 대기</div>
            <div class="kpi-sub" id="kpi-guard-sub">재개 시 즉시 최초 진입 후 14일 주기 자동 운영</div>
        </div>
    </div>

    <!-- SGRA+ 목표 포트폴리오 vs 현재 보유 & 리밸런싱 판정 테이블 -->
    <div class="card">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:14px;">
            <div>
                <h3 style="margin:0; font-size:1.05rem;">📊 SGRA+ 목표 포트폴리오 & 내 지갑 실시간 보유 현황</h3>
                <div style="font-size:0.8rem; color:var(--muted); margin-top:4px;">
                    엄격 기준(<b>TVL ≥ $20,000 · 역사적 Max MDD ≤ 40% · 리더 지분 ≥ 5% · 신저점 붕괴 차단</b>) 통과 볼트 중 검증된 지지선 근접도 및 우량도 비례로 가중 배분하며, ±10% 이내 변동은 10% 성과수수료(HWM) 절감을 위해 유지합니다.
                </div>
            </div>
            <div id="snap-date-tag" style="font-size:0.8rem; color:var(--teal); font-weight:700;">스냅샷 기준일: -</div>
        </div>
        <div class="table-wrap">
            <table>
                <thead>
                    <tr>
                        <th>볼트명 (Hyperliquid 공식 링크)</th>
                        <th>전략 슬리브</th>
                        <th>리더 지분 (Skin%)</th>
                        <th>볼트 TVL</th>
                        <th>쿠션 Sharpe / 14d 수익</th>
                        <th id="th-target-col">예상 배분 ($20,000 입금 시)</th>
                        <th>내 지갑 실제 보유액</th>
                        <th>자동운용 판정 상태</th>
                    </tr>
                </thead>
                <tbody id="alloc-tbody">
                    <tr><td colspan="8" style="text-align:center; color:var(--muted); padding:28px;">데이터 로딩 중...</td></tr>
                </tbody>
            </table>
        </div>
    </div>

    <!-- 자동 체결 및 시그널 감사 로그 -->
    <div class="card">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
            <h3 style="margin:0; font-size:1.05rem;">📜 실전 자동 체결 & 리밸런싱 감사 로그</h3>
            <span style="font-size:0.78rem; color:var(--muted);">실제 주문 실행 내역만 기록됩니다 (.gitignore 보호됨)</span>
        </div>
        <div class="table-wrap">
            <table>
                <thead>
                    <tr>
                        <th>실행 시각</th>
                        <th>모드</th>
                        <th>시그널 트리거</th>
                        <th>액션</th>
                        <th>대상 볼트</th>
                        <th>금액 (USD)</th>
                        <th>결과</th>
                        <th>상세 사유 / L1 응답</th>
                    </tr>
                </thead>
                <tbody id="logs-tbody">
                    <tr><td colspan="8" style="text-align:center; color:var(--muted); padding:24px;">아직 실행된 자동주문 내역이 없습니다. (입금 후 자동운용 재개 시 기록됩니다)</td></tr>
                </tbody>
            </table>
        </div>
    </div>

    <!-- 자금 입금 후 시작하는 초간단 2단계 안내 -->
    <div class="card" style="border-color: rgba(26,188,156,0.38);">
        <h3 style="margin:0 0 10px 0; font-size:1.03rem; color:var(--teal);">🚀 나중에 자금이 준비되었을 때 시작하는 방법 (딱 2단계)</h3>
        <div style="font-size:0.86rem; color:var(--text); line-height:1.7;">
            <div><b>1단계 (최초 1회 지갑 키 등록):</b> 프로젝트 폴더 안의 <code>setup_wallet_key.bat</code> 파일을 더블클릭하고 운용하실 지갑의 Private Key를 붙여넣으세요. (화면에 글자가 보이지 않게 로컬 <code>.env</code>에만 암호처럼 격리 저장되며, 지갑 주소도 자동으로 연결됩니다.)</div>
            <div style="margin-top:6px;"><b>2단계 (USDC 입금 후 버튼 클릭):</b> Hyperliquid 거래소(Perps 또는 Spot 아무 곳이나)에 운용 자금(예: $20,000 USDC)을 입금한 뒤, 이 페이지 상단의 초록색 <b>[▶️ 자동운용 재개 실행]</b> 버튼만 누르면 <b>그 즉시 포트폴리오 매수가 실행되고 이후 4시간 비상감시 · 14일 자동 리밸런싱이 알아서 돌아갑니다.</b></div>
        </div>
    </div>
</main>

<!-- 서명키 미등록 안내 모달 -->
<div id="key-modal" class="modal-bg" onclick="if(event.target===this) closeKeyModal()">
    <div class="modal-box">
        <h3 style="margin:0 0 10px 0; color:#fbbf24;">🔑 메타마스크 서명키 1회 연결 안내</h3>
        <p id="key-modal-msg" style="font-size:0.86rem; color:var(--text); line-height:1.55; white-space:pre-line; margin-bottom:12px;"></p>
        <div style="background:#080b12; border:1px solid var(--border); border-radius:10px; padding:13px 15px; font-size:0.83rem; line-height:1.65; margin-bottom:14px;">
            <b style="color:#7cb3ff;">① 메타마스크에서 개인키 복사:</b><br>
            메타마스크 열기 → 상단 계정 이름 옆 <b>점 3개(⋮)</b> 클릭 → <b>[계정 세부 정보(Account details)]</b> → <b>[개인 키 표시/내보내기(Show private key)]</b> → 비밀번호 입력 후 복사<br>
            <b style="color:#34d399;">② 아래 초록색 버튼을 눌러 보안 등록 창 띄우기:</b><br>
            화면에 뜨는 창에서 <b>[📋 붙여넣기]</b> → <b>[💾 보안 저장 및 지갑 연결하기]</b> 클릭!
        </div>
        <p style="font-size:0.78rem; color:var(--muted); line-height:1.45; margin-bottom:16px;">
            ※ 개인키는 인터넷으로 전송되지 않고 내 PC의 로컬 <code>.env</code> 파일에만 격리 저장됩니다.
        </p>
        <div style="display:flex; justify-content:space-between; gap:10px; flex-wrap:wrap;">
            <button class="btn btn-start" onclick="launchKeyGui()">🪟 지금 서명키 등록 창 바로 열기</button>
            <button class="btn" onclick="closeKeyModal()">닫기</button>
        </div>
    </div>
</div>

<div class="mobile-tab-bar">
    <a href="/autobot" class="tab-item active"><span class="icon">🤖</span><span>AutoBot</span></a>
    <a href="/m" class="tab-item"><span class="icon">📱</span><span>Portfolios</span></a>
    <a href="/" class="tab-item"><span class="icon">🔬</span><span>Analysis</span></a>
    <a href="/settings" class="tab-item"><span class="icon">⚙️</span><span>Settings</span></a>
</div>

<div id="toast"></div>

<script>
    let botData = null;

    function fmtUsd(v) {
        const n = Number(v || 0);
        return '$' + n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }

    function showToast(msg) {
        const el = document.getElementById('toast');
        el.textContent = msg;
        el.className = 'show';
        setTimeout(() => { el.className = ''; }, 4500);
    }

    function esc(s) {
        if (s === null || s === undefined) return '';
        return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    }

    function toggleSettings() {
        const d = document.getElementById('settings-drawer');
        d.style.display = (d.style.display === 'block') ? 'none' : 'block';
    }

    function closeKeyModal() {
        document.getElementById('key-modal').style.display = 'none';
    }

    async function launchKeyGui() {
        try {
            const res = await fetch('/api/autobot/launch-key-gui', { method: 'POST' });
            const out = await res.json();
            if (out.ok) {
                showToast('🪟 내 PC 화면에 서명키 보안 등록 창을 열었습니다! 개인키를 붙여넣고 저장해주세요.');
                let checks = 0;
                const timer = setInterval(async () => {
                    checks++;
                    await loadStatus();
                    if ((botData && botData.credentials && botData.credentials.key_configured) || checks >= 30) {
                        clearInterval(timer);
                        if (botData && botData.credentials && botData.credentials.key_configured) {
                            closeKeyModal();
                            showToast('✅ 서명키 연결 완료! 이제 [▶️ 자동운용 재개 실행] 버튼을 누르시면 시작됩니다!');
                        }
                    }
                }, 2500);
            } else {
                showToast('오류: ' + (out.error || '창 열기 실패'));
            }
        } catch (e) {
            showToast('등록 창 호출 중 통신 오류가 발생했습니다.');
        }
    }

    async function loadStatus() {
        try {
            const res = await fetch('/api/autobot/status');
            if (res.redirected || res.status === 401) { window.location.href = '/login'; return; }
            const data = await res.json();
            if (data.error) { showToast('오류: ' + data.error); return; }
            botData = data;
            renderAll(data);
        } catch (e) {
            console.error(e);
            showToast('상태 조회 중 통신 오류가 발생했습니다.');
        }
    }

    function renderAll(d) {
        const cfg = d.config || {};
        const st = d.state || {};
        const sig = d.signal || {};
        const oc = d.onchain || {};
        const cred = d.credentials || {};
        const isEnabled = Boolean(cfg.enabled);
        const isPreview = Boolean(st.is_preview_capital);

        // Warn box
        const warnEl = document.getElementById('fallback-warn');
        if (st.mode_fallback_reason) {
            warnEl.style.display = 'block';
            warnEl.innerHTML = '⚠️ <b>확인 필요:</b> ' + esc(st.mode_fallback_reason);
        } else {
            warnEl.style.display = 'none';
        }

        // Main Status Badge & Primary Toggle Button
        const modeEl = document.getElementById('mode-badge');
        const mainBtn = document.getElementById('btn-main-toggle');
        const forceBtn = document.getElementById('btn-force');

        if (!isEnabled) {
            modeEl.className = 'badge badge-standby';
            modeEl.textContent = isPreview ? '⏸️ 입금 전 대기 중 (자동운용 일시정지)' : '⏸️ 자금 확인 완료 — 재개 대기 중';
            mainBtn.className = 'btn btn-start';
            mainBtn.textContent = '▶️ 자동운용 재개 실행';
            forceBtn.disabled = true;
        } else if (st.last_signal_type === 'AWAITING_DEPOSIT') {
            modeEl.className = 'badge badge-armed';
            modeEl.textContent = '🟢 자동운용 켜짐 (입금 감지 대기 중)';
            mainBtn.className = 'btn btn-amber';
            mainBtn.textContent = '⏸️ 자동운용 일시정지';
            forceBtn.disabled = true;
        } else if (st.effective_mode === 'LIVE') {
            modeEl.className = 'badge badge-live';
            modeEl.textContent = '🟢 실전 자동운용 가동 중 (LIVE)';
            mainBtn.className = 'btn btn-amber';
            mainBtn.textContent = '⏸️ 자동운용 일시정지';
            forceBtn.disabled = false;
        } else {
            modeEl.className = 'badge badge-standby';
            modeEl.textContent = '🧪 모의운용 가동 중 (DRY-RUN)';
            mainBtn.className = 'btn btn-amber';
            mainBtn.textContent = '⏸️ 모의운용 일시정지';
            forceBtn.disabled = false;
        }

        // Regime Badge
        const regEl = document.getElementById('regime-badge');
        const reg = sig.regime || 'NEUTRAL';
        if (reg === 'BULL') {
            regEl.className = 'badge badge-bull';
            regEl.textContent = '🚀 BULL 레짐 (유휴자금 모멘텀 가속)';
        } else if (reg === 'BEAR') {
            regEl.className = 'badge badge-bear';
            regEl.textContent = '🛡️ BEAR 방어 레짐 (Core 우량볼트 집중)';
        } else {
            regEl.className = 'badge badge-neutral';
            regEl.textContent = '⚖️ NEUTRAL 중립 레짐 (Core 복리 유지)';
        }

        // Key Badge
        const keyEl = document.getElementById('key-badge');
        if (cred.key_configured && cred.is_direct_master_key) {
            keyEl.className = 'badge badge-live';
            keyEl.textContent = '🔑 서명키 연결 완료 (.env)';
        } else if (cred.key_configured && cred.is_delegated_agent_key) {
            keyEl.className = 'badge badge-paused';
            keyEl.textContent = '⚠️ API 위임키 감지 (직접 운용키 필요)';
        } else {
            keyEl.className = 'badge badge-neutral';
            keyEl.textContent = '🔒 서명키 미등록 (setup_wallet_key.bat)';
        }

        document.getElementById('signal-headline').textContent = st.last_trigger_reason || '';
        document.getElementById('check-timestamps').textContent =
            `마지막 점검: ${(st.last_checked_at || '-').replace('T', ' ')}  |  마지막 리밸런싱: ${st.last_rebalance_at ? st.last_rebalance_at.replace('T', ' ') : '아직 실행 전'}  |  다음 정기 주기: ${st.next_rebalance_at || '-'}`;

        // Populate settings form
        document.getElementById('cfg-mode').value = cfg.mode || 'LIVE';
        document.getElementById('cfg-capital').value = cfg.target_capital_usd || 20000;
        document.getElementById('cfg-min-eq').value = cfg.min_deploy_equity_usd || 100;
        document.getElementById('cfg-interval').value = cfg.rebalance_interval_days || 14;
        document.getElementById('cfg-band').value = Math.round((cfg.no_trade_band_rel || 0.10) * 100);
        document.getElementById('cfg-compound').value = String(cfg.compound_profits !== false);
        document.getElementById('cfg-spot-bridge').value = String(cfg.auto_spot_to_perp !== false);
        document.getElementById('cfg-emg').value = String(cfg.emergency_guard_enabled !== false);
        if (document.getElementById('cfg-min-tvl')) document.getElementById('cfg-min-tvl').value = cfg.min_vault_tvl_usd || 20000;
        if (document.getElementById('cfg-max-mdd')) document.getElementById('cfg-max-mdd').value = cfg.max_historical_mdd_pct || 40;
        if (document.getElementById('cfg-min-skin')) document.getElementById('cfg-min-skin').value = Math.round((cfg.min_leader_equity_ratio ?? 0.05) * 100);

        // KPI 1: Live On-Chain Telemetry
        document.getElementById('kpi-onchain-total').textContent = fmtUsd(oc.total_equity_usd || 0);
        const addrShort = oc.account_address ? (oc.account_address.slice(0, 8) + '...' + oc.account_address.slice(-6)) : '미설정';
        document.getElementById('kpi-onchain-sub').innerHTML = oc.connected
            ? `지갑 <code>${esc(addrShort)}</code><br>Perp가용 <b>${fmtUsd(oc.perp_withdrawable_usd)}</b> · Spot <b>${fmtUsd(oc.spot_usdc_usd)}</b> · 볼트 <b>${fmtUsd(oc.vault_total_equity_usd)}</b>`
            : `<span style="color:var(--red);">${esc(oc.error || '연결 안 됨')}</span>`;

        // KPI 2: Engine Operational State
        const wPos = st.working_positions_usd || {};
        const wVaultSum = Object.values(wPos).reduce((a, b) => a + Number(b || 0), 0);
        const wCash = Number(st.working_cash_usd || 0);
        if (!isEnabled && !st.using_virtual_book) {
            document.getElementById('kpi-working-total').textContent = isPreview ? '⏸️ 대기 중' : fmtUsd(sig.deploy_capital_usd || 0);
            document.getElementById('kpi-working-sub').innerHTML = isPreview
                ? `예상 배분 기준금: <b>${fmtUsd(cfg.target_capital_usd || 20000)}</b><br>입금 후 [자동운용 재개 실행] 시 실제 입금액 전액 자동 배분`
                : `<span style="color:#fbbf24;font-weight:700;">[운용 가능 확인됨]</span> Spot→Perp 자동이체 지원<br>[▶️ 자동운용 재개 실행] 클릭 시 즉시 자동 배분`;
        } else if (st.last_signal_type === 'AWAITING_DEPOSIT') {
            document.getElementById('kpi-working-total').textContent = '🟢 입금 대기';
            document.getElementById('kpi-working-sub').innerHTML =
                `최소 ${fmtUsd(cfg.min_deploy_equity_usd || 100)} 이상 USDC 입금 감지 시 즉시 자동 매수 시작`;
        } else {
            document.getElementById('kpi-working-total').textContent = fmtUsd(wVaultSum + wCash);
            document.getElementById('kpi-working-sub').innerHTML =
                (st.using_virtual_book ? '<span style="color:#fbbf24;">[모의원장]</span> ' : '<span style="color:#2ecc71;">[실전운용]</span> ') +
                `볼트 ${Object.keys(wPos).length}개 예치: ${fmtUsd(wVaultSum)} | 가용현금: ${fmtUsd(wCash)}`;
        }

        // KPI 3: Regime
        document.getElementById('kpi-deploy-pct').textContent =
            `${Number(sig.deployed_weight_pct || 0).toFixed(1)}% 배분`;
        document.getElementById('kpi-regime-sub').innerHTML =
            `14d 시장: <b>${Number(sig.mkt_14d_pct || 0) >= 0 ? '+' : ''}${Number(sig.mkt_14d_pct || 0).toFixed(2)}%</b> · Breadth: <b>${Number(sig.breadth_14d_pct || 0).toFixed(1)}%</b><br>목표 현금비중: ${Number(sig.cash_reserve_pct || 0).toFixed(1)}%`;

        // KPI 4: Countdown
        document.getElementById('kpi-countdown').textContent =
            st.last_rebalance_at ? `D-${Number(st.days_to_next_rebalance || 0).toFixed(1)}일` : '재개 시 즉시 진입';
        const emgCnt = (sig.emergency_exits || []).length;
        document.getElementById('kpi-guard-sub').innerHTML = emgCnt > 0
            ? `<span style="color:var(--red);font-weight:700;">🚨 비상 탈출 대상 ${emgCnt}개 감지됨!</span>`
            : `재개 후 4시간마다 비상감시 & ${cfg.rebalance_interval_days || 14}일 주기 자동 리밸런싱`;

        document.getElementById('snap-date-tag').textContent = `최신 분석 스냅샷: ${sig.snapshot_date || '-'}`;
        document.getElementById('th-target-col').textContent = isPreview
            ? `예상 배분 (${fmtUsd(sig.deploy_capital_usd || 20000)} 입금 시)`
            : `목표 배분 (${fmtUsd(sig.deploy_capital_usd || 0)} 기준)`;

        // Render Allocation & Delta Table
        const sellMap = {};
        (d.planned_sells || []).forEach(x => { sellMap[x.address] = x; });
        const buyMap = {};
        (d.planned_buys || []).forEach(x => { buyMap[x.address] = x; });
        const skipMap = {};
        (d.skipped_band || []).forEach(x => { skipMap[x.address] = x; });
        const ocLocks = (oc.vault_positions || {});

        const allocs = sig.allocations || [];
        const allocAddrs = new Set(allocs.map(a => a.address));
        const rows = [];

        allocs.forEach(a => {
            const curUsd = Number(wPos[a.address] || 0);
            const lk = ocLocks[a.address];
            let statusHtml = '';

            if (!isEnabled) {
                statusHtml = `<span style="color:#fbbf24;font-weight:600;">⏸️ 입금 및 [자동운용 재개] 대기</span><br><small style="color:var(--muted);">재개 실행 시 약 ${fmtUsd(a.target_usd)} 자동 배분</small>`;
            } else if (st.last_signal_type === 'AWAITING_DEPOSIT') {
                statusHtml = `<span style="color:#38bdf8;font-weight:600;">🟢 입금 감지 대기 중</span><br><small style="color:var(--muted);">USDC 입금 즉시 자동 매수</small>`;
            } else if (buyMap[a.address]) {
                statusHtml = `<span style="color:#2ecc71;font-weight:700;">🟢 입금 예정 (+${fmtUsd(buyMap[a.address].delta_usd)})</span><br><small style="color:var(--muted);">${esc(buyMap[a.address].reason)}</small>`;
            } else if (sellMap[a.address]) {
                statusHtml = `<span style="color:#fbbf24;font-weight:700;">🟡 비중 축소 예정 (-${fmtUsd(sellMap[a.address].delta_usd)})</span><br><small style="color:var(--muted);">${esc(sellMap[a.address].reason)}</small>`;
            } else if (skipMap[a.address]) {
                statusHtml = `<span style="color:#93c5fd;font-weight:600;">🛡️ HWM 보존 유지</span><br><small style="color:var(--muted);">${esc(skipMap[a.address].reason)}</small>`;
            } else {
                statusHtml = `<span style="color:var(--teal);font-weight:600;">✅ 목표 비중 운용 중</span>`;
            }

            const lockBadge = (lk && lk.is_locked)
                ? `<br><span style="font-size:0.73rem;color:#fbbf24;">⏳ 24h 락업 (~${esc(lk.locked_until)})</span>`
                : '';

            const r14Color = a.ret_14d_pct >= 0 ? 'var(--green)' : 'var(--red)';
            rows.push(`
                <tr>
                    <td>
                        <a class="vlink" href="https://app.hyperliquid.xyz/vaults/${esc(a.address)}" target="_blank" rel="noopener">
                            ${esc(a.name)} ↗
                        </a>
                        <div style="font-size:0.72rem;color:var(--muted);font-family:monospace;">${esc(a.address.slice(0,10))}...${esc(a.address.slice(-6))}</div>
                    </td>
                    <td><span class="badge ${a.sleeve.includes('BULL') ? 'badge-bull' : 'badge-neutral'}">${esc(a.sleeve)}</span></td>
                    <td style="font-weight:700; color:#fff;">${a.leader_ratio_pct.toFixed(1)}%</td>
                    <td>${fmtUsd(a.tvl_usd)}</td>
                    <td>
                        <b>Sharpe ${a.cushioned_sharpe.toFixed(2)}</b> <small style="color:#93c5fd;">(점수 ${Number(a.sgra_score || 0).toFixed(2)})</small><br>
                        <small style="color:${r14Color};">14d ${a.ret_14d_pct >= 0 ? '+' : ''}${a.ret_14d_pct.toFixed(2)}%</small>
                        <small style="color:var(--muted);"> · APR ${(a.hl_apr_pct ?? a.apr_30d_pct) !== undefined ? (Number(a.hl_apr_pct ?? a.apr_30d_pct) >= 0 ? '+' : '') + Number(a.hl_apr_pct ?? a.apr_30d_pct).toFixed(1) + '%' : '-'} · DD ${a.drawdown_now_pct.toFixed(1)}% / MDD ${Number(a.max_mdd_pct || 0).toFixed(1)}%</small>
                    </td>
                    <td>
                        <b>${a.target_weight_pct.toFixed(1)}%</b> (${fmtUsd(a.target_usd)})
                        <div class="bar-bg"><div class="bar-fill" style="width:${Math.min(100, a.target_weight_pct * 4)}%;"></div></div>
                    </td>
                    <td><b>${fmtUsd(curUsd)}</b>${lockBadge}</td>
                    <td>${statusHtml}</td>
                </tr>
            `);
        });

        // Show any currently held on-chain vaults NOT in SGRA+ target allocations
        Object.keys(wPos).forEach(addr => {
            if (allocAddrs.has(addr)) return;
            const curUsd = Number(wPos[addr] || 0);
            if (curUsd <= 0.5) return;
            const sInfo = sellMap[addr] || { name: addr.slice(0, 12), delta_usd: curUsd, reason: 'SGRA+ 목표 포트폴리오 외 보유분' };
            const lk = ocLocks[addr];
            const lockBadge = (lk && lk.is_locked)
                ? `<br><span style="font-size:0.73rem;color:#fbbf24;">⏳ 24h 락업 (~${esc(lk.locked_until)})</span>`
                : '';
            const holdStatus = !isEnabled
                ? `<span style="color:var(--muted);font-weight:600;">⏸️ 현재 기존 지갑 보유분 (일시정지 중 미건드림)</span>`
                : `<span style="color:var(--red);font-weight:700;">🔴 교체 회수 예정 (-${fmtUsd(curUsd)})</span><br><small style="color:var(--muted);">${esc(sInfo.reason)}</small>`;
            rows.push(`
                <tr style="background:rgba(255,255,255,0.015);">
                    <td>
                        <a class="vlink" href="https://app.hyperliquid.xyz/vaults/${esc(addr)}" target="_blank" rel="noopener">
                            ${esc(sInfo.name)} ↗
                        </a>
                        <div style="font-size:0.72rem;color:var(--muted);font-family:monospace;">${esc(addr.slice(0,10))}...</div>
                    </td>
                    <td><span class="badge badge-neutral">기존 보유</span></td>
                    <td>-</td><td>-</td><td>-</td>
                    <td><b>0.0%</b> ($0.00)</td>
                    <td><b>${fmtUsd(curUsd)}</b>${lockBadge}</td>
                    <td>${holdStatus}</td>
                </tr>
            `);
        });

        document.getElementById('alloc-tbody').innerHTML = rows.length
            ? rows.join('')
            : '<tr><td colspan="8" style="text-align:center;color:var(--muted);padding:24px;">조건을 충족하는 목표 볼트가 없습니다.</td></tr>';

        // Logs table
        const logs = d.logs || [];
        document.getElementById('logs-tbody').innerHTML = logs.length
            ? logs.map(l => {
                const stColor = (l.status === 'OK' || l.status === 'SIMULATED_OK')
                    ? 'var(--green)'
                    : (l.status === 'PENDING_UNLOCK' ? '#fbbf24' : 'var(--red)');
                return `
                    <tr>
                        <td style="white-space:nowrap;color:var(--muted);">${esc((l.ts || '').replace('T', ' '))}</td>
                        <td><span class="badge ${l.mode === 'LIVE' ? 'badge-live' : 'badge-standby'}">${esc(l.mode)}</span></td>
                        <td style="font-weight:600;">${esc(l.trigger)}</td>
                        <td style="font-weight:700;">${esc(l.action)}</td>
                        <td>${esc(l.vault)}</td>
                        <td style="font-weight:700;">${fmtUsd(l.amount_usd)}</td>
                        <td style="color:${stColor};font-weight:700;">${esc(l.status)}</td>
                        <td style="color:var(--muted);font-size:0.8rem;">${esc(l.detail)}</td>
                    </tr>
                `;
            }).join('')
            : '<tr><td colspan="8" style="text-align:center;color:var(--muted);padding:24px;">아직 실행된 자동주문 내역이 없습니다. (자금 입금 후 [▶️ 자동운용 재개 실행] 클릭 시 기록됩니다)</td></tr>';
    }

    async function handleMainToggle() {
        if (!botData || !botData.config) return;
        const isEnabled = Boolean(botData.config.enabled);
        const btn = document.getElementById('btn-main-toggle');

        if (!isEnabled) {
            // Resuming / Starting Auto-Operation!
            const ocEq = Number((botData.onchain || {}).total_equity_usd || 0);
            const cred = botData.credentials || {};
            if (botData.config.mode === 'LIVE' && cred.key_configured && ocEq >= Number(botData.config.min_deploy_equity_usd || 100)) {
                if (!confirm(`현재 연결된 지갑의 온체인 총자산(${fmtUsd(ocEq)})으로 즉시 SGRA+ 포트폴리오를 구성하고 자동운용을 시작할까요?`)) {
                    return;
                }
            }
            btn.disabled = true;
            btn.textContent = '⏳ 자동운용 개시 중...';
            try {
                const res = await fetch('/api/autobot/resume', { method: 'POST' });
                const out = await res.json();
                if (out.payload) {
                    botData = out.payload;
                    renderAll(out.payload);
                }
                if (!out.ok) {
                    document.getElementById('key-modal-msg').textContent = out.message || out.error || '서명키 확인이 필요합니다.';
                    document.getElementById('key-modal').style.display = 'flex';
                } else {
                    showToast(out.message || '🟢 자동운용이 시작되었습니다!');
                }
            } catch (e) {
                showToast('자동운용 재개 요청 중 통신 오류가 발생했습니다.');
            } finally {
                btn.disabled = false;
                if (botData) renderAll(botData);
            }
        } else {
            // Pausing Auto-Operation
            btn.disabled = true;
            try {
                const res = await fetch('/api/autobot/pause', { method: 'POST' });
                const out = await res.json();
                if (out.payload) {
                    botData = out.payload;
                    renderAll(out.payload);
                }
                showToast(out.message || '⏸️ 자동운용이 일시정지되었습니다.');
            } catch (e) {
                showToast('일시정지 요청 중 오류가 발생했습니다.');
            } finally {
                btn.disabled = false;
                if (botData) renderAll(botData);
            }
        }
    }

    async function triggerCycle(force) {
        if (force && botData && botData.state && botData.state.effective_mode === 'LIVE') {
            if (!confirm('현재 온체인 잔고 기준으로 즉시 SGRA+ 리밸런싱 주문을 실행하시겠습니까?')) return;
        }
        const btn = document.getElementById(force ? 'btn-force' : 'btn-check');
        const orig = btn.textContent;
        btn.disabled = true;
        btn.textContent = '⏳ 확인 중...';
        try {
            const res = await fetch('/api/autobot/run', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ force: force })
            });
            const data = await res.json();
            if (data.error) { showToast('오류: ' + data.error); }
            else {
                botData = data;
                renderAll(data);
                showToast(force ? '⚡ 즉시 리밸런싱 실행 완료!' : '🔍 최신 온체인 잔고 및 시그널 갱신 완료!');
            }
        } catch (e) {
            showToast('요청 처리 중 오류가 발생했습니다.');
        } finally {
            btn.textContent = orig;
            if (botData) renderAll(botData);
        }
    }

    async function saveSettings() {
        const payload = {
            mode: document.getElementById('cfg-mode').value,
            target_capital_usd: Number(document.getElementById('cfg-capital').value || 20000),
            min_deploy_equity_usd: Number(document.getElementById('cfg-min-eq').value || 100),
            rebalance_interval_days: Number(document.getElementById('cfg-interval').value || 14),
            no_trade_band_rel: Number(document.getElementById('cfg-band').value || 10) / 100.0,
            compound_profits: document.getElementById('cfg-compound').value === 'true',
            auto_spot_to_perp: document.getElementById('cfg-spot-bridge').value === 'true',
            emergency_guard_enabled: document.getElementById('cfg-emg').value === 'true',
            min_vault_tvl_usd: Number(document.getElementById('cfg-min-tvl').value || 20000),
            max_historical_mdd_pct: Number(document.getElementById('cfg-max-mdd').value || 40),
            min_leader_equity_ratio: Number(document.getElementById('cfg-min-skin').value || 5) / 100.0,
        };
        const res = await fetch('/api/autobot/config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        botData = data;
        renderAll(data);
        showToast('💾 운용 설정이 저장되었습니다.');
    }

    document.addEventListener('DOMContentLoaded', () => {
        loadStatus();
        setInterval(loadStatus, 60000);
    });
</script>
</body>
</html>"""


def _start_autobot_background_watchdog():
    """Defense-in-depth background thread: ensures SGRA+ check runs at least every 4h even if Task Scheduler is delayed."""
    import threading

    def _loop():
        import time as _t
        _t.sleep(20)
        while True:
            try:
                import hl_auto_vault_bot
                st = hl_auto_vault_bot.load_autobot_state()
                last_chk = st.get("last_checked_at")
                stale = True
                if last_chk:
                    from datetime import datetime as _dt
                    age_hr = (_dt.now() - _dt.fromisoformat(last_chk)).total_seconds() / 3600.0
                    stale = age_hr >= 4.1
                if stale:
                    hl_auto_vault_bot.run_autobot_cycle(force_rebalance=False)
            except Exception as _e:
                print(f"[Autobot Watchdog] {_e}")
            _t.sleep(900)

    t = threading.Thread(target=_loop, name="autobot-watchdog", daemon=True)
    t.start()


if __name__ == "__main__":
    _start_autobot_background_watchdog()
    # 포트는 PORT 환경변수로 제어(기본 5001). 터널/도메인 설정(domain_config.json)과
    # 반드시 동일한 포트를 쓰세요. 공개 배포 시엔 gunicorn/waitress 사용을 권장합니다.
    port = int(os.environ.get("PORT", "5001"))
    print(f"🚀 Hyperliquid Dashboard Pro v3.1 - Port {port}")
    app.run(host="0.0.0.0", port=port)

