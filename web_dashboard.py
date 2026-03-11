#!/usr/bin/env python3
"""
Hyperliquid Vault Analyzer — 웹 대시보드
=========================================
실행: python web_dashboard.py
브라우저: http://localhost:5000
"""

import os, sys, json, glob, subprocess, threading
from datetime import datetime
from pathlib import Path
from threading import Lock
from flask import Flask, render_template_string, send_file, jsonify, request, redirect, url_for

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

app = Flask(__name__)

DATA_DIR       = "vault_data"
SNAPSHOTS_DIR  = os.path.join(DATA_DIR, "snapshots")
REPORTS_DIR    = os.path.join(DATA_DIR, "reports")
STATUS_FILE    = os.path.join(DATA_DIR, "status.json")
PORTFOLIO_FILE = os.path.join(DATA_DIR, "my_portfolio.json")
STOP_FLAG      = "emergency_stop.flag"

# ── 분석 상태 관리 ────────────────────────────────────────────────────────────
_analysis_running = False
_analysis_log     = []
_analysis_lock    = Lock()

def load_status_file() -> dict:
    """scheduler.py가 기록한 status.json 읽기"""
    try:
        if os.path.exists(STATUS_FILE):
            with open(STATUS_FILE, encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def load_portfolio_file() -> dict:
    try:
        if os.path.exists(PORTFOLIO_FILE):
            with open(PORTFOLIO_FILE, encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def is_emergency_stopped() -> bool:
    return os.path.exists(STOP_FLAG)

def today_str():
    return datetime.now().strftime("%Y-%m-%d")

def get_latest_snapshot():
    files = sorted(glob.glob(os.path.join(SNAPSHOTS_DIR, "*.json")), reverse=True)
    if not files:
        return None, None
    path = files[0]
    date = os.path.basename(path).replace(".json", "")
    with open(path, encoding="utf-8") as f:
        return json.load(f), date

def get_reports():
    files = sorted(glob.glob(os.path.join(REPORTS_DIR, "*.xlsx")), reverse=True)
    return [{"name": os.path.basename(f), "path": f,
             "size_kb": round(os.path.getsize(f) / 1024, 1),
             "date": os.path.basename(f).replace("vault_report_","").replace(".xlsx","")}
            for f in files]

def risk_label(vol):
    if vol < 25:  return "LOW"
    if vol < 55:  return "MODERATE"
    return "HIGH"

def risk_color(vol):
    if vol < 25:  return "#27AE60"
    if vol < 55:  return "#F39C12"
    return "#E74C3C"

def grade_color(grade):
    if "A+" in grade: return "#1abc9c"
    if "A"  in grade: return "#27AE60"
    if "B"  in grade: return "#3498db"
    if "C"  in grade: return "#F39C12"
    return "#E74C3C"

# ── HTML 템플릿 ───────────────────────────────────────────────────────────────
HTML = r"""
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Hyperliquid Vault Analyzer</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
  <style>
    :root {
      --bg:       #0b0f1a;
      --card:     #131928;
      --card2:    #1a2340;
      --border:   #243050;
      --accent:   #4f8ef7;
      --accent2:  #1abc9c;
      --text:     #e8eaf0;
      --muted:    #7b8db0;
      --danger:   #e74c3c;
      --warn:     #f39c12;
      --success:  #27ae60;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { background: var(--bg); color: var(--text); font-family: 'Inter', sans-serif; min-height: 100vh; }

    /* ── 헤더 ── */
    header {
      background: linear-gradient(135deg, #0d1b40 0%, #111e3d 50%, #0b1530 100%);
      border-bottom: 1px solid var(--border);
      padding: 20px 32px;
      display: flex; align-items: center; justify-content: space-between;
      position: sticky; top: 0; z-index: 100;
      backdrop-filter: blur(20px);
    }
    header .brand { display: flex; align-items: center; gap: 12px; }
    header .brand .logo {
      width: 40px; height: 40px; border-radius: 10px;
      background: linear-gradient(135deg, var(--accent), var(--accent2));
      display: flex; align-items: center; justify-content: center;
      font-size: 20px;
    }
    header .brand h1 { font-size: 1.25rem; font-weight: 700; }
    header .brand p  { font-size: 0.75rem; color: var(--muted); margin-top: 2px; }
    header .hd-right { display: flex; align-items: center; gap: 12px; }
    .badge-date {
      background: var(--card2); border: 1px solid var(--border);
      border-radius: 8px; padding: 6px 14px;
      font-size: 0.8rem; color: var(--muted);
    }

    /* ── 버튼 ── */
    .btn {
      display: inline-flex; align-items: center; gap: 8px;
      padding: 10px 20px; border-radius: 10px; font-size: 0.85rem;
      font-weight: 600; cursor: pointer; border: none; text-decoration: none;
      transition: all 0.2s; white-space: nowrap;
    }
    .btn-primary { background: linear-gradient(135deg, var(--accent), #6a9ff8); color: #fff; }
    .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(79,142,247,0.4); }
    .btn-success { background: linear-gradient(135deg, var(--accent2), #16a085); color: #fff; }
    .btn-success:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(26,188,156,0.4); }
    .btn-outline {
      background: transparent; color: var(--text);
      border: 1px solid var(--border);
    }
    .btn-outline:hover { background: var(--card2); border-color: var(--accent); }
    .btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none !important; }

    /* ── 레이아웃 ── */
    main { max-width: 1400px; margin: 0 auto; padding: 28px 24px; }
    .section-title {
      font-size: 1rem; font-weight: 700;
      color: var(--muted); letter-spacing: 0.08em; text-transform: uppercase;
      margin-bottom: 16px; display: flex; align-items: center; gap: 8px;
    }
    .section-title::after {
      content: ''; flex: 1; height: 1px; background: var(--border);
    }

    /* ── 통계 카드 ── */
    .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 32px; }
    .stat-card {
      background: var(--card); border: 1px solid var(--border);
      border-radius: 14px; padding: 20px;
      transition: transform 0.2s, border-color 0.2s;
    }
    .stat-card:hover { transform: translateY(-3px); border-color: var(--accent); }
    .stat-card .label { font-size: 0.72rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.06em; }
    .stat-card .value { font-size: 1.6rem; font-weight: 800; margin: 6px 0 2px; }
    .stat-card .sub   { font-size: 0.75rem; color: var(--muted); }
    .stat-card .icon  { font-size: 1.5rem; margin-bottom: 8px; }

    /* ── 추천 포트폴리오 카드 ── */
    .rec-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; margin-bottom: 32px; }
    .rec-card {
      background: var(--card); border: 1px solid var(--border);
      border-radius: 14px; padding: 18px 20px;
      transition: transform 0.2s, border-color 0.2s;
      position: relative; overflow: hidden;
    }
    .rec-card::before {
      content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
      background: linear-gradient(90deg, var(--accent), var(--accent2));
    }
    .rec-card:hover { transform: translateY(-3px); border-color: var(--accent); }
    .rec-card .rank-badge {
      position: absolute; top: 12px; right: 14px;
      width: 28px; height: 28px; border-radius: 50%;
      background: var(--card2); border: 1px solid var(--border);
      display: flex; align-items: center; justify-content: center;
      font-size: 0.7rem; font-weight: 700; color: var(--accent);
    }
    .rec-card .vault-name { font-size: 1rem; font-weight: 700; margin-bottom: 4px; padding-right: 36px; }
    .rec-card .vault-addr { font-size: 0.7rem; color: var(--muted); font-family: monospace; margin-bottom: 12px; }
    .rec-metrics { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 12px; }
    .rec-metric .mk { font-size: 0.7rem; color: var(--muted); }
    .rec-metric .mv { font-size: 0.9rem; font-weight: 600; margin-top: 2px; }
    .alloc-bar-wrap { margin-top: 10px; }
    .alloc-bar-wrap .alloc-label { display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--muted); margin-bottom: 4px; }
    .alloc-bar { height: 6px; border-radius: 3px; background: var(--border); overflow: hidden; }
    .alloc-bar .fill { height: 100%; border-radius: 3px; background: linear-gradient(90deg, var(--accent), var(--accent2)); transition: width 1s ease; }
    .grade-badge {
      display: inline-block; padding: 2px 8px; border-radius: 6px;
      font-size: 0.7rem; font-weight: 700;
    }
    .invest-amount {
      background: var(--card2); border-radius: 8px; padding: 8px 12px;
      margin-top: 10px; display: flex; justify-content: space-between; align-items: center;
    }
    .invest-amount .ia-label { font-size: 0.7rem; color: var(--muted); }
    .invest-amount .ia-value { font-size: 1rem; font-weight: 700; color: var(--accent2); }

    /* ── 상위 볼트 테이블 ── */
    .table-wrap {
      background: var(--card); border: 1px solid var(--border);
      border-radius: 14px; overflow: hidden; margin-bottom: 32px;
    }
    table { width: 100%; border-collapse: collapse; }
    thead tr { background: var(--card2); }
    th {
      padding: 12px 14px; text-align: left; font-size: 0.72rem;
      font-weight: 600; color: var(--muted); letter-spacing: 0.05em;
      text-transform: uppercase; white-space: nowrap;
    }
    td { padding: 10px 14px; font-size: 0.82rem; border-top: 1px solid var(--border); }
    tr:hover td { background: rgba(79,142,247,0.04); }
    .rank-num { color: var(--muted); font-size: 0.75rem; }
    .vault-nm { font-weight: 600; max-width: 200px; }
    .pos { color: var(--success); }
    .neg { color: var(--danger); }
    .neu { color: var(--muted); }

    /* ── 다운로드 섹션 ── */
    .download-section {
      background: var(--card); border: 1px solid var(--border);
      border-radius: 14px; padding: 24px; margin-bottom: 32px;
    }
    .dl-list { display: grid; gap: 10px; margin-top: 16px; }
    .dl-item {
      display: flex; align-items: center; justify-content: space-between;
      background: var(--card2); border: 1px solid var(--border);
      border-radius: 10px; padding: 14px 18px;
      transition: border-color 0.2s;
    }
    .dl-item:hover { border-color: var(--accent2); }
    .dl-item .dl-info { display: flex; align-items: center; gap: 12px; }
    .dl-item .dl-icon { font-size: 1.8rem; }
    .dl-item .dl-name { font-weight: 600; font-size: 0.9rem; }
    .dl-item .dl-meta { font-size: 0.72rem; color: var(--muted); margin-top: 2px; }

    /* ── 진행 표시 ── */
    #run-overlay {
      display: none; position: fixed; inset: 0;
      background: rgba(0,0,0,0.7); z-index: 999;
      align-items: center; justify-content: center;
      backdrop-filter: blur(6px);
    }
    #run-overlay.show { display: flex; }
    .run-box {
      background: var(--card); border: 1px solid var(--border);
      border-radius: 20px; padding: 40px; text-align: center; max-width: 420px; width: 90%;
    }
    .spinner {
      width: 56px; height: 56px; border-radius: 50%;
      border: 4px solid var(--border);
      border-top-color: var(--accent);
      animation: spin 0.8s linear infinite;
      margin: 0 auto 20px;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    .run-box h3 { font-size: 1.2rem; margin-bottom: 8px; }
    .run-box p  { font-size: 0.85rem; color: var(--muted); }

    /* ── 요약 패널 ── */
    .sim-total {
      background: linear-gradient(135deg, #0d1b40, #111e3d);
      border: 1px solid var(--accent);
      border-radius: 14px; padding: 20px 24px;
      margin-bottom: 32px;
      display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 16px;
    }
    .sim-total .st-item .stk { font-size: 0.72rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; }
    .sim-total .st-item .stv { font-size: 1.5rem; font-weight: 800; margin-top: 4px; }
    .stv.green  { color: var(--accent2); }
    .stv.blue   { color: var(--accent); }

    .empty { text-align: center; padding: 60px; color: var(--muted); }
    .empty .em-icon { font-size: 3rem; margin-bottom: 12px; }
  </style>
</head>
<body>

<header>
  <div class="brand">
    <div class="logo">📊</div>
    <div>
      <h1>Hyperliquid Vault Analyzer</h1>
      <p>Robust Curve Edition — TVL &gt; $12K · MDD ≤ 25%</p>
    </div>
  </div>
  <div class="hd-right">
    <span class="badge-date" id="snap-date">{% if date %}분석일: {{ date }}{% else %}데이터 없음{% endif %}</span>
    <a class="btn btn-outline" href="/portfolio">🔬 포트폴리오 분석</a>
    <a class="btn btn-outline" href="/download-guide" download="집PC_설치가이드.txt">📄 설치가이드</a>
    <button class="btn btn-outline" onclick="location.reload()">🔄 새로고침</button>
    <button class="btn btn-primary" id="run-btn" onclick="runAnalysis()">⚡ 지금 분석 실행</button>
  </div>
</header>

<main>

{% if not vaults %}
  <div class="empty">
    <div class="em-icon">🔍</div>
    <p>아직 분석 데이터가 없습니다.<br>위의 <strong>"지금 분석 실행"</strong> 버튼을 눌러주세요.</p>
  </div>
{% else %}

  <!-- ── 통계 요약 ── -->
  <p class="section-title">📈 시장 현황</p>
  <div class="stats-grid">
    <div class="stat-card">
      <div class="icon">🏦</div>
      <div class="label">분석 볼트</div>
      <div class="value">{{ stats.total }}</div>
      <div class="sub">TVL ≥ $12,000 필터</div>
    </div>
    <div class="stat-card">
      <div class="icon">📉</div>
      <div class="label">평균 최대낙폭(MDD)</div>
      <div class="value" style="color:{% if stats.avg_mdd < 20 %}#27AE60{% elif stats.avg_mdd < 40 %}#F39C12{% else %}#E74C3C{% endif %}">{{ stats.avg_mdd }}%</div>
      <div class="sub">전체 200개 기준</div>
    </div>
    <div class="stat-card">
      <div class="icon">📊</div>
      <div class="label">평균 샤프비율</div>
      <div class="value">{{ stats.avg_sharpe }}</div>
      <div class="sub">리스크 대비 수익</div>
    </div>
    <div class="stat-card">
      <div class="icon">🌿</div>
      <div class="label">평균 로버스트니스</div>
      <div class="value" style="color:var(--accent2)">{{ stats.avg_robustness }}</div>
      <div class="sub">수익곡선 안정성 (0~1)</div>
    </div>
    <div class="stat-card">
      <div class="icon">💰</div>
      <div class="label">중앙값 30일 APR</div>
      <div class="value" style="color:var(--accent)">{{ stats.median_apr }}%</div>
      <div class="sub">이상치 제외 중앙값</div>
    </div>
  </div>

  <!-- ── $100K 시뮬레이션 총합 ── -->
  {% if recs %}
  <p class="section-title">💼 $100,000 포트폴리오 요약</p>
  <div class="sim-total">
    <div class="st-item">
      <div class="stk">투자 원금</div>
      <div class="stv blue">$100,000</div>
    </div>
    <div class="st-item">
      <div class="stk">예상 월 수익</div>
      <div class="stv green">${{ sim.monthly }}</div>
    </div>
    <div class="st-item">
      <div class="stk">예상 연 수익</div>
      <div class="stv green">${{ sim.annual }}</div>
    </div>
    <div class="st-item">
      <div class="stk">추천 볼트 수</div>
      <div class="stv blue">{{ recs|length }}개</div>
    </div>
    <div class="st-item">
      <div class="stk">MDD 상한</div>
      <div class="stv" style="color:var(--warn)">≤ 35%</div>
    </div>
    <div class="st-item">
      <div class="stk">최소 수익곡선등급</div>
      <div class="stv" style="color:#3498db">C 이상</div>
    </div>
    <div class="st-item">
      <div class="stk">필터: 리더 에쿼티</div>
      <div class="stv" style="color:var(--accent2)">≥ 40%</div>
    </div>
  </div>

  <!-- ── 추천 볼트 카드 ── -->
  <p class="section-title">⭐ 투자 추천 포트폴리오</p>
  <div class="rec-grid">
    {% for v in recs %}
    {% set invest = (v.suggested_allocation / 100 * 100000) %}
    {% set monthly = invest * v.apr_30d / 100 / 12 %}
    <div class="rec-card">
      <div class="rank-badge">{{ loop.index }}</div>
      <div class="vault-name">{{ v.name }}</div>
      <div class="vault-addr">{{ v.address[:20] }}…</div>
      <div class="rec-metrics">
        <div class="rec-metric">
          <div class="mk">30일 APR</div>
          <div class="mv {% if v.apr_30d > 0 %}pos{% else %}neg{% endif %}">{{ "%.1f"|format(v.apr_30d) }}%</div>
        </div>
        <div class="rec-metric">
          <div class="mk">샤프비율</div>
          <div class="mv">{{ "%.2f"|format(v.sharpe_ratio) }}</div>
        </div>
        <div class="rec-metric">
          <div class="mk">최대낙폭(MDD)</div>
          <div class="mv {% if v.max_drawdown < 15 %}pos{% elif v.max_drawdown < 30 %}" style="color:var(--warn)"{% else %}neg{% endif %}">{{ "%.1f"|format(v.max_drawdown) }}%</div>
        </div>
        <div class="rec-metric">
          <div class="mk">수익곡선등급</div>
          <div class="mv">
            <span class="grade-badge" style="background:{{ v.grade_color }}22; color:{{ v.grade_color }}">
              {{ v.equity_curve_grade.split('(')[0].strip() if v.equity_curve_grade != '-' else '-' }}
            </span>
          </div>
        </div>
        <div class="rec-metric">
          <div class="mk">로버스트(0~1)</div>
          <div class="mv" style="color:var(--accent2)">{{ "%.3f"|format(v.robustness_score) }}</div>
        </div>
        <div class="rec-metric">
          <div class="mk">리더 에쿼티</div>
          <div class="mv" style="color:var(--accent2)">{{ "%.1f"|format(v.leader_equity_ratio * 100) }}%</div>
        </div>
        <div class="rec-metric">
          <div class="mk">TVL</div>
          <div class="mv">${{ "{:,.0f}".format(v.tvl) }}</div>
        </div>
      </div>
      <div class="alloc-bar-wrap">
        <div class="alloc-label">
          <span>배분 비중</span>
          <span>{{ "%.1f"|format(v.suggested_allocation) }}%</span>
        </div>
        <div class="alloc-bar">
          <div class="fill" style="width:{{ v.suggested_allocation }}%"></div>
        </div>
      </div>
      <div class="invest-amount">
        <div>
          <div class="ia-label">투자 금액</div>
          <div class="ia-value">${{ "{:,.0f}".format(invest) }}</div>
        </div>
        <div style="text-align:right">
          <div class="ia-label">예상 월 수익</div>
          <div class="ia-value">+${{ "{:,.0f}".format(monthly) }}</div>
        </div>
      </div>
    </div>
    {% endfor %}
  </div>
  {% endif %}

  <!-- ── APR 분포 차트 (ECharts) ── -->
  <p class="section-title">📊 볼트 APR 분포</p>
  <div style="background:var(--card);border:1px solid var(--border);border-radius:14px;padding:20px;margin-bottom:32px;">
    <div id="apr-dist-chart" style="height:220px;"></div>
  </div>

  <!-- ── 상위 50 볼트 테이블 ── -->
  <p class="section-title">🏆 상위 50 볼트 (입금 가능 · 종합점수 기준)</p>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>순위</th>
          <th>볼트명</th>
          <th>생성일</th>
          <th>운영기간</th>
          <th>30일 APR</th>
          <th>샤프비율</th>
          <th>MDD</th>
          <th>수익곡선등급</th>
          <th>로버스트</th>
          <th>리더 에쿼티</th>
          <th>TVL ($)</th>
          <th>종합점수</th>
          <th>입금</th>
        </tr>
      </thead>
      <tbody>
        {% set deposit_vaults = vaults | selectattr('allow_deposits', 'true') | list %}
        {% for v in deposit_vaults[:50] %}
        <tr>
          <td class="rank-num">{{ v.rank }}</td>
          <td class="vault-nm">{{ v.name }}</td>
          <td class="neu" style="font-size:0.78rem; white-space:nowrap">{{ v.get('created_at', '-') }}</td>
          <td class="{% if v.get('age_days', 0) >= 180 %}pos{% elif v.get('age_days', 0) >= 60 %}neu{% else %}neg{% endif %}" style="text-align:right">
            {{ v.get('age_days', 0) }}일
          </td>
          <td class="{% if v.apr_30d > 0 %}pos{% else %}neg{% endif %}">{{ "%.1f"|format(v.apr_30d) }}%</td>
          <td class="{% if v.sharpe_ratio > 0 %}pos{% else %}neg{% endif %}">{{ "%.2f"|format(v.sharpe_ratio) }}</td>
          <td class="{% if v.max_drawdown < 20 %}pos{% elif v.max_drawdown < 50 %}neu{% else %}neg{% endif %}">{{ "%.1f"|format(v.max_drawdown) }}%</td>
          <td>
            {% if v.equity_curve_grade != '-' %}
            <span class="grade-badge" style="background:{{ v.grade_color }}22; color:{{ v.grade_color }}">
              {{ v.equity_curve_grade.split('(')[0].strip() }}
            </span>
            {% else %}<span class="neu">-</span>{% endif %}
          </td>
          <td class="{% if v.robustness_score >= 0.6 %}pos{% elif v.robustness_score >= 0.35 %}neu{% else %}neg{% endif %}">
            {{ "%.3f"|format(v.robustness_score) }}
          </td>
          <td class="{% if v.leader_equity_ratio >= 0.4 %}pos{% else %}neu{% endif %}">
            {{ "%.1f"|format(v.leader_equity_ratio * 100) }}%
          </td>
          <td>${{ "{:,.0f}".format(v.tvl) }}</td>
          <td style="font-weight:700; color:var(--accent)">{{ "%.2f"|format(v.score) }}</td>
          <td>{% if v.allow_deposits %}<span class="pos">✓</span>{% else %}<span class="neg">✗</span>{% endif %}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>

{% endif %}

  <!-- ── 다운로드 섹션 ── -->
  <p class="section-title">⬇️ Excel 리포트 다운로드</p>
  <div class="download-section">
    <p style="color:var(--muted); font-size:0.85rem; margin-bottom:4px;">
      분석 결과가 담긴 Excel 파일을 다운로드합니다.
      6개 시트: 상위200랭킹 · 일별변화 · 투자추천 · 월별리밸런싱 · 분석요약 · $100K시뮬레이션
    </p>
    {% if reports %}
    <div class="dl-list">
      {% for r in reports %}
      <div class="dl-item">
        <div class="dl-info">
          <div class="dl-icon">📊</div>
          <div>
            <div class="dl-name">{{ r.name }}</div>
            <div class="dl-meta">분석일: {{ r.date }} &nbsp;|&nbsp; 파일크기: {{ r.size_kb }} KB</div>
          </div>
        </div>
        <a class="btn btn-success" href="/download/{{ r.name }}" download>
          ⬇️ 다운로드
        </a>
      </div>
      {% endfor %}
    </div>
    {% else %}
    <div class="empty">
      <div class="em-icon">📭</div>
      <p>아직 생성된 리포트가 없습니다.<br>"지금 분석 실행"을 먼저 실행해주세요.</p>
    </div>
    {% endif %}
  </div>

</main>

<!-- ── 분석 실행 오버레이 ── -->
<div id="run-overlay">
  <div class="run-box">
    <div class="spinner"></div>
    <h3>분석 실행 중...</h3>
    <p>약 2~5분 소요됩니다.<br>200개 볼트 데이터를 수집하고 있습니다.</p>
    <p id="run-log" style="margin-top:12px; font-size:0.72rem; color:var(--accent2); min-height:18px;">준비 중...</p>
    <p style="margin-top:8px; font-size:0.72rem; color:var(--muted);">완료되면 자동으로 새로고침됩니다.</p>
  </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {

// ── APR 분포 차트 ECharts (/chart_data API) ──────────────────────────────
(function(){
  const el = document.getElementById('apr-dist-chart');
  if (!el) return;
  // 컨테이너 크기 명시
  el.style.width  = '100%';
  el.style.height = '240px';
  const chart = echarts.init(el, null, {renderer:'canvas'});
  chart.showLoading({text:'로딩 중...',textColor:'#7b8db0',maskColor:'rgba(11,15,26,.7)',color:'#4f8ef7'});

  fetch('/chart_data')
    .then(r => r.json())
    .then(d => {
      chart.hideLoading();
      if (d.error) {
        el.innerHTML = '<p style="color:#7b8db0;text-align:center;padding:60px">데이터 없음 — 분석 먼저 실행하세요</p>';
        return;
      }
      const hist = d.apr_hist;
      const colors = hist.labels.map(l => {
        const v = parseFloat(l);
        if (v < 0)   return 'rgba(231,76,60,.85)';
        if (v < 10)  return 'rgba(243,156,18,.85)';
        if (v < 30)  return 'rgba(79,142,247,.85)';
        return 'rgba(26,188,156,.85)';
      });
      chart.setOption({
        backgroundColor: 'transparent',
        tooltip: {
          trigger:'axis', axisPointer:{type:'shadow'},
          backgroundColor:'#131928', borderColor:'#243050', borderWidth:1,
          textStyle:{color:'#e8eaf0'},
          formatter: params => `<b>${params[0].name}</b>&nbsp; ${params[0].value}개 볼트`
        },
        grid: {top:16, left:52, right:16, bottom:68, containLabel:false},
        xAxis: {
          type:'category', data: hist.labels,
          axisLabel:{color:'#7b8db0', fontSize:10, rotate:45, interval:1},
          axisLine:{lineStyle:{color:'#243050'}}
        },
        yAxis: {
          type:'value',
          splitLine:{lineStyle:{color:'rgba(36,48,80,.55)'}},
          axisLabel:{color:'#7b8db0'}, axisLine:{lineStyle:{color:'#243050'}}
        },
        series: [{
          type:'bar', data: hist.counts, barWidth:'75%',
          itemStyle:{color: p => colors[p.dataIndex], borderRadius:[3,3,0,0]},
          emphasis:{itemStyle:{opacity:1, shadowBlur:8, shadowColor:'rgba(79,142,247,.5)'}},
          label:{show:true, position:'top', color:'#7b8db0', fontSize:9,
                 formatter: p => p.value > 0 ? p.value : ''}
        }]
      });
      chart.resize();
    })
    .catch(() => { chart.hideLoading(); });
  window.addEventListener('resize', () => chart.resize());
})();

}); // DOMContentLoaded

// ── 분석 실행 ────────────────────────────────────────────────────────────────
function runAnalysis() {
  const overlay = document.getElementById('run-overlay');
  const btn = document.getElementById('run-btn');
  const logEl = document.getElementById('run-log');
  overlay.classList.add('show');
  btn.disabled = true;
  if (logEl) logEl.textContent = '분석 시작 중...';

  fetch('/run-analysis', { method: 'POST' })
    .then(r => r.json())
    .then(d => {
      if (d.status === 'started' || d.status === 'already_running') {
        pollStatus();
      } else {
        alert('분석 시작 실패: ' + (d.message || '알 수 없는 오류'));
        overlay.classList.remove('show');
        btn.disabled = false;
      }
    })
    .catch(() => {
      overlay.classList.remove('show');
      btn.disabled = false;
    });
}

function pollStatus() {
  fetch('/analysis-status')
    .then(r => r.json())
    .then(d => {
      const logEl = document.getElementById('run-log');
      if (logEl && d.log && d.log.length > 0) {
        logEl.textContent = d.log[d.log.length - 1];
      }
      if (d.running) {
        setTimeout(pollStatus, 2000);
      } else {
        location.reload();
      }
    })
    .catch(() => setTimeout(pollStatus, 4000));
}
</script>
</body>
</html>
"""

# ── 라우트 ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    vaults, date = get_latest_snapshot()
    reports = get_reports()

    if not vaults:
        return render_template_string(HTML, vaults=[], recs=[], stats={}, sim={},
                                      date=None, reports=reports)

    # 통계
    valid = [v for v in vaults if v.get("data_points", 0) >= 3]
    import numpy as np
    stats = {}
    if valid:
        stats["total"]           = len(vaults)
        stats["avg_mdd"]         = round(float(np.mean([v["max_drawdown"] for v in valid])), 1)
        stats["avg_sharpe"]      = round(float(np.mean([v["sharpe_ratio"] for v in valid])), 2)
        stats["avg_robustness"]  = round(float(np.mean([v.get("robustness_score", 0) for v in valid])), 3)
        stats["median_apr"]      = round(float(np.median([v["apr_30d"] for v in valid])), 1)
    else:
        stats = dict(total=len(vaults), avg_mdd=0, avg_sharpe=0, avg_robustness=0, median_apr=0)

    # 추천 볼트 (robustness 필터) - 최대 30개로 상한 확장
    from analyze_top_vaults import get_recommendations
    recs_raw = get_recommendations(vaults, top_k=10)

    # 색상 추가
    for v in vaults:
        v["grade_color"] = grade_color(v.get("equity_curve_grade", "-"))
    for v in recs_raw:
        v["grade_color"] = grade_color(v.get("equity_curve_grade", "-"))

    # 시뮬레이션 합계
    sim_amount = 100_000
    total_monthly = sum(v["suggested_allocation"] / 100 * sim_amount * v.get("apr_30d", 0) / 100 / 12 for v in recs_raw)
    total_annual  = sum(v["suggested_allocation"] / 100 * sim_amount * v.get("apr_30d", 0) / 100       for v in recs_raw)
    sim = dict(
        monthly=f"{total_monthly:,.0f}",
        annual =f"{total_annual:,.0f}",
    )

    return render_template_string(HTML,
        vaults=vaults, recs=recs_raw,
        stats=stats, sim=sim,
        date=date, reports=reports)



# ── 포트폴리오 분석 페이지 ──────────────────────────────────────────────────
@app.route("/portfolio")
def portfolio_page():
    try:
        from portfolio_engine import run_portfolio_analysis
        d = run_portfolio_analysis(top_k=25, max_corr=0.55)
    except Exception as e:
        return render_template_string(PORTFOLIO_HTML, err=str(e), d=None, bt_json="null")
    if "error" in d:
        return render_template_string(PORTFOLIO_HTML, err=d["error"], d=None, bt_json="null")
    pfs = d["portfolios"]
    min_len = min(len(pfs[k]["backtest"].get("equity_curve",[1])) for k in pfs)
    import json as _j
    bt_json = _j.dumps({
        "sh": pfs["max_sharpe"]["backtest"].get("equity_curve",[])[:min_len],
        "mv": pfs["min_variance"]["backtest"].get("equity_curve",[])[:min_len],
        "rp": pfs["risk_parity"]["backtest"].get("equity_curve",[])[:min_len],
        "cv": pfs["min_cvar"]["backtest"].get("equity_curve",[])[:min_len],
    })
    return render_template_string(PORTFOLIO_HTML, err=None, d=d, bt_json=bt_json)





# ── 포트폴리오 분석 페이지 ──────────────────────────────────────────────────
PORTFOLIO_HTML = """
<!DOCTYPE html><html lang="ko">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>포트폴리오 분석</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
<style>
:root{--bg:#0b0f1a;--card:#131928;--card2:#1a2340;--border:#243050;
      --accent:#4f8ef7;--accent2:#1abc9c;--text:#e8eaf0;--muted:#7b8db0;
      --danger:#e74c3c;--warn:#f39c12;--success:#27ae60;}
*{box-sizing:border-box;margin:0;padding:0;}
body{background:var(--bg);color:var(--text);font-family:'Inter',sans-serif;}
header{background:linear-gradient(135deg,#0d1b40,#111e3d);border-bottom:1px solid var(--border);
       padding:16px 28px;display:flex;align-items:center;justify-content:space-between;
       position:sticky;top:0;z-index:100;}
header h1{font-size:1.1rem;font-weight:700;}header p{font-size:.72rem;color:var(--muted);}
.back{background:transparent;border:1px solid var(--border);color:var(--text);
      padding:8px 16px;border-radius:8px;font-size:.82rem;text-decoration:none;}
.back:hover{border-color:var(--accent);background:var(--card2);}
main{max-width:1400px;margin:0 auto;padding:24px 20px;}
.sec{font-size:.8rem;font-weight:700;color:var(--muted);letter-spacing:.08em;text-transform:uppercase;
     margin:28px 0 12px;display:flex;align-items:center;gap:8px;}
.sec::after{content:'';flex:1;height:1px;background:var(--border);}
.card{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:20px;margin-bottom:20px;}
.sg{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:12px;margin-bottom:24px;}
.sc{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:16px;}
.sc .k{font-size:.68rem;color:var(--muted);text-transform:uppercase;}
.sc .v{font-size:1.4rem;font-weight:800;margin-top:4px;}
.pfg{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px;margin-bottom:24px;}
.pfc{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:20px;position:relative;overflow:hidden;}
.pfc::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;}
.sh::before{background:linear-gradient(90deg,#4f8ef7,#1abc9c);}
.mv::before{background:linear-gradient(90deg,#27ae60,#1abc9c);}
.rp::before{background:linear-gradient(90deg,#f39c12,#e74c3c);}
.cv::before{background:linear-gradient(90deg,#9b59b6,#3498db);}
.pt{font-size:1rem;font-weight:700;margin-bottom:12px;}
.pr{display:flex;justify-content:space-between;font-size:.8rem;margin-bottom:6px;}
.pr .pk{color:var(--muted);} .pr .pv{font-weight:600;}
.pos{color:var(--success);} .neg{color:var(--danger);} .neu{color:var(--muted);}
.tbw{background:var(--card);border:1px solid var(--border);border-radius:14px;overflow:auto;margin-bottom:20px;}
table{width:100%;border-collapse:collapse;}
thead tr{background:var(--card2);}
th{padding:10px 12px;text-align:left;font-size:.68rem;font-weight:600;color:var(--muted);
   letter-spacing:.05em;text-transform:uppercase;white-space:nowrap;}
td{padding:9px 12px;font-size:.78rem;border-top:1px solid var(--border);}
tr:hover td{background:rgba(79,142,247,.04);}
.ct{border-collapse:collapse;font-size:.65rem;}
.ct th,.ct td{padding:4px 7px;border:1px solid var(--border);text-align:center;white-space:nowrap;}
.ct th{background:var(--card2);color:var(--muted);}
.cw{background:var(--card);border:1px solid var(--border);border-radius:14px;padding:20px;margin-bottom:20px;}
.err{text-align:center;padding:60px;color:var(--muted);}
</style></head>
<body>
<header>
  <div><h1>🔬 포트폴리오 최적화 분석</h1><p>저상관 볼트 · 4가지 최적화 · 백테스팅 · 원금보호</p></div>
  <a class="back" href="/">← 메인으로</a>
</header>
<main>
{% if err %}
  <div class="err"><p style="font-size:1.1rem">⚠️ {{ err }}</p>
    <p style="margin-top:12px;font-size:.85rem">먼저 메인 페이지에서 <strong>지금 분석 실행</strong>을 눌러 데이터를 생성하세요.</p>
  </div>
{% else %}
  <p class="sec">📊 분석 현황 ({{ d.date }})</p>
  <div class="sg">
    <div class="sc"><div class="k">전체 볼트</div><div class="v" style="color:var(--accent)">{{ d.n_total }}</div></div>
    <div class="sc"><div class="k">PnL 유효</div><div class="v">{{ d.n_valid }}</div></div>
    <div class="sc"><div class="k">필터 통과</div><div class="v">{{ d.n_filtered }}</div></div>
    <div class="sc"><div class="k">저상관 선택</div><div class="v" style="color:var(--accent2)">{{ d.n_selected }}</div></div>
    <div class="sc"><div class="k">분석 기간</div><div class="v">{{ d.analysis_days }}일</div></div>
    <div class="sc"><div class="k">히스토리</div><div class="v">{{ d.history_days }}일</div></div>
  </div>
  <p class="sec">💼 포트폴리오 최적화 비교 ($100,000 기준)</p>
  <div class="pfg">
  {% for key, pf in d.portfolios.items() %}
  {% set bt=pf.backtest %} {% set st=pf.stats %}
  {% set cls={'max_sharpe':'sh','min_variance':'mv','risk_parity':'rp','min_cvar':'cv'} %}
  <div class="pfc {{ cls[key] }}">
    <div class="pt">{{ pf.emoji }} {{ pf.label }}</div>
    <div class="pr"><span class="pk">예상 연수익</span>
      <span class="pv {% if st.annual_return_pct>0 %}pos{% else %}neg{% endif %}">{{ "%.1f"|format(st.annual_return_pct) }}%</span></div>
    <div class="pr"><span class="pk">연 변동성</span><span class="pv">{{ "%.1f"|format(st.annual_vol_pct) }}%</span></div>
    <div class="pr"><span class="pk">샤프비율</span>
      <span class="pv {% if st.sharpe>1 %}pos{% elif st.sharpe>0 %}neu{% else %}neg{% endif %}">{{ "%.2f"|format(st.sharpe) }}</span></div>
    <div style="height:1px;background:var(--border);margin:8px 0"></div>
    <div class="pr"><span class="pk">백테스팅 수익</span>
      <span class="pv {% if bt.total_profit>0 %}pos{% else %}neg{% endif %}">${{ "{:,.0f}".format(bt.total_profit) }}</span></div>
    <div class="pr"><span class="pk">총 수익률</span>
      <span class="pv {% if bt.total_return_pct>0 %}pos{% else %}neg{% endif %}">{{ "%.1f"|format(bt.total_return_pct) }}%</span></div>
    <div class="pr"><span class="pk">최대낙폭 MDD</span>
      <span class="pv {% if bt.max_drawdown_pct<10 %}pos{% elif bt.max_drawdown_pct<25 %}neu{% else %}neg{% endif %}">{{ "%.1f"|format(bt.max_drawdown_pct) }}%</span></div>
  </div>
  {% endfor %}
  </div>
  <p class="sec">📈 백테스팅 Equity Curve (인터랙티브 · 줌 가능)</p>
  <div class="cw" id="equity-chart" style="height:340px;width:100%;display:block;"></div>
  <p class="sec">📊 포트폴리오별 성과 비교 (APR · MDD · Sharpe)</p>
  <div class="cw" id="bar-chart" style="height:280px;width:100%;display:block;"></div>
  <p class="sec">⭐ 저상관 선택 볼트 (상관 55% 미만)</p>
  <div class="tbw"><table>
    <thead><tr><th>#</th><th>볼트명</th><th>APR 30d</th><th>Sharpe</th><th>MDD</th>
      <th>Robust</th><th>등급</th>
      <th style="color:#4f8ef7">MaxSharpe</th><th style="color:#27ae60">MinVar</th>
      <th style="color:#f39c12">RiskParity</th><th style="color:#9b59b6">MinCVaR</th><th>TVL</th></tr></thead>
    <tbody>
    {% for v in d.selected_vaults %}
    <tr>
      <td class="neu">{{ loop.index }}</td>
      <td style="font-weight:600">{{ v.name[:22] }}</td>
      <td class="{% if v.apr_30d>0 %}pos{% else %}neg{% endif %}">{{ "%.1f"|format(v.apr_30d) }}%</td>
      <td class="{% if v.sharpe_ratio>1 %}pos{% elif v.sharpe_ratio>0 %}neu{% else %}neg{% endif %}">{{ "%.2f"|format(v.sharpe_ratio) }}</td>
      <td class="{% if v.max_drawdown<15 %}pos{% elif v.max_drawdown<25 %}neu{% else %}neg{% endif %}">{{ "%.1f"|format(v.max_drawdown) }}%</td>
      <td class="{% if v.robustness_score>=0.6 %}pos{% elif v.robustness_score>=0.35 %}neu{% else %}neg{% endif %}">{{ "%.3f"|format(v.robustness_score) }}</td>
      <td>{{ v.equity_curve_grade.split("(")[0].strip() if v.equity_curve_grade != "-" else "-" }}</td>
      <td style="color:#4f8ef7;font-weight:600">{{ "%.1f"|format(v.alloc_sh) }}%</td>
      <td style="color:#27ae60;font-weight:600">{{ "%.1f"|format(v.alloc_mv) }}%</td>
      <td style="color:#f39c12;font-weight:600">{{ "%.1f"|format(v.alloc_rp) }}%</td>
      <td style="color:#9b59b6;font-weight:600">{{ "%.1f"|format(v.alloc_cv) }}%</td>
      <td>${{ "{:,.0f}".format(v.tvl) }}</td>
    </tr>
    {% endfor %}
    </tbody></table></div>
  <p class="sec">🔗 상관관계 행렬 — 🔴 높음(>0.7) 🟡 중간(0.4~0.7) 🟢 낮음(<0.4) 🔵 음의상관</p>
  <div class="card" style="overflow-x:auto">
  <table class="ct"><thead><tr><th></th>
    {% for n in d.corr_selected.names %}<th title="{{ n }}">{{ n[:9] }}</th>{% endfor %}
  </tr></thead><tbody>
  {% for i in range(d.corr_selected.names|length) %}
  <tr><th style="text-align:left">{{ d.corr_selected.names[i][:9] }}</th>
    {% for j in range(d.corr_selected.names|length) %}
    {% set v=d.corr_selected.matrix[i][j] %}
    {% if i==j %}<td style="background:#1a2340;color:var(--muted)">1.00</td>
    {% elif v>0.7 %}<td style="background:rgba(231,76,60,.35);font-weight:600">{{ "%.2f"|format(v) }}</td>
    {% elif v>0.4 %}<td style="background:rgba(243,156,18,.2)">{{ "%.2f"|format(v) }}</td>
    {% elif v>0.0 %}<td style="background:rgba(39,174,96,.15)">{{ "%.2f"|format(v) }}</td>
    {% else %}<td style="background:rgba(26,188,156,.2)">{{ "%.2f"|format(v) }}</td>
    {% endif %}
    {% endfor %}
  </tr>
  {% endfor %}
  </tbody></table></div>
{% endif %}
</main>
<script>
{% if not err %}
const bcd = {{ bt_json }};

document.addEventListener('DOMContentLoaded', function() {

// ── 1. Equity Curve — ECharts (인터랙티브 · 줌 · 툴팁) ─────────────────────
(function(){
  const elEc = document.getElementById('equity-chart');
  if (!elEc) return;
  elEc.style.width  = '100%';
  elEc.style.height = '340px';
  const ec = echarts.init(elEc, null, {renderer:'canvas'});
  const labels = Array.from({length: bcd.sh.length}, (_, i) => i);
  ec.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis', axisPointer: {type:'cross',lineStyle:{color:'#4f8ef7',opacity:.5}},
      backgroundColor:'#131928', borderColor:'#243050', borderWidth:1,
      textStyle:{color:'#e8eaf0', fontSize:12},
      formatter: params => {
        let s = '<b>Day ' + params[0].axisValue + '</b><br/>';
        params.forEach(p => {
          s += `<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${p.color};margin-right:6px;"></span>`
            + p.seriesName + ': <b>$' + Number(p.value).toLocaleString('en-US', {maximumFractionDigits:0}) + '</b><br/>';
        });
        return s;
      }
    },
    legend: {
      data:['📈 Max Sharpe','🛡 Min Variance','⚖ Risk Parity','🔒 Min CVaR'],
      textStyle:{color:'#e8eaf0'}, bottom:0, itemGap:20,
      icon: 'roundRect', itemWidth:14, itemHeight:4
    },
    dataZoom: [
      {type:'inside', xAxisIndex:0, start:0, end:100},
      {type:'slider',  xAxisIndex:0, start:0, end:100, bottom:36,
       borderColor:'#243050', fillerColor:'rgba(79,142,247,.1)',
       handleStyle:{color:'#4f8ef7'}, textStyle:{color:'#7b8db0'},
       height:20}
    ],
    grid: {top:20, left:70, right:20, bottom:100, containLabel:false},
    xAxis: {type:'category', data:labels, show:false},
    yAxis: {
      type:'value', splitLine:{lineStyle:{color:'rgba(36,48,80,.6)'}},
      axisLabel:{color:'#7b8db0', formatter: v => '$' + (v/1000).toFixed(0) + 'K'},
      axisLine:{lineStyle:{color:'#243050'}}
    },
    series: [
      {name:'📈 Max Sharpe',   type:'line', data:bcd.sh, smooth:true, symbol:'none',
       lineStyle:{color:'#4f8ef7',width:2.5}, areaStyle:{color:{type:'linear',x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:'rgba(79,142,247,.25)'},{offset:1,color:'rgba(79,142,247,0)'}]}}},
      {name:'🛡 Min Variance', type:'line', data:bcd.mv, smooth:true, symbol:'none',
       lineStyle:{color:'#27ae60',width:2.5}, areaStyle:{color:{type:'linear',x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:'rgba(39,174,96,.2)'},{offset:1,color:'rgba(39,174,96,0)'}]}}},
      {name:'⚖ Risk Parity',  type:'line', data:bcd.rp, smooth:true, symbol:'none',
       lineStyle:{color:'#f39c12',width:2.5}, areaStyle:{color:{type:'linear',x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:'rgba(243,156,18,.2)'},{offset:1,color:'rgba(243,156,18,0)'}]}}},
      {name:'🔒 Min CVaR',    type:'line', data:bcd.cv, smooth:true, symbol:'none',
       lineStyle:{color:'#9b59b6',width:2.5}, areaStyle:{color:{type:'linear',x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:'rgba(155,89,182,.2)'},{offset:1,color:'rgba(155,89,182,0)'}]}}},
    ]
  });
  window.addEventListener('resize', () => ec.resize());
  setTimeout(() => ec.resize(), 100);
})();

// ── 2. 포트폴리오별 성과 Bar Chart ───────────────────────────────────────────
(function(){
  const elBc = document.getElementById('bar-chart');
  if (!elBc) return;
  elBc.style.width  = '100%';
  elBc.style.height = '280px';
  const pf_labels = ['Max Sharpe', 'Min Variance', 'Risk Parity', 'Min CVaR'];
  const apr_data  = [
    {% for key, pf in d.portfolios.items() %}{{ pf.stats.annual_return_pct }}{% if not loop.last %},{% endif %}{% endfor %}
  ];
  const mdd_data  = [
    {% for key, pf in d.portfolios.items() %}{{ pf.backtest.max_drawdown_pct }}{% if not loop.last %},{% endif %}{% endfor %}
  ];
  const sharpe_data = [
    {% for key, pf in d.portfolios.items() %}{{ pf.stats.sharpe }}{% if not loop.last %},{% endif %}{% endfor %}
  ];

  const bc = echarts.init(elBc, null, {renderer:'canvas'});
  bc.setOption({
    backgroundColor: 'transparent',
    tooltip: {
      trigger:'axis', axisPointer:{type:'shadow'},
      backgroundColor:'#131928', borderColor:'#243050', borderWidth:1,
      textStyle:{color:'#e8eaf0'}
    },
    legend: {data:['APR (%)','MDD (%)','Sharpe×10'], textStyle:{color:'#e8eaf0'}, bottom:0, itemGap:16},
    grid: {top:16, left:60, right:20, bottom:60, containLabel:false},
    xAxis: {type:'category', data:pf_labels,
      axisLabel:{color:'#7b8db0', fontSize:11}, axisLine:{lineStyle:{color:'#243050'}}},
    yAxis: {type:'value', splitLine:{lineStyle:{color:'rgba(36,48,80,.6)'}},
      axisLabel:{color:'#7b8db0'}, axisLine:{lineStyle:{color:'#243050'}}},
    series: [
      {name:'APR (%)', type:'bar', data: apr_data, barWidth:'22%',
       itemStyle:{color:{type:'linear',x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:'#4f8ef7'},{offset:1,color:'#1a5fd1'}]}, borderRadius:[4,4,0,0]},
       label:{show:true, position:'top', color:'#4f8ef7', fontSize:11, formatter: v => v.value.toFixed(1)+'%'}},
      {name:'MDD (%)', type:'bar', data: mdd_data, barWidth:'22%',
       itemStyle:{color:{type:'linear',x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:'#e74c3c'},{offset:1,color:'#a52a2a'}]}, borderRadius:[4,4,0,0]},
       label:{show:true, position:'top', color:'#e74c3c', fontSize:11, formatter: v => v.value.toFixed(1)+'%'}},
      {name:'Sharpe×10', type:'bar', data: sharpe_data.map(v => +(v*10).toFixed(2)), barWidth:'22%',
       itemStyle:{color:{type:'linear',x:0,y:0,x2:0,y2:1,colorStops:[{offset:0,color:'#1abc9c'},{offset:1,color:'#0d8a6f'}]}, borderRadius:[4,4,0,0]},
       label:{show:true, position:'top', color:'#1abc9c', fontSize:11, formatter: v => (v.value/10).toFixed(2)}},
    ]
  });
  window.addEventListener('resize', () => bc.resize());
  setTimeout(() => bc.resize(), 100);
})();

}); // DOMContentLoaded
{% endif %}
</script>
</body></html>
"""

@app.route("/filtered-vaults")
def filtered_vaults_page():
    """필터 통과/탈락 전체 목록 페이지"""
    try:
        from portfolio_engine import run_portfolio_analysis
        d = run_portfolio_analysis(top_k=10, max_corr=0.55)
    except Exception as e:
        return f"<pre>오류: {e}</pre>", 500
    if "error" in d:
        return f"<pre>오류: {d['error']}</pre>", 500

    details = d.get("filter_details", [])
    passed  = [v for v in details if v.get("_filter_pass")]
    failed  = [v for v in details if not v.get("_filter_pass")]
    # 탈락 이유 분류
    for v in failed:
        reasons = []
        if not v.get("allow_deposits", True):
            reasons.append("입금불가")
        lr = v.get("leader_equity_ratio", -1)
        if 0 <= lr < 0.40:
            reasons.append(f"리더에쿼티 {lr:.0%}<40%")
        elif lr < 0:
            reasons.append("리더에쿼티 미확인")
        v["_reason"] = " / ".join(reasons) if reasons else "기준미달"

    FVHTML = """<!DOCTYPE html>
<html lang="ko"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>필터 통과 목록</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
<style>
:root{--bg:#0b0f1a;--card:#131928;--card2:#1a2340;--border:#243050;
      --accent:#4f8ef7;--accent2:#1abc9c;--text:#e8eaf0;--muted:#7b8db0;
      --danger:#e74c3c;--warn:#f39c12;--success:#27ae60;}
*{box-sizing:border-box;margin:0;padding:0;}
body{background:var(--bg);color:var(--text);font-family:'Inter',sans-serif;}
header{background:linear-gradient(135deg,#0d1b40,#111e3d);border-bottom:1px solid var(--border);
       padding:16px 28px;display:flex;align-items:center;justify-content:space-between;
       position:sticky;top:0;z-index:100;}
header h1{font-size:1.1rem;font-weight:700;}
header p{font-size:.72rem;color:var(--muted);}
.back{background:transparent;border:1px solid var(--border);color:var(--text);
      padding:8px 16px;border-radius:8px;font-size:.82rem;text-decoration:none;}
.back:hover{border-color:var(--accent);}
main{max-width:1500px;margin:0 auto;padding:24px 20px;}
.tab-bar{display:flex;gap:12px;margin-bottom:20px;}
.tab{padding:10px 24px;border-radius:10px;font-size:.85rem;font-weight:600;
     cursor:pointer;border:1px solid var(--border);background:var(--card2);color:var(--muted);}
.tab.active{background:linear-gradient(135deg,var(--accent),var(--accent2));
            color:#fff;border-color:transparent;}
.panel{display:none;}.panel.show{display:block;}
.sg{display:flex;gap:12px;flex-wrap:wrap;margin-bottom:20px;}
.sc{background:var(--card);border:1px solid var(--border);border-radius:12px;
    padding:14px 20px;min-width:140px;}
.sc .k{font-size:.68rem;color:var(--muted);text-transform:uppercase;}
.sc .v{font-size:1.4rem;font-weight:800;margin-top:4px;}
.sec{font-size:.8rem;font-weight:700;color:var(--muted);letter-spacing:.08em;
     text-transform:uppercase;margin:24px 0 10px;display:flex;align-items:center;gap:8px;}
.sec::after{content:'';flex:1;height:1px;background:var(--border);}
.tbw{background:var(--card);border:1px solid var(--border);border-radius:14px;
     overflow-x:auto;margin-bottom:20px;}
table{width:100%;border-collapse:collapse;}
thead tr{background:var(--card2);}
th{padding:9px 11px;text-align:left;font-size:.65rem;font-weight:600;color:var(--muted);
   letter-spacing:.05em;text-transform:uppercase;white-space:nowrap;}
td{padding:8px 11px;font-size:.76rem;border-top:1px solid var(--border);}
tr:hover td{background:rgba(79,142,247,.04);}
.pos{color:var(--success);} .neg{color:var(--danger);} .neu{color:var(--muted);}
.badge{display:inline-block;padding:2px 7px;border-radius:5px;font-size:.65rem;font-weight:700;}
.badge-ok{background:rgba(39,174,96,.2);color:#27ae60;}
.badge-no{background:rgba(231,76,60,.15);color:#e74c3c;}
.badge-warn{background:rgba(243,156,18,.15);color:#f39c12;}
input[type=text]{background:var(--card2);border:1px solid var(--border);color:var(--text);
  border-radius:8px;padding:8px 14px;font-size:.82rem;width:260px;margin-bottom:14px;}
input[type=text]:focus{outline:none;border-color:var(--accent);}
</style></head>
<body>
<header>
  <div>
    <h1>🔍 필터 통과 상세 목록</h1>
    <p>입금가능 · 리더에쿼티 ≥40% 기준 — PnL 데이터 보유 {{ total }}개 볼트 분석</p>
  </div>
  <div style="display:flex;gap:10px;">
    <a class="back" href="/portfolio">← 포트폴리오</a>
    <a class="back" href="/">← 메인</a>
  </div>
</header>
<main>
  <div class="sg">
    <div class="sc"><div class="k">PnL 보유 볼트</div>
      <div class="v" style="color:var(--accent)">{{ total }}</div></div>
    <div class="sc"><div class="k">✅ 필터 통과</div>
      <div class="v" style="color:var(--success)">{{ n_pass }}</div></div>
    <div class="sc"><div class="k">❌ 필터 탈락</div>
      <div class="v" style="color:var(--danger)">{{ n_fail }}</div></div>
    <div class="sc"><div class="k">입금불가로 탈락</div>
      <div class="v" style="color:var(--warn)">{{ n_no_deposit }}</div></div>
    <div class="sc"><div class="k">리더에쿼티 미달</div>
      <div class="v" style="color:var(--warn)">{{ n_no_leader }}</div></div>
  </div>

  <div class="tab-bar">
    <div class="tab active" onclick="showTab('pass',this)">✅ 통과 ({{ n_pass }}개)</div>
    <div class="tab"        onclick="showTab('fail',this)">❌ 탈락 ({{ n_fail }}개)</div>
  </div>

  <!-- 통과 목록 -->
  <div id="panel-pass" class="panel show">
    <input type="text" id="search-pass" oninput="filterTable('tbl-pass',this.value)"
           placeholder="볼트명 / 주소 검색...">
    <div class="tbw"><table id="tbl-pass">
      <thead><tr>
        <th>순위</th><th>볼트명</th><th>리더에쿼티</th><th>리더예치($)</th>
        <th>30일APR</th><th>Sharpe</th><th>MDD</th><th>Robust</th><th>등급</th>
        <th>TVL($)</th><th>점수</th><th>데이터</th>
      </tr></thead>
      <tbody>
      {% for v in passed %}
      <tr>
        <td class="neu">{{ v.rank }}</td>
        <td style="font-weight:600;max-width:200px">{{ v.name }}</td>
        <td>
          {% if v.leader_equity_ratio >= 0 %}
            <span class="badge {% if v.leader_equity_ratio >= 0.4 %}badge-ok{% else %}badge-no{% endif %}">
              {{ "%.0f"|format(v.leader_equity_ratio * 100) }}%
            </span>
          {% else %}
            <span class="badge badge-warn">미확인</span>
          {% endif %}
        </td>
        <td class="neu">${{ "{:,.0f}".format(v.leader_equity_usd) if v.leader_equity_usd else "-" }}</td>
        <td class="{% if v.apr_30d > 0 %}pos{% else %}neg{% endif %}">{{ "%.1f"|format(v.apr_30d) }}%</td>
        <td class="{% if v.sharpe_ratio > 1 %}pos{% elif v.sharpe_ratio > 0 %}neu{% else %}neg{% endif %}">
          {{ "%.2f"|format(v.sharpe_ratio) }}</td>
        <td class="{% if v.max_drawdown < 15 %}pos{% elif v.max_drawdown < 35 %}neu{% else %}neg{% endif %}">
          {{ "%.1f"|format(v.max_drawdown) }}%</td>
        <td class="{% if v.robustness_score >= 0.6 %}pos{% elif v.robustness_score >= 0.35 %}neu{% else %}neg{% endif %}">
          {{ "%.3f"|format(v.robustness_score) }}</td>
        <td>{{ v.equity_curve_grade.split("(")[0].strip() if v.equity_curve_grade != "-" else "-" }}</td>
        <td>${{ "{:,.0f}".format(v.tvl) }}</td>
        <td style="color:var(--accent);font-weight:700">{{ "%.2f"|format(v.score) }}</td>
        <td class="neu">{{ v.data_points }}pt</td>
      </tr>
      {% endfor %}
      </tbody>
    </table></div>
  </div>

  <!-- 탈락 목록 -->
  <div id="panel-fail" class="panel">
    <input type="text" id="search-fail" oninput="filterTable('tbl-fail',this.value)"
           placeholder="볼트명 / 주소 검색...">
    <div class="tbw"><table id="tbl-fail">
      <thead><tr>
        <th>순위</th><th>볼트명</th><th>탈락 이유</th><th>리더에쿼티</th>
        <th>입금</th><th>30일APR</th><th>MDD</th><th>Robust</th><th>TVL($)</th>
      </tr></thead>
      <tbody>
      {% for v in failed %}
      <tr>
        <td class="neu">{{ v.rank }}</td>
        <td style="font-weight:600;max-width:180px">{{ v.name }}</td>
        <td><span class="badge badge-no">{{ v._reason }}</span></td>
        <td>
          {% if v.leader_equity_ratio >= 0 %}
            <span class="badge badge-no">{{ "%.0f"|format(v.leader_equity_ratio * 100) }}%</span>
          {% else %}
            <span class="badge badge-warn">미확인</span>
          {% endif %}
        </td>
        <td>{% if v.allow_deposits %}<span class="pos">✓</span>
            {% else %}<span class="neg">✗</span>{% endif %}</td>
        <td class="{% if v.apr_30d > 0 %}pos{% else %}neg{% endif %}">{{ "%.1f"|format(v.apr_30d) }}%</td>
        <td>{{ "%.1f"|format(v.max_drawdown) }}%</td>
        <td class="neu">{{ "%.3f"|format(v.robustness_score) }}</td>
        <td>${{ "{:,.0f}".format(v.tvl) }}</td>
      </tr>
      {% endfor %}
      </tbody>
    </table></div>
  </div>
</main>
<script>
function showTab(id, el) {
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('show'));
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.getElementById('panel-' + id).classList.add('show');
  el.classList.add('active');
}
function filterTable(tblId, q) {
  q = q.toLowerCase();
  document.querySelectorAll('#' + tblId + ' tbody tr').forEach(row => {
    row.style.display = row.innerText.toLowerCase().includes(q) ? '' : 'none';
  });
}
</script>
</body></html>"""

    n_no_deposit = sum(1 for v in failed if not v.get("allow_deposits", True))
    n_no_leader  = sum(1 for v in failed if v.get("allow_deposits", True))  # 입금은 되지만 리더 에쿼티 미달

    return render_template_string(FVHTML,
        passed=passed, failed=failed,
        total=len(details),
        n_pass=len(passed), n_fail=len(failed),
        n_no_deposit=n_no_deposit, n_no_leader=n_no_leader,
    )


# ── /chart_data API (Task 4e) ────────────────────────────────────────────────
@app.route("/chart_data")
def chart_data():
    """ECharts용 차트 데이터 JSON API"""
    vaults, date = get_latest_snapshot()
    if not vaults:
        return jsonify({"error": "no_data", "date": None})

    import numpy as np
    valid = [v for v in vaults if v.get("data_points", 0) >= 3]

    # APR 분포
    apr_vals = [v["apr_30d"] for v in valid]
    # 히스토그램 bin (5% 간격, -20~100 범위)
    bins = list(range(-20, 101, 5))
    hist, _ = np.histogram(apr_vals, bins=bins)
    apr_hist = {
        "labels": [f"{b}~{b+5}%" for b in bins[:-1]],
        "counts": hist.tolist(),
    }

    # 상위 20 볼트 APR / Sharpe / MDD
    deposit = [v for v in vaults if v.get("allow_deposits")]
    top20 = sorted(deposit, key=lambda v: v.get("score", 0), reverse=True)[:20]
    bar_data = {
        "names":  [v["name"][:16] for v in top20],
        "apr":    [round(float(v.get("apr_30d", 0)), 2)   for v in top20],
        "mdd":    [round(float(v.get("max_drawdown", 0)), 2) for v in top20],
        "sharpe": [round(float(v.get("sharpe_ratio", 0)), 3) for v in top20],
    }

    # 요약 통계
    stats = {}
    if valid:
        stats["total"]       = len(vaults)
        stats["avg_apr"]     = round(float(np.mean(apr_vals)), 2)
        stats["median_apr"]  = round(float(np.median(apr_vals)), 2)
        stats["pct_positive"] = round(sum(1 for a in apr_vals if a > 0) / len(apr_vals) * 100, 1)

    return jsonify({
        "date":     date,
        "stats":    stats,
        "apr_hist": apr_hist,
        "bar_data": bar_data,
    })


@app.route("/download/<filename>")
def download(filename):
    """Excel 파일 다운로드"""
    safe_name = os.path.basename(filename)
    filepath  = os.path.join(REPORTS_DIR, safe_name)
    if not os.path.exists(filepath):
        return "파일을 찾을 수 없습니다.", 404
    return send_file(
        os.path.abspath(filepath),
        as_attachment=True,
        download_name=safe_name,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


@app.route("/download-guide")
def download_guide():
    """집 PC 설치 가이드 다운로드"""
    lines = [
        "집 PC 설치 가이드 - Hyperliquid Vault Analyzer",
        "================================================",
        "",
        "STEP 1 - Python 설치 확인",
        "  터미널에서 실행: python --version",
        "  OK: Python 3.10 이상 -> 다음 단계로",
        "  없으면 -> https://python.org/downloads 에서 설치",
        "           (설치 중 [Add Python to PATH] 반드시 체크!)",
        "",
        "STEP 2 - Git 설치 확인",
        "  터미널에서 실행: git --version",
        "  없으면 -> https://git-scm.com 에서 설치",
        "",
        "STEP 3 - 프로젝트 클론 (코드 가져오기)",
        "  PowerShell에서 실행:",
        r"  git clone https://github.com/neon0104/hyperliquid-vault-analyzer.git C:\Users\USER\.gemini\antigravity\scratch\hyperliquid-vault-analyzer",
        "",
        "STEP 4 - 폴더 이동 & 패키지 설치",
        r"  cd C:\Users\USER\.gemini\antigravity\scratch\hyperliquid-vault-analyzer",
        "  pip install -r requirements.txt",
        "  (약 2~5분 소요)",
        "",
        "STEP 5 - API 키 설정",
        "  copy config.example.json config.json",
        "",
        "  config.json 파일을 메모장으로 열어서 수정:",
        '  {',
        '      "account_address": "여기에_지갑주소_입력",',
        '      "secret_key": "여기에_시크릿키_입력"',
        '  }',
        "  (지갑주소/시크릿키는 회사 PC의 config.json에서 복사)",
        "",
        "STEP 6 - 실행!",
        "  python web_dashboard.py",
        "",
        "  브라우저에서 http://localhost:5000 자동으로 열림",
        "  -> [지금 분석 실행] 버튼 클릭 (2~5분 소요)",
        "  -> [다운로드] 로 Excel 다운로드",
        "",
        "================================================",
        " 매일 사용하는 명령어",
        "================================================",
        "",
        "  코드 최신본 받기 (작업 시작 전): git pull origin master",
        "  대시보드 시작:                  python web_dashboard.py",
        "  분석만 실행 (CLI):              python analyze_top_vaults.py",
        "  MDD 25% 미만으로만 분석:        python analyze_top_vaults.py --mdd 25",
        "",
        "================================================",
        " 자주 있는 문제",
        "================================================",
        "",
        "  git 명령어 없음  -> https://git-scm.com 설치",
        "  pip 오류         -> python -m pip install -r requirements.txt",
        "  포트 5000 충돌   -> 다른 프로그램 종료 후 재실행",
        "  브라우저 안 열림 -> 직접 http://localhost:5000 입력",
        "",
        "  GitHub repo: https://github.com/neon0104/hyperliquid-vault-analyzer",
    ]
    guide_content = "\n".join(lines)
    from flask import Response
    return Response(
        guide_content.encode("utf-8"),
        mimetype="text/plain; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename*=UTF-8''%EC%A7%91PC_%EC%84%A4%EC%B9%98%EA%B0%80%EC%9D%B4%EB%93%9C.txt"}
    )


@app.route("/run-analysis", methods=["POST"])
def run_analysis_route():
    global _analysis_running, _analysis_log
    with _analysis_lock:
        if _analysis_running:
            return jsonify(status="already_running", message="이미 분석이 실행 중입니다.", log=_analysis_log[-5:])

    def _run():
        global _analysis_running, _analysis_log
        _analysis_running = True
        _analysis_log = ["분석 시작..."];
        try:
            proc = subprocess.Popen(
                [sys.executable, "-u", "analyze_top_vaults.py", "--force"],
                cwd=os.path.dirname(os.path.abspath(__file__)),
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace"
            )
            for line in proc.stdout:
                line = line.rstrip()
                if line:
                    _analysis_log.append(line)
                    if len(_analysis_log) > 200:
                        _analysis_log = _analysis_log[-200:]
            proc.wait()
        except Exception as e:
            _analysis_log.append(f"오류: {e}")
        finally:
            _analysis_running = False

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return jsonify(status="started")


@app.route("/analysis-status")
def analysis_status():
    return jsonify(running=_analysis_running, log=_analysis_log[-10:])


@app.route("/analysis-log")
def analysis_log_route():
    return jsonify(running=_analysis_running, log=_analysis_log)


# ── 모바일 & API 라우트 ────────────────────────────────────────────────────────

@app.route("/api/status")
def api_status():
    """모바일 앱 / 외부에서 포트폴리오 상태 조회 JSON API"""
    status  = load_status_file()
    stopped = is_emergency_stopped()

    # my_portfolio.json 로드 (구형/신형 형식 모두 지원)
    raw_portfolio = load_portfolio_file()
    if isinstance(raw_portfolio, dict) and "positions" in raw_portfolio:
        # 신형: fetch_my_portfolio.py 저장 형식
        positions = raw_portfolio.get("positions", {})
        hl_holdings = raw_portfolio.get("holdings", [])
    else:
        # 구형: {주소: 금액} 단순 dict
        positions = raw_portfolio
        hl_holdings = []

    # holdings 이름 맵 (신형 데이터에서 이름 가져오기)
    hl_name_map = {h.get("vault_address", ""): h.get("name", "") for h in hl_holdings}

    vaults, date = get_latest_snapshot()
    vault_map = {v["address"]: v for v in (vaults or [])}

    holdings = []
    total_invested = 0.0
    total_monthly_est = 0.0
    for addr, usd in positions.items():
        usd = float(usd)  # 문자열/숫자 모두 처리
        v   = vault_map.get(addr, {})
        apr = float(v.get("apr_30d", 0))
        monthly = usd * apr / 100 / 12
        total_invested    += usd
        total_monthly_est += monthly
        name = v.get("name") or hl_name_map.get(addr) or addr[:12] + "..."
        holdings.append({
            "address":      addr,
            "name":         name,
            "invested_usd": round(usd, 2),
            "pct":          0,
            "apr_30d":      apr,
            "mdd":          float(v.get("max_drawdown", 0)),
            "monthly_est":  round(monthly, 2),
            "danger":       float(v.get("max_drawdown", 0)) > 20 or apr < 0,
        })
    for h in holdings:
        h["pct"] = round(h["invested_usd"] / total_invested * 100, 1) if total_invested else 0

    return jsonify({
        "emergency_stopped": stopped,
        "scheduler_running": status.get("scheduler_running", False),
        "last_run_date":     status.get("last_run_date"),
        "last_run_status":   status.get("last_run_status"),
        "next_run":          status.get("next_run"),
        "days_to_rebalance": status.get("days_to_rebalance", 30),
        "needs_rebalance":   status.get("needs_rebalance", False),
        "rebalance_reason":  status.get("rebalance_reason", ""),
        "total_invested":    round(total_invested, 2),
        "estimated_monthly": round(total_monthly_est, 2),
        "estimated_annual":  round(total_monthly_est * 12, 2),
        "holdings":          holdings,
        "recent_alerts":     status.get("recent_alerts", []),
        "vault_count":       status.get("vault_count", 0),
        "analysis_date":     date,
        "is_configured":     len(positions) > 0,
    })


@app.route("/emergency-stop", methods=["POST"])
def emergency_stop():
    """긴급 중단 — 플래그 파일 생성"""
    reason = request.json.get("reason", "Dashboard emergency stop") if request.is_json else "Dashboard emergency stop"
    with open(STOP_FLAG, "w", encoding="utf-8") as f:
        json.dump({"reason": reason, "time": datetime.now().isoformat()}, f)
    return jsonify(status="stopped", message="긴급 중단 완료")


@app.route("/emergency-clear", methods=["POST"])
def emergency_clear():
    """긴급 중단 해제"""
    if os.path.exists(STOP_FLAG):
        os.remove(STOP_FLAG)
    return jsonify(status="cleared", message="긴급 중단 해제 완료")


@app.route("/set-portfolio", methods=["POST"])
def set_portfolio():
    """포트폴리오 설정 저장 {address: usd_amount}"""
    data = request.get_json(silent=True) or {}
    portfolio = data.get("portfolio", {})
    if not isinstance(portfolio, dict):
        return jsonify(error="portfolio must be a dict"), 422
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(PORTFOLIO_FILE, "w", encoding="utf-8") as f:
        json.dump(portfolio, f, ensure_ascii=False, indent=2)
    return jsonify(status="ok", message="포트폴리오 저장 완료")


MOBILE_HTML = r"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
  <title>📊 내 포트폴리오</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root{--bg:#0b0f1a;--card:#131928;--card2:#1a2340;--border:#243050;
          --accent:#4f8ef7;--accent2:#1abc9c;--text:#e8eaf0;--muted:#7b8db0;
          --danger:#e74c3c;--warn:#f39c12;--success:#27ae60;}
    *{box-sizing:border-box;margin:0;padding:0;}
    body{background:var(--bg);color:var(--text);font-family:'Inter',sans-serif;
         min-height:100vh;padding-bottom:80px;}
    header{background:linear-gradient(135deg,#0d1b40,#111e3d);
           border-bottom:1px solid var(--border);padding:16px 20px;
           display:flex;align-items:center;justify-content:space-between;
           position:sticky;top:0;z-index:100;backdrop-filter:blur(20px);}
    header h1{font-size:1rem;font-weight:700;}
    header p{font-size:.68rem;color:var(--muted);}
    .back{color:var(--muted);text-decoration:none;font-size:.85rem;}
    main{padding:16px;}
    /* 상태 배너 */
    .status-banner{border-radius:12px;padding:14px 16px;margin-bottom:16px;
                   display:flex;align-items:center;gap:12px;}
    .status-banner.ok  {background:rgba(39,174,96,.15);border:1px solid #27ae60;}
    .status-banner.warn{background:rgba(243,156,18,.15);border:1px solid #f39c12;}
    .status-banner.danger{background:rgba(231,76,60,.2);border:1px solid #e74c3c;}
    .status-banner .icon{font-size:1.8rem;}
    .status-banner .st-title{font-weight:700;font-size:.9rem;}
    .status-banner .st-sub{font-size:.78rem;color:var(--muted);margin-top:2px;}
    /* 통계 카드 그리드 */
    .stats-row{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:16px;}
    .stat-card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:14px;}
    .stat-card .sk{font-size:.68rem;color:var(--muted);text-transform:uppercase;}
    .stat-card .sv{font-size:1.3rem;font-weight:800;margin-top:4px;}
    /* 홀딩 카드 */
    .holding-card{background:var(--card);border:1px solid var(--border);
                  border-radius:12px;padding:14px 16px;margin-bottom:10px;position:relative;}
    .holding-card.danger{border-color:var(--danger);}
    .holding-card .hname{font-weight:700;font-size:.9rem;margin-bottom:8px;padding-right:50px;}
    .holding-row{display:flex;justify-content:space-between;font-size:.78rem;margin-bottom:4px;}
    .holding-row .hk{color:var(--muted);}
    .holding-row .hv{font-weight:600;}
    .pct-bar{height:4px;background:var(--border);border-radius:2px;margin-top:8px;overflow:hidden;}
    .pct-bar .fill{height:100%;background:linear-gradient(90deg,var(--accent),var(--accent2));border-radius:2px;}
    .danger-badge{position:absolute;top:12px;right:12px;
                  background:rgba(231,76,60,.2);border:1px solid var(--danger);
                  color:var(--danger);font-size:.65rem;font-weight:700;
                  padding:2px 7px;border-radius:5px;}
    /* 긴급중단 버튼 */
    .emergency-bar{position:fixed;bottom:0;left:0;right:0;padding:12px 16px;
                   background:var(--card);border-top:1px solid var(--border);
                   display:flex;gap:10px;}
    .btn-emergency{flex:1;background:linear-gradient(135deg,#e74c3c,#c0392b);
                   color:#fff;border:none;border-radius:10px;padding:14px;
                   font-size:.9rem;font-weight:700;cursor:pointer;transition:all.2s;}
    .btn-emergency:active{transform:scale(.97);}
    .btn-home{flex:0 0 44px;background:var(--card2);border:1px solid var(--border);
              border-radius:10px;display:flex;align-items:center;justify-content:center;
              font-size:1.3rem;cursor:pointer;text-decoration:none;}
    /* 알림 */
    .alerts-section{margin-top:16px;}
    .alert-item{background:var(--card2);border:1px solid var(--border);
                border-radius:10px;padding:12px;margin-bottom:8px;font-size:.78rem;}
    .alert-item .at{color:var(--muted);font-size:.68rem;margin-bottom:4px;}
    .alert-item.WARN{border-left:3px solid var(--warn);}
    .alert-item.ERROR{border-left:3px solid var(--danger);}
    .alert-item.INFO{border-left:3px solid var(--accent);}
    /* 리밸런싱 카운트다운 */
    .countdown{background:linear-gradient(135deg,#0d1b40,#111e3d);
               border:1px solid var(--accent);border-radius:12px;
               padding:14px 16px;margin-bottom:16px;text-align:center;}
    .countdown .cd-num{font-size:2rem;font-weight:800;color:var(--accent);}
    .countdown .cd-label{font-size:.75rem;color:var(--muted);}
    .pos{color:var(--success);} .neg{color:var(--danger);} .warn-c{color:var(--warn);}
    /* 토스트 */
    #toast{position:fixed;top:80px;left:50%;transform:translateX(-50%);
           background:#131928;border:1px solid var(--accent);border-radius:10px;
           padding:12px 20px;font-size:.85rem;z-index:999;display:none;
           white-space:nowrap;}
  </style>
</head>
<body>
<header>
  <div>
    <h1>📊 내 포트폴리오</h1>
    <p id="last-updated">로딩 중...</p>
  </div>
  <a class="back" href="/">← 메인</a>
</header>
<main>
  <div id="content">
    <div style="text-align:center;padding:60px;color:var(--muted)">
      <div style="font-size:2rem;margin-bottom:12px">⏳</div>
      <p>데이터 로딩 중...</p>
    </div>
  </div>
</main>
<div class="emergency-bar">
  <a class="btn-home" href="/">🏠</a>
  <button class="btn-emergency" id="stop-btn" onclick="emergencyStop()">🔴 긴급 중단</button>
</div>
<div id="toast"></div>

<script>
let statusData = null;
let stopped = false;

function fmt(n){return '$'+Number(n).toLocaleString(undefined,{maximumFractionDigits:0});}
function fmtPct(n){return (n>0?'+':'')+n.toFixed(1)+'%';}

async function loadStatus(){
  try{
    const r = await fetch('/api/status');
    statusData = await r.json();
    stopped = statusData.emergency_stopped;
    renderPage();
  }catch(e){
    document.getElementById('content').innerHTML=
      '<div style="text-align:center;padding:40px;color:var(--muted)">⚠️ 서버 연결 실패</div>';
  }
}

function renderPage(){
  const d = statusData;
  let html = '';

  // 비상 상태 배너
  if(d.emergency_stopped){
    html += `<div class="status-banner danger">
      <div class="icon">🔴</div>
      <div><div class="st-title">긴급 중단 상태</div>
      <div class="st-sub">모든 자동 분석이 중단되었습니다</div></div></div>`;
  } else if(d.needs_rebalance){
    html += `<div class="status-banner warn">
      <div class="icon">⚠️</div>
      <div><div class="st-title">리밸런싱 권고</div>
      <div class="st-sub">${d.rebalance_reason||'포트폴리오 조정이 필요합니다'}</div></div></div>`;
  } else {
    html += `<div class="status-banner ok">
      <div class="icon">✅</div>
      <div><div class="st-title">포트폴리오 정상</div>
      <div class="st-sub">마지막 분석: ${d.last_run_date||'없음'}</div></div></div>`;
  }

  // 리밸런싱 카운트다운
  const days = d.days_to_rebalance || 30;
  const dColor = days<=3?'var(--danger)':days<=7?'var(--warn)':'var(--accent)';
  html += `<div class="countdown">
    <div class="cd-num" style="color:${dColor}">${days}일</div>
    <div class="cd-label">30일 리밸런싱까지</div>
  </div>`;

  // 통계
  html += `<div class="stats-row">
    <div class="stat-card">
      <div class="sk">총 투자금</div>
      <div class="sv" style="color:var(--accent)">${fmt(d.total_invested||0)}</div>
    </div>
    <div class="stat-card">
      <div class="sk">예상 월수익</div>
      <div class="sv" style="color:var(--accent2)">${fmt(d.estimated_monthly||0)}</div>
    </div>
    <div class="stat-card">
      <div class="sk">예상 연수익</div>
      <div class="sv" style="color:var(--accent2)">${fmt(d.estimated_annual||0)}</div>
    </div>
    <div class="stat-card">
      <div class="sk">분석 볼트 수</div>
      <div class="sv">${d.vault_count||0}<span style="font-size:.8rem;color:var(--muted)">개</span></div>
    </div>
  </div>`;

  // 보유 볼트
  if(d.holdings && d.holdings.length > 0){
    html += '<p style="font-size:.75rem;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;margin-bottom:10px">📌 보유 볼트</p>';
    d.holdings.forEach(h=>{
      const aprColor = h.apr_30d>0?'var(--success)':'var(--danger)';
      const mddColor = h.mdd<15?'var(--success)':h.mdd<25?'var(--warn)':'var(--danger)';
      html += `<div class="holding-card${h.danger?' danger':''}">
        ${h.danger?'<div class="danger-badge">⚠️ 주의</div>':''}
        <div class="hname">${h.name}</div>
        <div class="holding-row"><span class="hk">투자금액</span><span class="hv">${fmt(h.invested_usd)}</span></div>
        <div class="holding-row"><span class="hk">30일 APR</span>
          <span class="hv" style="color:${aprColor}">${fmtPct(h.apr_30d)}</span></div>
        <div class="holding-row"><span class="hk">MDD</span>
          <span class="hv" style="color:${mddColor}">${h.mdd.toFixed(1)}%</span></div>
        <div class="holding-row"><span class="hk">예상 월수익</span>
          <span class="hv" style="color:var(--accent2)">${fmt(h.monthly_est)}</span></div>
        <div class="pct-bar"><div class="fill" style="width:${Math.min(h.pct,100)}%"></div></div>
        <div style="text-align:right;font-size:.68rem;color:var(--muted);margin-top:4px">${h.pct.toFixed(1)}%</div>
      </div>`;
    });
  } else {
    html += `<div style="text-align:center;padding:30px;color:var(--muted);
              background:var(--card);border-radius:12px;border:1px solid var(--border);margin-bottom:16px">
      <div style="font-size:1.5rem;margin-bottom:8px">💼</div>
      <p style="font-size:.85rem">포트폴리오 미설정</p>
      <p style="font-size:.75rem;margin-top:6px">vault_data/my_portfolio.json 에 투자 현황 입력</p>
    </div>`;
  }

  // 최근 알림
  if(d.recent_alerts && d.recent_alerts.length > 0){
    html += '<p style="font-size:.75rem;color:var(--muted);text-transform:uppercase;letter-spacing:.08em;margin-bottom:10px">🔔 최근 알림</p>';
    html += '<div class="alerts-section">';
    d.recent_alerts.forEach(a=>{
      const t = a.time ? new Date(a.time).toLocaleString('ko-KR') : '';
      html += `<div class="alert-item ${a.level||'INFO'}">
        <div class="at">${t} · ${a.level}</div>
        <div style="font-weight:600">${a.title}</div>
        <div style="color:var(--muted);margin-top:2px">${a.message}</div>
      </div>`;
    });
    html += '</div>';
  }

  document.getElementById('content').innerHTML = html;
  document.getElementById('last-updated').textContent =
    '업데이트: ' + new Date().toLocaleString('ko-KR');

  // 긴급중단 버튼 라벨
  const btn = document.getElementById('stop-btn');
  if(d.emergency_stopped){
    btn.textContent = '✅ 긴급중단 해제';
    btn.style.background = 'linear-gradient(135deg,#27ae60,#1abc9c)';
    btn.onclick = emergencyClear;
  } else {
    btn.textContent = '🔴 긴급 중단';
    btn.style.background = 'linear-gradient(135deg,#e74c3c,#c0392b)';
    btn.onclick = emergencyStop;
  }
}

async function emergencyStop(){
  if(!confirm('⚠️ 정말 긴급 중단하시겠습니까?\n자동 분석이 중단됩니다.')) return;
  try{
    await fetch('/emergency-stop',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({reason:'Mobile dashboard emergency stop'})});
    showToast('🔴 긴급 중단 완료');
    setTimeout(loadStatus, 1000);
  }catch(e){showToast('오류: 서버 연결 실패');}
}

async function emergencyClear(){
  if(!confirm('✅ 긴급 중단을 해제하시겠습니까?')) return;
  try{
    await fetch('/emergency-clear',{method:'POST'});
    showToast('✅ 긴급 중단 해제 완료');
    setTimeout(loadStatus, 1000);
  }catch(e){showToast('오류: 서버 연결 실패');}
}

function showToast(msg){
  const t = document.getElementById('toast');
  t.textContent = msg; t.style.display='block';
  setTimeout(()=>{t.style.display='none';}, 3000);
}

// 초기 로드 + 30초마다 자동 갱신
loadStatus();
setInterval(loadStatus, 30000);
</script>
</body></html>"""


@app.route("/portfolio-status")
@app.route("/m")          # ← 단축 URL
@app.route("/mobile")     # ← 별명
def portfolio_status_page():
    """모바일 최적화 포트폴리오 현황 페이지"""
    return MOBILE_HTML


# ── 실행 ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import webbrowser, time
    os.makedirs(REPORTS_DIR, exist_ok=True)
    os.makedirs(SNAPSHOTS_DIR, exist_ok=True)
    print("=" * 55)
    print("  🚀 Hyperliquid Vault Dashboard 시작")
    print("  📌 브라우저: http://localhost:5000")
    print("  🛑 종료:     Ctrl+C")
    print("=" * 55)
    # 브라우저 자동 열기
    threading.Timer(1.2, lambda: webbrowser.open("http://localhost:5000")).start()
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
