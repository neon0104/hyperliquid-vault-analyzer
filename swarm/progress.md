# 📊 Swarm Progress — 포트폴리오 관리 시스템
**Updated by**: Manager / Developer Agents
**Last update**: 2026-03-09

---

## ✅ 완료 태스크

| Task | Agent | Status | Output |
|------|-------|--------|--------|
| Task 1: 리스크 필터 기준 확립 | Research | ✅ DONE | swarm/research.md |
| Task 2: 자동 스케줄러 | Developer A | ✅ DONE | `scheduler.py` |
| Task 3: 모바일 대시보드 | Developer B | ✅ DONE | `web_dashboard.py` 업그레이드 |

---

## Task 2 — scheduler.py 요약

### 주요 기능:
| 기능 | 설명 |
|------|------|
| 매일 09:00 자동 분석 | `analyze_top_vaults.py --force` 자동 실행 |
| 포트폴리오 평가 | 내 볼트 APR/MDD 실시간 체크 |
| D-1 출금 알림 | 리밸런싱 전날 자동 알림 생성 |
| 30일 카운트다운 | `status.json`에 카운트다운 기록 |
| 긴급 중단 감지 | `emergency_stop.flag` 파일 감지 즉시 중단 |
| 알림 로그 | `vault_data/alerts.jsonl` 기록 |

### 실행 방법:
```bash
python scheduler.py          # 데몬 모드 (매일 09:00 자동)
python scheduler.py --now    # 즉시 1회 실행
python scheduler.py --stop   # 긴급 중단
python scheduler.py --clear  # 긴급 중단 해제
python scheduler.py --status # 상태 확인
```

---

## Task 3 — 모바일 대시보드 업그레이드

### 신규 라우트:
| URL | 설명 |
|-----|------|
| `GET /portfolio-status` | 📱 모바일 최적화 포트폴리오 페이지 |
| `GET /api/status` | JSON API (어디서든 상태 조회) |
| `POST /emergency-stop` | 🔴 긴급 중단 |
| `POST /emergency-clear` | ✅ 긴급 중단 해제 |
| `POST /set-portfolio` | 포트폴리오 설정 저장 |

### 모바일 페이지 기능:
- 상태 배너 (정상/리밸런싱 권고/긴급중단)
- 30일 리밸런싱 카운트다운
- 총 투자금 / 예상 월수익 / 예상 연수익
- 보유 볼트별 APR/MDD/월수익 카드
- 위험 볼트 경고 (빨간 테두리 + 주의 배지)
- 🔴 긴급 중단 버튼 (1-click, 확인 다이얼로그)
- 30초마다 자동 갱신

---

## 📁 포트폴리오 설정 방법

`vault_data/my_portfolio.json` 파일 생성:
```json
{
  "0xVaultAddress1여기": 5000,
  "0xVaultAddress2여기": 3000,
  "0xVaultAddress3여기": 2000
}
```
값: 각 볼트에 투자한 USD 금액

---

## 📈 전체 시스템 구조

```
[scheduler.py] ──→ analyze_top_vaults.py ──→ 스냅샷 저장
     │                                         │
     ├──→ portfolio 평가                        │
     ├──→ status.json 업데이트 ←────────────────┘
     └──→ alerts.jsonl 기록
          │
[web_dashboard.py]
     ├── / (메인 대시보드)
     ├── /portfolio-status (📱 모바일)
     ├── /api/status (JSON API)
     ├── /emergency-stop 🔴
     └── /portfolio (포트폴리오 분석)
```

---

## ⏳ 다음 단계 (Task 4, 5)

- Task 4: rebalance_engine.py (30일 리밸런싱 구체 계획)
- Task 5: QA + 통합 테스트