// ═══════════════════════════════════════════════════════════════════
// HyperVault Analyzer Pro v3.1 — Static Dashboard (GitHub Pages)
// ═══════════════════════════════════════════════════════════════════
const DATA_URL = './data.json';
const KRW = 1400;
let DATA = null;
let modalCharts = {};
let sortCol = 'rank', sortDir = 1;

// ── Utilities ────────────────────────────────────────────────────
const fmt  = n => '$' + Number(n||0).toLocaleString(undefined, {maximumFractionDigits:0});
const fmtP = n => (n > 0 ? '+' : '') + Number(n||0).toFixed(1) + '%';
const fmtKRW = n => (n * KRW / 1e8).toFixed(1);
const aprColor = n => n > 10 ? 'var(--success)' : n > 0 ? 'var(--accent2)' : 'var(--danger)';
const mddColor = n => n < 10 ? 'var(--success)' : n < 20 ? 'var(--warn)' : 'var(--danger)';
const chgDir = d => d === 'up' ? '▲' : d === 'down' ? '▼' : '-';
const chgCol = (d, inv) => {
  if(inv) return d === 'up' ? 'var(--danger)' : d === 'down' ? 'var(--success)' : 'var(--muted)';
  return d === 'up' ? 'var(--success)' : d === 'down' ? 'var(--danger)' : 'var(--muted)';
};

function toast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg; t.style.display = 'block';
  setTimeout(() => t.style.display = 'none', 3000);
}

// ── Page Navigation ──────────────────────────────────────────────
function switchPage(name) {
  document.querySelectorAll('.page').forEach(p => p.style.display = 'none');
  document.querySelectorAll('#header-nav .btn').forEach(b => b.classList.remove('btn-active'));
  document.getElementById('page-' + name).style.display = 'block';
  const navBtn = document.getElementById('nav-' + (name === 'myportfolio' ? 'my' : name));
  if(navBtn) navBtn.classList.add('btn-active');
}

// ── Data Load ────────────────────────────────────────────────────
async function loadData() {
  document.getElementById('loading').style.display = 'block';
  try {
    const r = await fetch(DATA_URL + '?t=' + Date.now());
    if(!r.ok) throw new Error('No data');
    DATA = await r.json();
    document.getElementById('loading').style.display = 'none';
    render();
    document.getElementById('update-time').textContent =
      '분석: ' + (DATA.analysis_date||'-') + ' · ' + new Date().toLocaleTimeString('ko-KR');
  } catch(e) {
    document.getElementById('loading').innerHTML =
      '<div style="font-size:2rem">⚠️</div><p>데이터를 불러올 수 없습니다.<br>export_dashboard_data.py를 실행해주세요.</p>';
  }
}

function render() {
  renderMain();
  renderPortfolioAnalysis();
  renderMyPortfolio();
  switchPage('main');
  document.getElementById('nav-main').classList.add('btn-active');
}

// ═══════ MAIN DASHBOARD ═══════════════════════════════════════════
function renderMain() {
  const d = DATA;
  const s = d.stats || {};

  // Stats row
  document.getElementById('stats-row').innerHTML = `
    <div class="stat-box"><div class="stat-label">Analysis Date</div><div class="stat-val" style="color:#fff">${d.analysis_date||'-'} <small style="font-size:.8rem;color:var(--muted)">${d.prev_date ? '(vs '+d.prev_date+')' : ''}</small></div></div>
    <div class="stat-box"><div class="stat-label">Active Vaults</div><div class="stat-val">${s.total||0}</div></div>
    <div class="stat-box"><div class="stat-label">Avg 30D APR</div><div class="stat-val" style="color:var(--success)">${(s.avg_apr||0).toFixed(1)}%</div></div>
    <div class="stat-box"><div class="stat-label">Avg MDD</div><div class="stat-val" style="color:var(--danger)">${s.avg_mdd||0}%</div></div>`;

  renderVaultTable();

  // Sortable headers
  document.querySelectorAll('th.sortable').forEach(th => {
    th.onclick = () => {
      const col = th.dataset.col;
      if(sortCol === col) sortDir *= -1; else { sortCol = col; sortDir = 1; }
      renderVaultTable();
    };
  });
}

