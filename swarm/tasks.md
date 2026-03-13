# 🐝 Swarm Task Board — Hyperliquid Portfolio Manager
**Manager**: AI Swarm Manager
**Updated**: 2026-03-09T21:25:11+09:00
**Goal**: 자본보존 우선 자동 포트폴리오 관리 시스템

---

## 📊 현재 상태 요약

| 시스템 구성요소 | 상태 |
|---|---|
| Risk Filter 기준 (MDD≤20, APR>0, 운영≥90일) | ✅ 확립 완료 |
| scheduler.py (매일 09:00, 긴급중단 감지) | ✅ 완료 |
| web_dashboard.py (모바일 반응형, API, 긴급중단 버튼) | ✅ 완료 |
| ECharts 차트 업그레이드 (equity curve, bar chart) | 🔄 IN PROGRESS |
| rebalance_engine.py (30일 리밸런싱) | ⏳ NEXT |
| QA + 통합 테스트 | ⏳ WAITING |

---

## TASK 1 — 리스크 필터 강화 ✅ DONE
- **Agent**: Research Agent
- **Output**: swarm/research.md
- **Result**: MDD≤20%, 리더에쿼티≥40%, APR>0%, 운영≥90일, 입금가능 기준 확립

---

## TASK 2 — 자동 스케줄러 ✅ DONE
- **Agent**: Developer Agent A
- **Output**: scheduler.py
- **Result**: 매일 09:00 자동 분석, D-1 알림, emergency_stop.flag 감지, status.json 기록

---

## TASK 3 — 모바일 대시보드 ✅ DONE
- **Agent**: Developer Agent B
- **Output**: web_dashboard.py 업그레이드
- **Result**: /portfolio-status, /api/status, /emergency-stop, 30초 자동갱신

---

## TASK 4 — ECharts 차트 업그레이드 ✅ DONE
- **Agent**: Developer Agent (ECharts)
- **Output**: web_dashboard.py (수정)
- **Priority**: HIGH
- **담당 파일**: agents/tasks.md → Task 2
- **Sub-tasks**:
  - [x] 4a. ECharts CDN → 메인 HTML + PORTFOLIO_HTML `<head>` 추가
  - [x] 4b. Equity curve → ECharts 4전략 line chart + dataZoom 줌/팬
  - [x] 4c. Portfolio stats bar chart (APR/MDD/Sharpe×10 그룹 bar)
  - [x] 4d. APR distribution chart → 메인 대시보드 (#apr-dist-chart)
  - [x] 4e. `/chart_data` Flask API route 구현 (line 1144~1188)
  - [x] 4f. Python syntax 검증 → **OK** (Python 3.12)
- **Notes**: agents/research.md 에 ECharts 통합 가이드 있음

---

## TASK 5 — 30일 리밸런싱 엔진 ✅ DONE
- **Agent**: Developer Agent A
- **Output**: rebalance_engine.py (신규 파일)
- **Depends on**: Task 1 ✅
- **기능**:
  - 현재 포트폴리오 vs 최적 포트폴리오 비교 (portfolio_engine.py 활용)
  - 리밸런싱 필요 볼트 계산 (APR 하락, MDD 초과 감지)
  - 출금→재배분 실행 계획 생성 (구체적 USD 금액)
  - D-1 출금 알림 통합 (scheduler.py send_alert 연동)
  - JSON 리포트 저장: vault_data/rebalance_plan.json

---

## TASK 6 — QA + 통합 테스트 ✅ DONE (Syntax + API)
- **QA 결과**: API 테스트 PASS | 브라우저 Visual 대기
- **Agent**: QA Agent
- **Output**: swarm/progress.md 업데이트
- **Depends on**: Task 4 + Task 5
- **Test Coverage**:
  - [x] 6a. web_dashboard.py 구문 오류 없음 → **OK** (py_compile Python 3.12)
  - [x] 6b. 서버 기동 확인 → **OK** http://localhost:5000 정상 가동
  - [x] 6c. rebalance_engine.py --dry-run 실행 → **OK** (스냅샷 없음 메시지 정상)
  - [x] 6d. `/api/status` JSON 응답 → **OK** (emergency_stopped, holdings 등 확인)
  - [x] 6e. `/chart_data` JSON 응답 → **OK** (APR 히스토그램 + bar_data 16개 볼트)
  - [x] 6f. 메인 `/` 페이지 렌더링 → **OK** (시장 현황, 사비, 차트 div 확인)
  - [x] 6g. 브라우저 ECharts 실제 렌더링 (Visual QA 완료)

---

## 의존성 그래프
```
Task 1 ✅ ──────────────────────────→ Task 5
Task 2 ✅ ──┐
             ├──→ Task 4 ──→ Task 6
Task 3 ✅ ──┘
```

## 실행 계획
- **NOW Round (병렬)**: Task 4 (ECharts) + Task 5 (Rebalance Engine)
- **NEXT Round**: Task 6 (QA — Task 4+5 완료 후)