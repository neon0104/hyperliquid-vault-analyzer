# 🐝 Swarm Task Board — Hyperliquid Portfolio Manager
**Manager**: AI Swarm Manager
**Updated**: 2026-03-09
**Goal**: 자본보존 우선 자동 포트폴리오 관리 시스템

---

## 🎯 시스템 목표
- 투자금 (얼마든) → 최적 볼트 자동 분산
- 원금 절대 보존 (MDD 제한)
- 매일 모니터링 → 30일 단위 리밸런싱 권고
- 출금 1일 소요 → D-1 선제 알림
- 모바일 접근 + 긴급 중단 기능

---

## TASK 1 — 리스크 필터 강화 (Research Agent)
- **Status**: 🔄 IN PROGRESS
- **Agent**: Research Agent
- **Output**: swarm/research.md
- **목적**: 원금보존을 위한 볼트 선별 기준 확립
- **기준**:
  - MDD ≤ 20% (원금보존 최우선)
  - 리더 에쿼티 ≥ 40%
  - 30일 APR > 0%
  - 운영기간 ≥ 90일
  - 입금가능 상태
  - 볼트 생성 ≥ 3개월 (검증된 볼트만)

## TASK 2 — 자동 스케줄러 구축 (Developer Agent A)
- **Status**: 🔄 IN PROGRESS
- **Agent**: Developer Agent
- **Output**: scheduler.py
- **기능**:
  - 매일 오전 9시 자동 분석 실행
  - 볼트 상태 스냅샷 저장
  - 리밸런싱 필요 여부 감지
  - D-1 출금 알림 (리밸런싱 예정 하루 전)
  - 긴급중단 플래그 파일 감지 (emergency_stop.flag)

## TASK 3 — 모바일 대시보드 (Developer Agent B)
- **Status**: 🔄 IN PROGRESS (Task 2와 병렬)
- **Agent**: Developer Agent
- **Output**: web_dashboard.py 업그레이드
- **기능**:
  - 모바일 반응형 UI
  - 현재 포트폴리오 상태 실시간 표시
  - 수익/손실 현황 (총자산, 수익률)
  - 30일 리밸런싱 카운트다운
  - 🔴 긴급중단 버튼 (1-click)
  - 출금 타이밍 가이드 표시

## TASK 4 — 30일 리밸런싱 엔진 (Developer Agent A)
- **Status**: ⏳ WAITING (Task 1 완료 후)
- **Agent**: Developer Agent
- **Output**: rebalance_engine.py
- **기능**:
  - 현재 포트폴리오 vs 최적 포트폴리오 비교
  - 리밸런싱 필요 볼트 계산
  - 출금→재배분 실행 계획 생성
  - 구체적 액션 플랜 (어느 볼트에서 얼마 빼서 어디로)

## TASK 5 — QA + 통합 테스트 (QA Agent)
- **Status**: ⏳ WAITING (Task 2,3,4 완료 후)
- **Agent**: QA Agent
- **Output**: swarm/progress.md

---

## 의존성 그래프
```
Task 1 (Risk Filter) ──→ Task 4 (Rebalance Engine)
Task 2 (Scheduler)   ──┐
                        ├──→ Task 5 (QA)
Task 3 (Dashboard)   ──┘
```

## Round 실행 계획
- Round 1 (병렬): Task 1 + Task 2 + Task 3
- Round 2 (순차): Task 4 → Task 5