function getVaultSortVal(v, col) {
  switch(col) {
    case 'rank': return v.rank;
    case 'tvl': return v.tvl;
    case 'leader': return v.leader_equity_ratio;
    case 'pnl': return v.pnl_alltime;
    case 'mdd': return v.max_drawdown;
    case 'sharpe': return v.sharpe_ratio;
    case 'apr': return v.apr_30d;
    case 'score': return v.score;
    case 'age': return v.age_days || 0;
    default: return v.rank;
  }
}

function renderVaultTable() {
  const vaults = [...(DATA.vaults || [])];
  vaults.sort((a, b) => (getVaultSortVal(a, sortCol) - getVaultSortVal(b, sortCol)) * sortDir);

  let html = '';
  vaults.forEach(v => {
    const c = v.chg || {};
    const cp = v.chg_pct || {};
    html += `<tr data-leader="${v.leader_equity_ratio}" data-mdd="${v.max_drawdown}" data-tvl="${v.tvl}" data-age="${v.age_days||0}" data-address="${v.address}">
      <td style="text-align:center"><input type="checkbox" class="vault-cb" data-address="${v.address}" onchange="updateSelectionCount()" style="width:18px;height:18px;cursor:pointer;accent-color:var(--accent2);"></td>
      <td>#${v.rank}<br>${v.has_history && c.rank_val ? `<small style="color:${chgCol(c.rank_dir)}">${chgDir(c.rank_dir)} ${c.rank_val}</small>` : (v.has_history ? '<small style="color:var(--muted)">-</small>' : '<span class="badge bg-new">NEW</span>')}</td>
      <td><a href="https://app.hyperliquid.xyz/vaults/${v.address}" target="_blank"><b>${v.name}</b></a><br><small style="color:var(--muted)">${v.address.substring(0,10)}..</small></td>
      <td><span style="font-weight:600">$${Number(v.tvl).toLocaleString()}</span><br><small style="color:var(--muted)">≈ ${fmtKRW(v.tvl)} 억원</small></td>
      <td style="text-align:center"><span class="badge" style="background:rgba(26,188,156,.1);color:var(--accent2)">${(v.leader_equity_ratio*100).toFixed(1)}%</span><br><small style="color:var(--muted)">≈ ${fmtKRW(v.leader_equity_usd||0)} 억원</small></td>
      <td><span style="color:${v.pnl_alltime>=0?'var(--success)':'var(--danger)'};font-weight:600">$${Number(v.pnl_alltime).toLocaleString()}</span> <span style="font-size:.8rem;color:var(--accent2)">(${(v.alltime_roi_pct||0).toFixed(1)}%)</span><br><small style="color:var(--muted)">(${(v.pnl_alltime*KRW/1e8).toFixed(2)} 억원)</small>${v.has_history&&c.pnl_val?`<br><small style="color:${chgCol(c.pnl_dir)}">${chgDir(c.pnl_dir)} $${Number(c.pnl_val).toLocaleString()}</small>`:''}</td>
      <td><span style="color:var(--danger);font-weight:600">${v.max_drawdown}%</span>${v.has_history&&c.mdd_val?`<br><small style="color:${chgCol(c.mdd_dir,true)}">${chgDir(c.mdd_dir)} ${c.mdd_val}%p</small>`:''}</td>
      <td style="color:var(--accent);font-weight:600">${v.sharpe_ratio}</td>
      <td style="color:var(--success);font-weight:600">${v.apr_30d}%</td>
      <td style="cursor:pointer" onclick="showVaultDetails('${v.address}')"><span class="badge bg-accent" style="font-size:.9rem;transition:.2s;cursor:pointer">${v.score}</span>${v.has_history&&c.score_val?`<br><small style="color:${chgCol(c.score_dir)}">${chgDir(c.score_dir)} ${Number(c.score_val).toFixed(3)}</small>`:''}</td>
      <td style="text-align:center">${v.allow_deposits ? '<span class="badge bg-success">OPEN</span>' : '<span class="badge bg-danger">CLOSE</span>'}</td>
      <td style="text-align:center;color:var(--muted);font-weight:600">${v.age_days||'-'} D</td>
    </tr>`;
  });
  document.getElementById('vaultTableBody').innerHTML = html;
  filterTable();
}

