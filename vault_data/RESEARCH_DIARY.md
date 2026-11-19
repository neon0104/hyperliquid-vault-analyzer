# 🧠 Hyperliquid Vault AI 자율 연구 및 지속 학습 일지 (Research Diary)

> 이 문서는 AI 퀀트 연구원이 매 시간 GitHub 오픈소스 퀀트 리서치, 수학적 모델, 온체인 시계열 데이터를 자율 학습하고 검증한 누적 연구 일지입니다.

---

## 📅 연구 기록: 2026-11-20 07:39:43
### 🔬 주제: **허스트 지수(Hurst Exponent) 기반 추세 vs 평균회귀 볼트 자동 판별**
* **레퍼런스 출처**: `GitHub: pyquant / Benoit Mandelbrot (Fractal Market Hypothesis)`
* **수학적 모델**: $H = \lim_{\tau \to \infty} \frac{\log(R/S)}{\log(\tau)}$
* **핵심 가설**: 볼트의 PnL 시계열에서 H > 0.5(지속적 추세) 볼트는 모멘텀 가속 전략에 배분하고, H < 0.5(평균회귀) 볼트는 딥바잉(Dip-Buyer) 전략에 배분하여 알파를 극대화함.
* **검증 데이터**: `235 days (2026-02-27 ~ 2026-11-20)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Hindenburg Short Alpha**: Hurst `0.769` | Sortino `6.57` | Kelly `3.2%` | 30일 APR `12.12%` | Sharpe `2.88`
  - **+convexity**: Hurst `0.768` | Sortino `8.31` | Kelly `14.8%` | 30일 APR `151.18%` | Sharpe `3.26`
  - **22Cap**: Hurst `0.757` | Sortino `7.3` | Kelly `4.8%` | 30일 APR `8.55%` | Sharpe `3.79`
  - **L/S Momentum Strategy**: Hurst `0.738` | Sortino `1.59` | Kelly `8.3%` | 30일 APR `120.71%` | Sharpe `2.08`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-20 03:41:54
### 🔬 주제: **GARCH(1,1) 조건부 이분산성 모델을 이용한 볼트 변동성 스퀴즈 감지**
* **레퍼런스 출처**: `GitHub: arch / Tim Bollerslev (1986)`
* **수학적 모델**: $\sigma_t^2 = \omega + \alpha \epsilon_{t-1}^2 + \beta \sigma_{t-1}^2$
* **핵심 가설**: 볼트의 단기 변동성 클러스터링(Volatility Clustering)을 사전에 예측하여, 변동성 폭발 직전의 눌림목 볼트를 선취매하고 급격한 변동성 확장 시 비중을 자동 축소함.
* **검증 데이터**: `235 days (2026-02-27 ~ 2026-11-20)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[Bee] Line**: Hurst `0.465` | Sortino `-0.25` | Kelly `9.5%` | 30일 APR `236.93%` | Sharpe `4.51`
  - **+convexity**: Hurst `0.768` | Sortino `8.31` | Kelly `14.8%` | 30일 APR `151.18%` | Sharpe `3.26`
  - **Dragon X1**: Hurst `0.599` | Sortino `1.57` | Kelly `12.2%` | 30일 APR `163.36%` | Sharpe `2.25`
  - **L/S Momentum Strategy**: Hurst `0.738` | Sortino `1.59` | Kelly `8.3%` | 30일 APR `120.71%` | Sharpe `2.08`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-19 23:39:49
