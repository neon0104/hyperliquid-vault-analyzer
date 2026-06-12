# Windows 실행 파일 (.exe) 빌드 가이드

이 문서는 완성된 Python 코드를 사용자가 클릭 한 번으로 실행할 수 있는 단일 Windows 실행 파일(`.exe`)로 패키징하는 방법을 안내합니다.

## 필수 준비물
1.  **Windows OS**: `.exe` 파일은 Windows 환경에서 빌드해야 정상적으로 동작합니다.
2.  **Python 3.11+**: 시스템에 Python이 설치되어 있어야 합니다.
3.  **PyInstaller**: 파이썬 코드를 패키징해주는 도구입니다.

## 빌드 단계

1.  명령 프롬프트(cmd) 또는 PowerShell을 열고 프로젝트 폴더(`HyperliquidVaultAnalyzer`)로 이동합니다.
2.  가상 환경(선택 사항)을 활성화한 후, 필요한 패키지를 모두 설치합니다.
    ```bash
    pip install -r requirements.txt
    pip install pyinstaller
    ```
3.  다음 명령어를 실행하여 단일 실행 파일로 빌드합니다.
    ```bash
    pyinstaller --noconfirm --onedir --windowed --name "HyperliquidVaultAnalyzer" "main.py"
    ```
    *   `--onedir`: 실행 속도를 높이고 문제를 줄이기 위해 폴더 형태로 빌드합니다. 단일 파일을 원할 경우 `--onefile`을 사용할 수 있으나 PySide6 앱의 경우 초기 실행 속도가 느려질 수 있습니다.
    *   `--windowed`: 콘솔(검은색 터미널 창)을 숨기고 GUI만 띄웁니다.
    *   `--name`: 생성될 폴더 및 실행 파일의 이름을 지정합니다.

4.  빌드가 완료되면 프로젝트 폴더 내에 `dist` 폴더가 생성됩니다.
5.  `dist\HyperliquidVaultAnalyzer` 폴더 안으로 들어가면 `HyperliquidVaultAnalyzer.exe` 파일이 있습니다. 이 파일을 더블 클릭하면 애플리케이션이 실행됩니다.

## 배포
사용자에게 전달할 때는 `dist\HyperliquidVaultAnalyzer` 폴더 전체를 ZIP 파일로 압축하여 전달하면 됩니다. 사용자는 압축을 풀고 안의 `.exe` 파일을 실행하기만 하면 되며, 별도의 파이썬 설치가 필요하지 않습니다.
