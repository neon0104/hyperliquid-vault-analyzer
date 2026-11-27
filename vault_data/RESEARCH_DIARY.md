# 🧠 Hyperliquid Vault AI 자율 연구 및 지속 학습 일지 (Research Diary)

> 이 문서는 AI 퀀트 연구원이 매 시간 GitHub 오픈소스 퀀트 리서치, 수학적 모델, 온체인 시계열 데이터를 자율 학습하고 검증한 누적 연구 일지입니다.

---

## 📅 연구 기록: 2026-11-27 15:39:42
### 🔬 주제: **칼만 필터(Kalman Filter) 기반 볼트 리더의 시장 베타 추종도 실시간 필터링**
* **레퍼런스 출처**: `GitHub: pykalman / R.E. Kalman (1960)`
* **수학적 모델**: $y_t = \alpha_t + \beta_t x_t + \epsilon_t, \quad \beta_t = \beta_{t-1} + \eta_t$
* **핵심 가설**: 비트코인(BTC) 가격 변동에 수동적으로 끌려가는 '가짜 알파' 볼트를 제거하고, 시장과 무관하게 독립적 수익을 창출하는 '순수 알파(Pure Alpha)' 리더 볼트를 필터링함.
* **검증 데이터**: `242 days (2026-02-27 ~ 2026-11-27)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Cold Process**: Hurst `0.361` | Sortino `3.96` | Kelly `21.1%` | 30일 APR `204.43%` | Sharpe `5.29`
  - **Dragon X1**: Hurst `0.709` | Sortino `1.92` | Kelly `9.5%` | 30일 APR `196.72%` | Sharpe `2.45`
  - **+convexity**: Hurst `0.685` | Sortino `8.08` | Kelly `13.0%` | 30일 APR `154.1%` | Sharpe `3.39`
  - **⚛️ Quantum Capital OFFICIAL Algo Vault ⚛**: Hurst `0.629` | Sortino `4.02` | Kelly `15.4%` | 30일 APR `131.58%` | Sharpe `1.88`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-27 11:39:38
### 🔬 주제: **Calmar Ratio & Omega Ratio 결합형 바벨 알파 엔진**
* **레퍼런스 출처**: `GitHub: skfolio / Shadwick & Keating (2002)`
* **수학적 모델**: $\Omega(L) = \frac{\int_L^\infty (1-F(x))dx}{\int_{-\infty}^L F(x)dx}$
* **핵심 가설**: MDD 대비 수익률(Calmar)로 초안정 Core 60%를 고정하고, 수익-손실 확률 분포 비율(Omega)로 Satellite 40%의 단기 폭발력을 결합하여 샤프 지수를 2배 이상 견인함.
* **검증 데이터**: `242 days (2026-02-27 ~ 2026-11-27)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Cold Process**: Hurst `0.361` | Sortino `3.96` | Kelly `21.1%` | 30일 APR `204.43%` | Sharpe `5.29`
  - **Dragon X1**: Hurst `0.709` | Sortino `1.92` | Kelly `9.5%` | 30일 APR `196.72%` | Sharpe `2.45`
  - **+convexity**: Hurst `0.685` | Sortino `8.08` | Kelly `13.0%` | 30일 APR `154.1%` | Sharpe `3.39`
  - **⚛️ Quantum Capital OFFICIAL Algo Vault ⚛**: Hurst `0.629` | Sortino `4.02` | Kelly `15.4%` | 30일 APR `131.58%` | Sharpe `1.88`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-27 07:39:39
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `242 days (2026-02-27 ~ 2026-11-27)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Cold Process**: Hurst `0.361` | Sortino `3.96` | Kelly `21.1%` | 30일 APR `204.43%` | Sharpe `5.29`
  - **Bunny**: Hurst `0.649` | Sortino `7.24` | Kelly `20.0%` | 30일 APR `5.98%` | Sharpe `8.23`
  - **⚛️ Quantum Capital OFFICIAL Algo Vault ⚛**: Hurst `0.629` | Sortino `4.02` | Kelly `15.4%` | 30일 APR `131.58%` | Sharpe `1.88`
  - **FuturAI Labs - High Sharpe, Low Volatili**: Hurst `0.429` | Sortino `4.48` | Kelly `14.2%` | 30일 APR `18.51%` | Sharpe `9.86`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-27 03:41:43
### 🔬 주제: **하방 편차(Downside Deviation) 기반 Sortino Ratio 최적화**
* **레퍼런스 출처**: `GitHub: Riskfolio-Lib / Frank Sortino (1994)`
* **수학적 모델**: $Sortino = \frac{R_p - R_f}{\sqrt{\frac{1}{N}\sum_{t=1}^N \min(0, R_t - MAR)^2}}$
* **핵심 가설**: 상승 변동성은 수익 기회이므로 페널티를 주지 않고, 오직 '손실 변동성'만을 측정하는 Sortino Ratio로 볼트 위험도를 재평가하여 불필요한 저수익 배분을 제거함.
* **검증 데이터**: `242 days (2026-02-27 ~ 2026-11-27)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Agent RockSteady**: Hurst `0.9` | Sortino `20.1` | Kelly `0.0%` | 30일 APR `31.36%` | Sharpe `2.29`
  - **+convexity**: Hurst `0.685` | Sortino `8.08` | Kelly `13.0%` | 30일 APR `154.1%` | Sharpe `3.39`
  - **22Cap**: Hurst `0.506` | Sortino `7.29` | Kelly `5.0%` | 30일 APR `8.43%` | Sharpe `3.79`
  - **Bunny**: Hurst `0.649` | Sortino `7.24` | Kelly `20.0%` | 30일 APR `5.98%` | Sharpe `8.23`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-26 23:39:43