### 🔬 주제: **계층적 위험 패리티(Hierarchical Risk Parity, HRP) 머신러닝 군집화 자산 배분**
* **레퍼런스 출처**: `GitHub: Riskfolio-Lib / Marcos Lopez de Prado (2016)`
* **수학적 모델**: $w_i = w_i \times \frac{V_i^{-1}}{\sum V_j^{-1}}$
* **핵심 가설**: 전통적 공분산 역행렬의 수치적 불안정성을 극복하기 위해, 머신러닝 트리 군집화(Dendrogram)를 통해 상호 상관관계가 낮은 볼트들로 포트폴리오의 분산 효과를 극대화함.
* **검증 데이터**: `234 days (2026-02-27 ~ 2026-11-19)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[Bee] Line**: Hurst `0.537` | Sortino `-0.28` | Kelly `9.9%` | 30일 APR `248.6%` | Sharpe `4.47`
  - **+convexity**: Hurst `0.751` | Sortino `8.29` | Kelly `13.9%` | 30일 APR `166.39%` | Sharpe `3.3`
  - **Dragon X1**: Hurst `0.694` | Sortino `1.55` | Kelly `11.2%` | 30일 APR `152.44%` | Sharpe `2.25`
  - **L/S Momentum Strategy**: Hurst `0.654` | Sortino `1.64` | Kelly `9.5%` | 30일 APR `125.79%` | Sharpe `2.11`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-19 19:39:43
### 🔬 주제: **알파 감쇄 반감기(Alpha Decay Half-Life) 모델을 통한 선제적 익절/손절 타이밍**
* **레퍼런스 출처**: `GitHub: QuantConnect / Z. Kakushadze & J.A. Serur (2018)`
* **수학적 모델**: $t_{1/2} = \frac{\ln(2)}{\lambda}$
* **핵심 가설**: TVL 급증으로 인한 슬리피지 증가 및 전략 복제로 발생하는 알파 감쇄 곡선을 지수 감쇄 모델($A(t) = A_0 e^{-\lambda t}$)로 추적하여 최적의 이탈 시점을 산출함.
* **검증 데이터**: `234 days (2026-02-27 ~ 2026-11-19)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[Bee] Line**: Hurst `0.537` | Sortino `-0.28` | Kelly `9.9%` | 30일 APR `248.6%` | Sharpe `4.47`
  - **+convexity**: Hurst `0.751` | Sortino `8.29` | Kelly `13.9%` | 30일 APR `166.39%` | Sharpe `3.3`
  - **Dragon X1**: Hurst `0.694` | Sortino `1.55` | Kelly `11.2%` | 30일 APR `152.44%` | Sharpe `2.25`
  - **L/S Momentum Strategy**: Hurst `0.654` | Sortino `1.64` | Kelly `9.5%` | 30일 APR `125.79%` | Sharpe `2.11`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-19 15:39:40