// ── Filter & Selection ───────────────────────────────────────────
function filterTable() {
  let leaderMin = parseFloat(document.getElementById('leaderFilter').value);
  if(isNaN(leaderMin)) leaderMin = 0; else leaderMin /= 100;
  let mddMax = parseFloat(document.getElementById('mddFilter').value);
  if(isNaN(mddMax)) mddMax = 999;
  let tvlMin = parseFloat(document.getElementById('tvlFilter').value);
  if(isNaN(tvlMin)) tvlMin = 0;
  let ageMin = parseFloat(document.getElementById('ageFilter').value);
  if(isNaN(ageMin)) ageMin = 0;

  const rows = document.querySelectorAll('#vaultTable tbody tr');
  let count = 0;
  rows.forEach(row => {
    const leader = parseFloat(row.dataset.leader);
    const mdd = parseFloat(row.dataset.mdd);
    const tvl = parseFloat(row.dataset.tvl);
    const age = parseFloat(row.dataset.age) || 0;
    if(leader >= leaderMin && mdd <= mddMax && tvl >= tvlMin && age >= ageMin) { row.style.display=''; count++; }
    else { row.style.display='none'; const cb=row.querySelector('.vault-cb'); if(cb) cb.checked=false; }
  });
  document.getElementById('matchCount').innerText = `${count} vaults matched`;
  updateSelectionCount();
}

function updateSelectionCount() {
  const count = document.querySelectorAll('.vault-cb:checked').length;
  document.getElementById('selCount').innerText = `${count}/20 selected`;
  const btn = document.getElementById('btnAnalyzeSelected');
  btn.disabled = !(count >= 2 && count <= 20);
  if(count > 20) {
    alert('최대 20개까지 선택 가능합니다.');
    const all = document.querySelectorAll('.vault-cb:checked');
    all[all.length-1].checked = false;
    updateSelectionCount();
  }
}

function selectAllVisible() {
  document.querySelectorAll('.vault-cb').forEach(cb => cb.checked=false);
  let sel = 0;
  document.querySelectorAll('#vaultTable tbody tr').forEach(row => {
    if(row.style.display !== 'none' && sel < 20) { const cb=row.querySelector('.vault-cb'); if(cb){cb.checked=true;sel++;} }
  });
  updateSelectionCount();
}

function clearSelection() {
  document.querySelectorAll('.vault-cb').forEach(cb => cb.checked=false);
  updateSelectionCount();
}

function goAnalyzeSelected() {
  const checked = document.querySelectorAll('.vault-cb:checked');
  if(checked.length < 2) { alert('최소 2개 이상 선택해주세요.'); return; }
  toast(`선택한 ${checked.length}개 볼트를 분석합니다. (정적 사이트에서는 사전 계산된 포트폴리오 결과를 표시합니다)`);
  switchPage('portfolio');
}

