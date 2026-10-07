# 🧠 Hyperliquid Vault AI 자율 연구 및 지속 학습 일지 (Research Diary)

> 이 문서는 AI 퀀트 연구원이 매 시간 GitHub 오픈소스 퀀트 리서치, 수학적 모델, 온체인 시계열 데이터를 자율 학습하고 검증한 누적 연구 일지입니다.

---

## 📅 연구 기록: 2026-10-07 19:39:27
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-07)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `391752420.63` | Kelly `26.8%` | 30일 APR `10.19%` | Sharpe `9.55`
  - **Slow Stable**: Hurst `0.5` | Sortino `317091428.8` | Kelly `25.7%` | 30일 APR `38.42%` | Sharpe `8.25`
  - **wmm.club | scalp-hype-long-2x**: Hurst `0.5` | Sortino `32.87` | Kelly `15.0%` | 30일 APR `37.73%` | Sharpe `7.14`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `411.4%` | Sharpe `3.88`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-07 15:39:39
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-07)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `391752420.63` | Kelly `26.8%` | 30일 APR `10.19%` | Sharpe `9.55`
  - **Slow Stable**: Hurst `0.5` | Sortino `317091428.8` | Kelly `25.7%` | 30일 APR `38.42%` | Sharpe `8.25`
  - **wmm.club | scalp-hype-long-2x**: Hurst `0.5` | Sortino `32.87` | Kelly `15.0%` | 30일 APR `37.73%` | Sharpe `7.14`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `411.4%` | Sharpe `3.88`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-07 11:39:21
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-07)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `391752420.63` | Kelly `26.8%` | 30일 APR `10.19%` | Sharpe `9.55`
  - **Slow Stable**: Hurst `0.5` | Sortino `317091428.8` | Kelly `25.7%` | 30일 APR `38.42%` | Sharpe `8.25`
  - **wmm.club | scalp-hype-long-2x**: Hurst `0.5` | Sortino `32.87` | Kelly `15.0%` | 30일 APR `37.73%` | Sharpe `7.14`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `411.4%` | Sharpe `3.88`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-07 07:39:21
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-07)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `391752420.63` | Kelly `26.8%` | 30일 APR `10.19%` | Sharpe `9.55`
  - **Slow Stable**: Hurst `0.5` | Sortino `317091428.8` | Kelly `25.7%` | 30일 APR `38.42%` | Sharpe `8.25`
  - **wmm.club | scalp-hype-long-2x**: Hurst `0.5` | Sortino `32.87` | Kelly `15.0%` | 30일 APR `37.73%` | Sharpe `7.14`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `411.4%` | Sharpe `3.88`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-07 03:41:57
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-07)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `391752420.63` | Kelly `26.8%` | 30일 APR `10.19%` | Sharpe `9.55`
  - **Slow Stable**: Hurst `0.5` | Sortino `317091428.8` | Kelly `25.7%` | 30일 APR `38.42%` | Sharpe `8.25`
  - **wmm.club | scalp-hype-long-2x**: Hurst `0.5` | Sortino `32.87` | Kelly `15.0%` | 30일 APR `37.73%` | Sharpe `7.14`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `411.4%` | Sharpe `3.88`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-06 23:39:25
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-06)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `397476948.32` | Kelly `26.8%` | 30일 APR `10.39%` | Sharpe `9.55`
  - **Slow Stable**: Hurst `0.5` | Sortino `317129621.78` | Kelly `25.7%` | 30일 APR `36.71%` | Sharpe `8.25`
  - **wmm.club | scalp-hype-long-2x**: Hurst `0.5` | Sortino `33.13` | Kelly `15.0%` | 30일 APR `41.89%` | Sharpe `7.19`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `503.12%` | Sharpe `4.14`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-06 19:39:24
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-06)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `397476948.32` | Kelly `26.8%` | 30일 APR `10.39%` | Sharpe `9.55`
  - **Slow Stable**: Hurst `0.5` | Sortino `317129621.78` | Kelly `25.7%` | 30일 APR `36.71%` | Sharpe `8.25`
  - **wmm.club | scalp-hype-long-2x**: Hurst `0.5` | Sortino `33.13` | Kelly `15.0%` | 30일 APR `41.89%` | Sharpe `7.19`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `503.12%` | Sharpe `4.14`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-06 15:39:21
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-06)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `397476948.32` | Kelly `26.8%` | 30일 APR `10.39%` | Sharpe `9.55`
  - **Slow Stable**: Hurst `0.5` | Sortino `317129621.78` | Kelly `25.7%` | 30일 APR `36.71%` | Sharpe `8.25`
  - **wmm.club | scalp-hype-long-2x**: Hurst `0.5` | Sortino `33.13` | Kelly `15.0%` | 30일 APR `41.89%` | Sharpe `7.19`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `503.12%` | Sharpe `4.14`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-06 11:39:24
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-06)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `397476948.32` | Kelly `26.8%` | 30일 APR `10.39%` | Sharpe `9.55`
  - **Slow Stable**: Hurst `0.5` | Sortino `317129621.78` | Kelly `25.7%` | 30일 APR `36.71%` | Sharpe `8.25`
  - **wmm.club | scalp-hype-long-2x**: Hurst `0.5` | Sortino `33.13` | Kelly `15.0%` | 30일 APR `41.89%` | Sharpe `7.19`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `503.12%` | Sharpe `4.14`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-06 07:39:19
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-06)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `397476948.32` | Kelly `26.8%` | 30일 APR `10.39%` | Sharpe `9.55`
  - **Slow Stable**: Hurst `0.5` | Sortino `317129621.78` | Kelly `25.7%` | 30일 APR `36.71%` | Sharpe `8.25`
  - **wmm.club | scalp-hype-long-2x**: Hurst `0.5` | Sortino `33.13` | Kelly `15.0%` | 30일 APR `41.89%` | Sharpe `7.19`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `503.12%` | Sharpe `4.14`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-06 03:42:05
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-06)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `397476948.32` | Kelly `26.8%` | 30일 APR `10.39%` | Sharpe `9.55`
  - **Slow Stable**: Hurst `0.5` | Sortino `317129621.78` | Kelly `25.7%` | 30일 APR `36.71%` | Sharpe `8.25`
  - **wmm.club | scalp-hype-long-2x**: Hurst `0.5` | Sortino `33.13` | Kelly `15.0%` | 30일 APR `41.89%` | Sharpe `7.19`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `503.12%` | Sharpe `4.14`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-05 23:39:27
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-05)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `397342036.39` | Kelly `26.8%` | 30일 APR `11.15%` | Sharpe `9.55`
  - **Slow Stable**: Hurst `0.5` | Sortino `317089109.67` | Kelly `25.7%` | 30일 APR `65.06%` | Sharpe `8.25`
  - **Queen [Bee]**: Hurst `0.5` | Sortino `101.62` | Kelly `16.4%` | 30일 APR `24.96%` | Sharpe `5.7`
  - **wmm.club | scalp-hype-long-2x**: Hurst `0.5` | Sortino `32.36` | Kelly `14.9%` | 30일 APR `32.88%` | Sharpe `7.02`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-05 19:39:25
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-05)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `397342036.39` | Kelly `26.8%` | 30일 APR `11.15%` | Sharpe `9.55`
  - **Slow Stable**: Hurst `0.5` | Sortino `317089109.67` | Kelly `25.7%` | 30일 APR `65.06%` | Sharpe `8.25`
  - **Queen [Bee]**: Hurst `0.5` | Sortino `101.62` | Kelly `16.4%` | 30일 APR `24.96%` | Sharpe `5.7`
  - **wmm.club | scalp-hype-long-2x**: Hurst `0.5` | Sortino `32.36` | Kelly `14.9%` | 30일 APR `32.88%` | Sharpe `7.02`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-05 15:39:21
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-05)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `397342036.39` | Kelly `26.8%` | 30일 APR `11.15%` | Sharpe `9.55`
  - **Slow Stable**: Hurst `0.5` | Sortino `317089109.67` | Kelly `25.7%` | 30일 APR `65.06%` | Sharpe `8.25`
  - **Queen [Bee]**: Hurst `0.5` | Sortino `101.62` | Kelly `16.4%` | 30일 APR `24.96%` | Sharpe `5.7`
  - **wmm.club | scalp-hype-long-2x**: Hurst `0.5` | Sortino `32.36` | Kelly `14.9%` | 30일 APR `32.88%` | Sharpe `7.02`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-05 11:39:25
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-05)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `397342036.39` | Kelly `26.8%` | 30일 APR `11.15%` | Sharpe `9.55`
  - **Slow Stable**: Hurst `0.5` | Sortino `317089109.67` | Kelly `25.7%` | 30일 APR `65.06%` | Sharpe `8.25`
  - **Queen [Bee]**: Hurst `0.5` | Sortino `101.62` | Kelly `16.4%` | 30일 APR `24.96%` | Sharpe `5.7`
  - **wmm.club | scalp-hype-long-2x**: Hurst `0.5` | Sortino `32.36` | Kelly `14.9%` | 30일 APR `32.88%` | Sharpe `7.02`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---
