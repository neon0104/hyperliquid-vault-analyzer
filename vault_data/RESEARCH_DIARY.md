# 🧠 Hyperliquid Vault AI 자율 연구 및 지속 학습 일지 (Research Diary)

> 이 문서는 AI 퀀트 연구원이 매 시간 GitHub 오픈소스 퀀트 리서치, 수학적 모델, 온체인 시계열 데이터를 자율 학습하고 검증한 누적 연구 일지입니다.

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

## 📅 연구 기록: 2026-11-17 19:39:50
### 🔬 주제: **하방 편차(Downside Deviation) 기반 Sortino Ratio 최적화**
* **레퍼런스 출처**: `GitHub: Riskfolio-Lib / Frank Sortino (1994)`
* **수학적 모델**: $Sortino = \frac{R_p - R_f}{\sqrt{\frac{1}{N}\sum_{t=1}^N \min(0, R_t - MAR)^2}}$
* **핵심 가설**: 상승 변동성은 수익 기회이므로 페널티를 주지 않고, 오직 '손실 변동성'만을 측정하는 Sortino Ratio로 볼트 위험도를 재평가하여 불필요한 저수익 배분을 제거함.
* **검증 데이터**: `232 days (2026-02-27 ~ 2026-11-17)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Bunny**: Hurst `0.711` | Sortino `38.34` | Kelly `20.9%` | 30일 APR `4.32%` | Sharpe `8.12`
  - **+convexity**: Hurst `0.828` | Sortino `8.12` | Kelly `13.0%` | 30일 APR `148.16%` | Sharpe `3.23`
  - **V4 Alpha Quantum**: Hurst `0.608` | Sortino `7.35` | Kelly `11.6%` | 30일 APR `93.52%` | Sharpe `2.75`
  - **22Cap**: Hurst `0.517` | Sortino `7.24` | Kelly `1.7%` | 30일 APR `2.39%` | Sharpe `3.86`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-17 15:39:42
### 🔬 주제: **허스트 지수(Hurst Exponent) 기반 추세 vs 평균회귀 볼트 자동 판별**
* **레퍼런스 출처**: `GitHub: pyquant / Benoit Mandelbrot (Fractal Market Hypothesis)`
* **수학적 모델**: $H = \lim_{\tau \to \infty} \frac{\log(R/S)}{\log(\tau)}$
* **핵심 가설**: 볼트의 PnL 시계열에서 H > 0.5(지속적 추세) 볼트는 모멘텀 가속 전략에 배분하고, H < 0.5(평균회귀) 볼트는 딥바잉(Dip-Buyer) 전략에 배분하여 알파를 극대화함.
* **검증 데이터**: `232 days (2026-02-27 ~ 2026-11-17)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **+convexity**: Hurst `0.828` | Sortino `8.12` | Kelly `13.0%` | 30일 APR `148.16%` | Sharpe `3.23`
  - **Hindenburg Short Alpha**: Hurst `0.809` | Sortino `6.83` | Kelly `1.6%` | 30일 APR `15.63%` | Sharpe `2.9`
  - **[ Systemic Strategies ] L/S Grids**: Hurst `0.752` | Sortino `0.72` | Kelly `2.4%` | 30일 APR `173.54%` | Sharpe `2.77`
  - **Bunny**: Hurst `0.711` | Sortino `38.34` | Kelly `20.9%` | 30일 APR `4.32%` | Sharpe `8.12`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-17 11:39:53