// ═══════ VAULT MODAL ═══════════════════════════════════════════════
function showVaultDetails(address) {
  const v = (DATA.vaults||[]).find(x => x.address === address);
  if(!v) return;
  document.getElementById('modalTitle').innerText = v.name + ' Details';
  Object.values(modalCharts).forEach(c => { try{c.destroy();}catch(e){} });
  modalCharts = {};

  // PnL
  const pnlCtx = document.getElementById('modalPnlChart').getContext('2d');
  if(v.alltime_pnl && v.alltime_pnl.length > 0) {
    modalCharts.pnl = new Chart(pnlCtx, {type:'line',data:{labels:v.alltime_pnl.map((_,i)=>i+1),datasets:[{label:'PnL ($)',data:v.alltime_pnl,borderColor:'#1abc9c',backgroundColor:'rgba(26,188,156,.1)',fill:true,tension:.1,pointRadius:0}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{display:false}}}});
  }

  // Change bar
  const chgCtx = document.getElementById('modalChgChart').getContext('2d');
  if(v.has_history && v.chg_pct) {
    document.getElementById('modalChgChart').style.display = 'block';
    document.getElementById('modalNewIndicator').style.display = 'none';
    const cp = v.chg_pct;
    modalCharts.chg = new Chart(chgCtx,{type:'bar',data:{labels:['TVL','L_Eq','PnL','MDD','Sharpe','Score'],datasets:[{label:'% Change',data:[cp.tvl,cp.eq,cp.pnl,cp.mdd,cp.sharpe,cp.score],backgroundColor:ctx2=>(ctx2.raw>=0?'rgba(46,204,113,.8)':'rgba(231,76,60,.8)'),borderRadius:4}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{y:{suggestedMin:-5,suggestedMax:5}}}});
  } else {
    document.getElementById('modalChgChart').style.display = 'none';
    document.getElementById('modalNewIndicator').style.display = 'block';
  }

  // Score breakdown
  const scoreCtx = document.getElementById('modalScoreChart').getContext('2d');
  const sh=v.calc_sharpe*2, ap=v.calc_apr/50, md=v.calc_mdd/30, rb=v.calc_rob*3;
  modalCharts.score = new Chart(scoreCtx,{type:'bar',data:{labels:['Sharpe','APR','MDD Pen.','Robust'],datasets:[{data:[sh,ap,-md,rb],backgroundColor:['#3498db','#2ecc71','#e74c3c','#9b59b6'],borderRadius:4}]},options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}}}});

  // Trend charts
  function trend(id,arr,dates,bgC,bC){
    const ctx=document.getElementById(id).getContext('2d');
    if(!arr||!arr.length) return new Chart(ctx,{type:'line',data:{labels:['No Data'],datasets:[{data:[0]}]},options:{plugins:{legend:{display:false}}}});
    return new Chart(ctx,{type:'line',data:{labels:dates,datasets:[{data:arr,borderColor:bC,backgroundColor:bgC,fill:true,tension:.2,pointRadius:3,pointBackgroundColor:bC}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},tooltip:{mode:'index',intersect:false}},scales:{x:{ticks:{font:{size:9},maxRotation:45}},y:{ticks:{font:{size:9}}}}}});
  }
  const h = v.history || {};
  const td = h.dates || [];
  modalCharts.tS = trend('modalTrendScoreChart',h.score,td,'rgba(79,142,247,.1)','#4f8ef7');
  modalCharts.tM = trend('modalTrendMddChart',h.mdd,td,'rgba(231,76,60,.1)','#e74c3c');
  modalCharts.tH = trend('modalTrendSharpeChart',h.sharpe,td,'rgba(52,152,219,.1)','#3498db');
  modalCharts.tR = trend('modalTrendRobustChart',h.robust,td,'rgba(155,89,182,.1)','#9b59b6');

  document.getElementById('vaultModal').style.display = 'flex';
}

function closeModal() { document.getElementById('vaultModal').style.display = 'none'; }

// ═══════ PORTFOLIO ANALYSIS ═══════════════════════════════════════
let currentDateKey = null; // 선택된 분석 날짜

