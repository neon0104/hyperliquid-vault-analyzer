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
  
  let selectedAddresses = Array.from(checked).map(cb => cb.dataset.address);
  let selectedVaults = DATA.vaults.filter(v => selectedAddresses.includes(v.address) && v.alltime_pnl && v.alltime_pnl.length > 5);
  
  if(selectedVaults.length < 2) {
      alert('분석에 필요한 과거 수익률 데이터가 충분한 볼트가 2개 미만입니다. (신규 볼트 제외)');
      return;
  }
  
  currentPortfolioVaults = selectedVaults;
  portfolioWeights = {};
  
  let evenW = Math.floor(100 / selectedVaults.length);
  selectedVaults.forEach((v, i) => {
      portfolioWeights[v.address] = (i === selectedVaults.length - 1) ? (100 - evenW * i) : evenW;
  });
  
  toast(`선택한 ${selectedVaults.length}개 볼트를 분석합니다.`);
  renderPortfolioAnalysis('custom');
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
let currentPortfolioVaults = [];
let portfolioWeights = {};
let backtestChart = null;
let scatterChart = null;

function renderPortfolioAnalysis(mode) {
  const el = document.getElementById('page-portfolio');
  const d = DATA;
  
  if(!d.vaults || d.vaults.length === 0) {
    el.innerHTML = '<div class="card" style="text-align:center;padding:60px;"><h3>📊 분석 가능한 볼트 데이타가 없습니다</h3></div>'; 
    return; 
  }

  if(mode !== 'custom') {
      let vaults = d.vaults.filter(v => v.tvl > 10000 && v.alltime_pnl && v.alltime_pnl.length > 20);
      vaults.sort((a,b) => b.score - a.score);
      currentPortfolioVaults = vaults.slice(0, 15);
      portfolioWeights = {};
      for(let i=0; i<5; i++) {
         if(currentPortfolioVaults[i]) portfolioWeights[currentPortfolioVaults[i].address] = 20;
      }
      for(let i=5; i<currentPortfolioVaults.length; i++) {
         if(currentPortfolioVaults[i]) portfolioWeights[currentPortfolioVaults[i].address] = 0;
      }
  }

  let html = `
    <div class="card" style="border-left:4px solid var(--accent2)">
      <h2>🔬 Interactive Portfolio Backtester & Screener</h2>
      <p style="color:var(--muted);font-size:.9rem;margin-top:5px"> Growi.fi 프레임워크 기반: 수익성이 검증된 상위 볼트들의 과거 성과를 조합하여 매달 최적의 리밸런싱 비율을 시뮬레이션 합니다.</p>
      <p style="color:var(--accent);font-size:1rem;margin-top:10px;font-weight:bold;">📅 백테스트 기준 날짜: ${d.analysis_date || '알 수 없음'}</p>
    </div>
    
    <div class="grid grid-2" style="grid-template-columns: 2fr 1fr">
      
      <!-- Left: Backtest Chart -->
      <div class="card">
        <h3>📈 Portfolio Equity Curve (Simulated)</h3>
        <div style="font-size:1.4rem;font-weight:bold;color:var(--success);margin-bottom:10px" id="totalReturnText">Total Return: +0.00%</div>
        <div class="chart-container" style="height: 350px;">
          <canvas id="customBacktestChart"></canvas>
        </div>
        
        <h3 style="margin-top:30px">🛡️ Sweet Spot Screener (Risk vs Reward)</h3>
        <p style="font-size:.8rem;color:var(--muted)">좌측 상단일수록 리스크(MDD) 대비 가성비(APR)가 큰 볼트입니다. (버블 크기 = TVL)</p>
        <div class="chart-container" style="height: 320px;">
          <canvas id="customScatterChart"></canvas>
        </div>
      </div>

      <!-- Right: Control Deck -->
      <div class="card" style="display:flex; flex-direction:column; gap: 15px;">
        <h3>🎛️ Rebalancing Desk <button class="btn btn-sm" onclick="autoOptimize()" style="float:right;background:var(--accent);color:#fff;padding:4px 8px;font-size:0.8rem">✨ AI 최적 비중 (수익 극대화)</button></h3>
        <p style="font-size:.85rem;color:var(--muted);margin-bottom:10px;">총합 100%에 맞춰 슬라이더를 조정하거나 최적 비중을 찾으세요.</p>
        
        <div style="background:rgba(255,255,255,0.02); padding:15px; border-radius:8px;">
          <div style="display:flex; justify-content:space-between; margin-bottom:10px">
            <span style="font-weight:bold">투자금(USD):</span>
            <input type="number" id="simInvestAmount" value="10000" style="width:100px; text-align:right; background:#0b0f1a; color:#fff; border:1px solid #333; border-radius:4px;" oninput="document.getElementById('totalReturnText').innerHTML = '⚠️ 설정 변경됨. [분석 시작]을 누르세요!'; document.getElementById('totalReturnText').style.color='var(--warn)';">
          </div>
          <div style="display:flex; justify-content:space-between; margin-bottom:15px">
            <span style="font-weight:bold">비중 총합:</span>
            <span id="weightSumText" style="color:var(--success); font-weight:bold;">100%</span>
          </div>
          <button id="btnRunSim" class="btn btn-primary" style="width:100%; font-size:1.05rem; padding:10px" onclick="runSimulation()">🚀 분석 시작 (Run Simulation)</button>
        </div>
        
        <div id="slidersContainer" style="overflow-y:auto; max-height:550px; padding-right:10px;">
  `;

  currentPortfolioVaults.forEach(v => {
      let w = portfolioWeights[v.address] || 0;
      html += `
        <div style="margin-bottom: 12px; border-bottom:1px solid rgba(255,255,255,0.05); padding-bottom:8px;">
          <div style="display:flex; justify-content:space-between; font-size:.85rem; margin-bottom:5px;">
            <span><a href="https://app.hyperliquid.xyz/vaults/${v.address}" target="_blank" style="color:var(--accent)">${v.name.substring(0,18)}</a></span>
            <span id="label_w_${v.address}" style="font-weight:bold; color:${w>0?'var(--success)':'var(--muted)'}">${w}%</span>
          </div>
          <input type="range" id="w_${v.address}" min="0" max="100" value="${w}" style="width:100%; accent-color:var(--accent2); cursor:pointer" oninput="onWeightSliderChange('${v.address}')">
          <div style="display:flex; justify-content:space-between; font-size:.7rem; color:var(--muted); margin-top:2px;">
            <span style="color:var(--success)">APR: ${v.apr_30d}%</span>
            <span style="color:var(--danger)">MDD: ${v.max_drawdown}%</span>
          </div>
        </div>
      `;
  });

  html += `
        </div>
      </div>
    </div>
  `;
  
  el.innerHTML = html;
  
  setTimeout(() => {
     renderScatterChart();
     updateInteractiveBacktest();
  }, 100);
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

function onWeightSliderChange(addr) {
    let rawW = parseInt(document.getElementById('w_' + addr).value) || 0;
    portfolioWeights[addr] = rawW;
    
    // Total
    let sum = 0;
    currentPortfolioVaults.forEach(v => sum += (portfolioWeights[v.address] || 0));
    let tEl = document.getElementById('weightSumText');
    if(sum === 100) tEl.style.color = 'var(--success)';
    else tEl.style.color = 'var(--danger)';
    tEl.innerText = sum + '%';
    
    document.getElementById('label_w_' + addr).innerText = rawW + '%';
    document.getElementById('label_w_' + addr).style.color = rawW > 0 ? 'var(--success)' : 'var(--muted)';
    
    document.getElementById('totalReturnText').innerHTML = '⚠️ 설정 변경됨. [분석 시작]을 누르세요!';
    document.getElementById('totalReturnText').style.color = 'var(--warn)';
    
    const btn = document.getElementById('btnRunSim');
    if(btn) { btn.classList.add('pulse'); }
}

function runSimulation() {
    const btn = document.getElementById('btnRunSim');
    if(!btn) return;
    
    const originalText = btn.innerText;
    btn.innerText = "⏳ 시뮬레이터 구동 중...";
    btn.disabled = true;
    btn.classList.remove('pulse');
    
    // UI 업데이트를 위해 약간의 지연
    setTimeout(() => {
        updateInteractiveBacktest();
        btn.innerText = "✅ 백테스트 완료";
        
        setTimeout(() => {
            btn.innerText = originalText;
            btn.disabled = false;
        }, 1500);
    }, 400);
}

function autoOptimize() {
    let totalScore = 0;
    currentPortfolioVaults.forEach(v => {
        let score = Math.max(0, parseFloat(v.apr_30d) || 0);
        let mdd = parseFloat(v.max_drawdown) || 100;
        score = score / Math.max(1, mdd / 5); 
        totalScore += score;
    });
    
    currentPortfolioVaults.forEach((v, i) => {
        let w = 0;
        if(totalScore > 0) {
            let score = Math.max(0, parseFloat(v.apr_30d) || 0) / Math.max(1, (parseFloat(v.max_drawdown) || 100) / 5);
            w = Math.round((score / totalScore) * 100);
        } else {
            w = Math.floor(100 / currentPortfolioVaults.length);
        }
        portfolioWeights[v.address] = w;
    });
    
    let sum = 0;
    currentPortfolioVaults.forEach(v => sum += portfolioWeights[v.address]);
    if(sum !== 100 && currentPortfolioVaults.length > 0) {
        portfolioWeights[currentPortfolioVaults[0].address] += (100 - sum);
    }
    
    currentPortfolioVaults.forEach(v => {
        let w = portfolioWeights[v.address];
        let slider = document.getElementById('w_' + v.address);
        if(slider) slider.value = w;
        let label = document.getElementById('label_w_' + v.address);
        if(label) {
            label.innerText = w + '%';
            label.style.color = w > 0 ? 'var(--success)' : 'var(--muted)';
        }
    });
    
    let tEl = document.getElementById('weightSumText');
    if(tEl) {
        tEl.style.color = 'var(--success)';
        tEl.innerText = '100%';
    }
    
    let retText = document.getElementById('totalReturnText');
    if(retText) {
        retText.innerHTML = '⚠️ 최적의 비중을 찾았습니다! [분석 시작]을 누르세요.';
        retText.style.color = 'var(--accent)';
    }
    
    const btn = document.getElementById('btnRunSim');
    if(btn) { btn.classList.add('pulse'); }
}

function updateInteractiveBacktest() {
    let investAmount = parseFloat(document.getElementById('simInvestAmount').value) || 10000;
    
    // Normalize weights
    let normWeights = {};
    let sum = 0;
    currentPortfolioVaults.forEach(v => sum += (portfolioWeights[v.address] || 0));
    
    if(sum === 0) {
        if(backtestChart) backtestChart.destroy();
        document.getElementById('totalReturnText').innerText = "투자 비중을 설정해주세요.";
        return;
    }
    
    currentPortfolioVaults.forEach(v => {
        normWeights[v.address] = (portfolioWeights[v.address] || 0) / sum;
    });
    
    let validVaults = currentPortfolioVaults.filter(v => normWeights[v.address] > 0);
    // Filter out vaults missing pnl
    validVaults = validVaults.filter(v => v.alltime_pnl && v.alltime_pnl.length > 0);
    if(validVaults.length === 0) {
        if(backtestChart) backtestChart.destroy();
        document.getElementById('totalReturnText').innerText = "과거 수익률 기록이 없는 볼트를 선택하셨습니다.";
        return;
    }
    
    let SIM_DAYS = 30;
    let eqCurve = [];
    for(let i=0; i<SIM_DAYS; i++) eqCurve.push(investAmount);
    
    validVaults.forEach(v => {
        let w = normWeights[v.address];
        let pnlArr = v.alltime_pnl || [];
        
        let baselineCapital = v.tvl - (pnlArr.length > 0 ? pnlArr[pnlArr.length-1] : 0); 
        if(baselineCapital <= 0) baselineCapital = v.tvl || 10000;
        
        let availableLen = pnlArr.length;
        let startPnl = availableLen > 0 ? pnlArr[0] : 0;
        
        for(let i=0; i<SIM_DAYS; i++) {
             let pnlIdx = availableLen - SIM_DAYS + i;
             let pctReturn = 0;
             if (pnlIdx >= 0 && pnlIdx < availableLen) {
                 pctReturn = (pnlArr[pnlIdx] - startPnl) / baselineCapital;
             } else if (pnlIdx >= availableLen && availableLen > 0) {
                 pctReturn = (pnlArr[availableLen-1] - startPnl) / baselineCapital;
             }
             eqCurve[i] += (investAmount * w * pctReturn);
        }
    });

    let finalRet = ((eqCurve[SIM_DAYS-1] / investAmount) - 1) * 100;
    document.getElementById('totalReturnText').innerText = "Total 30D Return: " + (finalRet>=0?'+':'') + finalRet.toFixed(2) + "%";
    document.getElementById('totalReturnText').style.color = finalRet>=0 ? 'var(--success)' : 'var(--danger)';

    let labels = Array.from({length: SIM_DAYS}, (_, i) => "D-" + (SIM_DAYS - i - 1));

    if(backtestChart) backtestChart.destroy();
    const ctx = document.getElementById('customBacktestChart').getContext('2d');
    backtestChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Portfolio Value ($)',
                data: eqCurve,
                borderColor: '#1abc9c',
                backgroundColor: 'rgba(26,188,156,0.1)',
                fill: true,
                tension: 0.1,
                pointRadius: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            interaction: { mode: 'index', intersect: false },
            scales: {
                y: { ticks: { font: {size: 11} } },
                x: { ticks: { autoSkip: true, maxTicksLimit: 10, font: {size: 10} } }
            }
        }
    });
}

