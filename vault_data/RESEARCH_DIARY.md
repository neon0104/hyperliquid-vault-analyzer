# 🧠 Hyperliquid Vault AI 자율 연구 및 지속 학습 일지 (Research Diary)

> 이 문서는 AI 퀀트 연구원이 매 시간 GitHub 오픈소스 퀀트 리서치, 수학적 모델, 온체인 시계열 데이터를 자율 학습하고 검증한 누적 연구 일지입니다.

---

## 📅 연구 기록: 2026-09-17 15:39:21
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-17)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `297855416.56` | Kelly `23.9%` | 30일 APR `148.81%` | Sharpe `5.77`
  - **Slow Stable**: Hurst `0.5` | Sortino `51.16` | Kelly `22.8%` | 30일 APR `22.67%` | Sharpe `8.68`
  - **Aaroh**: Hurst `0.5` | Sortino `27.05` | Kelly `17.0%` | 30일 APR `443.88%` | Sharpe `9.65`
  - **Gentile Geopolitics | Iran War**: Hurst `0.5` | Sortino `50.92` | Kelly `16.8%` | 30일 APR `593.23%` | Sharpe `8.41`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-17 11:39:16
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-17)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `297855416.56` | Kelly `23.9%` | 30일 APR `148.81%` | Sharpe `5.77`
  - **Slow Stable**: Hurst `0.5` | Sortino `51.16` | Kelly `22.8%` | 30일 APR `22.67%` | Sharpe `8.68`
  - **Aaroh**: Hurst `0.5` | Sortino `27.05` | Kelly `17.0%` | 30일 APR `443.88%` | Sharpe `9.65`
  - **Gentile Geopolitics | Iran War**: Hurst `0.5` | Sortino `50.92` | Kelly `16.8%` | 30일 APR `593.23%` | Sharpe `8.41`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-17 07:39:17
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-17)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `297855416.56` | Kelly `23.9%` | 30일 APR `148.81%` | Sharpe `5.77`
  - **Slow Stable**: Hurst `0.5` | Sortino `51.16` | Kelly `22.8%` | 30일 APR `22.67%` | Sharpe `8.68`
  - **Hindenburg Short Alpha**: Hurst `0.719` | Sortino `37.59` | Kelly `17.1%` | 30일 APR `358.7%` | Sharpe `7.16`
  - **Aaroh**: Hurst `0.5` | Sortino `27.05` | Kelly `17.0%` | 30일 APR `443.88%` | Sharpe `9.65`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-17 03:41:53
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-17)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `297855416.56` | Kelly `23.9%` | 30일 APR `148.81%` | Sharpe `5.77`
  - **Slow Stable**: Hurst `0.5` | Sortino `51.16` | Kelly `22.8%` | 30일 APR `22.67%` | Sharpe `8.68`
  - **Hindenburg Short Alpha**: Hurst `0.719` | Sortino `37.59` | Kelly `17.1%` | 30일 APR `358.7%` | Sharpe `7.16`
  - **Aaroh**: Hurst `0.5` | Sortino `27.05` | Kelly `17.0%` | 30일 APR `443.88%` | Sharpe `9.65`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-16 23:39:24
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-16)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `297440475.43` | Kelly `23.9%` | 30일 APR `148.43%` | Sharpe `6.46`
  - **[Bee] Line**: Hurst `0.5` | Sortino `143251410.26` | Kelly `21.7%` | 30일 APR `85.52%` | Sharpe `7.6`
  - **Slow Stable**: Hurst `0.5` | Sortino `52.7` | Kelly `20.3%` | 30일 APR `22.65%` | Sharpe `8.28`
  - **Aaroh**: Hurst `0.5` | Sortino `25.64` | Kelly `17.2%` | 30일 APR `422.81%` | Sharpe `9.84`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-16 19:39:23
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-16)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `297440475.43` | Kelly `23.9%` | 30일 APR `148.43%` | Sharpe `6.46`
  - **[Bee] Line**: Hurst `0.5` | Sortino `143251410.26` | Kelly `21.7%` | 30일 APR `85.52%` | Sharpe `7.6`
  - **Slow Stable**: Hurst `0.5` | Sortino `52.7` | Kelly `20.3%` | 30일 APR `22.65%` | Sharpe `8.28`
  - **Aaroh**: Hurst `0.5` | Sortino `25.64` | Kelly `17.2%` | 30일 APR `422.81%` | Sharpe `9.84`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-16 15:39:23
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-16)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `297440475.43` | Kelly `23.9%` | 30일 APR `148.43%` | Sharpe `6.46`
  - **[Bee] Line**: Hurst `0.5` | Sortino `143251410.26` | Kelly `21.7%` | 30일 APR `85.52%` | Sharpe `7.6`
  - **Slow Stable**: Hurst `0.5` | Sortino `52.7` | Kelly `20.3%` | 30일 APR `22.65%` | Sharpe `8.28`
  - **Aaroh**: Hurst `0.5` | Sortino `25.64` | Kelly `17.2%` | 30일 APR `422.81%` | Sharpe `9.84`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-16 11:39:24
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-16)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `297440475.43` | Kelly `23.9%` | 30일 APR `148.43%` | Sharpe `6.46`
  - **[Bee] Line**: Hurst `0.5` | Sortino `143251410.26` | Kelly `21.7%` | 30일 APR `85.52%` | Sharpe `7.6`
  - **Slow Stable**: Hurst `0.5` | Sortino `52.7` | Kelly `20.3%` | 30일 APR `22.65%` | Sharpe `8.28`
  - **Aaroh**: Hurst `0.5` | Sortino `25.64` | Kelly `17.2%` | 30일 APR `422.81%` | Sharpe `9.84`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-16 07:39:20
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-16)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `297440475.43` | Kelly `23.9%` | 30일 APR `148.43%` | Sharpe `6.46`
  - **[Bee] Line**: Hurst `0.5` | Sortino `143251410.26` | Kelly `21.7%` | 30일 APR `85.52%` | Sharpe `7.6`
  - **Slow Stable**: Hurst `0.5` | Sortino `52.7` | Kelly `20.3%` | 30일 APR `22.65%` | Sharpe `8.28`
  - **Aaroh**: Hurst `0.5` | Sortino `25.64` | Kelly `17.2%` | 30일 APR `422.81%` | Sharpe `9.84`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-16 03:41:46
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-16)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `297440475.43` | Kelly `23.9%` | 30일 APR `148.43%` | Sharpe `6.46`
  - **[Bee] Line**: Hurst `0.5` | Sortino `143251410.26` | Kelly `21.7%` | 30일 APR `85.52%` | Sharpe `7.6`
  - **Slow Stable**: Hurst `0.5` | Sortino `52.7` | Kelly `20.3%` | 30일 APR `22.65%` | Sharpe `8.28`
  - **Aaroh**: Hurst `0.5` | Sortino `25.64` | Kelly `17.2%` | 30일 APR `422.81%` | Sharpe `9.84`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-15 23:39:22
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-15)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[Bee] Line**: Hurst `0.5` | Sortino `157466049.19` | Kelly `24.1%` | 30일 APR `95.46%` | Sharpe `9.1`
  - **Algo1**: Hurst `0.5` | Sortino `297452147.89` | Kelly `23.9%` | 30일 APR `148.44%` | Sharpe `6.46`
  - **Aaroh**: Hurst `0.5` | Sortino `25.49` | Kelly `20.4%` | 30일 APR `482.91%` | Sharpe `10.79`
  - **Slow Stable**: Hurst `0.5` | Sortino `52.67` | Kelly `20.3%` | 30일 APR `22.55%` | Sharpe `8.28`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-15 19:39:24
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-15)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[Bee] Line**: Hurst `0.5` | Sortino `157466049.19` | Kelly `24.1%` | 30일 APR `95.46%` | Sharpe `9.1`
  - **Algo1**: Hurst `0.5` | Sortino `297452147.89` | Kelly `23.9%` | 30일 APR `148.44%` | Sharpe `6.46`
  - **Aaroh**: Hurst `0.5` | Sortino `25.49` | Kelly `20.4%` | 30일 APR `482.91%` | Sharpe `10.79`
  - **Slow Stable**: Hurst `0.5` | Sortino `52.67` | Kelly `20.3%` | 30일 APR `22.55%` | Sharpe `8.28`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-15 15:39:21
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-15)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[Bee] Line**: Hurst `0.5` | Sortino `157466049.19` | Kelly `24.1%` | 30일 APR `95.46%` | Sharpe `9.1`
  - **Algo1**: Hurst `0.5` | Sortino `297452147.89` | Kelly `23.9%` | 30일 APR `148.44%` | Sharpe `6.46`
  - **Aaroh**: Hurst `0.5` | Sortino `25.49` | Kelly `20.4%` | 30일 APR `482.91%` | Sharpe `10.79`
  - **Slow Stable**: Hurst `0.5` | Sortino `52.67` | Kelly `20.3%` | 30일 APR `22.55%` | Sharpe `8.28`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-15 11:39:22
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-15)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[Bee] Line**: Hurst `0.5` | Sortino `157466049.19` | Kelly `24.1%` | 30일 APR `95.46%` | Sharpe `9.1`
  - **Algo1**: Hurst `0.5` | Sortino `297452147.89` | Kelly `23.9%` | 30일 APR `148.44%` | Sharpe `6.46`
  - **Aaroh**: Hurst `0.5` | Sortino `25.49` | Kelly `20.4%` | 30일 APR `482.91%` | Sharpe `10.79`
  - **Slow Stable**: Hurst `0.5` | Sortino `52.67` | Kelly `20.3%` | 30일 APR `22.55%` | Sharpe `8.28`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-14 23:39:22
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-14)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[Bee] Line**: Hurst `0.5` | Sortino `179345295.21` | Kelly `30.0%` | 30일 APR `111.26%` | Sharpe `11.93`
  - **Algo1**: Hurst `0.5` | Sortino `321940781.55` | Kelly `23.7%` | 30일 APR `148.19%` | Sharpe `6.78`
  - **Slow Stable**: Hurst `0.5` | Sortino `52.6` | Kelly `20.3%` | 30일 APR `22.22%` | Sharpe `8.27`
  - **Hindenburg Short Alpha**: Hurst `0.635` | Sortino `40.33` | Kelly `18.0%` | 30일 APR `409.25%` | Sharpe `7.08`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---