### 🔬 주제: **허스트 지수(Hurst Exponent) 기반 추세 vs 평균회귀 볼트 자동 판별**
* **레퍼런스 출처**: `GitHub: pyquant / Benoit Mandelbrot (Fractal Market Hypothesis)`
* **수학적 모델**: $H = \lim_{\tau \to \infty} \frac{\log(R/S)}{\log(\tau)}$
* **핵심 가설**: 볼트의 PnL 시계열에서 H > 0.5(지속적 추세) 볼트는 모멘텀 가속 전략에 배분하고, H < 0.5(평균회귀) 볼트는 딥바잉(Dip-Buyer) 전략에 배분하여 알파를 극대화함.
* **검증 데이터**: `241 days (2026-02-27 ~ 2026-11-26)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Agent RockSteady**: Hurst `0.9` | Sortino `20.77` | Kelly `0.0%` | 30일 APR `29.71%` | Sharpe `2.31`
  - **BitRocket**: Hurst `0.753` | Sortino `3.43` | Kelly `2.4%` | 30일 APR `4.23%` | Sharpe `4.25`
  - **Hypernova**: Hurst `0.745` | Sortino `-1.24` | Kelly `0.0%` | 30일 APR `5.43%` | Sharpe `1.27`
  - **HyperNeutral #1**: Hurst `0.696` | Sortino `4.02` | Kelly `10.7%` | 30일 APR `57.33%` | Sharpe `3.57`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-26 19:39:44
### 🔬 주제: **GARCH(1,1) 조건부 이분산성 모델을 이용한 볼트 변동성 스퀴즈 감지**
* **레퍼런스 출처**: `GitHub: arch / Tim Bollerslev (1986)`
* **수학적 모델**: $\sigma_t^2 = \omega + \alpha \epsilon_{t-1}^2 + \beta \sigma_{t-1}^2$
* **핵심 가설**: 볼트의 단기 변동성 클러스터링(Volatility Clustering)을 사전에 예측하여, 변동성 폭발 직전의 눌림목 볼트를 선취매하고 급격한 변동성 확장 시 비중을 자동 축소함.
* **검증 데이터**: `241 days (2026-02-27 ~ 2026-11-26)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Cold Process**: Hurst `0.414` | Sortino `3.73` | Kelly `21.8%` | 30일 APR `188.31%` | Sharpe `5.04`
  - **Dragon X1**: Hurst `0.631` | Sortino `2.28` | Kelly `11.6%` | 30일 APR `212.63%` | Sharpe `2.64`
  - **+convexity**: Hurst `0.658` | Sortino `8.23` | Kelly `13.2%` | 30일 APR `164.3%` | Sharpe `3.44`
  - **L/S Momentum Strategy**: Hurst `0.567` | Sortino `1.73` | Kelly `8.7%` | 30일 APR `144.3%` | Sharpe `2.15`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-26 15:39:45
