# 🧠 Hyperliquid Vault AI 자율 연구 및 지속 학습 일지 (Research Diary)

> 이 문서는 AI 퀀트 연구원이 매 시간 GitHub 오픈소스 퀀트 리서치, 수학적 모델, 온체인 시계열 데이터를 자율 학습하고 검증한 누적 연구 일지입니다.

---

## 📅 연구 기록: 2026-10-14 11:39:24
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-14)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Hyper2**: Hurst `0.5` | Sortino `289759026.4` | Kelly `27.4%` | 30일 APR `2.8%` | Sharpe `8.44`
  - **Algo1**: Hurst `0.5` | Sortino `363392998.07` | Kelly `27.3%` | 30일 APR `10.88%` | Sharpe `8.96`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `414.34%` | Sharpe `3.51`
  - **HighFDV**: Hurst `0.5` | Sortino `8.73` | Kelly `13.3%` | 30일 APR `209.84%` | Sharpe `6.97`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-14 07:39:23
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-14)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Hyper2**: Hurst `0.5` | Sortino `289759026.4` | Kelly `27.4%` | 30일 APR `2.8%` | Sharpe `8.44`
  - **Algo1**: Hurst `0.5` | Sortino `363392998.07` | Kelly `27.3%` | 30일 APR `10.88%` | Sharpe `8.96`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `414.34%` | Sharpe `3.51`
  - **HighFDV**: Hurst `0.5` | Sortino `8.73` | Kelly `13.3%` | 30일 APR `209.84%` | Sharpe `6.97`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-14 03:42:10
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-14)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Hyper2**: Hurst `0.5` | Sortino `289759026.4` | Kelly `27.4%` | 30일 APR `2.8%` | Sharpe `8.44`
  - **Algo1**: Hurst `0.5` | Sortino `363392998.07` | Kelly `27.3%` | 30일 APR `10.88%` | Sharpe `8.96`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `414.34%` | Sharpe `3.51`
  - **HighFDV**: Hurst `0.5` | Sortino `8.73` | Kelly `13.3%` | 30일 APR `209.84%` | Sharpe `6.97`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-13 23:39:26
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-13)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `399203369.54` | Kelly `27.0%` | 30일 APR `10.51%` | Sharpe `9.55`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `392.45%` | Sharpe `3.6`
  - **Momentum Edge**: Hurst `0.5` | Sortino `49.16` | Kelly `13.2%` | 30일 APR `1.81%` | Sharpe `7.39`
  - **Gucky_4coin_2dot5x**: Hurst `0.36` | Sortino `79.37` | Kelly `13.2%` | 30일 APR `33.76%` | Sharpe `0.87`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-13 19:39:26
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-13)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `399203369.54` | Kelly `27.0%` | 30일 APR `10.51%` | Sharpe `9.55`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `392.45%` | Sharpe `3.6`
  - **Momentum Edge**: Hurst `0.5` | Sortino `49.16` | Kelly `13.2%` | 30일 APR `1.81%` | Sharpe `7.39`
  - **Gucky_4coin_2dot5x**: Hurst `0.36` | Sortino `79.37` | Kelly `13.2%` | 30일 APR `33.76%` | Sharpe `0.87`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-13 15:39:31
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-13)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `399203369.54` | Kelly `27.0%` | 30일 APR `10.51%` | Sharpe `9.55`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `392.45%` | Sharpe `3.6`
  - **Momentum Edge**: Hurst `0.5` | Sortino `49.16` | Kelly `13.2%` | 30일 APR `1.81%` | Sharpe `7.39`
  - **Gucky_4coin_2dot5x**: Hurst `0.36` | Sortino `79.37` | Kelly `13.2%` | 30일 APR `33.76%` | Sharpe `0.87`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-13 11:39:28
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-13)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `399203369.54` | Kelly `27.0%` | 30일 APR `10.51%` | Sharpe `9.55`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `392.45%` | Sharpe `3.6`
  - **Momentum Edge**: Hurst `0.5` | Sortino `49.16` | Kelly `13.2%` | 30일 APR `1.81%` | Sharpe `7.39`
  - **Gucky_4coin_2dot5x**: Hurst `0.36` | Sortino `79.37` | Kelly `13.2%` | 30일 APR `33.76%` | Sharpe `0.87`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-13 07:39:21
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-13)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `399203369.54` | Kelly `27.0%` | 30일 APR `10.51%` | Sharpe `9.55`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `392.45%` | Sharpe `3.6`
  - **Guardian Alpha**: Hurst `0.9` | Sortino `61.59` | Kelly `13.8%` | 30일 APR `166.8%` | Sharpe `3.21`
  - **Momentum Edge**: Hurst `0.5` | Sortino `49.16` | Kelly `13.2%` | 30일 APR `1.81%` | Sharpe `7.39`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-13 03:41:59
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-13)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `399203369.54` | Kelly `27.0%` | 30일 APR `10.51%` | Sharpe `9.55`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `392.45%` | Sharpe `3.6`
  - **Guardian Alpha**: Hurst `0.9` | Sortino `61.59` | Kelly `13.8%` | 30일 APR `166.8%` | Sharpe `3.21`
  - **Momentum Edge**: Hurst `0.5` | Sortino `49.16` | Kelly `13.2%` | 30일 APR `1.81%` | Sharpe `7.39`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-12 23:39:29
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-12)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `398834560.22` | Kelly `27.0%` | 30일 APR `11.06%` | Sharpe `9.54`
  - **Slow Stable**: Hurst `0.5` | Sortino `317118403.43` | Kelly `25.7%` | 30일 APR `2.0%` | Sharpe `8.25`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `505.07%` | Sharpe `3.64`
  - **Guardian Alpha**: Hurst `0.9` | Sortino `61.59` | Kelly `13.8%` | 30일 APR `249.19%` | Sharpe `5.67`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-12 19:39:26
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-12)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `398834560.22` | Kelly `27.0%` | 30일 APR `11.06%` | Sharpe `9.54`
  - **Slow Stable**: Hurst `0.5` | Sortino `317118403.43` | Kelly `25.7%` | 30일 APR `2.0%` | Sharpe `8.25`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `505.07%` | Sharpe `3.64`
  - **Guardian Alpha**: Hurst `0.9` | Sortino `61.59` | Kelly `13.8%` | 30일 APR `249.19%` | Sharpe `5.67`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-12 15:39:30
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-12)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `398834560.22` | Kelly `27.0%` | 30일 APR `11.06%` | Sharpe `9.54`
  - **Slow Stable**: Hurst `0.5` | Sortino `317118403.43` | Kelly `25.7%` | 30일 APR `2.0%` | Sharpe `8.25`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `505.07%` | Sharpe `3.64`
  - **Guardian Alpha**: Hurst `0.9` | Sortino `61.59` | Kelly `13.8%` | 30일 APR `249.19%` | Sharpe `5.67`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-12 11:39:23
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-12)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `398834560.22` | Kelly `27.0%` | 30일 APR `11.06%` | Sharpe `9.54`
  - **Slow Stable**: Hurst `0.5` | Sortino `317118403.43` | Kelly `25.7%` | 30일 APR `2.0%` | Sharpe `8.25`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `505.07%` | Sharpe `3.64`
  - **Guardian Alpha**: Hurst `0.9` | Sortino `61.59` | Kelly `13.8%` | 30일 APR `249.19%` | Sharpe `5.67`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-12 07:39:19
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-12)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `398834560.22` | Kelly `27.0%` | 30일 APR `11.06%` | Sharpe `9.54`
  - **Slow Stable**: Hurst `0.5` | Sortino `317118403.43` | Kelly `25.7%` | 30일 APR `2.0%` | Sharpe `8.25`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `505.07%` | Sharpe `3.64`
  - **HighFDV**: Hurst `0.5` | Sortino `8.88` | Kelly `13.4%` | 30일 APR `214.64%` | Sharpe `7.04`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-10-12 03:41:55
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-10-12)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `398834560.22` | Kelly `27.0%` | 30일 APR `11.06%` | Sharpe `9.54`
  - **Slow Stable**: Hurst `0.5` | Sortino `317118403.43` | Kelly `25.7%` | 30일 APR `2.0%` | Sharpe `8.25`
  - **Mahamor**: Hurst `0.255` | Sortino `29.02` | Kelly `14.8%` | 30일 APR `505.07%` | Sharpe `3.64`
  - **HighFDV**: Hurst `0.5` | Sortino `8.88` | Kelly `13.4%` | 30일 APR `214.64%` | Sharpe `7.04`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---
