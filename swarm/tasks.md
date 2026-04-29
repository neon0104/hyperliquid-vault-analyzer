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

## TASK 7 — 메인 대시보드 필터 컨트롤 개선 ✅ DONE
- **Agent**: Developer Agent UI
- **Output**: web_dashboard.py
- **Result**:
  - 기존 Select 박스 형태의 Leader Equity(%), Max MDD(%) 필터를 직접 숫자를 입력할 수 있는 Input 필드로 변경
  - TVL 금액 필터 추가 (특정 금액 이상만 보기)
  - JS 필터 로직 및 DOM dataset 업데이트 완료

---

## TASK 8 — 포트폴리오 분석 페이지 기능 통합 ✅ DONE
- **Agent**: Developer Agent API / UI
- **Output**: web_dashboard.py
- **Result**: 
  - 불필요한 `/backtest` 페이지 경로 및 상단 네비게이션 버튼 완전 삭제
  - 포트폴리오(Analysis) 페이지 상단에 **Custom Portfolio Builder** 섹션 신설
  - 분석된 전체 볼트 리스트 중 원하는 볼트를 직접 선택(Select)하고, 원하는 투자 비율(Weight/금액)과 날짜를 지정하여 수익 시뮬레이션을 돌려보는 커스텀 백테스트 연동 완료 (/api/simulate API 재활용)
  - 하단의 AI 추천 포트폴리오 기반(Time-Travel Simulator) 백테스트 유지 

---

## 실행 계획
- **NOW Round (병렬)**: Task 9 진행 중 (데이터 분석 및 최적 투자 전략 수립 방안 강구)
- **NEXT Round**: 보스(USER)의 추가 지시 대기

---

## TASK 9 — 데이터 분석 및 최적 투자 전략 수립 ✅ DONE
- **Manager**: 목표 정의 및 에이전트 할당
- **Research Agent**: `smart_scorer.py` 및 `portfolio_engine.py`의 핵심 분석 로직 추출 및 효율적 투자 방안 강구
- **Developer Agent**: 도출된 전략을 시스템 파이프라인과 연계 분석
- **QA Agent**: 전략의 코드 정합성 검증
- **Output**: `artifacts/investment_strategy_report.md`

---

## TASK 10 — 일일 자동화 파이프라인(Dual Sync) 정합성 검증 ✅ DONE
- **Manager**: 최근 수 주간 진행된 데이터 자동 수집 파이프라인(GitHub Actions + Local PC)의 안정성 검증 지시.
- **Research Agent**: `daily_update.yml`과 로컬의 `auto_run.bat` 스크립트 간의 양방향 동기화(Dual Execution) 구조 분석. 동시에 실행되거나 지연될 경우 GitHub Actions의 커밋과 로컬 PC의 커밋이 충돌(Git Conflict)할 가능성을 잠재적 치명적 버그로 진단.
- **Developer Agent**: 로컬 봇의 `auto_run.bat` 스크립트 수정. 최종 `git push` 직전에 `git pull --rebase origin main`을 강제 수행하도록 패치하여 분기 충돌 완벽 차단.
- **QA Agent**: `auto_run.bat` 수정 사항 검수 및 패치 정상 반영 확인.

---

## TASK 11 — 바벨 전략(Barbell Strategy) 추천 알고리즘 구현 ✅ DONE
- **Manager**: 포트폴리오의 50%를 Robust(극단적 안정) 그룹에, 나머지 50%를 MDD 회복탄력성(Satellite) 그룹에 할당하는 바벨 전략 지시.
- **Research Agent**: `smart_scorer.py`의 `undervalue_score`와 `analyze_top_vaults.py`의 필터 로직 매핑. "회복탄력성"을 "장기 평균 수익률 대비 현재 슬럼프이나, 최근 30일 수익이 +로 전환된 상태(APR>0)"로 정의.
- **Developer Agent**: `analyze_top_vaults.py` 내 `get_recommendations()` 함수를 수정하여 CORE 그룹(Robustness 50%)과 SATELLITE 그룹(Undervalue 50%)으로 분리 분배 로직 적용.
- **QA Agent**: 포트폴리오 가중치 총합 100% 검증 및 터미널 출력 결과(`print_summary`)가 바벨 포맷으로 정상 렌더링되는지 확인.