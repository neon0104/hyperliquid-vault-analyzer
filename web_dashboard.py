#!/usr/bin/env python3
"""
Hyperliquid Vault Analyzer — 웹 대시보드
=========================================
실행: python web_dashboard.py
브라우저: http://localhost:5000
"""

import os, sys, json, glob, subprocess, threading
from datetime import datetime
from flask import Flask, render_template_string, send_file, jsonify, request, redirect, url_for

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

app = Flask(__name__)

DATA_DIR      = "vault_data"
SNAPSHOTS_DIR = os.path.join(DATA_DIR, "snapshots")
REPORTS_DIR   = os.path.join(DATA_DIR, "reports")

# ── 분석 상태 관리 ────────────────────────────────────────────────────────────
_analysis_running = False
_analysis_log     = []

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

  <!-- ── 상위 20 볼트 테이블 ── -->
  <p class="section-title">🏆 상위 20 볼트 (종합점수 기준)</p>
  <div class="table-wrap">
    <table>
      <thead>
        <tr>
          <th>순위</th>
          <th>볼트명</th>
          <th>30일 APR</th>
          <th>샤프비율</th>
          <th>MDD</th>
          <th>수익곡선등급</th>
          <th>로버스트</th>
          <th>TVL ($)</th>
          <th>종합점수</th>
          <th>입금</th>
        </tr>
      </thead>
      <tbody>
        {% for v in vaults[:20] %}
        <tr>
          <td class="rank-num">{{ v.rank }}</td>
          <td class="vault-nm">{{ v.name }}</td>
          <td class="{% if v.apr_30d > 0 %}pos{% else %}neg{% endif %}">{{ "%.1f"|format(v.apr_30d) }}%</td>
          <td class="{% if v.sharpe_ratio > 0 %}pos{% else %}neg{% endif %}">{{ "%.2f"|format(v.sharpe_ratio) }}</td>
          <td class="{% if v.max_drawdown < 20 %}pos{% elif v.max_drawdown < 40 %}neu{% else %}neg{% endif %}">{{ "%.1f"|format(v.max_drawdown) }}%</td>
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
    <p style="margin-top:16px; font-size:0.75rem; color:var(--muted);">완료되면 자동으로 새로고침됩니다.</p>
  </div>
</div>

<script>
function runAnalysis() {
  document.getElementById('run-overlay').classList.add('show');
  document.getElementById('run-btn').disabled = true;

  fetch('/run-analysis', { method: 'POST' })
    .then(r => r.json())
    .then(d => {
      if (d.status === 'started') {
        pollStatus();
      } else {
        alert('분석 시작 실패: ' + d.message);
        document.getElementById('run-overlay').classList.remove('show');
        document.getElementById('run-btn').disabled = false;
      }
    })
    .catch(() => {
      document.getElementById('run-overlay').classList.remove('show');
      document.getElementById('run-btn').disabled = false;
    });
}

function pollStatus() {
  fetch('/analysis-status')
    .then(r => r.json())
    .then(d => {
      if (d.running) {
        setTimeout(pollStatus, 3000);
      } else {
        location.reload();
      }
    })
    .catch(() => setTimeout(pollStatus, 5000));
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

    # 추천 볼트 (robustness 필터)
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


@app.route("/run-analysis", methods=["POST"])
def run_analysis():
    global _analysis_running
    if _analysis_running:
        return jsonify(status="already_running", message="이미 분석이 실행 중입니다.")

    def _run():
        global _analysis_running
        _analysis_running = True
        try:
            subprocess.run(
                [sys.executable, "analyze_top_vaults.py", "--force"],
                cwd=os.path.dirname(os.path.abspath(__file__)),
                capture_output=True, text=True, encoding="utf-8", errors="replace"
            )
        finally:
            _analysis_running = False

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return jsonify(status="started")


@app.route("/analysis-status")
def analysis_status():
    return jsonify(running=_analysis_running)


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
