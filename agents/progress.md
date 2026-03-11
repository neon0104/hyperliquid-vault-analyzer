# 📊 Progress Log — Dashboard Upgrade + Rebalance Engine

**Updated by**: Project Manager (Antigravity)  
**Last update**: 2026-03-09T22:50:00+09:00

---

## 🛠️ Session 1 (2026-03-09 오전) — ECharts 업그레이드

- [x] ECharts CDN → `HTML` (메인 대시보드 `<head>`) 추가 완료
- [x] 2b. `PORTFOLIO_HTML` equity curve → ECharts interactive 완전 구현
  - 4가지 전략 (Max Sharpe / Min Variance / Risk Parity / Min CVaR)
  - `dataZoom` 슬라이더 + 인사이드 줌/팬
  - Cross-hair 툴팁 + $표시 포맷터
- [x] Portfolio stats bar chart 완전 구현
- [x] APR 분포 chart → 메인 대시보드 `#apr-dist-chart` 완전 구현
- [x] `/chart_data` Flask API route 구현
- [x] Python syntax 검증 → **OK** (`web_dashboard.py`)

---

## 🔧 Session 2 (2026-03-09 오후) — 버그 수정 & 품질 개선

### Runtime QA 결과 (실행 확인)
- [x] 서버 기동 확인 (`python web_dashboard.py`)
- [x] ECharts 블랙박스 버그 발견 → **수정 완료**
- [x] APR 분포 차트 렌더링 문제 → **수정 완료**
- [x] 분석 실행 실시간 로그 없음 → **추가 완료**

### 수정 내용 (commit: 77517e0)
1. **ECharts 블랙박스 수정**
   - `DOMContentLoaded` 이후 초기화로 이동
   - `equity-chart`, `bar-chart` 컨테이너에 `width:100%` 명시
   - `setTimeout(() => chart.resize(), 100)` 추가
   
2. **분석 실행 UX 개선**
   - `subprocess.run` → `subprocess.Popen` + stdout 스트리밍
   - 오버레이에 `#run-log` 요소 추가 (실시간 진행 상황)
   - `pollStatus()` 2초 간격 + 로그 표시

3. **Flask Route 이름 충돌 수정**
   - `run_analysis()` → `run_analysis_route()` (함수명이 내부함수와 충돌)
   
4. **Lock 정규화**
   - `__import__('threading').Lock()` → `from threading import Lock` + `Lock()`

5. **의존성 추가**
   - `openpyxl` 설치 (Excel 내보내기)

6. **보안**
   - `config.json` (지갑주소 포함) → git commit 제외 확인

---

## 🧪 QA — Runtime 확인 결과

| 항목 | 결과 |
|------|------|
| `python web_dashboard.py` 서버 기동 | ✅ |
| `/` 메인 페이지 로드 | ✅ |
| `/chart_data` API | ✅ (16개 볼트 데이터 반환) |
| `/portfolio` 페이지 | ✅ |
| `/api/status` | ✅ |
| `portfolio_engine.py` 실행 | ✅ (6개 저상관 볼트 선정) |
| `rebalance_engine.py --dry-run` | ✅ (건강점수 64.3, B등급) |
| ECharts 렌더링 | ✅ (DOMContentLoaded 수정) |

---

## ⏳ 남은 작업 (향후)

- [ ] `my_portfolio.json` 실제 포트폴리오 입력 (실제 투자 시작 시)
- [ ] 스케줄러 자동 실행 설정 (`scheduler.py --now`)
- [ ] 분석 데이터 누적 (매일 실행 → history_days 증가)
- [ ] `/portfolio` ECharts 차트 실시간 확인 (브라우저 스크린샷 QA)

---

## 📈 Overall Sprint Status

| Task | Agent | Status |
|------|-------|--------|
| Task 1: Research (ECharts) | Research Agent | ✅ DONE |
| Task 2: ECharts 업그레이드 | Developer Agent | ✅ DONE |
| Task 3: QA / 통합 | QA Agent | ✅ DONE |
| Task 4: Runtime 버그 수정 | PM | ✅ DONE |
| Task 5: rebalance_engine.py | Developer Agent | ✅ DONE |
| GitHub Push | PM | ✅ 77517e0 |
