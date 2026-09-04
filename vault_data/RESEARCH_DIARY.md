# 🧠 Hyperliquid Vault AI 자율 연구 및 지속 학습 일지 (Research Diary)

> 이 문서는 AI 퀀트 연구원이 매 시간 GitHub 오픈소스 퀀트 리서치, 수학적 모델, 온체인 시계열 데이터를 자율 학습하고 검증한 누적 연구 일지입니다.

---

## 📅 연구 기록: 2026-09-05 03:41:50
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-05)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[Bee] Line**: Hurst `0.5` | Sortino `245548233.53` | Kelly `27.1%` | 30일 APR `140.79%` | Sharpe `12.35`
  - **Algo1**: Hurst `0.5` | Sortino `321159324.94` | Kelly `23.7%` | 30일 APR `147.62%` | Sharpe `6.73`
  - **Hindenburg Short Alpha**: Hurst `0.5` | Sortino `30.45` | Kelly `18.1%` | 30일 APR `420.4%` | Sharpe `7.41`
  - **HYPErQuantum4**: Hurst `0.636` | Sortino `14.11` | Kelly `17.7%` | 30일 APR `31.46%` | Sharpe `6.7`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-04 23:39:26
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-04)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[Bee] Line**: Hurst `0.5` | Sortino `225656834.34` | Kelly `27.1%` | 30일 APR `125.93%` | Sharpe `11.07`
  - **Algo1**: Hurst `0.5` | Sortino `19.98` | Kelly `21.6%` | 30일 APR `145.07%` | Sharpe `6.54`
  - **Hindenburg Short Alpha**: Hurst `0.5` | Sortino `30.91` | Kelly `18.2%` | 30일 APR `396.11%` | Sharpe `7.38`
  - **HYPErQuantum4**: Hurst `0.636` | Sortino `14.11` | Kelly `17.7%` | 30일 APR `31.7%` | Sharpe `6.7`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-04 19:39:24
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-04)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[Bee] Line**: Hurst `0.5` | Sortino `225656834.34` | Kelly `27.1%` | 30일 APR `125.93%` | Sharpe `11.07`
  - **Algo1**: Hurst `0.5` | Sortino `19.98` | Kelly `21.6%` | 30일 APR `145.07%` | Sharpe `6.54`
  - **Hindenburg Short Alpha**: Hurst `0.5` | Sortino `30.91` | Kelly `18.2%` | 30일 APR `396.11%` | Sharpe `7.38`
  - **HYPErQuantum4**: Hurst `0.636` | Sortino `14.11` | Kelly `17.7%` | 30일 APR `31.7%` | Sharpe `6.7`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-04 15:39:18
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-04)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[Bee] Line**: Hurst `0.5` | Sortino `225656834.34` | Kelly `27.1%` | 30일 APR `125.93%` | Sharpe `11.07`
  - **Algo1**: Hurst `0.5` | Sortino `19.98` | Kelly `21.6%` | 30일 APR `145.07%` | Sharpe `6.54`
  - **Hindenburg Short Alpha**: Hurst `0.5` | Sortino `30.91` | Kelly `18.2%` | 30일 APR `396.11%` | Sharpe `7.38`
  - **HYPErQuantum4**: Hurst `0.636` | Sortino `14.11` | Kelly `17.7%` | 30일 APR `31.7%` | Sharpe `6.7`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-04 11:39:25
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-04)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[Bee] Line**: Hurst `0.5` | Sortino `225656834.34` | Kelly `27.1%` | 30일 APR `125.93%` | Sharpe `11.07`
  - **Algo1**: Hurst `0.5` | Sortino `19.98` | Kelly `21.6%` | 30일 APR `145.07%` | Sharpe `6.54`
  - **Hindenburg Short Alpha**: Hurst `0.5` | Sortino `30.91` | Kelly `18.2%` | 30일 APR `396.11%` | Sharpe `7.38`
  - **HYPErQuantum4**: Hurst `0.636` | Sortino `14.11` | Kelly `17.7%` | 30일 APR `31.7%` | Sharpe `6.7`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-04 07:39:19
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-04)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[Bee] Line**: Hurst `0.5` | Sortino `225656834.34` | Kelly `27.1%` | 30일 APR `125.93%` | Sharpe `11.07`
  - **Algo1**: Hurst `0.5` | Sortino `19.98` | Kelly `21.6%` | 30일 APR `145.07%` | Sharpe `6.54`
  - **Hindenburg Short Alpha**: Hurst `0.5` | Sortino `30.91` | Kelly `18.2%` | 30일 APR `396.11%` | Sharpe `7.38`
  - **HYPErQuantum4**: Hurst `0.408` | Sortino `14.47` | Kelly `17.5%` | 30일 APR `31.7%` | Sharpe `6.7`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-04 03:42:00
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-04)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[Bee] Line**: Hurst `0.5` | Sortino `225656834.34` | Kelly `27.1%` | 30일 APR `125.93%` | Sharpe `11.07`
  - **Algo1**: Hurst `0.5` | Sortino `19.98` | Kelly `21.6%` | 30일 APR `145.07%` | Sharpe `6.54`
  - **Hindenburg Short Alpha**: Hurst `0.5` | Sortino `30.91` | Kelly `18.2%` | 30일 APR `396.11%` | Sharpe `7.38`
  - **HYPErQuantum4**: Hurst `0.408` | Sortino `14.47` | Kelly `17.5%` | 30일 APR `31.7%` | Sharpe `6.7`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-03 23:39:24
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-03)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `320408461.71` | Kelly `23.7%` | 30일 APR `147.09%` | Sharpe `6.55`
  - **Hindenburg Short Alpha**: Hurst `0.5` | Sortino `31.26` | Kelly `18.2%` | 30일 APR `397.66%` | Sharpe `7.36`
  - **HYPErQuantum4**: Hurst `0.408` | Sortino `14.47` | Kelly `17.5%` | 30일 APR `30.66%` | Sharpe `6.68`
  - **Lalo Capital**: Hurst `0.5` | Sortino `22.38` | Kelly `15.3%` | 30일 APR `554.46%` | Sharpe `7.51`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-03 19:39:37
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-03)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `320408461.71` | Kelly `23.7%` | 30일 APR `147.09%` | Sharpe `6.55`
  - **Hindenburg Short Alpha**: Hurst `0.5` | Sortino `31.26` | Kelly `18.2%` | 30일 APR `397.66%` | Sharpe `7.36`
  - **HYPErQuantum4**: Hurst `0.408` | Sortino `14.47` | Kelly `17.5%` | 30일 APR `30.66%` | Sharpe `6.68`
  - **Lalo Capital**: Hurst `0.5` | Sortino `22.38` | Kelly `15.3%` | 30일 APR `554.46%` | Sharpe `7.51`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-03 15:39:25
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-03)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `320408461.71` | Kelly `23.7%` | 30일 APR `147.09%` | Sharpe `6.55`
  - **Hindenburg Short Alpha**: Hurst `0.5` | Sortino `31.26` | Kelly `18.2%` | 30일 APR `397.66%` | Sharpe `7.36`
  - **HYPErQuantum4**: Hurst `0.408` | Sortino `14.47` | Kelly `17.5%` | 30일 APR `30.66%` | Sharpe `6.68`
  - **Lalo Capital**: Hurst `0.5` | Sortino `22.38` | Kelly `15.3%` | 30일 APR `554.46%` | Sharpe `7.51`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-03 11:39:24
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-03)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `320408461.71` | Kelly `23.7%` | 30일 APR `147.09%` | Sharpe `6.55`
  - **Hindenburg Short Alpha**: Hurst `0.5` | Sortino `31.26` | Kelly `18.2%` | 30일 APR `397.66%` | Sharpe `7.36`
  - **HYPErQuantum4**: Hurst `0.408` | Sortino `14.47` | Kelly `17.5%` | 30일 APR `30.66%` | Sharpe `6.68`
  - **Lalo Capital**: Hurst `0.5` | Sortino `22.38` | Kelly `15.3%` | 30일 APR `554.46%` | Sharpe `7.51`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-03 07:39:20
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-03)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `320408461.71` | Kelly `23.7%` | 30일 APR `147.09%` | Sharpe `6.55`
  - **Hindenburg Short Alpha**: Hurst `0.5` | Sortino `31.26` | Kelly `18.2%` | 30일 APR `397.66%` | Sharpe `7.36`
  - **HYPErQuantum4**: Hurst `0.443` | Sortino `14.88` | Kelly `17.3%` | 30일 APR `30.66%` | Sharpe `6.68`
  - **Lalo Capital**: Hurst `0.5` | Sortino `22.38` | Kelly `15.3%` | 30일 APR `554.46%` | Sharpe `7.51`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-03 03:41:43
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-03)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `320408461.71` | Kelly `23.7%` | 30일 APR `147.09%` | Sharpe `6.55`
  - **Hindenburg Short Alpha**: Hurst `0.5` | Sortino `31.26` | Kelly `18.2%` | 30일 APR `397.66%` | Sharpe `7.36`
  - **HYPErQuantum4**: Hurst `0.443` | Sortino `14.88` | Kelly `17.3%` | 30일 APR `30.66%` | Sharpe `6.68`
  - **Lalo Capital**: Hurst `0.5` | Sortino `22.38` | Kelly `15.3%` | 30일 APR `554.46%` | Sharpe `7.51`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-02 23:39:31
