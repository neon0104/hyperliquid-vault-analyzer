# Hyperliquid Vault Analyzer

Hyperliquid 거래소의 User Vault 데이터를 수집, 분석하여 **바벨 전략(Barbell Strategy)** 기반의 최적 포트폴리오를 추천하고, 사용자에게 텔레그램 푸시 알림을 제공하는 Windows 데스크톱 애플리케이션입니다.

## 주요 기능
*   **데이터 수집**: Hyperliquid 공식 API를 통해 TVL 상위 활성 Vault들의 전체 시계열(자산 가치 및 PnL) 데이터를 수집합니다.
*   **성과 분석**: 각 Vault의 누적 수익률, MDD(Maximum Drawdown), 현재 하락폭, 그리고 회복성(Recovery Factor)을 계산합니다.
*   **바벨 포트폴리오**: 
    *   안정 추구형(50%): MDD가 낮으면서 꾸준한 수익을 내는 Vault를 선정 (위험 역가중 배분).
    *   회복 탄력형(50%): 현재 큰 하락 중이나 과거 회복성이 뛰어난 Vault를 선정 (회복성 비례 배분).
    *   전체 포트폴리오는 20개 이하의 Vault로 구성됩니다.
*   **푸시 알림**: 포트폴리오 변경, 큰 폭의 수익/손실 발생 시, 혹은 정기 리포트(일간/주간)를 텔레그램을 통해 발송합니다.
*   **로컬 데이터 저장**: 사용자가 지정한 로컬 D드라이브 경로에 SQLite 데이터베이스 및 JSON 스냅샷 형태로 모든 데이터를 안전하게 저장합니다.

## 설치 및 실행 방법 (개발 환경)

1.  Python 3.11 이상 설치
2.  의존성 패키지 설치:
    ```bash
    pip install -r requirements.txt
    ```
3.  앱 실행 (GUI 모드):
    ```bash
    python main.py
    ```
4.  앱 실행 (Headless / 스케줄러 모드):
    ```bash
    python main.py --once
    ```

## D드라이브 경로 설정
애플리케이션을 처음 실행하면 Windows 환경에서 D드라이브가 존재할 경우 자동으로 `D:\HyperliquidVaultAnalyzer` 경로를 기본 데이터 저장소로 설정합니다. D드라이브가 없거나 다른 경로를 원할 경우, 앱 내 **Settings 탭**에서 `Browse...` 버튼을 눌러 원하는 폴더를 지정하고 `Save & Apply`를 클릭하세요. 데이터베이스와 스냅샷 폴더가 해당 경로에 자동 생성됩니다.

## 텔레그램 봇 연동 가이드
포트폴리오 알림을 받으려면 텔레그램 봇을 생성하여 앱에 연동해야 합니다.

