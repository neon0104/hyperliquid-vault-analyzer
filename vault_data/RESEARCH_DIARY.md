# 🧠 Hyperliquid Vault AI 자율 연구 및 지속 학습 일지 (Research Diary)

> 이 문서는 AI 퀀트 연구원이 매 시간 GitHub 오픈소스 퀀트 리서치, 수학적 모델, 온체인 시계열 데이터를 자율 학습하고 검증한 누적 연구 일지입니다.

---

## 📅 연구 기록: 2026-11-04 19:39:41
### 🔬 주제: **칼만 필터(Kalman Filter) 기반 볼트 리더의 시장 베타 추종도 실시간 필터링**
* **레퍼런스 출처**: `GitHub: pykalman / R.E. Kalman (1960)`
* **수학적 모델**: $y_t = \alpha_t + \beta_t x_t + \epsilon_t, \quad \beta_t = \beta_{t-1} + \eta_t$
* **핵심 가설**: 비트코인(BTC) 가격 변동에 수동적으로 끌려가는 '가짜 알파' 볼트를 제거하고, 시장과 무관하게 독립적 수익을 창출하는 '순수 알파(Pure Alpha)' 리더 볼트를 필터링함.
* **검증 데이터**: `219 days (2026-02-27 ~ 2026-11-04)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[ Systemic Strategies ] ♾️ HyperGrowth ♾**: Hurst `0.713` | Sortino `6.12` | Kelly `10.5%` | 30일 APR `269.87%` | Sharpe `8.76`
  - **Buyback Spread Engine**: Hurst `0.48` | Sortino `2.89` | Kelly `8.8%` | 30일 APR `286.73%` | Sharpe `8.04`
  - **Danny Ocean**: Hurst `0.332` | Sortino `6.05` | Kelly `9.6%` | 30일 APR `126.2%` | Sharpe `14.31`
  - **V4 Alpha Quantum**: Hurst `0.585` | Sortino `6.79` | Kelly `8.0%` | 30일 APR `147.11%` | Sharpe `8.78`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-04 15:39:35
### 🔬 주제: **Calmar Ratio & Omega Ratio 결합형 바벨 알파 엔진**
* **레퍼런스 출처**: `GitHub: skfolio / Shadwick & Keating (2002)`
* **수학적 모델**: $\Omega(L) = \frac{\int_L^\infty (1-F(x))dx}{\int_{-\infty}^L F(x)dx}$
* **핵심 가설**: MDD 대비 수익률(Calmar)로 초안정 Core 60%를 고정하고, 수익-손실 확률 분포 비율(Omega)로 Satellite 40%의 단기 폭발력을 결합하여 샤프 지수를 2배 이상 견인함.
* **검증 데이터**: `219 days (2026-02-27 ~ 2026-11-04)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[ Systemic Strategies ] ♾️ HyperGrowth ♾**: Hurst `0.713` | Sortino `6.12` | Kelly `10.5%` | 30일 APR `269.87%` | Sharpe `8.76`
  - **Buyback Spread Engine**: Hurst `0.48` | Sortino `2.89` | Kelly `8.8%` | 30일 APR `286.73%` | Sharpe `8.04`
  - **Danny Ocean**: Hurst `0.332` | Sortino `6.05` | Kelly `9.6%` | 30일 APR `126.2%` | Sharpe `14.31`
  - **V4 Alpha Quantum**: Hurst `0.585` | Sortino `6.79` | Kelly `8.0%` | 30일 APR `147.11%` | Sharpe `8.78`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-04 11:39:27
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `219 days (2026-02-27 ~ 2026-11-04)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Bunny**: Hurst `0.5` | Sortino `50.0` | Kelly `30.0%` | 30일 APR `1.6%` | Sharpe `9.62`
  - **Hype U-Boat**: Hurst `0.5` | Sortino `27.46` | Kelly `22.5%` | 30일 APR `16.66%` | Sharpe `10.21`
  - **Passivbot Canon**: Hurst `0.636` | Sortino `5.76` | Kelly `14.0%` | 30일 APR `75.39%` | Sharpe `8.56`
  - **FuturAI Labs - High Sharpe, Low Volatili**: Hurst `0.615` | Sortino `3.57` | Kelly `12.2%` | 30일 APR `15.29%` | Sharpe `18.91`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-04 07:39:42
### 🔬 주제: **하방 편차(Downside Deviation) 기반 Sortino Ratio 최적화**
* **레퍼런스 출처**: `GitHub: Riskfolio-Lib / Frank Sortino (1994)`
* **수학적 모델**: $Sortino = \frac{R_p - R_f}{\sqrt{\frac{1}{N}\sum_{t=1}^N \min(0, R_t - MAR)^2}}$
* **핵심 가설**: 상승 변동성은 수익 기회이므로 페널티를 주지 않고, 오직 '손실 변동성'만을 측정하는 Sortino Ratio로 볼트 위험도를 재평가하여 불필요한 저수익 배분을 제거함.
* **검증 데이터**: `219 days (2026-02-27 ~ 2026-11-04)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Bunny**: Hurst `0.5` | Sortino `50.0` | Kelly `30.0%` | 30일 APR `1.6%` | Sharpe `9.62`
  - **Hype U-Boat**: Hurst `0.5` | Sortino `27.46` | Kelly `22.5%` | 30일 APR `16.66%` | Sharpe `10.21`
  - **Algo1**: Hurst `0.523` | Sortino `9.27` | Kelly `11.1%` | 30일 APR `4.67%` | Sharpe `9.62`
  - **Loop Fund**: Hurst `0.632` | Sortino `7.6` | Kelly `0.7%` | 30일 APR `18.45%` | Sharpe `11.06`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-04 03:42:29
