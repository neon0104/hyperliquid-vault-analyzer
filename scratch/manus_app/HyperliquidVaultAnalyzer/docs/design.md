# Hyperliquid Vault 바벨 전략 포트폴리오 데스크톱 앱 설계 문서

## 1. 아키텍처 개요

본 애플리케이션은 Hyperliquid 거래소의 User Vault 데이터를 수집, 분석하여 바벨 전략 기반의 최적 포트폴리오를 추천하고, 사용자에게 텔레그램 등의 채널로 푸시 알림을 제공하는 Windows 데스크톱 애플리케이션입니다. 

사용자 UI, 데이터 수집 스케줄러, 분석 모듈, 알림 모듈이 유기적으로 상호작용하는 구조로 설계되었습니다. 애플리케이션은 Python 3.11 이상 환경에서 PySide6를 이용한 그래픽 인터페이스를 제공하며, 백그라운드에서는 APScheduler를 통해 주기적인 데이터 수집 및 분석을 수행합니다. 데이터는 사용자가 지정한 D드라이브 경로에 SQLite 데이터베이스와 JSON 스냅샷 형태로 안전하게 보관됩니다. 배포 시에는 PyInstaller를 사용하여 단일 실행 파일(`.exe`)로 패키징되어 사용자의 설치 편의성을 높입니다.

## 2. 데이터 흐름 (Data Flow)

애플리케이션의 데이터 파이프라인은 크게 수집, 저장, 분석, 포트폴리오 구성, 알림의 5단계로 이루어집니다.

첫째, **데이터 수집 단계**에서는 비동기 네트워크 통신을 통해 Hyperliquid 공식 stats API로부터 전체 Vault 스냅샷을 가져옵니다. 수집된 수천 개의 Vault 중 운영이 종료되지 않은 활성 상태이면서 Total Value Locked(TVL) 기준 상위 200개만을 1차로 필터링합니다. 이후 선별된 상위 200개 Vault 각각에 대해 상세 API를 호출하여 자산 가치(Account Value)와 손익(PnL)에 대한 시계열 데이터를 확보합니다.

둘째, **데이터 저장 단계**에서는 수집된 시계열 데이터와 메타데이터를 로컬 저장소에 기록합니다. 사용자가 설정 화면에서 지정한 D드라이브 경로(예: `D:\HyperliquidVaultAnalyzer\data`)를 최우선으로 사용하며, 해당 경로에 SQLite 데이터베이스 테이블을 구성하고 원본 JSON 데이터를 스냅샷 형태로 백업합니다.

셋째, **데이터 분석 단계**에서는 저장된 시계열 데이터를 바탕으로 각 Vault의 핵심 성과 지표를 산출합니다. 가장 높은 고점 대비 하락폭을 의미하는 MDD(Maximum Drawdown), 누적 수익률, 그리고 하락 이후의 회복력을 나타내는 Recovery Factor를 수학적 모델을 통해 계산합니다.

넷째, **포트폴리오 구성 단계**에서는 계산된 지표를 바탕으로 바벨 전략을 적용합니다. 전체 포트폴리오는 최대 20개의 Vault로 제한되며, 안정성을 추구하는 그룹과 회복 탄력성을 노리는 공격형 그룹으로 50%씩 비중이 나뉩니다. 각 그룹 내에서의 개별 Vault 비중은 위험도나 회복성에 비례하여 차등 산정됩니다.

다섯째, **알림 발송 단계**에서는 백그라운드 스케줄러가 포트폴리오의 변경 사항이나 설정된 임계값을 초과하는 큰 손익 발생을 감지합니다. 조건이 충족되면 추상화된 알림 제공자(Notification Provider)를 통해 사용자에게 즉각적인 푸시 메시지나 정기 리포트를 전송합니다.

## 3. 분석 알고리즘 및 바벨 전략 비중 산정

### 3.1 핵심 지표 산출 수식

각 Vault의 성과를 평가하기 위해 세 가지 핵심 지표를 산출합니다.

| 지표명 | 설명 | 산출 수식 |
| :--- | :--- | :--- |
| **수익률 (Return)** | 초기 투자금 대비 현재 자산 가치의 증감 비율입니다. | $Return = \frac{Current\_Value - Initial\_Value}{Initial\_Value}$ |
| **MDD (Maximum Drawdown)** | 특정 기간 동안 최고점(Peak) 대비 최저점(Trough)의 최대 하락 비율을 의미하며, 위험도를 측정합니다. | $MDD = \max \left( \frac{Peak\_Value - Trough\_Value}{Peak\_Value} \right)$ |
| **회복성 (Recovery Factor)** | 누적 수익을 MDD로 나눈 값으로, 하락을 겪은 후 얼마나 빠르고 강하게 수익을 회복하는지를 나타냅니다. | $Recovery\_Factor = \frac{Cumulative\_Return}{MDD}$ |

### 3.2 바벨 전략 (Barbell Strategy) 구성

바벨 전략은 극단적인 두 가지 성향의 자산을 조합하여 중간 수준의 위험을 배제하고, 하방 경직성을 확보하면서 상방 잠재력을 극대화하는 투자 기법입니다. 본 애플리케이션은 선정된 최대 20개의 Vault를 두 그룹으로 나누어 각각 50%의 자금을 배분합니다.

**안정 추구형 그룹 (비중 50%)**
이 그룹은 MDD가 낮으면서도 꾸준한 우상향 수익률을 기록하는 Vault들로 구성됩니다. 수익률을 MDD로 나눈 값(Calmar Ratio와 유사)이 높은 상위 Vault들을 선별합니다. 그룹 내 개별 Vault의 투자 비중은 위험 역가중 방식을 적용하여, MDD가 낮을수록 더 높은 비중을 할당받도록 설계되었습니다.