1.  텔레그램 앱을 열고 **@BotFather**를 검색합니다.
2.  `/newbot` 메시지를 보내고 봇의 이름과 사용자명(username)을 설정합니다.
3.  BotFather가 제공하는 **봇 토큰(Bot Token)**(예: `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)을 복사합니다.
4.  텔레그램에서 방금 만든 봇을 검색하여 대화방을 열고 `/start`를 보냅니다.
5.  웹 브라우저를 열고 `https://api.telegram.org/bot<복사한_봇_토큰>/getUpdates` 주소로 접속합니다.
6.  화면에 표시된 JSON 응답에서 `"chat": {"id": 123456789}` 부분을 찾아 **숫자(chat_id)**를 복사합니다.
7.  앱의 **Settings 탭**에서 `Notification provider`를 `telegram`으로 두고, 복사한 토큰과 chat_id를 입력한 뒤 `Save & Apply`를 누릅니다.
8.  `Send Test Notification` 메뉴를 클릭하여 텔레그램 메시지가 정상적으로 오는지 확인합니다.

## 푸시 채널 교체 방법 (모바일 앱 연동 준비)
본 애플리케이션의 알림 시스템은 확장 가능한 인터페이스(`NotificationProvider`)로 설계되었습니다. 향후 전용 모바일 앱(Expo 또는 FCM 기반)이 준비되면 코드 수정 없이 설정만으로 채널을 교체할 수 있습니다.

1.  앱의 **Settings 탭**에서 `Notification provider` 드롭다운을 `expo` 또는 `fcm`으로 변경합니다.
2.  현재 UI에는 토큰 입력 칸이 텔레그램용만 노출되므로, 설정 파일(`C:\Users\<사용자명>\.hyperliquid_vault_analyzer\config.json`)을 직접 텍스트 편집기로 엽니다.
3.  다음 키를 추가/수정합니다.
    *   Expo의 경우: `"expo_push_token": "ExponentPushToken[xxxxxx]"`
    *   FCM의 경우: `"fcm_server_key": "AAAA...", "fcm_token": "..."`
4.  앱을 재시작하면 새로운 푸시 채널을 통해 알림이 발송됩니다. 새로운 채널의 구체적인 구현은 `app/notifications/expo_notifier.py` 및 `fcm_notifier.py`를 참고하세요.

## 바벨 전략 및 알람 조건 설명

**바벨 전략 배분**
포트폴리오는 전체 자본을 50:50으로 두 그룹에 나눕니다. 안정 그룹은 MDD 역가중 방식(`1/MDD`)을 사용하여 MDD가 0에 가까운 Vault에 비중이 집중될 수 있습니다. 만약 특정 Vault의 비중이 과도하게 쏠리는 것을 원치 않는다면, 추후 `portfolio.py`의 `_normalize` 함수 내에 개별 최대 비중 캡(Cap)을 추가할 수 있습니다.

**알람 트리거 조건**
앱은 백그라운드 스케줄러를 통해 지정된 간격(기본 60분)마다 다음 조건들을 검사합니다.
*   **(a) 추천 포트폴리오 변경**: 바벨 전략에 의해 선정된 Vault 목록이 바뀌거나 개별 비중이 1% 이상 변동되었을 때 알림을 보냅니다.
*   **(b) 큰 손실 또는 수익**: 포트폴리오에 포함된 Vault 중 누적 수익률의 절대값이 설정된 임계값(기본 10%)을 초과할 때 즉각 알림을 보냅니다.
*   **(c) 정기 리포트**: Settings 탭에서 설정한 일간(Daily) 또는 주간(Weekly) 지정 시간에 현재 포트폴리오 요약 정보를 발송합니다.

---
**Author**: Manus AI

## Protocol Vault 제외 정책 (User Vault 전용)
Hyperliquid 공식이 운영하는 프로토콜 금고(HLP, HLP Liquidator 등)는 사용자 운영(User Vault)이 아니므로 포트폴리오 분석 대상에서 **완전히 제외**됩니다. 제외 기준은 다음과 같습니다.
1.  알려진 Protocol Leader 주소 차단 (`0x677d831aef5328190852e24f13c46cac05f984e7` 등)
2.  알려진 Protocol Vault 주소 차단 (HLP, HLP Strategy A/B, HLP Liquidator 2 등)
3.  Vault 이름 내에 `HLP`, `Hyperliquidity Provider`, `Liquidator` 등 특정 문자열 포함 시 차단
4.  다른 Vault의 자식(child)으로 종속된 하위 전략 Vault 차단

이 정책은 앱 실행 시 자동으로 적용되며, 사용자가 직접 `~/.hyperliquid_vault_analyzer/config.json` 파일을 열어 `exclude_name_substrings`, `exclude_vault_addresses` 배열에 블랙리스트를 추가하여 커스터마이징할 수 있습니다.

## 검증 결과 (TVL 상위 200개)
실제 Hyperliquid Mainnet 데이터를 대상으로 수행한 200개 풀 파이프라인 검증 결과입니다.
*   **처리 시간**: 약 57초 (동시성 5, 지수 백오프 적용으로 Rate Limit 429 회피)
*   **전체 Vault 풀**: 9,451개 중 활성 Vault 3,287개 추출
*   **Protocol Vault 제외**: 총 11개 제외 (이름 매칭 3건, 자식 종속 4건, 직접 주소 차단 4건)
*   **최종 대상**: 남은 3,276개의 User Vault 중 TVL 상위 200개
*   **데이터 수집 성공률**: 200개 중 182개 시계열 확보 성공, 18개는 거래 이력이 없는 신규 Vault로 분석 자동 스킵
*   **최종 포트폴리오**: Stable 그룹 10개(49.98%), Recovery 그룹 10개(50.01%)로 정확한 50:50 비중 분할 확인. HLP 등 Protocol Vault 누출 0건.
