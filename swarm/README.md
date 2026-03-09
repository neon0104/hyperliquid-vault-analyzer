# 🐝 AI Swarm Coordination Guide

## 필수 Manager System Prompt

```
You are the manager of an AI engineering swarm.

Responsibilities:
- break user requests into tasks
- write tasks into /swarm/tasks.md
- assign tasks to appropriate agents
- coordinate work between agents
- review results

Workflow:
1. analyze user request
2. create task list in /swarm/tasks.md
3. delegate tasks to specialized agents
4. collect results in /swarm/progress.md

Always coordinate work using the /swarm folder.
Agents must read and update shared files.

Never implement everything yourself.
Use swarm agents whenever possible.
```

> ⚠️ **핵심**: 마지막 두 줄 없으면 Agent가 혼자 다 해버림
> - `Always coordinate work using the /swarm folder.`
> - `Agents must read and update shared files.`

---

## 폴더 구조

```
project/
│
├── src/
├── backend/
├── frontend/
│
└── swarm/
    ├── README.md      ← 이 파일 (swarm 사용법)
    ├── tasks.md       ← Manager가 작성 (태스크 목록 + 담당 에이전트)
    ├── progress.md    ← Developer/QA가 업데이트 (진행 현황)
    ├── research.md    ← Research Agent가 업데이트 (조사 결과)
    └── decisions.md   ← Developer Agent가 업데이트 (설계 결정)
```

---

## 각 파일의 역할

| 파일 | 작성자 | 목적 |
|------|--------|------|
| `tasks.md` | **Manager** | 태스크 분해, 담당자 지정, 의존성 정의 |
| `progress.md` | **Developer + QA** | 진행 체크리스트, 완료 결과 기록 |
| `research.md` | **Research Agent** | 라이브러리/기술 조사 결과 |
| `decisions.md` | **Developer Agent** | 기술 선택 근거, 스키마, 아키텍처 |

---

## Parallel Workflow (병렬 실행)

```
Manager (tasks.md 작성)
    │
    ├──→ Research Agent  → research.md   ─┐
    │                                      ├ 동시 실행 (Round 1)
    ├──→ Developer Agent → decisions.md  ─┘
    │
    └──→ (Round 1 완료 후)
            ├──→ Developer Agent → progress.md (구현)
            └──→ QA Agent        → progress.md (테스트)
```

### Round 1: 독립 태스크 → 병렬 실행
### Round 2: 의존 태스크 → 순차 실행

---

## 에이전트 유형 가이드

| Agent | 역할 | 읽는 파일 | 쓰는 파일 |
|-------|------|-----------|-----------|
| **Manager** | 조율 | progress.md | tasks.md |
| **Research Agent** | 기술 조사 | tasks.md | research.md |
| **Developer Agent** | 구현 | tasks.md, research.md, decisions.md | progress.md, decisions.md |
| **QA Agent** | 테스트 | tasks.md, progress.md | progress.md |

---

## ✅ Swarm이 잘 작동하는 조건

1. Manager Prompt에 `/swarm` 폴더 참조 명시
2. 각 Agent에게 "어떤 파일을 읽고 쓸지" 명확히 지시
3. 태스크 간 의존성을 `tasks.md`에 명시
4. 병렬 가능한 태스크와 순차 필요 태스크를 구분
