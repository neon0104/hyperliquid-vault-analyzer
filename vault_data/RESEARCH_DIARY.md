# 🧠 Hyperliquid Vault AI 자율 연구 및 지속 학습 일지 (Research Diary)

> 이 문서는 AI 퀀트 연구원이 매 시간 GitHub 오픈소스 퀀트 리서치, 수학적 모델, 온체인 시계열 데이터를 자율 학습하고 검증한 누적 연구 일지입니다.

---

## 📅 연구 기록: 2026-09-29 15:39:21
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-29)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `396739385.92` | Kelly `30.0%` | 30일 APR `11.28%` | Sharpe `9.59`
  - **Slow Stable**: Hurst `0.5` | Sortino `154.76` | Kelly `22.3%` | 30일 APR `24.79%` | Sharpe `8.08`
  - **Aaroh**: Hurst `0.5` | Sortino `29.37` | Kelly `20.8%` | 30일 APR `148.35%` | Sharpe `11.68`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `505.8%` | Sharpe `4.22`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-29 11:39:28
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-29)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `396739385.92` | Kelly `30.0%` | 30일 APR `11.28%` | Sharpe `9.59`
  - **Slow Stable**: Hurst `0.5` | Sortino `154.76` | Kelly `22.3%` | 30일 APR `24.79%` | Sharpe `8.08`
  - **Aaroh**: Hurst `0.5` | Sortino `29.37` | Kelly `20.8%` | 30일 APR `148.35%` | Sharpe `11.68`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `505.8%` | Sharpe `4.22`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-29 07:39:20
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-29)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `396739385.92` | Kelly `30.0%` | 30일 APR `11.28%` | Sharpe `9.59`
  - **Slow Stable**: Hurst `0.5` | Sortino `154.76` | Kelly `22.3%` | 30일 APR `24.79%` | Sharpe `8.08`
  - **Aaroh**: Hurst `0.5` | Sortino `29.37` | Kelly `20.8%` | 30일 APR `148.35%` | Sharpe `11.68`
  - **Probot 2/7/15**: Hurst `0.817` | Sortino `19.87` | Kelly `15.2%` | 30일 APR `456.1%` | Sharpe `3.79`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-29 03:41:57
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-29)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `396739385.92` | Kelly `30.0%` | 30일 APR `11.28%` | Sharpe `9.59`
  - **Slow Stable**: Hurst `0.5` | Sortino `154.76` | Kelly `22.3%` | 30일 APR `24.79%` | Sharpe `8.08`
  - **Aaroh**: Hurst `0.5` | Sortino `29.37` | Kelly `20.8%` | 30일 APR `148.35%` | Sharpe `11.68`
  - **Probot 2/7/15**: Hurst `0.817` | Sortino `19.87` | Kelly `15.2%` | 30일 APR `456.1%` | Sharpe `3.79`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-28 23:39:25
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-28)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `19.3` | Kelly `22.0%` | 30일 APR `11.23%` | Sharpe `5.92`
  - **Slow Stable**: Hurst `0.5` | Sortino `52.96` | Kelly `20.0%` | 30일 APR `56.42%` | Sharpe `8.08`
  - **Aaroh**: Hurst `0.5` | Sortino `30.31` | Kelly `17.9%` | 30일 APR `131.2%` | Sharpe `11.14`
  - **Lalo Capital**: Hurst `0.5` | Sortino `29.7` | Kelly `16.4%` | 30일 APR `129.49%` | Sharpe `8.18`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-28 19:39:23
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-28)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `19.3` | Kelly `22.0%` | 30일 APR `11.23%` | Sharpe `5.92`
  - **Slow Stable**: Hurst `0.5` | Sortino `52.96` | Kelly `20.0%` | 30일 APR `56.42%` | Sharpe `8.08`
  - **Aaroh**: Hurst `0.5` | Sortino `30.31` | Kelly `17.9%` | 30일 APR `131.2%` | Sharpe `11.14`
  - **Lalo Capital**: Hurst `0.5` | Sortino `29.7` | Kelly `16.4%` | 30일 APR `129.49%` | Sharpe `8.18`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-28 15:39:16
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-28)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `19.3` | Kelly `22.0%` | 30일 APR `11.23%` | Sharpe `5.92`
  - **Slow Stable**: Hurst `0.5` | Sortino `52.96` | Kelly `20.0%` | 30일 APR `56.42%` | Sharpe `8.08`
  - **Aaroh**: Hurst `0.5` | Sortino `30.31` | Kelly `17.9%` | 30일 APR `131.2%` | Sharpe `11.14`
  - **Lalo Capital**: Hurst `0.5` | Sortino `29.7` | Kelly `16.4%` | 30일 APR `129.49%` | Sharpe `8.18`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-28 11:39:23
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-28)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `19.3` | Kelly `22.0%` | 30일 APR `11.23%` | Sharpe `5.92`
  - **Slow Stable**: Hurst `0.5` | Sortino `52.96` | Kelly `20.0%` | 30일 APR `56.42%` | Sharpe `8.08`
  - **Aaroh**: Hurst `0.5` | Sortino `30.31` | Kelly `17.9%` | 30일 APR `131.2%` | Sharpe `11.14`
  - **Lalo Capital**: Hurst `0.5` | Sortino `29.7` | Kelly `16.4%` | 30일 APR `129.49%` | Sharpe `8.18`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-28 07:39:18
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-28)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `19.3` | Kelly `22.0%` | 30일 APR `11.23%` | Sharpe `5.92`
  - **Slow Stable**: Hurst `0.5` | Sortino `52.96` | Kelly `20.0%` | 30일 APR `56.42%` | Sharpe `8.08`
  - **Aaroh**: Hurst `0.5` | Sortino `30.31` | Kelly `17.9%` | 30일 APR `131.2%` | Sharpe `11.14`
  - **Lalo Capital**: Hurst `0.5` | Sortino `29.7` | Kelly `16.4%` | 30일 APR `129.49%` | Sharpe `8.18`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-28 03:42:08
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-28)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `19.3` | Kelly `22.0%` | 30일 APR `11.23%` | Sharpe `5.92`
  - **Slow Stable**: Hurst `0.5` | Sortino `52.96` | Kelly `20.0%` | 30일 APR `56.42%` | Sharpe `8.08`
  - **Aaroh**: Hurst `0.5` | Sortino `30.31` | Kelly `17.9%` | 30일 APR `131.2%` | Sharpe `11.14`
  - **Lalo Capital**: Hurst `0.5` | Sortino `29.7` | Kelly `16.4%` | 30일 APR `129.49%` | Sharpe `8.18`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-27 23:39:23
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-27)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `19.37` | Kelly `22.0%` | 30일 APR `11.41%` | Sharpe `5.92`
  - **Slow Stable**: Hurst `0.5` | Sortino `168.76` | Kelly `21.9%` | 30일 APR `40.9%` | Sharpe `8.56`
  - **Aaroh**: Hurst `0.5` | Sortino `29.28` | Kelly `20.8%` | 30일 APR `144.83%` | Sharpe `11.35`
  - **Lalo Capital**: Hurst `0.5` | Sortino `29.28` | Kelly `16.4%` | 30일 APR `228.07%` | Sharpe `8.61`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-27 19:39:22
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-27)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `19.37` | Kelly `22.0%` | 30일 APR `11.41%` | Sharpe `5.92`
  - **Slow Stable**: Hurst `0.5` | Sortino `168.76` | Kelly `21.9%` | 30일 APR `40.9%` | Sharpe `8.56`
  - **Aaroh**: Hurst `0.5` | Sortino `29.28` | Kelly `20.8%` | 30일 APR `144.83%` | Sharpe `11.35`
  - **Lalo Capital**: Hurst `0.5` | Sortino `29.28` | Kelly `16.4%` | 30일 APR `228.07%` | Sharpe `8.61`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-27 15:39:18
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-27)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `19.37` | Kelly `22.0%` | 30일 APR `11.41%` | Sharpe `5.92`
  - **Slow Stable**: Hurst `0.5` | Sortino `168.76` | Kelly `21.9%` | 30일 APR `40.9%` | Sharpe `8.56`
  - **Aaroh**: Hurst `0.5` | Sortino `29.28` | Kelly `20.8%` | 30일 APR `144.83%` | Sharpe `11.35`
  - **Lalo Capital**: Hurst `0.5` | Sortino `29.28` | Kelly `16.4%` | 30일 APR `228.07%` | Sharpe `8.61`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-27 11:39:25
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-27)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `19.37` | Kelly `22.0%` | 30일 APR `11.41%` | Sharpe `5.92`
  - **Slow Stable**: Hurst `0.5` | Sortino `168.76` | Kelly `21.9%` | 30일 APR `40.9%` | Sharpe `8.56`
  - **Aaroh**: Hurst `0.5` | Sortino `29.28` | Kelly `20.8%` | 30일 APR `144.83%` | Sharpe `11.35`
  - **Lalo Capital**: Hurst `0.5` | Sortino `29.28` | Kelly `16.4%` | 30일 APR `228.07%` | Sharpe `8.61`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-27 07:39:18
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-27)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `19.37` | Kelly `22.0%` | 30일 APR `11.41%` | Sharpe `5.92`
  - **Slow Stable**: Hurst `0.5` | Sortino `168.76` | Kelly `21.9%` | 30일 APR `40.9%` | Sharpe `8.56`
  - **Aaroh**: Hurst `0.5` | Sortino `29.28` | Kelly `20.8%` | 30일 APR `144.83%` | Sharpe `11.35`
  - **Lalo Capital**: Hurst `0.5` | Sortino `29.28` | Kelly `16.4%` | 30일 APR `228.07%` | Sharpe `8.61`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---