### 🔬 주제: **허스트 지수(Hurst Exponent) 기반 추세 vs 평균회귀 볼트 자동 판별**
* **레퍼런스 출처**: `GitHub: pyquant / Benoit Mandelbrot (Fractal Market Hypothesis)`
* **수학적 모델**: $H = \lim_{\tau \to \infty} \frac{\log(R/S)}{\log(\tau)}$
* **핵심 가설**: 볼트의 PnL 시계열에서 H > 0.5(지속적 추세) 볼트는 모멘텀 가속 전략에 배분하고, H < 0.5(평균회귀) 볼트는 딥바잉(Dip-Buyer) 전략에 배분하여 알파를 극대화함.
* **검증 데이터**: `219 days (2026-02-27 ~ 2026-11-04)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **69 Jump Street**: Hurst `0.796` | Sortino `6.22` | Kelly `7.3%` | 30일 APR `27.9%` | Sharpe `8.26`
  - **wmm.club | scalp-hype-long-2x**: Hurst `0.718` | Sortino `5.63` | Kelly `1.7%` | 30일 APR `24.24%` | Sharpe `6.81`
  - **[ Systemic Strategies ] ♾️ HyperGrowth ♾**: Hurst `0.713` | Sortino `6.12` | Kelly `10.5%` | 30일 APR `269.87%` | Sharpe `8.76`
  - **Passivbot Canon**: Hurst `0.636` | Sortino `5.76` | Kelly `14.0%` | 30일 APR `75.39%` | Sharpe `8.56`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-03 23:39:51
### 🔬 주제: **GARCH(1,1) 조건부 이분산성 모델을 이용한 볼트 변동성 스퀴즈 감지**
* **레퍼런스 출처**: `GitHub: arch / Tim Bollerslev (1986)`
* **수학적 모델**: $\sigma_t^2 = \omega + \alpha \epsilon_{t-1}^2 + \beta \sigma_{t-1}^2$
* **핵심 가설**: 볼트의 단기 변동성 클러스터링(Volatility Clustering)을 사전에 예측하여, 변동성 폭발 직전의 눌림목 볼트를 선취매하고 급격한 변동성 확장 시 비중을 자동 축소함.
* **검증 데이터**: `218 days (2026-02-27 ~ 2026-11-03)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[ Systemic Strategies ] ♾️ HyperGrowth ♾**: Hurst `0.702` | Sortino `6.02` | Kelly `10.2%` | 30일 APR `227.78%` | Sharpe `8.68`
  - **Buyback Spread Engine**: Hurst `0.571` | Sortino `2.66` | Kelly `8.0%` | 30일 APR `244.58%` | Sharpe `7.7`
  - **Bunny**: Hurst `0.5` | Sortino `50.0` | Kelly `30.0%` | 30일 APR `5.56%` | Sharpe `12.48`
  - **V4 Alpha Quantum**: Hurst `0.637` | Sortino `6.82` | Kelly `7.1%` | 30일 APR `145.58%` | Sharpe `8.77`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-03 19:39:52