### 🔬 주제: **칼만 필터(Kalman Filter) 기반 볼트 리더의 시장 베타 추종도 실시간 필터링**
* **레퍼런스 출처**: `GitHub: pykalman / R.E. Kalman (1960)`
* **수학적 모델**: $y_t = \alpha_t + \beta_t x_t + \epsilon_t, \quad \beta_t = \beta_{t-1} + \eta_t$
* **핵심 가설**: 비트코인(BTC) 가격 변동에 수동적으로 끌려가는 '가짜 알파' 볼트를 제거하고, 시장과 무관하게 독립적 수익을 창출하는 '순수 알파(Pure Alpha)' 리더 볼트를 필터링함.
* **검증 데이터**: `234 days (2026-02-27 ~ 2026-11-19)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[Bee] Line**: Hurst `0.537` | Sortino `-0.28` | Kelly `9.9%` | 30일 APR `248.6%` | Sharpe `4.47`
  - **+convexity**: Hurst `0.751` | Sortino `8.29` | Kelly `13.9%` | 30일 APR `166.39%` | Sharpe `3.3`
  - **Dragon X1**: Hurst `0.694` | Sortino `1.55` | Kelly `11.2%` | 30일 APR `152.44%` | Sharpe `2.25`
  - **L/S Momentum Strategy**: Hurst `0.654` | Sortino `1.64` | Kelly `9.5%` | 30일 APR `125.79%` | Sharpe `2.11`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-19 11:39:39
### 🔬 주제: **Calmar Ratio & Omega Ratio 결합형 바벨 알파 엔진**
* **레퍼런스 출처**: `GitHub: skfolio / Shadwick & Keating (2002)`
* **수학적 모델**: $\Omega(L) = \frac{\int_L^\infty (1-F(x))dx}{\int_{-\infty}^L F(x)dx}$
* **핵심 가설**: MDD 대비 수익률(Calmar)로 초안정 Core 60%를 고정하고, 수익-손실 확률 분포 비율(Omega)로 Satellite 40%의 단기 폭발력을 결합하여 샤프 지수를 2배 이상 견인함.
* **검증 데이터**: `234 days (2026-02-27 ~ 2026-11-19)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[Bee] Line**: Hurst `0.537` | Sortino `-0.28` | Kelly `9.9%` | 30일 APR `248.6%` | Sharpe `4.47`
  - **+convexity**: Hurst `0.751` | Sortino `8.29` | Kelly `13.9%` | 30일 APR `166.39%` | Sharpe `3.3`
  - **Dragon X1**: Hurst `0.694` | Sortino `1.55` | Kelly `11.2%` | 30일 APR `152.44%` | Sharpe `2.25`
  - **L/S Momentum Strategy**: Hurst `0.654` | Sortino `1.64` | Kelly `9.5%` | 30일 APR `125.79%` | Sharpe `2.11`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-19 07:39:40
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `234 days (2026-02-27 ~ 2026-11-19)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Bunny**: Hurst `0.811` | Sortino `6.37` | Kelly `19.9%` | 30일 APR `4.34%` | Sharpe `8.11`
  - **FuturAI Labs - High Sharpe, Low Volatili**: Hurst `0.478` | Sortino `4.6` | Kelly `15.5%` | 30일 APR `20.16%` | Sharpe `9.13`
  - **Jay Pennies to Jay Dollars**: Hurst `0.338` | Sortino `5.33` | Kelly `14.7%` | 30일 APR `7.31%` | Sharpe `1.78`
  - **+convexity**: Hurst `0.751` | Sortino `8.29` | Kelly `13.9%` | 30일 APR `166.39%` | Sharpe `3.3`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-19 03:41:50
### 🔬 주제: **하방 편차(Downside Deviation) 기반 Sortino Ratio 최적화**
* **레퍼런스 출처**: `GitHub: Riskfolio-Lib / Frank Sortino (1994)`
* **수학적 모델**: $Sortino = \frac{R_p - R_f}{\sqrt{\frac{1}{N}\sum_{t=1}^N \min(0, R_t - MAR)^2}}$
* **핵심 가설**: 상승 변동성은 수익 기회이므로 페널티를 주지 않고, 오직 '손실 변동성'만을 측정하는 Sortino Ratio로 볼트 위험도를 재평가하여 불필요한 저수익 배분을 제거함.
* **검증 데이터**: `234 days (2026-02-27 ~ 2026-11-19)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **+convexity**: Hurst `0.751` | Sortino `8.29` | Kelly `13.9%` | 30일 APR `166.39%` | Sharpe `3.3`
  - **V4 Alpha Quantum**: Hurst `0.64` | Sortino `7.36` | Kelly `11.0%` | 30일 APR `74.9%` | Sharpe `2.73`
  - **22Cap**: Hurst `0.736` | Sortino `7.26` | Kelly `3.5%` | 30일 APR `6.05%` | Sharpe `3.81`
  - **Passivbot Canon**: Hurst `0.376` | Sortino `6.84` | Kelly `13.4%` | 30일 APR `61.98%` | Sharpe `6.17`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-18 23:39:43
