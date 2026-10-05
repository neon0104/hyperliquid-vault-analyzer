# 🧠 Hyperliquid Vault AI 자율 연구 및 지속 학습 일지 (Research Diary)

> 이 문서는 AI 퀀트 연구원이 매 시간 GitHub 오픈소스 퀀트 리서치, 수학적 모델, 온체인 시계열 데이터를 자율 학습하고 검증한 누적 연구 일지입니다.

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

## 📅 연구 기록: 2026-10-05 07:39:19
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

## 📅 연구 기록: 2026-10-05 03:41:57
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

## 📅 연구 기록: 2026-10-04 23:39:24
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-04)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `397271366.61` | Kelly `26.5%` | 30일 APR `10.95%` | Sharpe `9.53`
  - **Slow Stable**: Hurst `0.5` | Sortino `317035335.27` | Kelly `25.7%` | 30일 APR `18.22%` | Sharpe `8.25`
  - **⚛️ Quantum Capital OFFICIAL Algo Vault ⚛**: Hurst `0.5` | Sortino `160953544.39` | Kelly `16.0%` | 30일 APR `35.94%` | Sharpe `4.7`
  - **Queen [Bee]**: Hurst `0.5` | Sortino `50.13` | Kelly `15.1%` | 30일 APR `13.35%` | Sharpe `5.27`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-04 19:39:23
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-04)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `397271366.61` | Kelly `26.5%` | 30일 APR `10.95%` | Sharpe `9.53`
  - **Slow Stable**: Hurst `0.5` | Sortino `317035335.27` | Kelly `25.7%` | 30일 APR `18.22%` | Sharpe `8.25`
  - **⚛️ Quantum Capital OFFICIAL Algo Vault ⚛**: Hurst `0.5` | Sortino `160953544.39` | Kelly `16.0%` | 30일 APR `35.94%` | Sharpe `4.7`
  - **Queen [Bee]**: Hurst `0.5` | Sortino `50.13` | Kelly `15.1%` | 30일 APR `13.35%` | Sharpe `5.27`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-04 15:39:19
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-04)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `397271366.61` | Kelly `26.5%` | 30일 APR `10.95%` | Sharpe `9.53`
  - **Slow Stable**: Hurst `0.5` | Sortino `317035335.27` | Kelly `25.7%` | 30일 APR `18.22%` | Sharpe `8.25`
  - **⚛️ Quantum Capital OFFICIAL Algo Vault ⚛**: Hurst `0.5` | Sortino `160953544.39` | Kelly `16.0%` | 30일 APR `35.94%` | Sharpe `4.7`
  - **Queen [Bee]**: Hurst `0.5` | Sortino `50.13` | Kelly `15.1%` | 30일 APR `13.35%` | Sharpe `5.27`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-04 11:39:25
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-04)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `397271366.61` | Kelly `26.5%` | 30일 APR `10.95%` | Sharpe `9.53`
  - **Slow Stable**: Hurst `0.5` | Sortino `317035335.27` | Kelly `25.7%` | 30일 APR `18.22%` | Sharpe `8.25`
  - **⚛️ Quantum Capital OFFICIAL Algo Vault ⚛**: Hurst `0.5` | Sortino `160953544.39` | Kelly `16.0%` | 30일 APR `35.94%` | Sharpe `4.7`
  - **Queen [Bee]**: Hurst `0.5` | Sortino `50.13` | Kelly `15.1%` | 30일 APR `13.35%` | Sharpe `5.27`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-04 07:39:19
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-04)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `397271366.61` | Kelly `26.5%` | 30일 APR `10.95%` | Sharpe `9.53`
  - **Slow Stable**: Hurst `0.5` | Sortino `317035335.27` | Kelly `25.7%` | 30일 APR `18.22%` | Sharpe `8.25`
  - **⚛️ Quantum Capital OFFICIAL Algo Vault ⚛**: Hurst `0.5` | Sortino `160953544.39` | Kelly `16.0%` | 30일 APR `35.94%` | Sharpe `4.7`
  - **Queen [Bee]**: Hurst `0.5` | Sortino `50.13` | Kelly `15.1%` | 30일 APR `13.35%` | Sharpe `5.27`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-04 03:41:42
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-04)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `397271366.61` | Kelly `26.5%` | 30일 APR `10.95%` | Sharpe `9.53`
  - **Slow Stable**: Hurst `0.5` | Sortino `317035335.27` | Kelly `25.7%` | 30일 APR `18.22%` | Sharpe `8.25`
  - **⚛️ Quantum Capital OFFICIAL Algo Vault ⚛**: Hurst `0.5` | Sortino `160953544.39` | Kelly `16.0%` | 30일 APR `35.94%` | Sharpe `4.7`
  - **Queen [Bee]**: Hurst `0.5` | Sortino `50.13` | Kelly `15.1%` | 30일 APR `13.35%` | Sharpe `5.27`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-03 23:39:29
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-03)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `305521636.41` | Kelly `24.0%` | 30일 APR `10.95%` | Sharpe `5.93`
  - **Slow Stable**: Hurst `0.5` | Sortino `312.86` | Kelly `21.7%` | 30일 APR `18.69%` | Sharpe `7.95`
  - **⚛️ Quantum Capital OFFICIAL Algo Vault ⚛**: Hurst `0.5` | Sortino `159976610.34` | Kelly `16.0%` | 30일 APR `34.95%` | Sharpe `4.67`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `588.85%` | Sharpe `4.19`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-03 19:39:24
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-03)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `305521636.41` | Kelly `24.0%` | 30일 APR `10.95%` | Sharpe `5.93`
  - **Slow Stable**: Hurst `0.5` | Sortino `312.86` | Kelly `21.7%` | 30일 APR `18.69%` | Sharpe `7.95`
  - **⚛️ Quantum Capital OFFICIAL Algo Vault ⚛**: Hurst `0.5` | Sortino `159976610.34` | Kelly `16.0%` | 30일 APR `34.95%` | Sharpe `4.67`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `588.85%` | Sharpe `4.19`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-03 15:39:17
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-03)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `305521636.41` | Kelly `24.0%` | 30일 APR `10.95%` | Sharpe `5.93`
  - **Slow Stable**: Hurst `0.5` | Sortino `312.86` | Kelly `21.7%` | 30일 APR `18.69%` | Sharpe `7.95`
  - **⚛️ Quantum Capital OFFICIAL Algo Vault ⚛**: Hurst `0.5` | Sortino `159976610.34` | Kelly `16.0%` | 30일 APR `34.95%` | Sharpe `4.67`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `588.85%` | Sharpe `4.19`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-03 11:39:26
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-03)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `305521636.41` | Kelly `24.0%` | 30일 APR `10.95%` | Sharpe `5.93`
  - **Slow Stable**: Hurst `0.5` | Sortino `312.86` | Kelly `21.7%` | 30일 APR `18.69%` | Sharpe `7.95`
  - **⚛️ Quantum Capital OFFICIAL Algo Vault ⚛**: Hurst `0.5` | Sortino `159976610.34` | Kelly `16.0%` | 30일 APR `34.95%` | Sharpe `4.67`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `588.85%` | Sharpe `4.19`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-03 07:39:18
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-03)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `305521636.41` | Kelly `24.0%` | 30일 APR `10.95%` | Sharpe `5.93`
  - **Slow Stable**: Hurst `0.5` | Sortino `312.86` | Kelly `21.7%` | 30일 APR `18.69%` | Sharpe `7.95`
  - **⚛️ Quantum Capital OFFICIAL Algo Vault ⚛**: Hurst `0.5` | Sortino `159976610.34` | Kelly `16.0%` | 30일 APR `34.95%` | Sharpe `4.67`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `588.85%` | Sharpe `4.19`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---
