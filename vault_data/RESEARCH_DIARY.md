# 🧠 Hyperliquid Vault AI 자율 연구 및 지속 학습 일지 (Research Diary)

> 이 문서는 AI 퀀트 연구원이 매 시간 GitHub 오픈소스 퀀트 리서치, 수학적 모델, 온체인 시계열 데이터를 자율 학습하고 검증한 누적 연구 일지입니다.

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

## 📅 연구 기록: 2026-09-23 19:39:20
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

## 📅 연구 기록: 2026-09-23 15:39:17
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

## 📅 연구 기록: 2026-09-23 11:39:23
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

## 📅 연구 기록: 2026-09-23 07:39:18
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-23)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `20.7` | Kelly `21.6%` | 30일 APR `112.54%` | Sharpe `6.37`
  - **Aaroh**: Hurst `0.5` | Sortino `37.76` | Kelly `17.1%` | 30일 APR `339.92%` | Sharpe `9.08`
  - **Probot 2/7/15**: Hurst `0.647` | Sortino `37.69` | Kelly `17.0%` | 30일 APR `640.33%` | Sharpe `3.79`
  - **Lemontrding **: Hurst `0.5` | Sortino `59.05` | Kelly `16.2%` | 30일 APR `380.03%` | Sharpe `8.23`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-23 03:41:44
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-23)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `20.7` | Kelly `21.6%` | 30일 APR `112.54%` | Sharpe `6.37`
  - **Aaroh**: Hurst `0.5` | Sortino `37.76` | Kelly `17.1%` | 30일 APR `339.92%` | Sharpe `9.08`
  - **Probot 2/7/15**: Hurst `0.647` | Sortino `37.69` | Kelly `17.0%` | 30일 APR `640.33%` | Sharpe `3.79`
  - **Lemontrding **: Hurst `0.5` | Sortino `59.05` | Kelly `16.2%` | 30일 APR `380.03%` | Sharpe `8.23`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-22 23:39:23
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-22)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Compounder Lab**: Hurst `0.5` | Sortino `976.94` | Kelly `20.7%` | 30일 APR `16.45%` | Sharpe `6.83`
  - **V3 momentum**: Hurst `0.5` | Sortino `37.6` | Kelly `18.5%` | 30일 APR `35.03%` | Sharpe `10.07`
  - **Probot 2/7/15**: Hurst `0.647` | Sortino `37.69` | Kelly `17.0%` | 30일 APR `674.52%` | Sharpe `3.72`
  - **Lemontrding **: Hurst `0.5` | Sortino `58.87` | Kelly `16.2%` | 30일 APR `360.07%` | Sharpe `8.16`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-22 19:39:23
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-22)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Compounder Lab**: Hurst `0.5` | Sortino `976.94` | Kelly `20.7%` | 30일 APR `16.45%` | Sharpe `6.83`
  - **V3 momentum**: Hurst `0.5` | Sortino `37.6` | Kelly `18.5%` | 30일 APR `35.03%` | Sharpe `10.07`
  - **Probot 2/7/15**: Hurst `0.647` | Sortino `37.69` | Kelly `17.0%` | 30일 APR `674.52%` | Sharpe `3.72`
  - **Lemontrding **: Hurst `0.5` | Sortino `58.87` | Kelly `16.2%` | 30일 APR `360.07%` | Sharpe `8.16`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-22 15:39:24
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-22)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Compounder Lab**: Hurst `0.5` | Sortino `976.94` | Kelly `20.7%` | 30일 APR `16.45%` | Sharpe `6.83`
  - **V3 momentum**: Hurst `0.5` | Sortino `37.6` | Kelly `18.5%` | 30일 APR `35.03%` | Sharpe `10.07`
  - **Probot 2/7/15**: Hurst `0.647` | Sortino `37.69` | Kelly `17.0%` | 30일 APR `674.52%` | Sharpe `3.72`
  - **Lemontrding **: Hurst `0.5` | Sortino `58.87` | Kelly `16.2%` | 30일 APR `360.07%` | Sharpe `8.16`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-22 11:39:22
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-22)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Compounder Lab**: Hurst `0.5` | Sortino `976.94` | Kelly `20.7%` | 30일 APR `16.45%` | Sharpe `6.83`
  - **V3 momentum**: Hurst `0.5` | Sortino `37.6` | Kelly `18.5%` | 30일 APR `35.03%` | Sharpe `10.07`
  - **Probot 2/7/15**: Hurst `0.647` | Sortino `37.69` | Kelly `17.0%` | 30일 APR `674.52%` | Sharpe `3.72`
  - **Lemontrding **: Hurst `0.5` | Sortino `58.87` | Kelly `16.2%` | 30일 APR `360.07%` | Sharpe `8.16`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-22 07:39:16
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-22)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Compounder Lab**: Hurst `0.5` | Sortino `976.94` | Kelly `20.7%` | 30일 APR `16.45%` | Sharpe `6.83`
  - **V3 momentum**: Hurst `0.5` | Sortino `37.6` | Kelly `18.5%` | 30일 APR `35.03%` | Sharpe `10.07`
  - **Lemontrding **: Hurst `0.5` | Sortino `58.87` | Kelly `16.2%` | 30일 APR `360.07%` | Sharpe `8.16`
  - **Probot 2/7/15**: Hurst `0.635` | Sortino `36.62` | Kelly `16.2%` | 30일 APR `674.52%` | Sharpe `3.72`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-22 03:41:53
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-22)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Compounder Lab**: Hurst `0.5` | Sortino `976.94` | Kelly `20.7%` | 30일 APR `16.45%` | Sharpe `6.83`
  - **V3 momentum**: Hurst `0.5` | Sortino `37.6` | Kelly `18.5%` | 30일 APR `35.03%` | Sharpe `10.07`
  - **Lemontrding **: Hurst `0.5` | Sortino `58.87` | Kelly `16.2%` | 30일 APR `360.07%` | Sharpe `8.16`
  - **Probot 2/7/15**: Hurst `0.635` | Sortino `36.62` | Kelly `16.2%` | 30일 APR `674.52%` | Sharpe `3.72`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---
