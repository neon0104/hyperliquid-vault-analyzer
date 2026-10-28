# 🧠 Hyperliquid Vault AI 자율 연구 및 지속 학습 일지 (Research Diary)

> 이 문서는 AI 퀀트 연구원이 매 시간 GitHub 오픈소스 퀀트 리서치, 수학적 모델, 온체인 시계열 데이터를 자율 학습하고 검증한 누적 연구 일지입니다.

---

## 📅 연구 기록: 2026-10-28 15:39:26
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-28)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `383862839.05` | Kelly `30.0%` | 30일 APR `4.04%` | Sharpe `9.57`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `-280.09%` | Sharpe `3.4`
  - **wmm.club | scalp-hype-long-2x**: Hurst `0.5` | Sortino `23.16` | Kelly `13.0%` | 30일 APR `-12.88%` | Sharpe `6.35`
  - **Gucky_4coin_2dot5x**: Hurst `0.59` | Sortino `67.83` | Kelly `12.9%` | 30일 APR `23.76%` | Sharpe `0.97`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-28 11:39:28
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-28)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `383862839.05` | Kelly `30.0%` | 30일 APR `4.04%` | Sharpe `9.57`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `-280.09%` | Sharpe `3.4`
  - **wmm.club | scalp-hype-long-2x**: Hurst `0.5` | Sortino `23.16` | Kelly `13.0%` | 30일 APR `-12.88%` | Sharpe `6.35`
  - **Gucky_4coin_2dot5x**: Hurst `0.59` | Sortino `67.83` | Kelly `12.9%` | 30일 APR `23.76%` | Sharpe `0.97`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-28 07:39:21
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-28)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `383862839.05` | Kelly `30.0%` | 30일 APR `4.04%` | Sharpe `9.57`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `-280.09%` | Sharpe `3.4`
  - **Gucky_4coin_2dot5x**: Hurst `0.588` | Sortino `69.37` | Kelly `13.3%` | 30일 APR `23.76%` | Sharpe `0.97`
  - **wmm.club | scalp-hype-long-2x**: Hurst `0.5` | Sortino `23.16` | Kelly `13.0%` | 30일 APR `-12.88%` | Sharpe `6.35`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-28 03:41:50
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-28)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `383862839.05` | Kelly `30.0%` | 30일 APR `4.04%` | Sharpe `9.57`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `-280.09%` | Sharpe `3.4`
  - **Gucky_4coin_2dot5x**: Hurst `0.588` | Sortino `69.37` | Kelly `13.3%` | 30일 APR `23.76%` | Sharpe `0.97`
  - **wmm.club | scalp-hype-long-2x**: Hurst `0.5` | Sortino `23.16` | Kelly `13.0%` | 30일 APR `-12.88%` | Sharpe `6.35`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-27 23:39:30
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-27)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `383701023.16` | Kelly `30.0%` | 30일 APR `3.92%` | Sharpe `9.56`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `-266.36%` | Sharpe `3.39`
  - **Gucky_4coin_2dot5x**: Hurst `0.588` | Sortino `69.37` | Kelly `13.3%` | 30일 APR `23.76%` | Sharpe `0.97`
  - **22Cap**: Hurst `0.352` | Sortino `23.08` | Kelly `11.9%` | 30일 APR `0.61%` | Sharpe `10.09`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-27 19:39:29
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-27)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `383701023.16` | Kelly `30.0%` | 30일 APR `3.92%` | Sharpe `9.56`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `-266.36%` | Sharpe `3.39`
  - **Gucky_4coin_2dot5x**: Hurst `0.588` | Sortino `69.37` | Kelly `13.3%` | 30일 APR `23.76%` | Sharpe `0.97`
  - **22Cap**: Hurst `0.352` | Sortino `23.08` | Kelly `11.9%` | 30일 APR `0.61%` | Sharpe `10.09`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-27 11:39:33
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-27)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `383701023.16` | Kelly `30.0%` | 30일 APR `3.92%` | Sharpe `9.56`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `-266.36%` | Sharpe `3.39`
  - **Gucky_4coin_2dot5x**: Hurst `0.588` | Sortino `69.37` | Kelly `13.3%` | 30일 APR `23.76%` | Sharpe `0.97`
  - **22Cap**: Hurst `0.352` | Sortino `23.08` | Kelly `11.9%` | 30일 APR `0.61%` | Sharpe `10.09`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-27 07:39:25
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-27)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `383701023.16` | Kelly `30.0%` | 30일 APR `3.92%` | Sharpe `9.56`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `-266.36%` | Sharpe `3.39`
  - **HighFDV**: Hurst `0.5` | Sortino `9.72` | Kelly `13.8%` | 30일 APR `241.48%` | Sharpe `7.42`
  - **Gucky_4coin_2dot5x**: Hurst `0.567` | Sortino `70.99` | Kelly `13.6%` | 30일 APR `23.76%` | Sharpe `0.97`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-27 03:42:02
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-27)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `383701023.16` | Kelly `30.0%` | 30일 APR `3.92%` | Sharpe `9.56`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `-266.36%` | Sharpe `3.39`
  - **HighFDV**: Hurst `0.5` | Sortino `9.72` | Kelly `13.8%` | 30일 APR `241.48%` | Sharpe `7.42`
  - **Gucky_4coin_2dot5x**: Hurst `0.567` | Sortino `70.99` | Kelly `13.6%` | 30일 APR `23.76%` | Sharpe `0.97`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-26 23:39:29
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-26)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `383725287.97` | Kelly `30.0%` | 30일 APR `4.0%` | Sharpe `9.56`
  - **Hyper2**: Hurst `0.5` | Sortino `291423028.35` | Kelly `27.4%` | 30일 APR `2.63%` | Sharpe `8.47`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `-110.71%` | Sharpe `3.43`
  - **HighFDV**: Hurst `0.5` | Sortino `9.72` | Kelly `13.8%` | 30일 APR `241.48%` | Sharpe `7.42`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-26 19:39:30
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-26)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `383725287.97` | Kelly `30.0%` | 30일 APR `4.0%` | Sharpe `9.56`
  - **Hyper2**: Hurst `0.5` | Sortino `291423028.35` | Kelly `27.4%` | 30일 APR `2.63%` | Sharpe `8.47`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `-110.71%` | Sharpe `3.43`
  - **HighFDV**: Hurst `0.5` | Sortino `9.72` | Kelly `13.8%` | 30일 APR `241.48%` | Sharpe `7.42`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-26 15:39:27
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-26)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `383725287.97` | Kelly `30.0%` | 30일 APR `4.0%` | Sharpe `9.56`
  - **Hyper2**: Hurst `0.5` | Sortino `291423028.35` | Kelly `27.4%` | 30일 APR `2.63%` | Sharpe `8.47`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `-110.71%` | Sharpe `3.43`
  - **HighFDV**: Hurst `0.5` | Sortino `9.72` | Kelly `13.8%` | 30일 APR `241.48%` | Sharpe `7.42`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-26 11:39:24
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-26)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `383725287.97` | Kelly `30.0%` | 30일 APR `4.0%` | Sharpe `9.56`
  - **Hyper2**: Hurst `0.5` | Sortino `291423028.35` | Kelly `27.4%` | 30일 APR `2.63%` | Sharpe `8.47`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `-110.71%` | Sharpe `3.43`
  - **HighFDV**: Hurst `0.5` | Sortino `9.72` | Kelly `13.8%` | 30일 APR `241.48%` | Sharpe `7.42`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-26 07:39:20
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-26)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `383725287.97` | Kelly `30.0%` | 30일 APR `4.0%` | Sharpe `9.56`
  - **Hyper2**: Hurst `0.5` | Sortino `291423028.35` | Kelly `27.4%` | 30일 APR `2.63%` | Sharpe `8.47`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `-110.71%` | Sharpe `3.43`
  - **Gucky_4coin_2dot5x**: Hurst `0.401` | Sortino `72.68` | Kelly `14.0%` | 30일 APR `23.76%` | Sharpe `0.97`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-26 03:41:47
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-26)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `383725287.97` | Kelly `30.0%` | 30일 APR `4.0%` | Sharpe `9.56`
  - **Hyper2**: Hurst `0.5` | Sortino `291423028.35` | Kelly `27.4%` | 30일 APR `2.63%` | Sharpe `8.47`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `-110.71%` | Sharpe `3.43`
  - **Gucky_4coin_2dot5x**: Hurst `0.401` | Sortino `72.68` | Kelly `14.0%` | 30일 APR `23.76%` | Sharpe `0.97`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---