### 🔬 주제: **하방 편차(Downside Deviation) 기반 Sortino Ratio 최적화**
* **레퍼런스 출처**: `GitHub: Riskfolio-Lib / Frank Sortino (1994)`
* **수학적 모델**: $Sortino = \frac{R_p - R_f}{\sqrt{\frac{1}{N}\sum_{t=1}^N \min(0, R_t - MAR)^2}}$
* **핵심 가설**: 상승 변동성은 수익 기회이므로 페널티를 주지 않고, 오직 '손실 변동성'만을 측정하는 Sortino Ratio로 볼트 위험도를 재평가하여 불필요한 저수익 배분을 제거함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-02)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Algo1**: Hurst `0.5` | Sortino `320298787.09` | Kelly `23.7%` | 30일 APR `147.0%` | Sharpe `5.97`
  - **137S IF Long I**: Hurst `0.569` | Sortino `1960101.87` | Kelly `0.3%` | 30일 APR `11.57%` | Sharpe `3.45`
  - **YEELON**: Hurst `0.1` | Sortino `338707.89` | Kelly `3.4%` | 30일 APR `0.0%` | Sharpe `5.32`
  - **AJ Pro**: Hurst `0.1` | Sortino `249468.16` | Kelly `1.3%` | 30일 APR `0.0%` | Sharpe `0.81`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-09-02 19:39:30
