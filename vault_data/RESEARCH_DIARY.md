# 🧠 Hyperliquid Vault AI 자율 연구 및 지속 학습 일지 (Research Diary)

> 이 문서는 AI 퀀트 연구원이 매 시간 GitHub 오픈소스 퀀트 리서치, 수학적 모델, 온체인 시계열 데이터를 자율 학습하고 검증한 누적 연구 일지입니다.

---

## 📅 연구 기록: 2026-10-10 15:39:27
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-10)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `399053123.47` | Kelly `30.0%` | 30일 APR `11.4%` | Sharpe `9.61`
  - **Slow Stable**: Hurst `0.5` | Sortino `48.8` | Kelly `20.9%` | 30일 APR `1.68%` | Sharpe `8.23`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `312.87%` | Sharpe `3.55`
  - **Gucky_4coin_2dot5x**: Hurst `0.397` | Sortino `77.71` | Kelly `13.6%` | 30일 APR `33.81%` | Sharpe `0.88`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-10 11:39:29
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-10)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `399053123.47` | Kelly `30.0%` | 30일 APR `11.4%` | Sharpe `9.61`
  - **Slow Stable**: Hurst `0.5` | Sortino `48.8` | Kelly `20.9%` | 30일 APR `1.68%` | Sharpe `8.23`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `312.87%` | Sharpe `3.55`
  - **Gucky_4coin_2dot5x**: Hurst `0.397` | Sortino `77.71` | Kelly `13.6%` | 30일 APR `33.81%` | Sharpe `0.88`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-10 07:39:22
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-10)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `399053123.47` | Kelly `30.0%` | 30일 APR `11.4%` | Sharpe `9.61`
  - **Slow Stable**: Hurst `0.5` | Sortino `48.8` | Kelly `20.9%` | 30일 APR `1.68%` | Sharpe `8.23`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `312.87%` | Sharpe `3.55`
  - **Gucky_4coin_2dot5x**: Hurst `0.396` | Sortino `74.32` | Kelly `13.9%` | 30일 APR `33.81%` | Sharpe `0.88`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-10 03:41:58
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-10)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `399053123.47` | Kelly `30.0%` | 30일 APR `11.4%` | Sharpe `9.61`
  - **Slow Stable**: Hurst `0.5` | Sortino `48.8` | Kelly `20.9%` | 30일 APR `1.68%` | Sharpe `8.23`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `312.87%` | Sharpe `3.55`
  - **Gucky_4coin_2dot5x**: Hurst `0.396` | Sortino `74.32` | Kelly `13.9%` | 30일 APR `33.81%` | Sharpe `0.88`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-09 23:39:30
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-09)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `392435092.87` | Kelly `26.6%` | 30일 APR `6.22%` | Sharpe `9.37`
  - **Slow Stable**: Hurst `0.5` | Sortino `50.46` | Kelly `20.8%` | 30일 APR `24.79%` | Sharpe `8.18`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `296.98%` | Sharpe `3.53`
  - **Gucky_4coin_2dot5x**: Hurst `0.396` | Sortino `74.32` | Kelly `13.9%` | 30일 APR `13.1%` | Sharpe `0.63`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-09 19:39:26
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-09)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `392435092.87` | Kelly `26.6%` | 30일 APR `6.22%` | Sharpe `9.37`
  - **Slow Stable**: Hurst `0.5` | Sortino `50.46` | Kelly `20.8%` | 30일 APR `24.79%` | Sharpe `8.18`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `296.98%` | Sharpe `3.53`
  - **Gucky_4coin_2dot5x**: Hurst `0.396` | Sortino `74.32` | Kelly `13.9%` | 30일 APR `13.1%` | Sharpe `0.63`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-09 15:39:20
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-09)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `392435092.87` | Kelly `26.6%` | 30일 APR `6.22%` | Sharpe `9.37`
  - **Slow Stable**: Hurst `0.5` | Sortino `50.46` | Kelly `20.8%` | 30일 APR `24.79%` | Sharpe `8.18`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `296.98%` | Sharpe `3.53`
  - **Gucky_4coin_2dot5x**: Hurst `0.396` | Sortino `74.32` | Kelly `13.9%` | 30일 APR `13.1%` | Sharpe `0.63`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-09 11:39:27
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-09)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `392435092.87` | Kelly `26.6%` | 30일 APR `6.22%` | Sharpe `9.37`
  - **Slow Stable**: Hurst `0.5` | Sortino `50.46` | Kelly `20.8%` | 30일 APR `24.79%` | Sharpe `8.18`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `296.98%` | Sharpe `3.53`
  - **Gucky_4coin_2dot5x**: Hurst `0.396` | Sortino `74.32` | Kelly `13.9%` | 30일 APR `13.1%` | Sharpe `0.63`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-09 07:39:20
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-09)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `392435092.87` | Kelly `26.6%` | 30일 APR `6.22%` | Sharpe `9.37`
  - **Slow Stable**: Hurst `0.5` | Sortino `50.46` | Kelly `20.8%` | 30일 APR `24.79%` | Sharpe `8.18`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `296.98%` | Sharpe `3.53`
  - **Gucky_4coin_2dot5x**: Hurst `0.506` | Sortino `64.28` | Kelly `13.2%` | 30일 APR `13.1%` | Sharpe `0.63`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-09 03:41:58
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-09)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `392435092.87` | Kelly `26.6%` | 30일 APR `6.22%` | Sharpe `9.37`
  - **Slow Stable**: Hurst `0.5` | Sortino `50.46` | Kelly `20.8%` | 30일 APR `24.79%` | Sharpe `8.18`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `296.98%` | Sharpe `3.53`
  - **Gucky_4coin_2dot5x**: Hurst `0.506` | Sortino `64.28` | Kelly `13.2%` | 30일 APR `13.1%` | Sharpe `0.63`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-08 23:39:28
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-08)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `391430365.23` | Kelly `30.0%` | 30일 APR `9.96%` | Sharpe `9.54`
  - **Slow Stable**: Hurst `0.5` | Sortino `45.09` | Kelly `23.3%` | 30일 APR `43.67%` | Sharpe `8.24`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `311.0%` | Sharpe `3.73`
  - **Momentum Edge**: Hurst `0.5` | Sortino `35.92` | Kelly `13.2%` | 30일 APR `-55.84%` | Sharpe `6.72`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-08 19:39:25
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-08)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `391430365.23` | Kelly `30.0%` | 30일 APR `9.96%` | Sharpe `9.54`
  - **Slow Stable**: Hurst `0.5` | Sortino `45.09` | Kelly `23.3%` | 30일 APR `43.67%` | Sharpe `8.24`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `311.0%` | Sharpe `3.73`
  - **Momentum Edge**: Hurst `0.5` | Sortino `35.92` | Kelly `13.2%` | 30일 APR `-55.84%` | Sharpe `6.72`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-08 15:39:19
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-08)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `391430365.23` | Kelly `30.0%` | 30일 APR `9.96%` | Sharpe `9.54`
  - **Slow Stable**: Hurst `0.5` | Sortino `45.09` | Kelly `23.3%` | 30일 APR `43.67%` | Sharpe `8.24`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `311.0%` | Sharpe `3.73`
  - **Momentum Edge**: Hurst `0.5` | Sortino `35.92` | Kelly `13.2%` | 30일 APR `-55.84%` | Sharpe `6.72`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-08 11:39:26
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-08)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `391430365.23` | Kelly `30.0%` | 30일 APR `9.96%` | Sharpe `9.54`
  - **Slow Stable**: Hurst `0.5` | Sortino `45.09` | Kelly `23.3%` | 30일 APR `43.67%` | Sharpe `8.24`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `311.0%` | Sharpe `3.73`
  - **Momentum Edge**: Hurst `0.5` | Sortino `35.92` | Kelly `13.2%` | 30일 APR `-55.84%` | Sharpe `6.72`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-08 07:39:21
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-08)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `391430365.23` | Kelly `30.0%` | 30일 APR `9.96%` | Sharpe `9.54`
  - **Slow Stable**: Hurst `0.5` | Sortino `45.09` | Kelly `23.3%` | 30일 APR `43.67%` | Sharpe `8.24`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `311.0%` | Sharpe `3.73`
  - **Momentum Edge**: Hurst `0.5` | Sortino `35.92` | Kelly `13.2%` | 30일 APR `-55.84%` | Sharpe `6.72`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---
