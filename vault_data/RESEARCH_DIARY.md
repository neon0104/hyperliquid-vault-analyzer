# 🧠 Hyperliquid Vault AI 자율 연구 및 지속 학습 일지 (Research Diary)

> 이 문서는 AI 퀀트 연구원이 매 시간 GitHub 오픈소스 퀀트 리서치, 수학적 모델, 온체인 시계열 데이터를 자율 학습하고 검증한 누적 연구 일지입니다.

---

## 📅 연구 기록: 2026-09-26 07:39:19
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-26)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `19.37` | Kelly `22.0%` | 30일 APR `11.48%` | Sharpe `5.92`
  - **Aaroh**: Hurst `0.5` | Sortino `31.1` | Kelly `21.0%` | 30일 APR `153.58%` | Sharpe `11.79`
  - **Slow Stable**: Hurst `0.5` | Sortino `35.34` | Kelly `19.8%` | 30일 APR `36.63%` | Sharpe `7.83`
  - **⚛️ Quantum Capital OFFICIAL Algo Vault ⚛**: Hurst `0.5` | Sortino `152026820.94` | Kelly `15.6%` | 30일 APR `38.26%` | Sharpe `4.46`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-26 03:42:06
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-26)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `19.37` | Kelly `22.0%` | 30일 APR `11.48%` | Sharpe `5.92`
  - **Aaroh**: Hurst `0.5` | Sortino `31.1` | Kelly `21.0%` | 30일 APR `153.58%` | Sharpe `11.79`
  - **Slow Stable**: Hurst `0.5` | Sortino `35.34` | Kelly `19.8%` | 30일 APR `36.63%` | Sharpe `7.83`
  - **⚛️ Quantum Capital OFFICIAL Algo Vault ⚛**: Hurst `0.5` | Sortino `152026820.94` | Kelly `15.6%` | 30일 APR `38.26%` | Sharpe `4.46`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-25 23:39:24
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-25)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Slow Stable**: Hurst `0.5` | Sortino `316725215.58` | Kelly `25.7%` | 30일 APR `42.47%` | Sharpe `8.27`
  - **Algo1**: Hurst `0.5` | Sortino `20.52` | Kelly `21.8%` | 30일 APR `11.79%` | Sharpe `5.93`
  - **Aaroh**: Hurst `0.5` | Sortino `31.2` | Kelly `21.0%` | 30일 APR `153.85%` | Sharpe `11.82`
  - **⚛️ Quantum Capital OFFICIAL Algo Vault ⚛**: Hurst `0.5` | Sortino `151440602.2` | Kelly `15.6%` | 30일 APR `39.49%` | Sharpe `4.44`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-25 19:39:23
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-25)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Slow Stable**: Hurst `0.5` | Sortino `316725215.58` | Kelly `25.7%` | 30일 APR `42.47%` | Sharpe `8.27`
  - **Algo1**: Hurst `0.5` | Sortino `20.52` | Kelly `21.8%` | 30일 APR `11.79%` | Sharpe `5.93`
  - **Aaroh**: Hurst `0.5` | Sortino `31.2` | Kelly `21.0%` | 30일 APR `153.85%` | Sharpe `11.82`
  - **⚛️ Quantum Capital OFFICIAL Algo Vault ⚛**: Hurst `0.5` | Sortino `151440602.2` | Kelly `15.6%` | 30일 APR `39.49%` | Sharpe `4.44`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-25 15:39:18
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-25)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Slow Stable**: Hurst `0.5` | Sortino `316725215.58` | Kelly `25.7%` | 30일 APR `42.47%` | Sharpe `8.27`
  - **Algo1**: Hurst `0.5` | Sortino `20.52` | Kelly `21.8%` | 30일 APR `11.79%` | Sharpe `5.93`
  - **Aaroh**: Hurst `0.5` | Sortino `31.2` | Kelly `21.0%` | 30일 APR `153.85%` | Sharpe `11.82`
  - **⚛️ Quantum Capital OFFICIAL Algo Vault ⚛**: Hurst `0.5` | Sortino `151440602.2` | Kelly `15.6%` | 30일 APR `39.49%` | Sharpe `4.44`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-25 11:39:31
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-25)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Slow Stable**: Hurst `0.5` | Sortino `316725215.58` | Kelly `25.7%` | 30일 APR `42.47%` | Sharpe `8.27`
  - **Algo1**: Hurst `0.5` | Sortino `20.52` | Kelly `21.8%` | 30일 APR `11.79%` | Sharpe `5.93`
  - **Aaroh**: Hurst `0.5` | Sortino `31.2` | Kelly `21.0%` | 30일 APR `153.85%` | Sharpe `11.82`
  - **⚛️ Quantum Capital OFFICIAL Algo Vault ⚛**: Hurst `0.5` | Sortino `151440602.2` | Kelly `15.6%` | 30일 APR `39.49%` | Sharpe `4.44`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-25 07:39:25
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-25)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Slow Stable**: Hurst `0.5` | Sortino `316725215.58` | Kelly `25.7%` | 30일 APR `42.47%` | Sharpe `8.27`
  - **Algo1**: Hurst `0.5` | Sortino `20.52` | Kelly `21.8%` | 30일 APR `11.79%` | Sharpe `5.93`
  - **Aaroh**: Hurst `0.5` | Sortino `31.2` | Kelly `21.0%` | 30일 APR `153.85%` | Sharpe `11.82`
  - **⚛️ Quantum Capital OFFICIAL Algo Vault ⚛**: Hurst `0.5` | Sortino `151440602.2` | Kelly `15.6%` | 30일 APR `39.49%` | Sharpe `4.44`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-25 03:41:51
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-25)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Slow Stable**: Hurst `0.5` | Sortino `316725215.58` | Kelly `25.7%` | 30일 APR `42.47%` | Sharpe `8.27`
  - **Algo1**: Hurst `0.5` | Sortino `20.52` | Kelly `21.8%` | 30일 APR `11.79%` | Sharpe `5.93`
  - **Aaroh**: Hurst `0.5` | Sortino `31.2` | Kelly `21.0%` | 30일 APR `153.85%` | Sharpe `11.82`
  - **⚛️ Quantum Capital OFFICIAL Algo Vault ⚛**: Hurst `0.5` | Sortino `151440602.2` | Kelly `15.6%` | 30일 APR `39.49%` | Sharpe `4.44`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-24 23:39:23
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-24)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `304669448.42` | Kelly `24.0%` | 30일 APR `11.54%` | Sharpe `6.67`
  - **Aaroh**: Hurst `0.5` | Sortino `29.62` | Kelly `20.8%` | 30일 APR `129.85%` | Sharpe `11.57`
  - **Momentum Edge**: Hurst `0.5` | Sortino `58.48` | Kelly `15.2%` | 30일 APR `46.05%` | Sharpe `8.53`
  - **wmm.club | scalp-hype-long-2x**: Hurst `0.5` | Sortino `31.85` | Kelly `14.8%` | 30일 APR `46.5%` | Sharpe `6.98`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-24 19:39:21
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-24)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `304669448.42` | Kelly `24.0%` | 30일 APR `11.54%` | Sharpe `6.67`
  - **Aaroh**: Hurst `0.5` | Sortino `29.62` | Kelly `20.8%` | 30일 APR `129.85%` | Sharpe `11.57`
  - **Momentum Edge**: Hurst `0.5` | Sortino `58.48` | Kelly `15.2%` | 30일 APR `46.05%` | Sharpe `8.53`
  - **wmm.club | scalp-hype-long-2x**: Hurst `0.5` | Sortino `31.85` | Kelly `14.8%` | 30일 APR `46.5%` | Sharpe `6.98`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-24 15:39:18
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-24)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `304669448.42` | Kelly `24.0%` | 30일 APR `11.54%` | Sharpe `6.67`
  - **Aaroh**: Hurst `0.5` | Sortino `29.62` | Kelly `20.8%` | 30일 APR `129.85%` | Sharpe `11.57`
  - **Momentum Edge**: Hurst `0.5` | Sortino `58.48` | Kelly `15.2%` | 30일 APR `46.05%` | Sharpe `8.53`
  - **wmm.club | scalp-hype-long-2x**: Hurst `0.5` | Sortino `31.85` | Kelly `14.8%` | 30일 APR `46.5%` | Sharpe `6.98`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-24 11:39:31
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-24)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `304669448.42` | Kelly `24.0%` | 30일 APR `11.54%` | Sharpe `6.67`
  - **Aaroh**: Hurst `0.5` | Sortino `29.62` | Kelly `20.8%` | 30일 APR `129.85%` | Sharpe `11.57`
  - **Momentum Edge**: Hurst `0.5` | Sortino `58.48` | Kelly `15.2%` | 30일 APR `46.05%` | Sharpe `8.53`
  - **wmm.club | scalp-hype-long-2x**: Hurst `0.5` | Sortino `31.85` | Kelly `14.8%` | 30일 APR `46.5%` | Sharpe `6.98`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-24 07:39:19
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-24)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `304669448.42` | Kelly `24.0%` | 30일 APR `11.54%` | Sharpe `6.67`
  - **Aaroh**: Hurst `0.5` | Sortino `29.62` | Kelly `20.8%` | 30일 APR `129.85%` | Sharpe `11.57`
  - **Mahamor**: Hurst `0.723` | Sortino `45.1` | Kelly `16.0%` | 30일 APR `372.03%` | Sharpe `4.37`
  - **Probot 2/7/15**: Hurst `0.577` | Sortino `37.16` | Kelly `15.7%` | 30일 APR `615.58%` | Sharpe `3.09`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-24 03:42:03
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-24)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `304669448.42` | Kelly `24.0%` | 30일 APR `11.54%` | Sharpe `6.67`
  - **Aaroh**: Hurst `0.5` | Sortino `29.62` | Kelly `20.8%` | 30일 APR `129.85%` | Sharpe `11.57`
  - **Mahamor**: Hurst `0.723` | Sortino `45.1` | Kelly `16.0%` | 30일 APR `372.03%` | Sharpe `4.37`
  - **Probot 2/7/15**: Hurst `0.577` | Sortino `37.16` | Kelly `15.7%` | 30일 APR `615.58%` | Sharpe `3.09`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-23 23:39:22
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-23)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `20.7` | Kelly `21.6%` | 30일 APR `112.54%` | Sharpe `6.37`
  - **Aaroh**: Hurst `0.5` | Sortino `37.76` | Kelly `17.1%` | 30일 APR `339.92%` | Sharpe `9.08`
  - **Lemontrding **: Hurst `0.5` | Sortino `59.05` | Kelly `16.2%` | 30일 APR `380.03%` | Sharpe `8.23`
  - **Mahamor**: Hurst `0.723` | Sortino `45.1` | Kelly `16.0%` | 30일 APR `461.52%` | Sharpe `4.63`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---