**회복 탄력성/공격형 그룹 (비중 50%)**
이 그룹은 현재 고점 대비 상당한 하락(MDD에 근접한 마이너스 수익률)을 겪고 있으나, 과거 데이터상 회복성(Recovery Factor)이 매우 뛰어난 Vault들로 구성됩니다. 즉, 반등 시 큰 수익을 기대할 수 있는 자산들입니다. 그룹 내 개별 비중은 각 Vault의 Recovery Factor 수치에 정비례하여 산정되며, 과거 회복력이 입증된 곳에 더 많은 자본을 투입합니다.

## 4. 푸시 채널 교체 설계 (Notification Provider)

알림 시스템은 향후 모바일 앱 전용 푸시 등 다양한 채널로의 확장을 고려하여 추상화된 인터페이스로 설계되었습니다. 의존성 역전 원칙을 적용하여 비즈니스 로직은 구체적인 알림 방식에 의존하지 않습니다.

추상 기본 클래스인 `NotificationProvider`는 메시지 전송을 위한 단일 인터페이스를 정의합니다. 초기 버전에서는 텔레그램 Bot API를 활용하는 `TelegramNotifier`가 기본 구현체로 제공됩니다. 사용자는 앱 설정 화면에서 발급받은 봇 토큰과 채팅 ID를 입력하여 알림을 수신할 수 있습니다.

앱의 설정 데이터(config.json 또는 SQLite)에는 현재 활성화된 알림 제공자의 식별자(예: `telegram`)가 저장됩니다. 런타임 시 팩토리 패턴이 이 설정값을 읽어 적절한 알림 객체를 생성하고 주입합니다. 향후 `ExpoPushNotifier`나 `FCMNotifier`와 같은 새로운 클래스가 추가되더라도, 핵심 로직의 수정 없이 설정 변경만으로 푸시 채널을 유연하게 교체할 수 있습니다.

## 5. API 호출 명세

데이터 수집은 Hyperliquid의 두 가지 주요 엔드포인트를 조합하여 이루어집니다.

| 목적 | HTTP 메서드 및 엔드포인트 | 요청/응답 주요 데이터 |
| :--- | :--- | :--- |
| **전체 Vault 요약 및 TVL 필터링** | `GET https://stats-data.hyperliquid.xyz/Mainnet/vaults` | 전체 Vault 배열 반환. 각 객체의 `summary` 필드 내 `tvl`, `vaultAddress`, `isClosed` 확인 |
| **Vault 상세 시계열 데이터 획득** | `POST https://api.hyperliquid.xyz/info` | Payload: `{"type": "vaultDetails", "vaultAddress": "..."}`<br>응답: `portfolio` 내 시계열 `accountValueHistory`, `pnlHistory` |

전체 요약 API를 1회 호출하여 활성 상태의 상위 200개 대상을 선별한 후, 해당 대상들에 한해 상세 API를 개별 호출함으로써 네트워크 부하를 최소화하고 효율적으로 시계열 데이터를 구축합니다.

## 6. Protocol Vault 제외 정책 (User Vault 전용)

Hyperliquid의 생태계에는 공식이 직접 운영하는 HLP(Hyperliquidity Provider) 및 그 하위 전략(Liquidator 등)이 존재합니다. 본 애플리케이션은 **일반 사용자가 운영하는 User Vault**만을 대상으로 하므로, 데이터 수집 직후 아래 4가지 독립적인 필터를 통해 Protocol Vault를 완벽히 제외합니다.

1.  **Leader 주소 블랙리스트**: HLP를 운영하는 공식 Leader 주소(`0x677d831aef5328190852e24f13c46cac05f984e7`)를 차단합니다.
2.  **Vault 주소 블랙리스트**: 알려진 HLP 본체 및 Strategy A/B, Liquidator 2 등의 직접 주소를 차단합니다.
3.  **이름 포함어 블랙리스트**: Vault 이름에 `HLP`, `Hyperliquidity Provider`, `Liquidator`가 포함된 경우 차단합니다.
4.  **Relationship 필터**: `relationship.type == 'child'`인 Vault는 마스터 Vault에 종속된 전략이므로 차단합니다.

이 필터들은 `app/data/filters.py`에 구현되어 있으며, 차단 조건은 `config.json`을 통해 사용자가 런타임에 갱신할 수 있습니다.

## 7. 검증 결과 (TVL 상위 200개 풀 테스트)

실제 Hyperliquid Mainnet 데이터를 대상으로 수행한 200개 풀 파이프라인 검증 결과입니다.
*   **처리 시간**: 약 57초 (동시성 5, 지수 백오프 적용으로 Rate Limit 429 회피)
*   **전체 Vault 풀**: 9,451개 중 활성 Vault 3,287개 추출
*   **Protocol Vault 제외**: 총 11개 제외 (이름 매칭 3건, 자식 종속 4건, 직접 주소 차단 4건)
*   **최종 대상**: 남은 3,276개의 User Vault 중 TVL 상위 200개
*   **데이터 수집 성공률**: 200개 중 182개 시계열 확보 성공, 18개는 거래 이력이 없는 신규 Vault로 분석 자동 스킵
*   **최종 포트폴리오**: Stable 그룹 10개(49.98%), Recovery 그룹 10개(50.01%)로 정확한 50:50 비중 분할 확인. HLP 등 Protocol Vault 누출 0건.