function renderPortfolioAnalysis(dateKey) {
  const byDate = DATA.portfolio_by_date || {};
  const availableDates = Object.keys(byDate).sort();

  // 기본값: 최신 날짜
  if(!dateKey) {
    dateKey = availableDates.length ? availableDates[availableDates.length - 1] : null;
  }
  currentDateKey = dateKey;

  const pf = dateKey && byDate[dateKey] ? byDate[dateKey] : DATA.portfolio;
  const el = document.getElementById('page-portfolio');
  if(!pf) { el.innerHTML = '<div class="card" style="text-align:center;padding:60px;"><h3>📊 포트폴리오 분석 데이터가 없습니다</h3><p style="color:var(--muted)">export_dashboard_data.py를 먼저 실행해주세요.</p></div>'; return; }

  let html = '';

  // ── Date Selector ──
  if(availableDates.length > 1) {
    // 최신 날짜와 선택 날짜의 차이(일) 계산
    const latestDate = availableDates[availableDates.length - 1];
    const selectedDate = new Date(dateKey + 'T00:00:00');
    const latestDt = new Date(latestDate + 'T00:00:00');
    const diffDays = Math.round((latestDt - selectedDate) / (1000 * 60 * 60 * 24));
    const diffLabel = diffDays === 0 ? '최신' : `${diffDays}일 전`;

    html += `<div class="card" style="display:flex;align-items:center;gap:15px;flex-wrap:wrap;border:1px solid var(--accent);padding:16px 20px;">
      <span style="font-size:1.2rem;">📅</span>
      <div style="flex:1;">
        <h3 style="margin:0;color:var(--accent);">분석 날짜 선택 <span style="font-size:.85rem;color:var(--accent2);font-weight:400;margin-left:8px;">${dateKey} (${diffLabel})</span></h3>
        <p style="margin:3px 0 0;font-size:.82rem;color:var(--muted);">스냅샷 날짜를 선택하면 해당 시점의 볼트 데이터로 포트폴리오가 재계산됩니다. 데이터 포인트: <b style="color:var(--accent2)">${pf.analysis_days||0}개</b></p>
      </div>
      <div style="display:flex;gap:6px;flex-wrap:wrap;">`;
    for(const d of availableDates) {
      const isActive = d === currentDateKey;
      const isLatest = d === latestDate;
      const short = d.substring(5); // "MM-DD"
      const label = isLatest ? `${short} ★` : short;
      html += `<button onclick="renderPortfolioAnalysis('${d}')" class="btn ${isActive ? 'btn-primary' : ''}" style="padding:8px 14px;font-size:.82rem;min-width:70px;">${label}</button>`;
    }
    html += `</div></div>`;
  }

  // Info banner
  html += `<div class="card" style="border-left:4px solid var(--accent2)"><h3>🔬 Portfolio Analysis</h3><p style="color:var(--muted);font-size:.9rem;margin-top:5px">총 ${pf.n_total||0}개 볼트 중 ${pf.n_filtered||0}개 필터 통과 → ${pf.n_selected||0}개 최종 선택 (분석 기간: ${pf.analysis_days||0}일)</p></div>`;

  // Investment simulator
  html += `<div class="card" style="border:1px solid var(--accent2);display:flex;align-items:center;gap:20px;flex-wrap:wrap">
    <div style="flex:1"><h3 style="color:var(--accent2)">💡 Custom Investment Simulation</h3><p style="margin:5px 0 0;font-size:.9rem;color:var(--muted)">투자 금액을 입력하면 전략별 배분 금액을 확인할 수 있습니다.</p></div>
    <div style="display:flex;flex-direction:column;align-items:flex-end;gap:6px">
      <div style="position:relative;display:flex;align-items:center"><span style="position:absolute;left:15px;font-weight:bold;color:#fff">$</span>
      <input type="text" id="simAmount" value="100,000" oninput="formatAmountInput(this);updateSimulation()" style="width:200px;padding:12px 12px 12px 30px;font-size:1.2rem;font-weight:bold;background:#0b0f1a;border:1px solid var(--border);color:#fff;border-radius:8px;text-align:right"></div>
      <span id="simAmountKRW" style="font-size:.85rem;color:var(--accent2);font-weight:600">≈ ₩140,000,000</span>
    </div></div>`;

  // Selected vaults comparison table
  if(pf.selected_vaults && pf.selected_vaults.length) {
    html += `<div class="card"><h2 style="margin-bottom:5px">📊 분석 대상 볼트 비교</h2><p style="color:var(--muted);font-size:.9rem;margin-bottom:15px">${pf.n_selected||0}개 볼트의 핵심 지표 비교</p><div class="table-wrap"><table style="min-width:800px"><thead><tr><th>Vault</th><th style="text-align:center">30d APR</th><th style="text-align:center">Sharpe</th><th style="text-align:center">MDD</th><th style="text-align:center">Robustness</th><th style="text-align:center">TVL</th><th style="text-align:center">Score</th></tr></thead><tbody>`;
    pf.selected_vaults.forEach(v => {
      const rc = v.robustness_score >= 0.7 ? 'var(--success)' : v.robustness_score < 0.4 ? 'var(--danger)' : 'var(--warn)';
      html += `<tr><td><a href="https://app.hyperliquid.xyz/vaults/${v.address}" target="_blank"><b>${(v.name||'').substring(0,25)}</b></a></td>
        <td style="text-align:center;color:var(--success);font-weight:600">${v.apr_30d}%</td>
        <td style="text-align:center;color:var(--accent)">${v.sharpe_ratio}</td>
        <td style="text-align:center;color:var(--danger)">${v.max_drawdown}%</td>
        <td style="text-align:center;color:${rc}">${v.robustness_score}</td>
        <td style="text-align:center">$${Number(v.tvl||0).toLocaleString()}</td>
        <td style="text-align:center;font-weight:800;color:var(--accent)">${v.score}</td></tr>`;
    });
    html += '</tbody></table></div></div>';
  }

  // Strategy cards
  const strategyInfo = {
    max_sharpe: {cls:'',emoji:'📈',desc:'위험 대비 수익이 가장 높은 조합. Sharpe가 높은 볼트에 집중 배분합니다. 수익률은 높지만 특정 볼트에 쏠릴 수 있습니다.'},
    min_variance: {cls:'s-mv',emoji:'🛡️',desc:'전체 변동성을 최소화. MDD가 낮고 변동성이 작은 볼트에 집중합니다. 안정적이며 서로 반대로 움직이는 볼트끼리 조합합니다.'},
    risk_parity: {cls:'s-rp',emoji:'⚖️',desc:'각 볼트가 위험에 동일하게 기여하도록 배분. 변동성이 큰 볼트는 비중을 줄이고 안정적인 볼트는 비중을 높입니다.'},
    min_cvar: {cls:'s-cv',emoji:'🔒',desc:'최악의 손실 시나리오(하위 5%)를 최소화. 원금 보호를 최우선으로 합니다.'}
  };

  if(pf.portfolios && Object.keys(pf.portfolios).length) {
    html += `<div class="card"><h2 style="margin-bottom:5px">💡 왜 이렇게 추천했는가?</h2><p style="color:var(--muted);font-size:.9rem;margin-bottom:20px">4가지 전략은 각각 다른 투자 철학을 반영합니다.</p><div class="grid grid-2">`;
    for(const [key, p] of Object.entries(pf.portfolios)) {
      const si = strategyInfo[key] || {cls:'',emoji:'📊',desc:''};
      const st = p.stats || {};
      const bt = p.backtest || {};
      const weights = st.weights || {};
      html += `<div class="card strategy-card ${si.cls}"><div class="strategy-header"><h4 style="color:var(--accent)">${si.emoji} ${p.label||key}</h4><span style="font-size:1.8rem;font-weight:800;color:var(--success)">${st.annual_return_pct||0}%</span></div>
        <div class="strategy-desc"><p style="margin:0;color:var(--text)">📌 <b>핵심 원리:</b> ${si.desc}</p></div>
        <div class="strategy-metrics">
          <div class="metric-box"><div class="mk">연 수익률</div><div class="mv" style="color:var(--success)">${st.annual_return_pct||0}%</div></div>
          <div class="metric-box"><div class="mk">변동성</div><div class="mv" style="color:var(--warn)">${st.annual_vol_pct||0}%</div></div>
          <div class="metric-box"><div class="mk">Sharpe</div><div class="mv" style="color:var(--accent)">${st.sharpe||0}</div></div>
          <div class="metric-box"><div class="mk">Max MDD</div><div class="mv" style="color:var(--danger)">${bt.max_drawdown_pct||0}%</div></div>
        </div>
        <div style="background:rgba(255,255,255,.03);padding:10px;border-radius:8px">`;
      for(const [name, w] of Object.entries(weights)) {
        if(w > 3) {
          html += `<div class="weight-bar"><span style="font-weight:600;max-width:55%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${name.substring(0,30)}</span>
            <div style="display:flex;align-items:center;gap:10px"><div class="weight-bar-fill"><div class="fill" style="width:${Math.min(w*2.86,100)}%"></div></div>
            <span style="color:var(--accent2);font-weight:800;min-width:40px;text-align:right">${w}%</span>
            <span class="alloc-dollar" data-weight="${w}" style="color:#fff;min-width:60px;text-align:right">$0</span></div></div>`;
        }
      }
      html += '</div></div>';
    }
    html += '</div></div>';
  }

  // Correlation matrix
  if(pf.corr_selected && pf.corr_selected.names) {
    const names = pf.corr_selected.names;
    const matrix = pf.corr_selected.matrix;
    html += `<div class="card"><h2 style="margin-bottom:5px">🔗 상관관계 분석</h2><p style="color:var(--muted);font-size:.9rem;margin-bottom:15px">볼트 간 상관관계가 낮을수록 분산 효과가 큽니다.</p><div class="table-wrap"><table style="min-width:500px;font-size:.75rem"><thead><tr><th></th>`;
    names.forEach(n => html += `<th style="text-align:center;max-width:80px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:.65rem" title="${n}">${n.substring(0,12)}</th>`);
    html += '</tr></thead><tbody>';
    names.forEach((n, i) => {
      html += `<tr><td style="font-weight:600;max-width:80px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:.7rem" title="${n}">${n.substring(0,12)}</td>`;
      names.forEach((_, j) => {
        const val = matrix[i][j];
        const bg = val > 0.3 ? `rgba(231,76,60,${val*0.4})` : val < -0.1 ? `rgba(79,142,247,${Math.abs(val)*0.5})` : 'rgba(255,255,255,.02)';
        const color = val > 0.5 ? 'var(--danger)' : val < -0.1 ? 'var(--accent)' : 'var(--muted)';
        const fw = Math.abs(val) > 0.5 ? '700' : '400';
        html += `<td class="corr-cell" style="background:${bg};font-weight:${fw};color:${color}">${i===j?'-':val}</td>`;
      });
      html += '</tr>';
    });
    html += '</tbody></table></div>';
    html += `<div style="margin-top:15px;background:rgba(255,255,255,.03);padding:15px;border-radius:8px;font-size:.85rem;line-height:1.7">
      <p style="margin:0;color:var(--text)"><b>📖 읽는 법:</b></p>
      <ul style="margin:5px 0 0;padding-left:20px;color:var(--muted)">
        <li><span style="color:var(--danger)">빨간 숫자 (0.5 이상)</span> = 같이 움직임 → 분산 효과 ❌</li>
        <li><span style="color:var(--accent)">파란 숫자 (음수)</span> = 반대로 움직임 → 분산 효과 ✅</li>
        <li><span style="color:var(--muted)">회색 숫자 (0 근처)</span> = 독립적 → 분산 효과 ✅</li>
      </ul></div></div>`;
  }

  // Strategy guide
  html += `<div class="card" style="border-left:4px solid var(--accent2)"><h2 style="margin-bottom:5px">📝 투자 전략 가이드</h2>
    <div style="font-size:.9rem;line-height:1.8;color:var(--muted)"><div class="grid grid-2" style="margin-top:10px">
      <div class="guide-box aggressive"><p style="margin:0;color:var(--success);font-weight:600">✅ 공격적 투자자 (수익 우선)</p><p style="margin:8px 0 0">→ <b>최대 샤프 📈</b> 전략 추천<br>높은 Sharpe 볼트에 집중, 수익률 극대화.</p></div>
      <div class="guide-box stable"><p style="margin:0;color:var(--accent2);font-weight:600">🛡️ 안정형 투자자 (원금 보호)</p><p style="margin:8px 0 0">→ <b>원금보호 CVaR 🔒</b> 또는 <b>최소분산 🛡️</b> 추천<br>최악의 시나리오를 최소화, 변동성 억제.</p></div>
      <div class="guide-box balanced"><p style="margin:0;color:var(--warn);font-weight:600">⚖️ 균형형 투자자</p><p style="margin:8px 0 0">→ <b>위험 균형 ⚖️</b> 전략 추천<br>모든 볼트가 위험에 균등 기여, 특정 볼트 의존도 낮음.</p></div>
      <div class="guide-box info"><p style="margin:0;color:var(--accent);font-weight:600">🧠 분석 기간</p><p style="margin:8px 0 0">본 분석은 <b>최근 ${pf.analysis_days||0}일</b> 데이터 기반.<br>${pf.n_selected||0}개 볼트가 저상관 기준으로 최종 선택.</p></div>
    </div></div></div>`;

  el.innerHTML = html;
  updateSimulation();
}