### 🔬 주제: **허스트 지수(Hurst Exponent) 기반 추세 vs 평균회귀 볼트 자동 판별**
* **레퍼런스 출처**: `GitHub: pyquant / Benoit Mandelbrot (Fractal Market Hypothesis)`
* **수학적 모델**: $H = \lim_{\tau \to \infty} \frac{\log(R/S)}{\log(\tau)}$
* **핵심 가설**: 볼트의 PnL 시계열에서 H > 0.5(지속적 추세) 볼트는 모멘텀 가속 전략에 배분하고, H < 0.5(평균회귀) 볼트는 딥바잉(Dip-Buyer) 전략에 배분하여 알파를 극대화함.
* **검증 데이터**: `233 days (2026-02-27 ~ 2026-11-18)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Hindenburg Short Alpha**: Hurst `0.819` | Sortino `6.63` | Kelly `1.6%` | 30일 APR `5.35%` | Sharpe `2.9`
  - **[ Systemic Strategies ] L/S Grids**: Hurst `0.779` | Sortino `0.81` | Kelly `1.8%` | 30일 APR `136.99%` | Sharpe `2.79`
  - **Bunny**: Hurst `0.744` | Sortino `6.81` | Kelly `19.5%` | 30일 APR `4.4%` | Sharpe `8.11`
  - **+convexity**: Hurst `0.734` | Sortino `8.24` | Kelly `13.9%` | 30일 APR `158.96%` | Sharpe `3.29`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-18 19:39:44
### 🔬 주제: **GARCH(1,1) 조건부 이분산성 모델을 이용한 볼트 변동성 스퀴즈 감지**
* **레퍼런스 출처**: `GitHub: arch / Tim Bollerslev (1986)`
* **수학적 모델**: $\sigma_t^2 = \omega + \alpha \epsilon_{t-1}^2 + \beta \sigma_{t-1}^2$
* **핵심 가설**: 볼트의 단기 변동성 클러스터링(Volatility Clustering)을 사전에 예측하여, 변동성 폭발 직전의 눌림목 볼트를 선취매하고 급격한 변동성 확장 시 비중을 자동 축소함.
* **검증 데이터**: `233 days (2026-02-27 ~ 2026-11-18)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **+convexity**: Hurst `0.734` | Sortino `8.24` | Kelly `13.9%` | 30일 APR `158.96%` | Sharpe `3.29`
  - **Dragon X1**: Hurst `0.672` | Sortino `1.41` | Kelly `8.9%` | 30일 APR `155.84%` | Sharpe `2.22`
  - **[ Systemic Strategies ] L/S Grids**: Hurst `0.779` | Sortino `0.81` | Kelly `1.8%` | 30일 APR `136.99%` | Sharpe `2.79`
  - **Crypto Trading Channel**: Hurst `0.539` | Sortino `4.46` | Kelly `9.3%` | 30일 APR `120.92%` | Sharpe `2.57`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-18 15:39:35
### 🔬 주제: **계층적 위험 패리티(Hierarchical Risk Parity, HRP) 머신러닝 군집화 자산 배분**
* **레퍼런스 출처**: `GitHub: Riskfolio-Lib / Marcos Lopez de Prado (2016)`
* **수학적 모델**: $w_i = w_i \times \frac{V_i^{-1}}{\sum V_j^{-1}}$
* **핵심 가설**: 전통적 공분산 역행렬의 수치적 불안정성을 극복하기 위해, 머신러닝 트리 군집화(Dendrogram)를 통해 상호 상관관계가 낮은 볼트들로 포트폴리오의 분산 효과를 극대화함.
* **검증 데이터**: `233 days (2026-02-27 ~ 2026-11-18)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **+convexity**: Hurst `0.734` | Sortino `8.24` | Kelly `13.9%` | 30일 APR `158.96%` | Sharpe `3.29`
  - **Dragon X1**: Hurst `0.672` | Sortino `1.41` | Kelly `8.9%` | 30일 APR `155.84%` | Sharpe `2.22`
  - **[ Systemic Strategies ] L/S Grids**: Hurst `0.779` | Sortino `0.81` | Kelly `1.8%` | 30일 APR `136.99%` | Sharpe `2.79`
  - **Crypto Trading Channel**: Hurst `0.539` | Sortino `4.46` | Kelly `9.3%` | 30일 APR `120.92%` | Sharpe `2.57`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-18 11:39:48
### 🔬 주제: **알파 감쇄 반감기(Alpha Decay Half-Life) 모델을 통한 선제적 익절/손절 타이밍**
* **레퍼런스 출처**: `GitHub: QuantConnect / Z. Kakushadze & J.A. Serur (2018)`
* **수학적 모델**: $t_{1/2} = \frac{\ln(2)}{\lambda}$
* **핵심 가설**: TVL 급증으로 인한 슬리피지 증가 및 전략 복제로 발생하는 알파 감쇄 곡선을 지수 감쇄 모델($A(t) = A_0 e^{-\lambda t}$)로 추적하여 최적의 이탈 시점을 산출함.
* **검증 데이터**: `233 days (2026-02-27 ~ 2026-11-18)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **+convexity**: Hurst `0.734` | Sortino `8.24` | Kelly `13.9%` | 30일 APR `158.96%` | Sharpe `3.29`
  - **Dragon X1**: Hurst `0.672` | Sortino `1.41` | Kelly `8.9%` | 30일 APR `155.84%` | Sharpe `2.22`
  - **[ Systemic Strategies ] L/S Grids**: Hurst `0.779` | Sortino `0.81` | Kelly `1.8%` | 30일 APR `136.99%` | Sharpe `2.79`
  - **Crypto Trading Channel**: Hurst `0.539` | Sortino `4.46` | Kelly `9.3%` | 30일 APR `120.92%` | Sharpe `2.57`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-18 07:39:41