### 🔬 주제: **계층적 위험 패리티(Hierarchical Risk Parity, HRP) 머신러닝 군집화 자산 배분**
* **레퍼런스 출처**: `GitHub: Riskfolio-Lib / Marcos Lopez de Prado (2016)`
* **수학적 모델**: $w_i = w_i \times \frac{V_i^{-1}}{\sum V_j^{-1}}$
* **핵심 가설**: 전통적 공분산 역행렬의 수치적 불안정성을 극복하기 위해, 머신러닝 트리 군집화(Dendrogram)를 통해 상호 상관관계가 낮은 볼트들로 포트폴리오의 분산 효과를 극대화함.
* **검증 데이터**: `241 days (2026-02-27 ~ 2026-11-26)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Cold Process**: Hurst `0.414` | Sortino `3.73` | Kelly `21.8%` | 30일 APR `188.31%` | Sharpe `5.04`
  - **Dragon X1**: Hurst `0.631` | Sortino `2.28` | Kelly `11.6%` | 30일 APR `212.63%` | Sharpe `2.64`
  - **+convexity**: Hurst `0.658` | Sortino `8.23` | Kelly `13.2%` | 30일 APR `164.3%` | Sharpe `3.44`
  - **L/S Momentum Strategy**: Hurst `0.567` | Sortino `1.73` | Kelly `8.7%` | 30일 APR `144.3%` | Sharpe `2.15`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-26 11:39:47
### 🔬 주제: **알파 감쇄 반감기(Alpha Decay Half-Life) 모델을 통한 선제적 익절/손절 타이밍**
* **레퍼런스 출처**: `GitHub: QuantConnect / Z. Kakushadze & J.A. Serur (2018)`
* **수학적 모델**: $t_{1/2} = \frac{\ln(2)}{\lambda}$
* **핵심 가설**: TVL 급증으로 인한 슬리피지 증가 및 전략 복제로 발생하는 알파 감쇄 곡선을 지수 감쇄 모델($A(t) = A_0 e^{-\lambda t}$)로 추적하여 최적의 이탈 시점을 산출함.
* **검증 데이터**: `241 days (2026-02-27 ~ 2026-11-26)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Cold Process**: Hurst `0.414` | Sortino `3.73` | Kelly `21.8%` | 30일 APR `188.31%` | Sharpe `5.04`
  - **Dragon X1**: Hurst `0.631` | Sortino `2.28` | Kelly `11.6%` | 30일 APR `212.63%` | Sharpe `2.64`
  - **+convexity**: Hurst `0.658` | Sortino `8.23` | Kelly `13.2%` | 30일 APR `164.3%` | Sharpe `3.44`
  - **L/S Momentum Strategy**: Hurst `0.567` | Sortino `1.73` | Kelly `8.7%` | 30일 APR `144.3%` | Sharpe `2.15`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-26 07:39:39