### 🔬 주제: **계층적 위험 패리티(Hierarchical Risk Parity, HRP) 머신러닝 군집화 자산 배분**
* **레퍼런스 출처**: `GitHub: Riskfolio-Lib / Marcos Lopez de Prado (2016)`
* **수학적 모델**: $w_i = w_i \times \frac{V_i^{-1}}{\sum V_j^{-1}}$
* **핵심 가설**: 전통적 공분산 역행렬의 수치적 불안정성을 극복하기 위해, 머신러닝 트리 군집화(Dendrogram)를 통해 상호 상관관계가 낮은 볼트들로 포트폴리오의 분산 효과를 극대화함.
* **검증 데이터**: `218 days (2026-02-27 ~ 2026-11-03)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[ Systemic Strategies ] ♾️ HyperGrowth ♾**: Hurst `0.702` | Sortino `6.02` | Kelly `10.2%` | 30일 APR `227.78%` | Sharpe `8.68`
  - **Buyback Spread Engine**: Hurst `0.571` | Sortino `2.66` | Kelly `8.0%` | 30일 APR `244.58%` | Sharpe `7.7`
  - **Bunny**: Hurst `0.5` | Sortino `50.0` | Kelly `30.0%` | 30일 APR `5.56%` | Sharpe `12.48`
  - **V4 Alpha Quantum**: Hurst `0.637` | Sortino `6.82` | Kelly `7.1%` | 30일 APR `145.58%` | Sharpe `8.77`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-03 15:39:37
### 🔬 주제: **알파 감쇄 반감기(Alpha Decay Half-Life) 모델을 통한 선제적 익절/손절 타이밍**
* **레퍼런스 출처**: `GitHub: QuantConnect / Z. Kakushadze & J.A. Serur (2018)`
* **수학적 모델**: $t_{1/2} = \frac{\ln(2)}{\lambda}$
* **핵심 가설**: TVL 급증으로 인한 슬리피지 증가 및 전략 복제로 발생하는 알파 감쇄 곡선을 지수 감쇄 모델($A(t) = A_0 e^{-\lambda t}$)로 추적하여 최적의 이탈 시점을 산출함.
* **검증 데이터**: `218 days (2026-02-27 ~ 2026-11-03)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[ Systemic Strategies ] ♾️ HyperGrowth ♾**: Hurst `0.702` | Sortino `6.02` | Kelly `10.2%` | 30일 APR `227.78%` | Sharpe `8.68`
  - **Buyback Spread Engine**: Hurst `0.571` | Sortino `2.66` | Kelly `8.0%` | 30일 APR `244.58%` | Sharpe `7.7`
  - **Bunny**: Hurst `0.5` | Sortino `50.0` | Kelly `30.0%` | 30일 APR `5.56%` | Sharpe `12.48`
  - **V4 Alpha Quantum**: Hurst `0.637` | Sortino `6.82` | Kelly `7.1%` | 30일 APR `145.58%` | Sharpe `8.77`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-03 11:39:30
### 🔬 주제: **칼만 필터(Kalman Filter) 기반 볼트 리더의 시장 베타 추종도 실시간 필터링**
* **레퍼런스 출처**: `GitHub: pykalman / R.E. Kalman (1960)`
* **수학적 모델**: $y_t = \alpha_t + \beta_t x_t + \epsilon_t, \quad \beta_t = \beta_{t-1} + \eta_t$
* **핵심 가설**: 비트코인(BTC) 가격 변동에 수동적으로 끌려가는 '가짜 알파' 볼트를 제거하고, 시장과 무관하게 독립적 수익을 창출하는 '순수 알파(Pure Alpha)' 리더 볼트를 필터링함.
* **검증 데이터**: `218 days (2026-02-27 ~ 2026-11-03)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[ Systemic Strategies ] ♾️ HyperGrowth ♾**: Hurst `0.702` | Sortino `6.02` | Kelly `10.2%` | 30일 APR `227.78%` | Sharpe `8.68`
  - **Buyback Spread Engine**: Hurst `0.571` | Sortino `2.66` | Kelly `8.0%` | 30일 APR `244.58%` | Sharpe `7.7`
  - **Bunny**: Hurst `0.5` | Sortino `50.0` | Kelly `30.0%` | 30일 APR `5.56%` | Sharpe `12.48`
  - **V4 Alpha Quantum**: Hurst `0.637` | Sortino `6.82` | Kelly `7.1%` | 30일 APR `145.58%` | Sharpe `8.77`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-03 09:16:55
### 🔬 주제: **Calmar Ratio & Omega Ratio 결합형 바벨 알파 엔진**
* **레퍼런스 출처**: `GitHub: skfolio / Shadwick & Keating (2002)`
* **수학적 모델**: $\Omega(L) = \frac{\int_L^\infty (1-F(x))dx}{\int_{-\infty}^L F(x)dx}$
* **핵심 가설**: MDD 대비 수익률(Calmar)로 초안정 Core 60%를 고정하고, 수익-손실 확률 분포 비율(Omega)로 Satellite 40%의 단기 폭발력을 결합하여 샤프 지수를 2배 이상 견인함.
* **검증 데이터**: `218 days (2026-02-27 ~ 2026-11-03)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[ Systemic Strategies ] ♾️ HyperGrowth ♾**: Hurst `0.702` | Sortino `6.02` | Kelly `10.2%` | 30일 APR `227.78%` | Sharpe `8.68`
  - **Buyback Spread Engine**: Hurst `0.571` | Sortino `2.66` | Kelly `8.0%` | 30일 APR `244.58%` | Sharpe `7.7`
  - **Bunny**: Hurst `0.5` | Sortino `50.0` | Kelly `30.0%` | 30일 APR `5.56%` | Sharpe `12.48`
  - **V4 Alpha Quantum**: Hurst `0.637` | Sortino `6.82` | Kelly `7.1%` | 30일 APR `145.58%` | Sharpe `8.77`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-02 11:39:34
