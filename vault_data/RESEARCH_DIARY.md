# 🧠 Hyperliquid Vault AI 자율 연구 및 지속 학습 일지 (Research Diary)

> 이 문서는 AI 퀀트 연구원이 매 시간 GitHub 오픈소스 퀀트 리서치, 수학적 모델, 온체인 시계열 데이터를 자율 학습하고 검증한 누적 연구 일지입니다.

---

## 📅 연구 기록: 2026-09-14 03:42:04
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-14)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[Bee] Line**: Hurst `0.5` | Sortino `179345295.21` | Kelly `30.0%` | 30일 APR `111.26%` | Sharpe `11.93`
  - **Algo1**: Hurst `0.5` | Sortino `321940781.55` | Kelly `23.7%` | 30일 APR `148.19%` | Sharpe `6.78`
  - **Slow Stable**: Hurst `0.5` | Sortino `52.6` | Kelly `20.3%` | 30일 APR `22.22%` | Sharpe `8.27`
  - **Hindenburg Short Alpha**: Hurst `0.656` | Sortino `41.83` | Kelly `17.6%` | 30일 APR `409.25%` | Sharpe `7.08`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-13 23:39:22
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-13)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[Bee] Line**: Hurst `0.5` | Sortino `234008987.81` | Kelly `27.1%` | 30일 APR `143.99%` | Sharpe `9.95`
  - **Algo1**: Hurst `0.5` | Sortino `321745893.01` | Kelly `23.7%` | 30일 APR `148.04%` | Sharpe `6.77`
  - **Slow Stable**: Hurst `0.5` | Sortino `9110.66` | Kelly `21.4%` | 30일 APR `22.23%` | Sharpe `8.48`
  - **Hindenburg Short Alpha**: Hurst `0.656` | Sortino `41.83` | Kelly `17.6%` | 30일 APR `413.26%` | Sharpe `7.1`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-13 19:39:26
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-13)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[Bee] Line**: Hurst `0.5` | Sortino `234008987.81` | Kelly `27.1%` | 30일 APR `143.99%` | Sharpe `9.95`
  - **Algo1**: Hurst `0.5` | Sortino `321745893.01` | Kelly `23.7%` | 30일 APR `148.04%` | Sharpe `6.77`
  - **Slow Stable**: Hurst `0.5` | Sortino `9110.66` | Kelly `21.4%` | 30일 APR `22.23%` | Sharpe `8.48`
  - **Hindenburg Short Alpha**: Hurst `0.656` | Sortino `41.83` | Kelly `17.6%` | 30일 APR `413.26%` | Sharpe `7.1`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-13 15:39:22
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-13)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[Bee] Line**: Hurst `0.5` | Sortino `234008987.81` | Kelly `27.1%` | 30일 APR `143.99%` | Sharpe `9.95`
  - **Algo1**: Hurst `0.5` | Sortino `321745893.01` | Kelly `23.7%` | 30일 APR `148.04%` | Sharpe `6.77`
  - **Slow Stable**: Hurst `0.5` | Sortino `9110.66` | Kelly `21.4%` | 30일 APR `22.23%` | Sharpe `8.48`
  - **Hindenburg Short Alpha**: Hurst `0.656` | Sortino `41.83` | Kelly `17.6%` | 30일 APR `413.26%` | Sharpe `7.1`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-13 11:39:21
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-13)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[Bee] Line**: Hurst `0.5` | Sortino `234008987.81` | Kelly `27.1%` | 30일 APR `143.99%` | Sharpe `9.95`
  - **Algo1**: Hurst `0.5` | Sortino `321745893.01` | Kelly `23.7%` | 30일 APR `148.04%` | Sharpe `6.77`
  - **Slow Stable**: Hurst `0.5` | Sortino `9110.66` | Kelly `21.4%` | 30일 APR `22.23%` | Sharpe `8.48`
  - **Hindenburg Short Alpha**: Hurst `0.656` | Sortino `41.83` | Kelly `17.6%` | 30일 APR `413.26%` | Sharpe `7.1`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-13 07:39:17
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-13)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[Bee] Line**: Hurst `0.5` | Sortino `234008987.81` | Kelly `27.1%` | 30일 APR `143.99%` | Sharpe `9.95`
  - **Algo1**: Hurst `0.5` | Sortino `321745893.01` | Kelly `23.7%` | 30일 APR `148.04%` | Sharpe `6.77`
  - **Slow Stable**: Hurst `0.5` | Sortino `9110.66` | Kelly `21.4%` | 30일 APR `22.23%` | Sharpe `8.48`
  - **Hindenburg Short Alpha**: Hurst `0.512` | Sortino `44.33` | Kelly `17.1%` | 30일 APR `413.26%` | Sharpe `7.1`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-13 03:41:52
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-13)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[Bee] Line**: Hurst `0.5` | Sortino `234008987.81` | Kelly `27.1%` | 30일 APR `143.99%` | Sharpe `9.95`
  - **Algo1**: Hurst `0.5` | Sortino `321745893.01` | Kelly `23.7%` | 30일 APR `148.04%` | Sharpe `6.77`
  - **Slow Stable**: Hurst `0.5` | Sortino `9110.66` | Kelly `21.4%` | 30일 APR `22.23%` | Sharpe `8.48`
  - **Hindenburg Short Alpha**: Hurst `0.512` | Sortino `44.33` | Kelly `17.1%` | 30일 APR `413.26%` | Sharpe `7.1`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-12 23:39:23
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-12)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[Bee] Line**: Hurst `0.5` | Sortino `254421870.94` | Kelly `26.8%` | 30일 APR `143.26%` | Sharpe `10.6`
  - **Algo1**: Hurst `0.5` | Sortino `321776647.83` | Kelly `23.7%` | 30일 APR `148.2%` | Sharpe `6.61`
  - **Slow Stable**: Hurst `0.5` | Sortino `9111.08` | Kelly `21.4%` | 30일 APR `22.29%` | Sharpe `8.42`
  - **Momentum Edge**: Hurst `0.5` | Sortino `66.94` | Kelly `17.5%` | 30일 APR `19.74%` | Sharpe `8.33`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-12 19:39:16
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-12)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[Bee] Line**: Hurst `0.5` | Sortino `254421870.94` | Kelly `26.8%` | 30일 APR `143.26%` | Sharpe `10.6`
  - **Algo1**: Hurst `0.5` | Sortino `321776647.83` | Kelly `23.7%` | 30일 APR `148.2%` | Sharpe `6.61`
  - **Slow Stable**: Hurst `0.5` | Sortino `9111.08` | Kelly `21.4%` | 30일 APR `22.29%` | Sharpe `8.42`
  - **Momentum Edge**: Hurst `0.5` | Sortino `66.94` | Kelly `17.5%` | 30일 APR `19.74%` | Sharpe `8.33`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-12 15:39:20
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-12)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[Bee] Line**: Hurst `0.5` | Sortino `254421870.94` | Kelly `26.8%` | 30일 APR `143.26%` | Sharpe `10.6`
  - **Algo1**: Hurst `0.5` | Sortino `321776647.83` | Kelly `23.7%` | 30일 APR `148.2%` | Sharpe `6.61`
  - **Slow Stable**: Hurst `0.5` | Sortino `9111.08` | Kelly `21.4%` | 30일 APR `22.29%` | Sharpe `8.42`
  - **Momentum Edge**: Hurst `0.5` | Sortino `66.94` | Kelly `17.5%` | 30일 APR `19.74%` | Sharpe `8.33`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-12 11:39:21
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-12)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[Bee] Line**: Hurst `0.5` | Sortino `254421870.94` | Kelly `26.8%` | 30일 APR `143.26%` | Sharpe `10.6`
  - **Algo1**: Hurst `0.5` | Sortino `321776647.83` | Kelly `23.7%` | 30일 APR `148.2%` | Sharpe `6.61`
  - **Slow Stable**: Hurst `0.5` | Sortino `9111.08` | Kelly `21.4%` | 30일 APR `22.29%` | Sharpe `8.42`
  - **Momentum Edge**: Hurst `0.5` | Sortino `66.94` | Kelly `17.5%` | 30일 APR `19.74%` | Sharpe `8.33`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-12 07:39:16
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-12)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[Bee] Line**: Hurst `0.5` | Sortino `254421870.94` | Kelly `26.8%` | 30일 APR `143.26%` | Sharpe `10.6`
  - **Algo1**: Hurst `0.5` | Sortino `321776647.83` | Kelly `23.7%` | 30일 APR `148.2%` | Sharpe `6.61`
  - **Slow Stable**: Hurst `0.5` | Sortino `9111.08` | Kelly `21.4%` | 30일 APR `22.29%` | Sharpe `8.42`
  - **Hindenburg Short Alpha**: Hurst `0.701` | Sortino `44.8` | Kelly `18.8%` | 30일 APR `437.03%` | Sharpe `7.12`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-12 03:41:49
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-12)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[Bee] Line**: Hurst `0.5` | Sortino `254421870.94` | Kelly `26.8%` | 30일 APR `143.26%` | Sharpe `10.6`
  - **Algo1**: Hurst `0.5` | Sortino `321776647.83` | Kelly `23.7%` | 30일 APR `148.2%` | Sharpe `6.61`
  - **Slow Stable**: Hurst `0.5` | Sortino `9111.08` | Kelly `21.4%` | 30일 APR `22.29%` | Sharpe `8.42`
  - **Hindenburg Short Alpha**: Hurst `0.701` | Sortino `44.8` | Kelly `18.8%` | 30일 APR `437.03%` | Sharpe `7.12`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-11 23:39:20
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-11)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[Bee] Line**: Hurst `0.5` | Sortino `215496067.83` | Kelly `30.0%` | 30일 APR `131.24%` | Sharpe `10.2`
  - **Algo1**: Hurst `0.5` | Sortino `296127980.31` | Kelly `23.9%` | 30일 APR `147.43%` | Sharpe `6.18`
  - **Slow Stable**: Hurst `0.5` | Sortino `62.56` | Kelly `19.3%` | 30일 APR `22.27%` | Sharpe `8.47`
  - **Hindenburg Short Alpha**: Hurst `0.701` | Sortino `44.8` | Kelly `18.8%` | 30일 APR `402.72%` | Sharpe `7.1`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-11 19:39:20
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-11)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[Bee] Line**: Hurst `0.5` | Sortino `215496067.83` | Kelly `30.0%` | 30일 APR `131.24%` | Sharpe `10.2`
  - **Algo1**: Hurst `0.5` | Sortino `296127980.31` | Kelly `23.9%` | 30일 APR `147.43%` | Sharpe `6.18`
  - **Slow Stable**: Hurst `0.5` | Sortino `62.56` | Kelly `19.3%` | 30일 APR `22.27%` | Sharpe `8.47`
  - **Hindenburg Short Alpha**: Hurst `0.701` | Sortino `44.8` | Kelly `18.8%` | 30일 APR `402.72%` | Sharpe `7.1`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---