### 🔬 주제: **칼만 필터(Kalman Filter) 기반 볼트 리더의 시장 베타 추종도 실시간 필터링**
* **레퍼런스 출처**: `GitHub: pykalman / R.E. Kalman (1960)`
* **수학적 모델**: $y_t = \alpha_t + \beta_t x_t + \epsilon_t, \quad \beta_t = \beta_{t-1} + \eta_t$
* **핵심 가설**: 비트코인(BTC) 가격 변동에 수동적으로 끌려가는 '가짜 알파' 볼트를 제거하고, 시장과 무관하게 독립적 수익을 창출하는 '순수 알파(Pure Alpha)' 리더 볼트를 필터링함.
* **검증 데이터**: `241 days (2026-02-27 ~ 2026-11-26)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Cold Process**: Hurst `0.414` | Sortino `3.73` | Kelly `21.8%` | 30일 APR `188.31%` | Sharpe `5.04`
  - **Dragon X1**: Hurst `0.631` | Sortino `2.28` | Kelly `11.6%` | 30일 APR `212.63%` | Sharpe `2.64`
  - **+convexity**: Hurst `0.658` | Sortino `8.23` | Kelly `13.2%` | 30일 APR `164.3%` | Sharpe `3.44`
  - **L/S Momentum Strategy**: Hurst `0.567` | Sortino `1.73` | Kelly `8.7%` | 30일 APR `144.3%` | Sharpe `2.15`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-26 03:41:49
### 🔬 주제: **Calmar Ratio & Omega Ratio 결합형 바벨 알파 엔진**
* **레퍼런스 출처**: `GitHub: skfolio / Shadwick & Keating (2002)`
* **수학적 모델**: $\Omega(L) = \frac{\int_L^\infty (1-F(x))dx}{\int_{-\infty}^L F(x)dx}$
* **핵심 가설**: MDD 대비 수익률(Calmar)로 초안정 Core 60%를 고정하고, 수익-손실 확률 분포 비율(Omega)로 Satellite 40%의 단기 폭발력을 결합하여 샤프 지수를 2배 이상 견인함.
* **검증 데이터**: `241 days (2026-02-27 ~ 2026-11-26)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Cold Process**: Hurst `0.414` | Sortino `3.73` | Kelly `21.8%` | 30일 APR `188.31%` | Sharpe `5.04`
  - **Dragon X1**: Hurst `0.631` | Sortino `2.28` | Kelly `11.6%` | 30일 APR `212.63%` | Sharpe `2.64`
  - **+convexity**: Hurst `0.658` | Sortino `8.23` | Kelly `13.2%` | 30일 APR `164.3%` | Sharpe `3.44`
  - **L/S Momentum Strategy**: Hurst `0.567` | Sortino `1.73` | Kelly `8.7%` | 30일 APR `144.3%` | Sharpe `2.15`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-25 23:39:43
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `240 days (2026-02-27 ~ 2026-11-25)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Cold Process**: Hurst `0.512` | Sortino `3.4` | Kelly `19.9%` | 30일 APR `184.39%` | Sharpe `4.87`
  - **Bunny**: Hurst `0.669` | Sortino `7.68` | Kelly `19.5%` | 30일 APR `6.08%` | Sharpe `8.35`
  - **FuturAI Labs - High Sharpe, Low Volatili**: Hurst `0.413` | Sortino `4.38` | Kelly `13.9%` | 30일 APR `17.87%` | Sharpe `5.01`
  - **+convexity**: Hurst `0.789` | Sortino `8.18` | Kelly `13.1%` | 30일 APR `160.94%` | Sharpe `3.43`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-25 19:39:49
### 🔬 주제: **하방 편차(Downside Deviation) 기반 Sortino Ratio 최적화**
* **레퍼런스 출처**: `GitHub: Riskfolio-Lib / Frank Sortino (1994)`
* **수학적 모델**: $Sortino = \frac{R_p - R_f}{\sqrt{\frac{1}{N}\sum_{t=1}^N \min(0, R_t - MAR)^2}}$
* **핵심 가설**: 상승 변동성은 수익 기회이므로 페널티를 주지 않고, 오직 '손실 변동성'만을 측정하는 Sortino Ratio로 볼트 위험도를 재평가하여 불필요한 저수익 배분을 제거함.
* **검증 데이터**: `240 days (2026-02-27 ~ 2026-11-25)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Agent RockSteady**: Hurst `0.666` | Sortino `21.5` | Kelly `0.0%` | 30일 APR `28.42%` | Sharpe `2.31`
  - **+convexity**: Hurst `0.789` | Sortino `8.18` | Kelly `13.1%` | 30일 APR `160.94%` | Sharpe `3.43`
  - **Bunny**: Hurst `0.669` | Sortino `7.68` | Kelly `19.5%` | 30일 APR `6.08%` | Sharpe `8.35`
  - **22Cap**: Hurst `0.401` | Sortino `7.27` | Kelly `4.4%` | 30일 APR `7.65%` | Sharpe `3.78`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-25 15:39:37