### 🔬 주제: **GARCH(1,1) 조건부 이분산성 모델을 이용한 볼트 변동성 스퀴즈 감지**
* **레퍼런스 출처**: `GitHub: arch / Tim Bollerslev (1986)`
* **수학적 모델**: $\sigma_t^2 = \omega + \alpha \epsilon_{t-1}^2 + \beta \sigma_{t-1}^2$
* **핵심 가설**: 볼트의 단기 변동성 클러스터링(Volatility Clustering)을 사전에 예측하여, 변동성 폭발 직전의 눌림목 볼트를 선취매하고 급격한 변동성 확장 시 비중을 자동 축소함.
* **검증 데이터**: `232 days (2026-02-27 ~ 2026-11-17)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[ Systemic Strategies ] L/S Grids**: Hurst `0.752` | Sortino `0.72` | Kelly `2.4%` | 30일 APR `173.54%` | Sharpe `2.77`
  - **+convexity**: Hurst `0.828` | Sortino `8.12` | Kelly `13.0%` | 30일 APR `148.16%` | Sharpe `3.23`
  - **Dragon X1**: Hurst `0.649` | Sortino `1.21` | Kelly `8.5%` | 30일 APR `147.68%` | Sharpe `2.05`
  - **Bunny**: Hurst `0.711` | Sortino `38.34` | Kelly `20.9%` | 30일 APR `4.32%` | Sharpe `8.12`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-17 07:39:37
### 🔬 주제: **계층적 위험 패리티(Hierarchical Risk Parity, HRP) 머신러닝 군집화 자산 배분**
* **레퍼런스 출처**: `GitHub: Riskfolio-Lib / Marcos Lopez de Prado (2016)`
* **수학적 모델**: $w_i = w_i \times \frac{V_i^{-1}}{\sum V_j^{-1}}$
* **핵심 가설**: 전통적 공분산 역행렬의 수치적 불안정성을 극복하기 위해, 머신러닝 트리 군집화(Dendrogram)를 통해 상호 상관관계가 낮은 볼트들로 포트폴리오의 분산 효과를 극대화함.
* **검증 데이터**: `232 days (2026-02-27 ~ 2026-11-17)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[ Systemic Strategies ] L/S Grids**: Hurst `0.752` | Sortino `0.72` | Kelly `2.4%` | 30일 APR `173.54%` | Sharpe `2.77`
  - **+convexity**: Hurst `0.828` | Sortino `8.12` | Kelly `13.0%` | 30일 APR `148.16%` | Sharpe `3.23`
  - **Dragon X1**: Hurst `0.649` | Sortino `1.21` | Kelly `8.5%` | 30일 APR `147.68%` | Sharpe `2.05`
  - **Bunny**: Hurst `0.711` | Sortino `38.34` | Kelly `20.9%` | 30일 APR `4.32%` | Sharpe `8.12`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-17 03:42:21
### 🔬 주제: **알파 감쇄 반감기(Alpha Decay Half-Life) 모델을 통한 선제적 익절/손절 타이밍**
* **레퍼런스 출처**: `GitHub: QuantConnect / Z. Kakushadze & J.A. Serur (2018)`
* **수학적 모델**: $t_{1/2} = \frac{\ln(2)}{\lambda}$
* **핵심 가설**: TVL 급증으로 인한 슬리피지 증가 및 전략 복제로 발생하는 알파 감쇄 곡선을 지수 감쇄 모델($A(t) = A_0 e^{-\lambda t}$)로 추적하여 최적의 이탈 시점을 산출함.
* **검증 데이터**: `232 days (2026-02-27 ~ 2026-11-17)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[ Systemic Strategies ] L/S Grids**: Hurst `0.752` | Sortino `0.72` | Kelly `2.4%` | 30일 APR `173.54%` | Sharpe `2.77`
  - **+convexity**: Hurst `0.828` | Sortino `8.12` | Kelly `13.0%` | 30일 APR `148.16%` | Sharpe `3.23`
  - **Dragon X1**: Hurst `0.649` | Sortino `1.21` | Kelly `8.5%` | 30일 APR `147.68%` | Sharpe `2.05`
  - **Bunny**: Hurst `0.711` | Sortino `38.34` | Kelly `20.9%` | 30일 APR `4.32%` | Sharpe `8.12`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-16 23:39:41
### 🔬 주제: **칼만 필터(Kalman Filter) 기반 볼트 리더의 시장 베타 추종도 실시간 필터링**
* **레퍼런스 출처**: `GitHub: pykalman / R.E. Kalman (1960)`
* **수학적 모델**: $y_t = \alpha_t + \beta_t x_t + \epsilon_t, \quad \beta_t = \beta_{t-1} + \eta_t$
* **핵심 가설**: 비트코인(BTC) 가격 변동에 수동적으로 끌려가는 '가짜 알파' 볼트를 제거하고, 시장과 무관하게 독립적 수익을 창출하는 '순수 알파(Pure Alpha)' 리더 볼트를 필터링함.
* **검증 데이터**: `231 days (2026-02-27 ~ 2026-11-16)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **+convexity**: Hurst `0.731` | Sortino `8.22` | Kelly `13.2%` | 30일 APR `145.93%` | Sharpe `3.24`
  - **[ Systemic Strategies ] L/S Grids**: Hurst `0.841` | Sortino `0.7` | Kelly `4.1%` | 30일 APR `157.56%` | Sharpe `2.75`
  - **Dragon X1**: Hurst `0.777` | Sortino `1.2` | Kelly `9.3%` | 30일 APR `149.82%` | Sharpe `2.06`
  - **Bunny**: Hurst `0.742` | Sortino `39.24` | Kelly `23.2%` | 30일 APR `4.4%` | Sharpe `8.24`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-16 19:39:36