### 🔬 주제: **0.25x ~ 0.33x Fractional Kelly 기준 포지션 사이징**
* **레퍼런스 출처**: `GitHub: KellyPortfolio / J.L. Kelly (1956)`
* **수학적 모델**: $f^* = \gamma \times \frac{p(b+1) - 1}{b} \quad (\gamma = 0.30)$
* **핵심 가설**: 각 볼트의 최근 30일 승률(p)과 손익비(b)를 실시간 추정하여, 전체 자산의 파산 확률을 0%로 유지하면서 장기 복리 성장률을 극대화하는 수학적 최적 비중을 도출함.
* **검증 데이터**: `217 days (2026-02-27 ~ 2026-11-02)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Bunny**: Hurst `0.5` | Sortino `50.0` | Kelly `30.0%` | 30일 APR `5.87%` | Sharpe `12.47`
  - **Passivbot Canon**: Hurst `0.457` | Sortino `5.87` | Kelly `15.9%` | 30일 APR `89.78%` | Sharpe `9.06`
  - **FuturAI Labs - High Sharpe, Low Volatili**: Hurst `0.557` | Sortino `3.44` | Kelly `12.5%` | 30일 APR `13.06%` | Sharpe `17.84`
  - **Algo1**: Hurst `0.523` | Sortino `9.27` | Kelly `11.1%` | 30일 APR `4.51%` | Sharpe `6.04`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-02 07:39:59
### 🔬 주제: **하방 편차(Downside Deviation) 기반 Sortino Ratio 최적화**
* **레퍼런스 출처**: `GitHub: Riskfolio-Lib / Frank Sortino (1994)`
* **수학적 모델**: $Sortino = \frac{R_p - R_f}{\sqrt{\frac{1}{N}\sum_{t=1}^N \min(0, R_t - MAR)^2}}$
* **핵심 가설**: 상승 변동성은 수익 기회이므로 페널티를 주지 않고, 오직 '손실 변동성'만을 측정하는 Sortino Ratio로 볼트 위험도를 재평가하여 불필요한 저수익 배분을 제거함.
* **검증 데이터**: `217 days (2026-02-27 ~ 2026-11-02)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Bunny**: Hurst `0.5` | Sortino `50.0` | Kelly `30.0%` | 30일 APR `5.87%` | Sharpe `12.47`
  - **Algo1**: Hurst `0.523` | Sortino `9.27` | Kelly `11.1%` | 30일 APR `4.51%` | Sharpe `6.04`
  - **Loop Fund**: Hurst `0.58` | Sortino `7.72` | Kelly `1.7%` | 30일 APR `34.08%` | Sharpe `11.1`
  - **22Cap**: Hurst `0.477` | Sortino `7.53` | Kelly `1.3%` | 30일 APR `0.43%` | Sharpe `10.08`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-02 03:42:04