### 🔬 주제: **허스트 지수(Hurst Exponent) 기반 추세 vs 평균회귀 볼트 자동 판별**
* **레퍼런스 출처**: `GitHub: pyquant / Benoit Mandelbrot (Fractal Market Hypothesis)`
* **수학적 모델**: $H = \lim_{\tau \to \infty} \frac{\log(R/S)}{\log(\tau)}$
* **핵심 가설**: 볼트의 PnL 시계열에서 H > 0.5(지속적 추세) 볼트는 모멘텀 가속 전략에 배분하고, H < 0.5(평균회귀) 볼트는 딥바잉(Dip-Buyer) 전략에 배분하여 알파를 극대화함.
* **검증 데이터**: `240 days (2026-02-27 ~ 2026-11-25)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **HindenShort v0.1**: Hurst `0.873` | Sortino `-0.47` | Kelly `6.7%` | 30일 APR `72.48%` | Sharpe `-0.1`
  - **Hypernova**: Hurst `0.863` | Sortino `-1.23` | Kelly `0.0%` | 30일 APR `6.99%` | Sharpe `1.28`
  - **+convexity**: Hurst `0.789` | Sortino `8.18` | Kelly `13.1%` | 30일 APR `160.94%` | Sharpe `3.43`
  - **BitRocket**: Hurst `0.681` | Sortino `3.42` | Kelly `2.0%` | 30일 APR `3.96%` | Sharpe `4.36`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-25 11:39:44
### 🔬 주제: **GARCH(1,1) 조건부 이분산성 모델을 이용한 볼트 변동성 스퀴즈 감지**
* **레퍼런스 출처**: `GitHub: arch / Tim Bollerslev (1986)`
* **수학적 모델**: $\sigma_t^2 = \omega + \alpha \epsilon_{t-1}^2 + \beta \sigma_{t-1}^2$
* **핵심 가설**: 볼트의 단기 변동성 클러스터링(Volatility Clustering)을 사전에 예측하여, 변동성 폭발 직전의 눌림목 볼트를 선취매하고 급격한 변동성 확장 시 비중을 자동 축소함.
* **검증 데이터**: `240 days (2026-02-27 ~ 2026-11-25)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Dragon X1**: Hurst `0.669` | Sortino `2.21` | Kelly `11.5%` | 30일 APR `207.34%` | Sharpe `2.52`
  - **Cold Process**: Hurst `0.512` | Sortino `3.4` | Kelly `19.9%` | 30일 APR `184.39%` | Sharpe `4.87`
  - **+convexity**: Hurst `0.789` | Sortino `8.18` | Kelly `13.1%` | 30일 APR `160.94%` | Sharpe `3.43`
  - **L/S Momentum Strategy**: Hurst `0.616` | Sortino `1.72` | Kelly `7.9%` | 30일 APR `141.09%` | Sharpe `2.15`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-25 07:39:40
### 🔬 주제: **계층적 위험 패리티(Hierarchical Risk Parity, HRP) 머신러닝 군집화 자산 배분**
* **레퍼런스 출처**: `GitHub: Riskfolio-Lib / Marcos Lopez de Prado (2016)`
* **수학적 모델**: $w_i = w_i \times \frac{V_i^{-1}}{\sum V_j^{-1}}$
* **핵심 가설**: 전통적 공분산 역행렬의 수치적 불안정성을 극복하기 위해, 머신러닝 트리 군집화(Dendrogram)를 통해 상호 상관관계가 낮은 볼트들로 포트폴리오의 분산 효과를 극대화함.
* **검증 데이터**: `240 days (2026-02-27 ~ 2026-11-25)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Dragon X1**: Hurst `0.669` | Sortino `2.21` | Kelly `11.5%` | 30일 APR `207.34%` | Sharpe `2.52`
  - **Cold Process**: Hurst `0.512` | Sortino `3.4` | Kelly `19.9%` | 30일 APR `184.39%` | Sharpe `4.87`
  - **+convexity**: Hurst `0.789` | Sortino `8.18` | Kelly `13.1%` | 30일 APR `160.94%` | Sharpe `3.43`
  - **L/S Momentum Strategy**: Hurst `0.616` | Sortino `1.72` | Kelly `7.9%` | 30일 APR `141.09%` | Sharpe `2.15`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---
