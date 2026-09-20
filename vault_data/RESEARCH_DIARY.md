# 🧠 Hyperliquid Vault AI 자율 연구 및 지속 학습 일지 (Research Diary)

> 이 문서는 AI 퀀트 연구원이 매 시간 GitHub 오픈소스 퀀트 리서치, 수학적 모델, 온체인 시계열 데이터를 자율 학습하고 검증한 누적 연구 일지입니다.

---

## 📅 연구 기록: 2026-09-20 15:39:24
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-20)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Aaroh**: Hurst `0.5` | Sortino `56.19` | Kelly `18.8%` | 30일 APR `458.59%` | Sharpe `9.13`
  - **V3 momentum**: Hurst `0.5` | Sortino `35.2` | Kelly `18.5%` | 30일 APR `61.51%` | Sharpe `9.83`
  - **Apex Strategy**: Hurst `0.5` | Sortino `21.44` | Kelly `16.2%` | 30일 APR `565.77%` | Sharpe `9.52`
  - **Momentum Edge**: Hurst `0.5` | Sortino `57.52` | Kelly `15.1%` | 30일 APR `27.6%` | Sharpe `8.43`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-20 11:39:24
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-20)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Aaroh**: Hurst `0.5` | Sortino `56.19` | Kelly `18.8%` | 30일 APR `458.59%` | Sharpe `9.13`
  - **V3 momentum**: Hurst `0.5` | Sortino `35.2` | Kelly `18.5%` | 30일 APR `61.51%` | Sharpe `9.83`
  - **Apex Strategy**: Hurst `0.5` | Sortino `21.44` | Kelly `16.2%` | 30일 APR `565.77%` | Sharpe `9.52`
  - **Momentum Edge**: Hurst `0.5` | Sortino `57.52` | Kelly `15.1%` | 30일 APR `27.6%` | Sharpe `8.43`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-20 07:39:18
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-20)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Aaroh**: Hurst `0.5` | Sortino `56.19` | Kelly `18.8%` | 30일 APR `458.59%` | Sharpe `9.13`
  - **V3 momentum**: Hurst `0.5` | Sortino `35.2` | Kelly `18.5%` | 30일 APR `61.51%` | Sharpe `9.83`
  - **Apex Strategy**: Hurst `0.5` | Sortino `21.44` | Kelly `16.2%` | 30일 APR `565.77%` | Sharpe `9.52`
  - **Momentum Edge**: Hurst `0.5` | Sortino `57.52` | Kelly `15.1%` | 30일 APR `27.6%` | Sharpe `8.43`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-20 03:42:04
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-20)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Aaroh**: Hurst `0.5` | Sortino `56.19` | Kelly `18.8%` | 30일 APR `458.59%` | Sharpe `9.13`
  - **V3 momentum**: Hurst `0.5` | Sortino `35.2` | Kelly `18.5%` | 30일 APR `61.51%` | Sharpe `9.83`
  - **Apex Strategy**: Hurst `0.5` | Sortino `21.44` | Kelly `16.2%` | 30일 APR `565.77%` | Sharpe `9.52`
  - **Momentum Edge**: Hurst `0.5` | Sortino `57.52` | Kelly `15.1%` | 30일 APR `27.6%` | Sharpe `8.43`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-19 23:39:20
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-19)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **V3 momentum**: Hurst `0.5` | Sortino `173715528.26` | Kelly `24.0%` | 30일 APR `81.52%` | Sharpe `11.46`
  - **Slow Stable**: Hurst `0.5` | Sortino `102.77` | Kelly `22.1%` | 30일 APR `22.62%` | Sharpe `8.58`
  - **Algo1**: Hurst `0.5` | Sortino `19.08` | Kelly `21.8%` | 30일 APR `147.89%` | Sharpe `6.2`
  - **Aaroh**: Hurst `0.5` | Sortino `33.4` | Kelly `16.6%` | 30일 APR `506.72%` | Sharpe `9.87`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-19 19:39:20
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-19)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **V3 momentum**: Hurst `0.5` | Sortino `173715528.26` | Kelly `24.0%` | 30일 APR `81.52%` | Sharpe `11.46`
  - **Slow Stable**: Hurst `0.5` | Sortino `102.77` | Kelly `22.1%` | 30일 APR `22.62%` | Sharpe `8.58`
  - **Algo1**: Hurst `0.5` | Sortino `19.08` | Kelly `21.8%` | 30일 APR `147.89%` | Sharpe `6.2`
  - **Aaroh**: Hurst `0.5` | Sortino `33.4` | Kelly `16.6%` | 30일 APR `506.72%` | Sharpe `9.87`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-19 15:39:21
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-19)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **V3 momentum**: Hurst `0.5` | Sortino `173715528.26` | Kelly `24.0%` | 30일 APR `81.52%` | Sharpe `11.46`
  - **Slow Stable**: Hurst `0.5` | Sortino `102.77` | Kelly `22.1%` | 30일 APR `22.62%` | Sharpe `8.58`
  - **Algo1**: Hurst `0.5` | Sortino `19.08` | Kelly `21.8%` | 30일 APR `147.89%` | Sharpe `6.2`
  - **Aaroh**: Hurst `0.5` | Sortino `33.4` | Kelly `16.6%` | 30일 APR `506.72%` | Sharpe `9.87`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-19 11:39:17
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-19)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **V3 momentum**: Hurst `0.5` | Sortino `173715528.26` | Kelly `24.0%` | 30일 APR `81.52%` | Sharpe `11.46`
  - **Slow Stable**: Hurst `0.5` | Sortino `102.77` | Kelly `22.1%` | 30일 APR `22.62%` | Sharpe `8.58`
  - **Algo1**: Hurst `0.5` | Sortino `19.08` | Kelly `21.8%` | 30일 APR `147.89%` | Sharpe `6.2`
  - **Aaroh**: Hurst `0.5` | Sortino `33.4` | Kelly `16.6%` | 30일 APR `506.72%` | Sharpe `9.87`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-19 07:39:16
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-19)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **V3 momentum**: Hurst `0.5` | Sortino `173715528.26` | Kelly `24.0%` | 30일 APR `81.52%` | Sharpe `11.46`
  - **Slow Stable**: Hurst `0.5` | Sortino `102.77` | Kelly `22.1%` | 30일 APR `22.62%` | Sharpe `8.58`
  - **Algo1**: Hurst `0.5` | Sortino `19.08` | Kelly `21.8%` | 30일 APR `147.89%` | Sharpe `6.2`
  - **Aaroh**: Hurst `0.5` | Sortino `33.4` | Kelly `16.6%` | 30일 APR `506.72%` | Sharpe `9.87`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-19 03:41:52
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-19)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **V3 momentum**: Hurst `0.5` | Sortino `173715528.26` | Kelly `24.0%` | 30일 APR `81.52%` | Sharpe `11.46`
  - **Slow Stable**: Hurst `0.5` | Sortino `102.77` | Kelly `22.1%` | 30일 APR `22.62%` | Sharpe `8.58`
  - **Algo1**: Hurst `0.5` | Sortino `19.08` | Kelly `21.8%` | 30일 APR `147.89%` | Sharpe `6.2`
  - **Aaroh**: Hurst `0.5` | Sortino `33.4` | Kelly `16.6%` | 30일 APR `506.72%` | Sharpe `9.87`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-18 23:39:22
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-18)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Slow Stable**: Hurst `0.5` | Sortino `51.19` | Kelly `22.8%` | 30일 APR `22.72%` | Sharpe `8.69`
  - **Algo1**: Hurst `0.5` | Sortino `18.68` | Kelly `21.9%` | 30일 APR `148.74%` | Sharpe `6.23`
  - **V3 momentum**: Hurst `0.5` | Sortino `43.46` | Kelly `20.1%` | 30일 APR `69.64%` | Sharpe `7.97`
  - **Momentum Edge**: Hurst `0.5` | Sortino `51.61` | Kelly `15.6%` | 30일 APR `45.79%` | Sharpe `9.0`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-18 19:39:21
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-18)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Slow Stable**: Hurst `0.5` | Sortino `51.19` | Kelly `22.8%` | 30일 APR `22.72%` | Sharpe `8.69`
  - **Algo1**: Hurst `0.5` | Sortino `18.68` | Kelly `21.9%` | 30일 APR `148.74%` | Sharpe `6.23`
  - **V3 momentum**: Hurst `0.5` | Sortino `43.46` | Kelly `20.1%` | 30일 APR `69.64%` | Sharpe `7.97`
  - **Momentum Edge**: Hurst `0.5` | Sortino `51.61` | Kelly `15.6%` | 30일 APR `45.79%` | Sharpe `9.0`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-18 15:39:21
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-18)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Slow Stable**: Hurst `0.5` | Sortino `51.19` | Kelly `22.8%` | 30일 APR `22.72%` | Sharpe `8.69`
  - **Algo1**: Hurst `0.5` | Sortino `18.68` | Kelly `21.9%` | 30일 APR `148.74%` | Sharpe `6.23`
  - **V3 momentum**: Hurst `0.5` | Sortino `43.46` | Kelly `20.1%` | 30일 APR `69.64%` | Sharpe `7.97`
  - **Momentum Edge**: Hurst `0.5` | Sortino `51.61` | Kelly `15.6%` | 30일 APR `45.79%` | Sharpe `9.0`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-18 11:39:18
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-18)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Slow Stable**: Hurst `0.5` | Sortino `51.19` | Kelly `22.8%` | 30일 APR `22.72%` | Sharpe `8.69`
  - **Algo1**: Hurst `0.5` | Sortino `18.68` | Kelly `21.9%` | 30일 APR `148.74%` | Sharpe `6.23`
  - **V3 momentum**: Hurst `0.5` | Sortino `43.46` | Kelly `20.1%` | 30일 APR `69.64%` | Sharpe `7.97`
  - **Momentum Edge**: Hurst `0.5` | Sortino `51.61` | Kelly `15.6%` | 30일 APR `45.79%` | Sharpe `9.0`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-18 07:39:18
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-18)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[Bee] Line**: Hurst `0.5` | Sortino `181866450.47` | Kelly `30.0%` | 30일 APR `112.32%` | Sharpe `14.83`
  - **Slow Stable**: Hurst `0.5` | Sortino `51.19` | Kelly `22.8%` | 30일 APR `22.72%` | Sharpe `8.69`
  - **Algo1**: Hurst `0.5` | Sortino `18.68` | Kelly `21.9%` | 30일 APR `148.74%` | Sharpe `6.23`
  - **V3 momentum**: Hurst `0.5` | Sortino `43.46` | Kelly `20.1%` | 30일 APR `69.64%` | Sharpe `7.97`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---