### 🔬 주제: **Calmar Ratio & Omega Ratio 결합형 바벨 알파 엔진**
* **레퍼런스 출처**: `GitHub: skfolio / Shadwick & Keating (2002)`
* **수학적 모델**: $\Omega(L) = \frac{\int_L^\infty (1-F(x))dx}{\int_{-\infty}^L F(x)dx}$
* **핵심 가설**: MDD 대비 수익률(Calmar)로 초안정 Core 60%를 고정하고, 수익-손실 확률 분포 비율(Omega)로 Satellite 40%의 단기 폭발력을 결합하여 샤프 지수를 2배 이상 견인함.
* **검증 데이터**: `231 days (2026-02-27 ~ 2026-11-16)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **+convexity**: Hurst `0.731` | Sortino `8.22` | Kelly `13.2%` | 30일 APR `145.93%` | Sharpe `3.24`
  - **[ Systemic Strategies ] L/S Grids**: Hurst `0.841` | Sortino `0.7` | Kelly `4.1%` | 30일 APR `157.56%` | Sharpe `2.75`
  - **Dragon X1**: Hurst `0.777` | Sortino `1.2` | Kelly `9.3%` | 30일 APR `149.82%` | Sharpe `2.06`
  - **Bunny**: Hurst `0.742` | Sortino `39.24` | Kelly `23.2%` | 30일 APR `4.4%` | Sharpe `8.24`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-16 15:41:05
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `231 days (2026-02-27 ~ 2026-11-16)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Bunny**: Hurst `0.742` | Sortino `39.24` | Kelly `23.2%` | 30일 APR `4.4%` | Sharpe `8.24`
  - **FuturAI Labs - High Sharpe, Low Volatili**: Hurst `0.526` | Sortino `4.49` | Kelly `15.4%` | 30일 APR `18.17%` | Sharpe `8.64`
  - **Jay Pennies to Jay Dollars**: Hurst `0.423` | Sortino `5.36` | Kelly `15.3%` | 30일 APR `8.37%` | Sharpe `1.8`
  - **Passivbot Canon**: Hurst `0.418` | Sortino `6.61` | Kelly `13.4%` | 30일 APR `69.08%` | Sharpe `6.11`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-16 11:39:45
### 🔬 주제: **하방 편차(Downside Deviation) 기반 Sortino Ratio 최적화**
* **레퍼런스 출처**: `GitHub: Riskfolio-Lib / Frank Sortino (1994)`
* **수학적 모델**: $Sortino = \frac{R_p - R_f}{\sqrt{\frac{1}{N}\sum_{t=1}^N \min(0, R_t - MAR)^2}}$
* **핵심 가설**: 상승 변동성은 수익 기회이므로 페널티를 주지 않고, 오직 '손실 변동성'만을 측정하는 Sortino Ratio로 볼트 위험도를 재평가하여 불필요한 저수익 배분을 제거함.
* **검증 데이터**: `231 days (2026-02-27 ~ 2026-11-16)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Bunny**: Hurst `0.742` | Sortino `39.24` | Kelly `23.2%` | 30일 APR `4.4%` | Sharpe `8.24`
  - **+convexity**: Hurst `0.731` | Sortino `8.22` | Kelly `13.2%` | 30일 APR `145.93%` | Sharpe `3.24`
  - **V4 Alpha Quantum**: Hurst `0.625` | Sortino `7.28` | Kelly `12.0%` | 30일 APR `101.99%` | Sharpe `2.73`
  - **22Cap**: Hurst `0.51` | Sortino `7.24` | Kelly `1.0%` | 30일 APR `0.95%` | Sharpe `3.89`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-16 07:39:40
### 🔬 주제: **허스트 지수(Hurst Exponent) 기반 추세 vs 평균회귀 볼트 자동 판별**
* **레퍼런스 출처**: `GitHub: pyquant / Benoit Mandelbrot (Fractal Market Hypothesis)`
* **수학적 모델**: $H = \lim_{\tau \to \infty} \frac{\log(R/S)}{\log(\tau)}$
* **핵심 가설**: 볼트의 PnL 시계열에서 H > 0.5(지속적 추세) 볼트는 모멘텀 가속 전략에 배분하고, H < 0.5(평균회귀) 볼트는 딥바잉(Dip-Buyer) 전략에 배분하여 알파를 극대화함.
* **검증 데이터**: `231 days (2026-02-27 ~ 2026-11-16)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[ Systemic Strategies ] L/S Grids**: Hurst `0.841` | Sortino `0.7` | Kelly `4.1%` | 30일 APR `157.56%` | Sharpe `2.75`
  - **Hindenburg Short Alpha**: Hurst `0.808` | Sortino `6.83` | Kelly `1.3%` | 30일 APR `27.2%` | Sharpe `2.9`
  - **Dragon X1**: Hurst `0.777` | Sortino `1.2` | Kelly `9.3%` | 30일 APR `149.82%` | Sharpe `2.06`
  - **Abs Return Sophon Quant**: Hurst `0.761` | Sortino `-0.67` | Kelly `0.0%` | 30일 APR `0.12%` | Sharpe `-2.36`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---
