# 🧠 Hyperliquid Vault AI 자율 연구 및 지속 학습 일지 (Research Diary)

> 이 문서는 AI 퀀트 연구원이 매 시간 GitHub 오픈소스 퀀트 리서치, 수학적 모델, 온체인 시계열 데이터를 자율 학습하고 검증한 누적 연구 일지입니다.

---

## 📅 연구 기록: 2026-10-21 15:39:30
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-21)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `383165281.1` | Kelly `30.0%` | 30일 APR `11.68%` | Sharpe `9.54`
  - **Hyper2**: Hurst `0.5` | Sortino `291559178.95` | Kelly `27.4%` | 30일 APR `2.98%` | Sharpe `8.48`
  - **Gucky_4coin_2dot5x**: Hurst `0.19` | Sortino `77.89` | Kelly `14.9%` | 30일 APR `29.68%` | Sharpe `0.94`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `102.07%` | Sharpe `3.47`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-21 11:39:26
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-21)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `383165281.1` | Kelly `30.0%` | 30일 APR `11.68%` | Sharpe `9.54`
  - **Hyper2**: Hurst `0.5` | Sortino `291559178.95` | Kelly `27.4%` | 30일 APR `2.98%` | Sharpe `8.48`
  - **Gucky_4coin_2dot5x**: Hurst `0.19` | Sortino `77.89` | Kelly `14.9%` | 30일 APR `29.68%` | Sharpe `0.94`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `102.07%` | Sharpe `3.47`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-21 07:39:21
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-21)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `383165281.1` | Kelly `30.0%` | 30일 APR `11.68%` | Sharpe `9.54`
  - **Hyper2**: Hurst `0.5` | Sortino `291559178.95` | Kelly `27.4%` | 30일 APR `2.98%` | Sharpe `8.48`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `102.07%` | Sharpe `3.47`
  - **Gucky_4coin_2dot5x**: Hurst `0.321` | Sortino `76.72` | Kelly `14.5%` | 30일 APR `29.68%` | Sharpe `0.94`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-21 03:42:06
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-21)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `383165281.1` | Kelly `30.0%` | 30일 APR `11.68%` | Sharpe `9.54`
  - **Hyper2**: Hurst `0.5` | Sortino `291559178.95` | Kelly `27.4%` | 30일 APR `2.98%` | Sharpe `8.48`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `102.07%` | Sharpe `3.47`
  - **Gucky_4coin_2dot5x**: Hurst `0.321` | Sortino `76.72` | Kelly `14.5%` | 30일 APR `29.68%` | Sharpe `0.94`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-20 23:39:25
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-20)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `382851299.96` | Kelly `30.0%` | 30일 APR `11.69%` | Sharpe `9.54`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `21.35%` | Sharpe `3.46`
  - **Gucky_4coin_2dot5x**: Hurst `0.321` | Sortino `76.72` | Kelly `14.5%` | 30일 APR `32.09%` | Sharpe `0.93`
  - **HighFDV**: Hurst `0.5` | Sortino `10.08` | Kelly `14.0%` | 30일 APR `253.5%` | Sharpe `7.55`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-20 19:39:27
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-20)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `382851299.96` | Kelly `30.0%` | 30일 APR `11.69%` | Sharpe `9.54`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `21.35%` | Sharpe `3.46`
  - **Gucky_4coin_2dot5x**: Hurst `0.321` | Sortino `76.72` | Kelly `14.5%` | 30일 APR `32.09%` | Sharpe `0.93`
  - **HighFDV**: Hurst `0.5` | Sortino `10.08` | Kelly `14.0%` | 30일 APR `253.5%` | Sharpe `7.55`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-20 15:39:25
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-20)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `382851299.96` | Kelly `30.0%` | 30일 APR `11.69%` | Sharpe `9.54`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `21.35%` | Sharpe `3.46`
  - **Gucky_4coin_2dot5x**: Hurst `0.321` | Sortino `76.72` | Kelly `14.5%` | 30일 APR `32.09%` | Sharpe `0.93`
  - **HighFDV**: Hurst `0.5` | Sortino `10.08` | Kelly `14.0%` | 30일 APR `253.5%` | Sharpe `7.55`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-20 11:39:26
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-20)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `382851299.96` | Kelly `30.0%` | 30일 APR `11.69%` | Sharpe `9.54`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `21.35%` | Sharpe `3.46`
  - **Gucky_4coin_2dot5x**: Hurst `0.321` | Sortino `76.72` | Kelly `14.5%` | 30일 APR `32.09%` | Sharpe `0.93`
  - **HighFDV**: Hurst `0.5` | Sortino `10.08` | Kelly `14.0%` | 30일 APR `253.5%` | Sharpe `7.55`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-20 07:39:22
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-20)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `382851299.96` | Kelly `30.0%` | 30일 APR `11.69%` | Sharpe `9.54`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `21.35%` | Sharpe `3.46`
  - **Gucky_4coin_2dot5x**: Hurst `0.318` | Sortino `78.85` | Kelly `14.1%` | 30일 APR `32.09%` | Sharpe `0.93`
  - **HighFDV**: Hurst `0.5` | Sortino `10.08` | Kelly `14.0%` | 30일 APR `253.5%` | Sharpe `7.55`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-20 03:41:57
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-20)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `382851299.96` | Kelly `30.0%` | 30일 APR `11.69%` | Sharpe `9.54`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `21.35%` | Sharpe `3.46`
  - **Gucky_4coin_2dot5x**: Hurst `0.318` | Sortino `78.85` | Kelly `14.1%` | 30일 APR `32.09%` | Sharpe `0.93`
  - **HighFDV**: Hurst `0.5` | Sortino `10.08` | Kelly `14.0%` | 30일 APR `253.5%` | Sharpe `7.55`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-19 23:39:25
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-19)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `382575073.44` | Kelly `30.0%` | 30일 APR `10.2%` | Sharpe `9.53`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `404.0%` | Sharpe `3.46`
  - **Gucky_4coin_2dot5x**: Hurst `0.318` | Sortino `78.85` | Kelly `14.1%` | 30일 APR `32.09%` | Sharpe `0.93`
  - **HighFDV**: Hurst `0.5` | Sortino `10.07` | Kelly `14.0%` | 30일 APR `253.19%` | Sharpe `7.55`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-19 19:39:22
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-19)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `382575073.44` | Kelly `30.0%` | 30일 APR `10.2%` | Sharpe `9.53`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `404.0%` | Sharpe `3.46`
  - **Gucky_4coin_2dot5x**: Hurst `0.318` | Sortino `78.85` | Kelly `14.1%` | 30일 APR `32.09%` | Sharpe `0.93`
  - **HighFDV**: Hurst `0.5` | Sortino `10.07` | Kelly `14.0%` | 30일 APR `253.19%` | Sharpe `7.55`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-19 15:39:24
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-19)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `382575073.44` | Kelly `30.0%` | 30일 APR `10.2%` | Sharpe `9.53`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `404.0%` | Sharpe `3.46`
  - **Gucky_4coin_2dot5x**: Hurst `0.318` | Sortino `78.85` | Kelly `14.1%` | 30일 APR `32.09%` | Sharpe `0.93`
  - **HighFDV**: Hurst `0.5` | Sortino `10.07` | Kelly `14.0%` | 30일 APR `253.19%` | Sharpe `7.55`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-19 11:39:24
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-19)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `382575073.44` | Kelly `30.0%` | 30일 APR `10.2%` | Sharpe `9.53`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `404.0%` | Sharpe `3.46`
  - **Gucky_4coin_2dot5x**: Hurst `0.318` | Sortino `78.85` | Kelly `14.1%` | 30일 APR `32.09%` | Sharpe `0.93`
  - **HighFDV**: Hurst `0.5` | Sortino `10.07` | Kelly `14.0%` | 30일 APR `253.19%` | Sharpe `7.55`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-19 07:39:20
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-19)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `382575073.44` | Kelly `30.0%` | 30일 APR `10.2%` | Sharpe `9.53`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `404.0%` | Sharpe `3.46`
  - **HighFDV**: Hurst `0.5` | Sortino `10.07` | Kelly `14.0%` | 30일 APR `253.19%` | Sharpe `7.55`
  - **Gucky_4coin_2dot5x**: Hurst `0.282` | Sortino `80.91` | Kelly `13.7%` | 30일 APR `32.09%` | Sharpe `0.93`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---