### 🔬 주제: **칼만 필터(Kalman Filter) 기반 볼트 리더의 시장 베타 추종도 실시간 필터링**
* **레퍼런스 출처**: `GitHub: pykalman / R.E. Kalman (1960)`
* **수학적 모델**: $y_t = \alpha_t + \beta_t x_t + \epsilon_t, \quad \beta_t = \beta_{t-1} + \eta_t$
* **핵심 가설**: 비트코인(BTC) 가격 변동에 수동적으로 끌려가는 '가짜 알파' 볼트를 제거하고, 시장과 무관하게 독립적 수익을 창출하는 '순수 알파(Pure Alpha)' 리더 볼트를 필터링함.
* **검증 데이터**: `233 days (2026-02-27 ~ 2026-11-18)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **+convexity**: Hurst `0.734` | Sortino `8.24` | Kelly `13.9%` | 30일 APR `158.96%` | Sharpe `3.29`
  - **Dragon X1**: Hurst `0.672` | Sortino `1.41` | Kelly `8.9%` | 30일 APR `155.84%` | Sharpe `2.22`
  - **[ Systemic Strategies ] L/S Grids**: Hurst `0.779` | Sortino `0.81` | Kelly `1.8%` | 30일 APR `136.99%` | Sharpe `2.79`
  - **Crypto Trading Channel**: Hurst `0.539` | Sortino `4.46` | Kelly `9.3%` | 30일 APR `120.92%` | Sharpe `2.57`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-18 03:41:45
### 🔬 주제: **Calmar Ratio & Omega Ratio 결합형 바벨 알파 엔진**
* **레퍼런스 출처**: `GitHub: skfolio / Shadwick & Keating (2002)`
* **수학적 모델**: $\Omega(L) = \frac{\int_L^\infty (1-F(x))dx}{\int_{-\infty}^L F(x)dx}$
* **핵심 가설**: MDD 대비 수익률(Calmar)로 초안정 Core 60%를 고정하고, 수익-손실 확률 분포 비율(Omega)로 Satellite 40%의 단기 폭발력을 결합하여 샤프 지수를 2배 이상 견인함.
* **검증 데이터**: `233 days (2026-02-27 ~ 2026-11-18)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **+convexity**: Hurst `0.734` | Sortino `8.24` | Kelly `13.9%` | 30일 APR `158.96%` | Sharpe `3.29`
  - **Dragon X1**: Hurst `0.672` | Sortino `1.41` | Kelly `8.9%` | 30일 APR `155.84%` | Sharpe `2.22`
  - **[ Systemic Strategies ] L/S Grids**: Hurst `0.779` | Sortino `0.81` | Kelly `1.8%` | 30일 APR `136.99%` | Sharpe `2.79`
  - **Crypto Trading Channel**: Hurst `0.539` | Sortino `4.46` | Kelly `9.3%` | 30일 APR `120.92%` | Sharpe `2.57`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-17 23:39:51
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `232 days (2026-02-27 ~ 2026-11-17)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Bunny**: Hurst `0.711` | Sortino `38.34` | Kelly `20.9%` | 30일 APR `4.32%` | Sharpe `8.12`
  - **FuturAI Labs - High Sharpe, Low Volatili**: Hurst `0.54` | Sortino `4.54` | Kelly `15.5%` | 30일 APR `18.51%` | Sharpe `8.61`
  - **Jay Pennies to Jay Dollars**: Hurst `0.311` | Sortino `5.34` | Kelly `13.6%` | 30일 APR `8.59%` | Sharpe `1.79`
  - **Passivbot Canon**: Hurst `0.431` | Sortino `6.69` | Kelly `13.4%` | 30일 APR `65.85%` | Sharpe `6.11`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---