// ═══════ MY PORTFOLIO ═════════════════════════════════════════════
function renderMyPortfolio() {
  const mp = DATA.my_portfolio;
  const el = document.getElementById('page-myportfolio');
  if(!mp || !mp.holdings || !mp.holdings.length) {
    el.innerHTML = `<div class="card" style="text-align:center;padding:60px"><h3>📱 My Portfolio</h3><p style="color:var(--muted);margin-top:10px">포트폴리오가 설정되지 않았습니다.<br>my_portfolio.json 파일에 투자 현황을 입력하세요.</p></div>`;
    return;
  }

  let html = `<div class="card"><h3>📱 Performance Summary</h3>
    <div class="perf-grid" style="margin-top:20px">
      <div class="perf-box"><div class="stat-label">Total Invested (${mp.days_held||0} Days)</div><div class="stat-val" style="color:#fff;font-size:1.6rem">${fmt(mp.total_invested)}</div></div>
      <div class="perf-box"><div class="stat-label">Gross PnL (Before Fees)</div><div class="stat-val" style="color:${mp.gross_pnl>=0?'var(--success)':'var(--danger)'};font-size:1.6rem">${fmt(mp.gross_pnl)}</div><div style="font-size:.9rem;margin-top:5px;color:${mp.gross_pnl>=0?'var(--success)':'var(--danger)'}">${mp.gross_pnl_pct||0}%</div></div>
      <div class="perf-box highlight"><div class="stat-label" style="color:var(--accent2)">Net Return / Final Payout</div><div class="stat-val" style="color:${mp.net_pnl>=0?'var(--success)':'var(--danger)'};font-size:2rem">${fmt(mp.total_invested+(mp.net_pnl||0))}</div><div style="font-size:1rem;font-weight:600;margin-top:5px;color:${mp.net_pnl>=0?'var(--success)':'var(--danger)'}">Net PnL: ${fmt(mp.net_pnl)} (${mp.net_pnl_pct||0}%)</div></div>
    </div></div>`;

  // Holdings table
  html += `<div class="card"><h3>Current Positions</h3><div class="table-wrap"><table><thead><tr><th>Vault</th><th>Invested / Weight</th><th>APR / MDD</th><th>Gross PnL</th><th>Status</th></tr></thead><tbody>`;
  mp.holdings.forEach(h => {
    const netPnl = h.pnl > 0 ? h.pnl * 0.9 : h.pnl;
    html += `<tr>
      <td><a href="https://app.hyperliquid.xyz/vaults/${h.address}" target="_blank"><b>${h.name}</b></a><br><small style="color:var(--muted)">${h.address.substring(0,12)}...</small></td>
      <td>${fmt(h.invested_usd)}<br><small style="color:var(--accent2)">${h.weight_pct}%</small></td>
      <td><span style="color:var(--success)">${h.apr_30d}%</span><br><small style="color:var(--danger)">${h.mdd}%</small></td>
      <td><span style="color:${h.pnl>=0?'var(--success)':'var(--danger)'};font-weight:600">${fmt(h.pnl)}</span><br><small style="color:${h.pnl_pct>=0?'var(--success)':'var(--danger)'}">${h.pnl_pct}%</small></td>
      <td>${h.danger ? '<span class="badge bg-danger">⚠️ 주의</span>' : '<span class="badge bg-success">✅ 정상</span>'}</td>
    </tr>`;
  });
  html += '</tbody></table></div></div>';
  el.innerHTML = html;
}

// ── Simulation Input ─────────────────────────────────────────────
function parseAmountValue(el) { return parseFloat(el.value.replace(/,/g,'')) || 0; }
function formatAmountInput(el) {
  const cursor = el.selectionStart;
  const oldLen = el.value.length;
  const raw = el.value.replace(/[^0-9]/g,'');
  const num = parseInt(raw) || 0;
  el.value = num.toLocaleString();
  const newLen = el.value.length;
  el.setSelectionRange(cursor + (newLen - oldLen), cursor + (newLen - oldLen));
}

function updateSimulation() {
  const input = document.getElementById('simAmount');
  if(!input) return;
  let simAmount = parseAmountValue(input);
  if(simAmount <= 0) simAmount = 100000;
  const krwEl = document.getElementById('simAmountKRW');
  if(krwEl) krwEl.innerText = '≈ ₩' + Math.round(simAmount * KRW).toLocaleString();
  document.querySelectorAll('.alloc-dollar').forEach(el => {
    const w = parseFloat(el.dataset.weight) || 0;
    el.innerText = '$' + Math.round(simAmount * w / 100).toLocaleString();
  });
}

// ── Init ─────────────────────────────────────────────────────────
loadData();
setInterval(loadData, 300000);
