# 🧠 Hyperliquid Vault AI 자율 연구 및 지속 학습 일지 (Research Diary)

> 이 문서는 AI 퀀트 연구원이 매 시간 GitHub 오픈소스 퀀트 리서치, 수학적 모델, 온체인 시계열 데이터를 자율 학습하고 검증한 누적 연구 일지입니다.

---

## 📅 연구 기록: 2026-10-25 03:42:04
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-25)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Hyper2**: Hurst `0.5` | Sortino `290742437.41` | Kelly `27.4%` | 30일 APR `2.08%` | Sharpe `8.44`
  - **Algo1**: Hurst `0.5` | Sortino `19.7` | Kelly `22.0%` | 30일 APR `3.59%` | Sharpe `6.0`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `-102.56%` | Sharpe `3.35`
  - **HighFDV**: Hurst `0.5` | Sortino `9.72` | Kelly `13.8%` | 30일 APR `241.48%` | Sharpe `7.42`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-24 23:39:26
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-24)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `401287161.99` | Kelly `30.0%` | 30일 APR `13.51%` | Sharpe `9.56`
  - **Hyper2**: Hurst `0.5` | Sortino `291390282.76` | Kelly `27.4%` | 30일 APR `2.67%` | Sharpe `8.47`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `-179.94%` | Sharpe `3.47`
  - **HighFDV**: Hurst `0.5` | Sortino `9.72` | Kelly `13.8%` | 30일 APR `241.2%` | Sharpe `7.42`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-24 19:39:25
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-24)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `401287161.99` | Kelly `30.0%` | 30일 APR `13.51%` | Sharpe `9.56`
  - **Hyper2**: Hurst `0.5` | Sortino `291390282.76` | Kelly `27.4%` | 30일 APR `2.67%` | Sharpe `8.47`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `-179.94%` | Sharpe `3.47`
  - **HighFDV**: Hurst `0.5` | Sortino `9.72` | Kelly `13.8%` | 30일 APR `241.2%` | Sharpe `7.42`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-24 15:39:24
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-24)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `401287161.99` | Kelly `30.0%` | 30일 APR `13.51%` | Sharpe `9.56`
  - **Hyper2**: Hurst `0.5` | Sortino `291390282.76` | Kelly `27.4%` | 30일 APR `2.67%` | Sharpe `8.47`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `-179.94%` | Sharpe `3.47`
  - **HighFDV**: Hurst `0.5` | Sortino `9.72` | Kelly `13.8%` | 30일 APR `241.2%` | Sharpe `7.42`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-24 11:39:29
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-24)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `401287161.99` | Kelly `30.0%` | 30일 APR `13.51%` | Sharpe `9.56`
  - **Hyper2**: Hurst `0.5` | Sortino `291390282.76` | Kelly `27.4%` | 30일 APR `2.67%` | Sharpe `8.47`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `-179.94%` | Sharpe `3.47`
  - **HighFDV**: Hurst `0.5` | Sortino `9.72` | Kelly `13.8%` | 30일 APR `241.2%` | Sharpe `7.42`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-24 07:39:24
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-24)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `401287161.99` | Kelly `30.0%` | 30일 APR `13.51%` | Sharpe `9.56`
  - **Hyper2**: Hurst `0.5` | Sortino `291390282.76` | Kelly `27.4%` | 30일 APR `2.67%` | Sharpe `8.47`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `-179.94%` | Sharpe `3.47`
  - **Gucky_4coin_2dot5x**: Hurst `0.352` | Sortino `74.0` | Kelly `14.0%` | 30일 APR `30.7%` | Sharpe `0.96`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-24 03:42:07
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-24)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `401287161.99` | Kelly `30.0%` | 30일 APR `13.51%` | Sharpe `9.56`
  - **Hyper2**: Hurst `0.5` | Sortino `291390282.76` | Kelly `27.4%` | 30일 APR `2.67%` | Sharpe `8.47`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `-179.94%` | Sharpe `3.47`
  - **Gucky_4coin_2dot5x**: Hurst `0.352` | Sortino `74.0` | Kelly `14.0%` | 30일 APR `30.7%` | Sharpe `0.96`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-23 23:39:20
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-23)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `401040434.34` | Kelly `30.0%` | 30일 APR `16.38%` | Sharpe `9.56`
  - **Hyper2**: Hurst `0.5` | Sortino `291200499.85` | Kelly `27.4%` | 30일 APR `2.54%` | Sharpe `8.46`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `-159.41%` | Sharpe `3.47`
  - **Gucky_4coin_2dot5x**: Hurst `0.352` | Sortino `74.0` | Kelly `14.0%` | 30일 APR `30.7%` | Sharpe `0.96`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-23 19:39:29
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-23)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `401040434.34` | Kelly `30.0%` | 30일 APR `16.38%` | Sharpe `9.56`
  - **Hyper2**: Hurst `0.5` | Sortino `291200499.85` | Kelly `27.4%` | 30일 APR `2.54%` | Sharpe `8.46`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `-159.41%` | Sharpe `3.47`
  - **Gucky_4coin_2dot5x**: Hurst `0.352` | Sortino `74.0` | Kelly `14.0%` | 30일 APR `30.7%` | Sharpe `0.96`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-23 15:39:25
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-23)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `401040434.34` | Kelly `30.0%` | 30일 APR `16.38%` | Sharpe `9.56`
  - **Hyper2**: Hurst `0.5` | Sortino `291200499.85` | Kelly `27.4%` | 30일 APR `2.54%` | Sharpe `8.46`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `-159.41%` | Sharpe `3.47`
  - **Gucky_4coin_2dot5x**: Hurst `0.352` | Sortino `74.0` | Kelly `14.0%` | 30일 APR `30.7%` | Sharpe `0.96`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-23 11:39:27
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-23)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `401040434.34` | Kelly `30.0%` | 30일 APR `16.38%` | Sharpe `9.56`
  - **Hyper2**: Hurst `0.5` | Sortino `291200499.85` | Kelly `27.4%` | 30일 APR `2.54%` | Sharpe `8.46`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `-159.41%` | Sharpe `3.47`
  - **Gucky_4coin_2dot5x**: Hurst `0.352` | Sortino `74.0` | Kelly `14.0%` | 30일 APR `30.7%` | Sharpe `0.96`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-23 07:39:20
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-23)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `401040434.34` | Kelly `30.0%` | 30일 APR `16.38%` | Sharpe `9.56`
  - **Hyper2**: Hurst `0.5` | Sortino `291200499.85` | Kelly `27.4%` | 30일 APR `2.54%` | Sharpe `8.46`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `-159.41%` | Sharpe `3.47`
  - **Gucky_4coin_2dot5x**: Hurst `0.322` | Sortino `75.9` | Kelly `14.4%` | 30일 APR `30.7%` | Sharpe `0.96`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-23 03:42:09
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-23)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `401040434.34` | Kelly `30.0%` | 30일 APR `16.38%` | Sharpe `9.56`
  - **Hyper2**: Hurst `0.5` | Sortino `291200499.85` | Kelly `27.4%` | 30일 APR `2.54%` | Sharpe `8.46`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `-159.41%` | Sharpe `3.47`
  - **Gucky_4coin_2dot5x**: Hurst `0.322` | Sortino `75.9` | Kelly `14.4%` | 30일 APR `30.7%` | Sharpe `0.96`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-22 23:39:26
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-22)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Hyper2**: Hurst `0.5` | Sortino `291559178.95` | Kelly `27.4%` | 30일 APR `2.89%` | Sharpe `8.48`
  - **Algo1**: Hurst `0.5` | Sortino `364574469.37` | Kelly `27.3%` | 30일 APR `10.41%` | Sharpe `8.94`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `153.27%` | Sharpe `3.6`
  - **Gucky_4coin_2dot5x**: Hurst `0.322` | Sortino `75.9` | Kelly `14.4%` | 30일 APR `30.7%` | Sharpe `0.96`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-22 19:39:28
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-22)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Hyper2**: Hurst `0.5` | Sortino `291559178.95` | Kelly `27.4%` | 30일 APR `2.89%` | Sharpe `8.48`
  - **Algo1**: Hurst `0.5` | Sortino `364574469.37` | Kelly `27.3%` | 30일 APR `10.41%` | Sharpe `8.94`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `153.27%` | Sharpe `3.6`
  - **Gucky_4coin_2dot5x**: Hurst `0.322` | Sortino `75.9` | Kelly `14.4%` | 30일 APR `30.7%` | Sharpe `0.96`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---