### 🔬 주제: **허스트 지수(Hurst Exponent) 기반 추세 vs 평균회귀 볼트 자동 판별**
* **레퍼런스 출처**: `GitHub: pyquant / Benoit Mandelbrot (Fractal Market Hypothesis)`
* **수학적 모델**: $H = \lim_{\tau \to \infty} \frac{\log(R/S)}{\log(\tau)}$
* **핵심 가설**: 볼트의 PnL 시계열에서 H > 0.5(지속적 추세) 볼트는 모멘텀 가속 전략에 배분하고, H < 0.5(평균회귀) 볼트는 딥바잉(Dip-Buyer) 전략에 배분하여 알파를 극대화함.
* **검증 데이터**: `143 days (2026-02-27 ~ 2026-09-02)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Liquidator**: Hurst `0.9` | Sortino `-0.7` | Kelly `0.0%` | 30일 APR `0.0%` | Sharpe `-0.95`
  - **Trading Strategy - IchiV3 LS**: Hurst `0.9` | Sortino `-1.82` | Kelly `0.0%` | 30일 APR `-1.66%` | Sharpe `-4.56`
  - **OnlyShortsTestingVault**: Hurst `0.804` | Sortino `-0.42` | Kelly `0.0%` | 30일 APR `-500.0%` | Sharpe `0.22`
  - **JizzJazz**: Hurst `0.776` | Sortino `1.19` | Kelly `1.8%` | 30일 APR `199.01%` | Sharpe `1.98`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---
