# 🔬 Research Report — Hyperliquid Vault Analyzer
**Agent**: Research Agent  
**Updated**: 2026-03-09T21:27:30+09:00  
**Tasks covered**: Task 4 (ECharts 업그레이드), Task 5 (리밸런싱 엔진)

---

## 📋 섹션 인덱스

1. [기존 Task 1 연구 (인증 라이브러리)](#1-기존-task-1-연구-인증-라이브러리)
2. [Task 4 — ECharts 통합 가이드](#2-task-4--echarts-통합-가이드)
3. [Task 5 — 리밸런싱 엔진 설계 연구](#3-task-5--리밸런싱-엔진-설계-연구)
4. [Hyperliquid SDK API 참조](#4-hyperliquid-sdk-api-참조)

---

## 1. 기존 Task 1 연구 (인증 라이브러리)

| Library | Type | Pros | Cons |
|---------|------|------|------|
| **Flask-JWT-Extended** | Token (JWT) | Feature-rich, refresh tokens, fresh tokens, revocation support | Stateless by default |
| **Flask-Login** | Session (Cookie) | Simple, battle-tested | Not ideal for cross-origin APIs |
| **Authlib** | OAuth2 / OpenID | Standards-compliant, most flexible | More setup complexity |
| **Flask-Dance** | OAuth2 | Simple for common providers | Less flexible than Authlib |

### ✅ Recommendation (Task 1)
> **Authlib (OAuth2) + Flask-JWT-Extended** 조합 권장

---

## 2. Task 4 — ECharts 통합 가이드

### 2.1 라이브러리 비교

| Rank | Library | Reason |
|------|---------|--------|
| **1st** | **Apache ECharts** | Best for financial data, dark theme built-in, high performance, zoom/pan, candlestick |
| 2nd | Plotly / Dash | Python-first, heaviest but most interactive |
| 3rd | ApexCharts | Modern, glow effects, lighter than Plotly |

**→ 결정: Apache ECharts 채택 (CDN, Flask 구조 변경 불필요)**

### 2.2 CDN 교체

```html
<!-- PORTFOLIO_HTML <head>에서 교체: -->
<!-- 제거: -->
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>

<!-- 추가: -->
<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>
```

### 2.3 ECharts 다크 테마 초기화

```javascript
// 기존 --bg: #0b0f1a 와 완벽히 매칭
const chart = echarts.init(document.getElementById('chartDiv'), 'dark');
chart.setOption({
    backgroundColor: '#0b0f1a',
    // ...
});

// 반응형 리사이즈 필수
window.addEventListener('resize', () => chart.resize());
```

### 2.4 에쿼티 커브 (interactive, zoomable)

```javascript
// Chart.js 대체 → ECharts 라인 차트
const option = {
    backgroundColor: '#0b0f1a',
    tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' },  // 크로스헤어 — 여러 볼트 동시 표시
    },
    legend: { textStyle: { color: '#7b8db0' } },
    dataZoom: [
        { type: 'slider', bottom: 10 },   // 줌 슬라이더
        { type: 'inside' }                 // 마우스 휠 줌
    ],
    xAxis: { type: 'category', data: dates, axisLabel: { color: '#7b8db0' } },
    yAxis: {
        type: 'value',
        axisLabel: {
            color: '#7b8db0',
            formatter: v => '$' + v.toLocaleString()  // 달러 포맷
        }
    },
    series: portfolioSeries.map(pf => ({
        name: pf.label,
        type: 'line',
        data: pf.values,
        smooth: true,
        symbol: 'none',  // 데이터 포인트 마커 제거 (성능)
        lineStyle: { width: 2 },
        areaStyle: { opacity: 0.1 }  // 면적 채우기 (선택)
    }))
};
```

### 2.5 포트폴리오 Bar Chart (APR/MDD/Sharpe 비교)

```javascript
const barOption = {
    backgroundColor: '#0b0f1a',
    tooltip: { trigger: 'axis' },
    legend: { textStyle: { color: '#7b8db0' } },
    xAxis: { type: 'category', data: vaultNames, axisLabel: { color: '#7b8db0', rotate: 30 } },
    yAxis: { type: 'value', axisLabel: { color: '#7b8db0' } },
    series: [
        { name: 'APR (%)', type: 'bar', data: aprValues },
        { name: 'MDD (%)', type: 'bar', data: mddValues },
        { name: 'Sharpe', type: 'bar', data: sharpeValues },
    ]
};
```

### 2.6 APR 분포 히스토그램 (메인 대시보드)

```javascript
// APR 분포 히스토그램 (메인 페이지 vault 목록 활용)
const histBuckets = [0, 10, 20, 30, 50, 100, 200];  // % 구간
const histOption = {
    backgroundColor: '#0b0f1a',
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: ['0-10%', '10-20%', '20-30%', '30-50%', '50-100%', '100%+'] },
    yAxis: { type: 'value', name: '볼트 수' },
    series: [{
        type: 'bar',
        data: bucketCounts,
        itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#4f8ef7' },
                { offset: 1, color: '#1abc9c' }
            ])
        }
    }]
};
```

### 2.7 `chart_data` Flask route 연결

**Flask 측 (Python)**:
```python
@app.route('/chart-data')
def chart_data():
    """ECharts 차트 데이터 API"""
    from portfolio_engine import get_portfolio_summary, load_portfolio_history
    history = load_portfolio_history()
    summary = get_portfolio_summary(history) if history else {}
    
    # value_series: [(date, value), ...]
    dates = [d for d, _ in summary.get('value_series', [])]
    values = [v for _, v in summary.get('value_series', [])]
    
    return jsonify({
        'dates': dates,
        'equity_values': values,
        'mdd_series': summary.get('mdd_series', []),
        'risk_series': summary.get('risk_series', []),
    })
```

### 2.8 Py Compile 검증

```python
# Task 4f — Python syntax 검증
import py_compile
try:
    py_compile.compile('web_dashboard.py', doraise=True)
    print("✅ 구문 오류 없음")
except py_compile.PyCompileError as e:
    print(f"❌ 구문 오류: {e}")
```

---

## 3. Task 5 — 리밸런싱 엔진 설계 연구

### 3.1 Architecture Overview

```
rebalance_engine.py
│
├── load_current_portfolio()    ← vault_data/my_portfolio.json
├── load_optimal_portfolio()    ← portfolio_engine.run_portfolio_analysis()
├── compare_portfolios()        ← 현재 vs 최적 차이 분석
├── detect_triggers()           ← APR 하락 / MDD 초과 / 30일 경과
├── build_rebalance_plan()      ← 구체적 USD 금액 + 실행 순서
├── send_d1_alerts()            ← scheduler.send_alert() 연동
└── save_plan()                 ← vault_data/rebalance_plan.json
```

### 3.2 리밸런싱 트리거 기준 (연구 결과)

| 트리거 | 기준 | 우선순위 |
|--------|------|----------|
| MDD 초과 | `max_drawdown > 20%` | 🔴 긴급 |
| APR 음수 | `apr_30d < 0` | 🔴 긴급 |
| 입금 불가 | `allow_deposits == False` | 🔴 긴급 |
| 비중 이탈 | 현재 vs 목표 차이 `> 10%` | 🟡 권고 |
| 30일 경과 | `days_since_last_rebalance >= 30` | 🟡 정기 |
| APR 30% 하락 | `current_apr < 0.7 * initial_apr` | 🟡 권고 |

### 3.3 출금 순서 최적화 (D-1 전략)

> **핵심**: Hyperliquid User Vault는 **출금 요청 후 1일(T+1) 후 실제 출금 가능**  
> → 오늘 출금 요청 → 내일 자금 도착 → 재배분 실행

**실행 순서**:
1. **D-1**: 비중 초과 볼트 출금 요청 (WITHDRAW 액션)
2. **D-0**: 출금된 자금으로 비중 부족 볼트 입금 (DEPOSIT 액션)

### 3.4 `rebalance_plan.json` 스키마

```json
{
  "generated_at": "2026-03-09T21:27:30+09:00",
  "trigger_date": "2026-03-09",
  "trigger_reasons": ["30일 정기 리밸런싱", "MDD 초과: AlphaVault (22.3%)"],
  "total_portfolio_usd": 50000.00,
  "current_portfolio": {
    "0xVaultA": { "invested_usd": 25000, "pct": 50.0, "apr_30d": 35.2, "mdd": 22.3 },
    "0xVaultB": { "invested_usd": 25000, "pct": 50.0, "apr_30d": 18.5, "mdd": 8.1 }
  },
  "optimal_portfolio": {
    "0xVaultC": { "target_pct": 40.0, "target_usd": 20000 },
    "0xVaultB": { "target_pct": 35.0, "target_usd": 17500 },
    "0xVaultD": { "target_pct": 25.0, "target_usd": 12500 }
  },
  "actions": [
    {
      "step": 1,
      "action": "WITHDRAW",
      "vault_address": "0xVaultA",
      "vault_name": "AlphaVault",
      "amount_usd": 25000.00,
      "reason": "MDD 초과 (22.3% > 20%) + 포트폴리오 미포함",
      "urgency": "🔴 긴급",
      "deadline": "오늘 출금 요청 필요 (T+1 지연)"
    },
    {
      "step": 2,
      "action": "WITHDRAW",
      "vault_address": "0xVaultB",
      "vault_name": "BetaVault",
      "amount_usd": 7500.00,
      "reason": "비중 50.0% → 35.0% 감소",
      "urgency": "🟡 권고",
      "deadline": "오늘 출금 요청 필요 (T+1 지연)"
    },
    {
      "step": 3,
      "action": "DEPOSIT",
      "vault_address": "0xVaultC",
      "vault_name": "GammaVault",
      "amount_usd": 20000.00,
      "reason": "신규 진입 (최적 포트폴리오 1위)",
      "urgency": "🟡 권고",
      "deadline": "출금 완료 후 즉시 실행"
    }
  ],
  "estimated_new_apr": 28.5,
  "estimated_new_mdd": 11.2,
  "net_transfers": {
    "total_withdraw_usd": 32500.00,
    "total_deposit_usd": 32500.00
  },
  "status": "PENDING"
}
```

### 3.5 scheduler.py 연동 인터페이스

```python
# rebalance_engine.py에서 scheduler.send_alert 연동 방법
import sys
sys.path.insert(0, str(Path(__file__).parent))
from scheduler import send_alert

# D-1 출금 알림
send_alert(
    "⚠️ 리밸런싱 D-1 출금 필요",
    f"오늘 출금 요청 필요:\n" + "\n".join(
        f"  - {a['vault_name']}: ${a['amount_usd']:,.0f} ({a['reason']})"
        for a in plan['actions'] if a['action'] == 'WITHDRAW'
    ),
    "WARNING"
)
```

### 3.6 portfolio_engine.py 활용 함수들

`rebalance_engine.py`에서 사용 가능한 기존 함수:

| 함수 | 위치 | 용도 |
|------|------|------|
| `run_portfolio_analysis()` | `portfolio_engine.py` | 최적 포트폴리오 생성 |
| `get_portfolio_summary()` | `portfolio_engine.py` | 현재 포트폴리오 이력 요약 |
| `load_portfolio_history()` | `portfolio_engine.py` | 일별 이력 로드 |
| `get_recommendations(vaults)` | `analyze_top_vaults.py` | 추천 볼트 + 비중 |
| `get_rebalancing_advice()` | `analyze_top_vaults.py` | ENTER/EXIT/INCREASE/DECREASE 액션 |
| `evaluate_portfolio()` | `scheduler.py` | 현재 포트폴리오 위험 평가 |
| `load_portfolio()` | `scheduler.py` | `my_portfolio.json` 로드 |
| `send_alert()` | `scheduler.py` | D-1 출금 알림 전송 |

---

## 4. Hyperliquid SDK API 참조

> 패키지: `hyperliquid-python-sdk >= 0.10.0` (이미 requirements.txt에 포함)

### 4.1 vault_usd_transfer — 볼트 입출금

```python
# hyperliquid/exchange.py → vault_usd_transfer()
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants

exchange = Exchange(wallet, constants.MAINNET_API_URL)

# ── 출금 (isDeposit=False) ──
result = exchange.vault_usd_transfer(
    vault_address="0xVaultAddress",
    is_deposit=False,         # False = 출금
    usd=int(amount * 1e6)    # USD → 6 decimals (e.g., $25000 → 25000000000)
)

# ── 입금 (isDeposit=True) ──
result = exchange.vault_usd_transfer(
    vault_address="0xVaultAddress",
    is_deposit=True,
    usd=int(amount * 1e6)
)
```

> ⚠️ **중요**: `usd` 파라미터는 **raw integer (6 decimals)**  
> → `$1.00 = 1_000_000`, `$25,000 = 25_000_000_000`

### 4.2 user_vault_equities — 사용자 볼트 에쿼티 조회

```python
# hyperliquid/info.py → user_vault_equities()
from hyperliquid.info import Info

info = Info(constants.MAINNET_API_URL, skip_ws=True)
equities = info.user_vault_equities(user_address)
# 반환값: [{ vaultAddress, equity, pnl, ... }, ...]
```

### 4.3 vaultDetails — 볼트 상세 정보 (이미 사용 중)

```python
# analyze_top_vaults.py에서 이미 사용 중
details = info_client.post("/info", {"type": "vaultDetails", "vaultAddress": addr})
# 반환: { allowDeposits, followers, leaderFraction, ... }
```

### 4.4 출금 제약사항

| 항목 | 내용 |
|------|------|
| **출금 딜레이** | T+1 (출금 요청 24시간 후 실제 수령) |
| **입금 즉시성** | 즉시 적용 |
| **최소 출금액** | 볼트별 상이 (일반적으로 없음) |
| **Private Key 필요** | `Exchange` 인스턴스 생성에 필요 |
| **D-1 전략 필수** | 리밸런싱 전날 출금 요청해야 당일 재배분 가능 |

### 4.5 Private Key 처리 (보안 가이드)

```python
# ✅ 권장: .env 파일에서 로드 (python-dotenv 사용 — 이미 requirements.txt에 있음)
from dotenv import load_dotenv
import os

load_dotenv()
private_key = os.getenv("HL_PRIVATE_KEY")  # .env 파일에 저장

# ✅ rebalance_engine.py에서 dry_run 모드 지원 필수
# → Private Key 없어도 계획(plan.json)만 생성 가능하게
def build_rebalance_plan(dry_run=True):
    """dry_run=True: 계획만 생성, 실제 거래 없음"""
    ...
```

---

## 5. 태스크별 구현 권고사항

### Task 4 (ECharts) 체크리스트

- [x] CDN URL: `https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js`
- [x] 초기화: `echarts.init(el, 'dark')` + `backgroundColor: '#0b0f1a'`
- [x] dataZoom: `[{type:'slider'}, {type:'inside'}]` → 줌/패닝
- [x] tooltip: `{trigger:'axis', axisPointer:{type:'cross'}}`
- [x] 리사이즈: `window.addEventListener('resize', () => chart.resize())`
- [x] `/chart-data` Flask route → `portfolio_engine.get_portfolio_summary()` 연결
- [x] `py_compile` 검증

### Task 5 (Rebalance Engine) 체크리스트

- [x] `my_portfolio.json` vs `portfolio_engine.run_portfolio_analysis()` 비교
- [x] 트리거 감지: MDD>20%, APR<0, 입금불가, 비중이탈>10%, 30일경과
- [x] 출금 계획: USD 금액 + D-1 마감시한
- [x] `scheduler.send_alert()` 연동
- [x] `rebalance_plan.json` 저장
- [x] `dry_run` 모드 지원 (Private Key 없이 계획만 생성)
- [x] `vault_usd_transfer(is_deposit=False, usd=int(amt*1e6))` API 문서화
- [x] T+1 출금 딜레이 고려한 D-1 알림 로직

---

*연구 완료: 2026-03-09T21:27:30+09:00*