function renderScatterChart() {
    if(scatterChart) scatterChart.destroy();
    const ctx = document.getElementById('customScatterChart').getContext('2d');
    
    let dataset = currentPortfolioVaults.map(v => {
        return {
            x: v.max_drawdown,
            y: v.apr_30d,
            r: Math.max(5, Math.min(25, v.tvl / 50000)),
            vaultName: v.name,
            tvl: v.tvl
        }
    });

    scatterChart = new Chart(ctx, {
        type: 'bubble',
        data: {
            datasets: [{
                label: 'Top Vaults',
                data: dataset,
                backgroundColor: dataset.map(d => d.y > 10 && d.x < 15 ? 'rgba(46,204,113,0.7)' : 'rgba(52,152,219,0.5)'),
                borderColor: 'rgba(255,255,255,0.2)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: function(ctx) {
                            let d = ctx.raw;
                            return d.vaultName + ' | MDD: ' + d.x + '% | APR: ' + d.y + '% | TVL: $' + d.tvl.toLocaleString();
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: { display: true, text: 'Max Drawdown (%)', color: '#999', font:{size:11} },
                    reverse: false,
                    grid: { color: 'rgba(255,255,255,0.05)'}
                },
                y: {
                    title: { display: true, text: '30d APR (%)', color: '#999', font:{size:11} },
                    grid: { color: 'rgba(255,255,255,0.05)'}
                }
            }
        }
    });
}

// ── Init ─────────────────────────────────────────────────────────
loadData();
setInterval(loadData, 300000);