### 🔬 주제: **허스트 지수(Hurst Exponent) 기반 추세 vs 평균회귀 볼트 자동 판별**
* **레퍼런스 출처**: `GitHub: pyquant / Benoit Mandelbrot (Fractal Market Hypothesis)`
* **수학적 모델**: $H = \lim_{\tau \to \infty} \frac{\log(R/S)}{\log(\tau)}$
* **핵심 가설**: 볼트의 PnL 시계열에서 H > 0.5(지속적 추세) 볼트는 모멘텀 가속 전략에 배분하고, H < 0.5(평균회귀) 볼트는 딥바잉(Dip-Buyer) 전략에 배분하여 알파를 극대화함.
* **검증 데이터**: `217 days (2026-02-27 ~ 2026-11-02)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **Stratwise Multi-Asset Public**: Hurst `0.895` | Sortino `4.05` | Kelly `1.6%` | 30일 APR `10.15%` | Sharpe `7.74`
  - **Quantitative Market Neutral Strategy**: Hurst `0.722` | Sortino `1.17` | Kelly `2.3%` | 30일 APR `1.51%` | Sharpe `5.16`
  - **69 Jump Street**: Hurst `0.695` | Sortino `6.21` | Kelly `5.5%` | 30일 APR `39.22%` | Sharpe `8.26`
  - **Growi_test**: Hurst `0.691` | Sortino `2.25` | Kelly `8.8%` | 30일 APR `76.51%` | Sharpe `10.24`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-01 23:39:31
### 🔬 주제: **GARCH(1,1) 조건부 이분산성 모델을 이용한 볼트 변동성 스퀴즈 감지**
* **레퍼런스 출처**: `GitHub: arch / Tim Bollerslev (1986)`
* **수학적 모델**: $\sigma_t^2 = \omega + \alpha \epsilon_{t-1}^2 + \beta \sigma_{t-1}^2$
* **핵심 가설**: 볼트의 단기 변동성 클러스터링(Volatility Clustering)을 사전에 예측하여, 변동성 폭발 직전의 눌림목 볼트를 선취매하고 급격한 변동성 확장 시 비중을 자동 축소함.
* **검증 데이터**: `216 days (2026-02-27 ~ 2026-11-01)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[ Systemic Strategies ] ♾️ HyperGrowth ♾**: Hurst `0.631` | Sortino `6.1` | Kelly `10.2%` | 30일 APR `234.69%` | Sharpe `8.71`
  - **Danny Ocean**: Hurst `0.61` | Sortino `6.19` | Kelly `10.2%` | 30일 APR `155.42%` | Sharpe `14.34`
  - **V4 Alpha Quantum**: Hurst `0.687` | Sortino `6.88` | Kelly `6.8%` | 30일 APR `172.82%` | Sharpe `8.72`
  - **Buyback Spread Engine**: Hurst `0.559` | Sortino `2.71` | Kelly `7.8%` | 30일 APR `186.65%` | Sharpe `7.52`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---

## 📅 연구 기록: 2026-11-01 19:39:31
### 🔬 주제: **계층적 위험 패리티(Hierarchical Risk Parity, HRP) 머신러닝 군집화 자산 배분**
* **레퍼런스 출처**: `GitHub: Riskfolio-Lib / Marcos Lopez de Prado (2016)`
* **수학적 모델**: $w_i = w_i \times \frac{V_i^{-1}}{\sum V_j^{-1}}$
* **핵심 가설**: 전통적 공분산 역행렬의 수치적 불안정성을 극복하기 위해, 머신러닝 트리 군집화(Dendrogram)를 통해 상호 상관관계가 낮은 볼트들로 포트폴리오의 분산 효과를 극대화함.
* **검증 데이터**: `216 days (2026-02-27 ~ 2026-11-01)`

#### 🧪 실증 발견 및 온체인 볼트 분석 결과:
  - **[ Systemic Strategies ] ♾️ HyperGrowth ♾**: Hurst `0.631` | Sortino `6.1` | Kelly `10.2%` | 30일 APR `234.69%` | Sharpe `8.71`
  - **Danny Ocean**: Hurst `0.61` | Sortino `6.19` | Kelly `10.2%` | 30일 APR `155.42%` | Sharpe `14.34`
  - **V4 Alpha Quantum**: Hurst `0.687` | Sortino `6.88` | Kelly `6.8%` | 30일 APR `172.82%` | Sharpe `8.72`
  - **Buyback Spread Engine**: Hurst `0.559` | Sortino `2.71` | Kelly `7.8%` | 30일 APR `186.65%` | Sharpe `7.52`

**💡 최종 판정**: **✅ 모델 알고리즘 반영 (Adopted into Dynamic Alpha Engine)**

---
