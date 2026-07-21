# Hyperliquid Vault Analyzer

A heuristic analysis tool for Hyperliquid vaults that provides portfolio scoring, risk metrics, and rebalancing suggestions.

> Note: This project uses **rule-based heuristic scoring** (weighted metric sums, robustness of the PnL curve, drawdown/Sharpe filters). It does **not** use machine-learning models. Any "prediction" is an extrapolation of recent APR, not an ML forecast. Treat all projected returns as rough estimates, not guarantees.

## Features

### Heuristic Portfolio Scoring
- Weighted-metric allocation across vaults (Sharpe, APR, drawdown, robustness)
- Risk-adjusted ranking and filters
- Dynamic rebalancing recommendations

### Risk Analysis & Metrics
- Volatility assessment
- Drawdown calculations
- Sharpe ratio computation
- Risk level classification

### Performance Estimation
- Recent-APR-based return extrapolation (rough estimate, not a forecast)
- Heuristic robustness scoring of the PnL curve

### APR Calculations
- 30-day and all-time APR tracking
- Weighted portfolio APR
- ROI analysis

### Comprehensive Reporting
- Excel report generation
- Multi-sheet detailed analysis
- Portfolio summary statistics

## Installation

1. Clone the repository:
```bash
git clone https://github.com/StreetJammer/hyperliquid-vault-analyzer.git
cd hyperliquid-vault-analyzer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Copy the example configuration file:
```bash
cp config.example.json config.json
```

2. Edit `config.json` with your **public wallet address only**:
```json
{
    "account_address": "your_wallet_address"
}
```

> ⚠️ **Do NOT put a private key / API secret in this file.** This tool only reads public
> vault data, so no secret key is required. `config.json` is git-ignored, but committing a
> private key here would expose your funds. For CI, set the `ACCOUNT_ADDRESS` secret instead
> of committing the file.


## Usage

The actual entry points are the scripts in the repository root (there is no `analyzer` package):

### Run a one-off vault analysis
```bash
python analyze_top_vaults.py          # 최신 스냅샷 분석 + 추천 + Excel 리포트
python analyze_top_vaults.py --force  # 캐시 무시하고 새로 수집
```

### Collect daily PnL history
```bash
python daily_pnl_collector.py         # 상위 볼트 PnL을 vault_data/pnl_history.db 에 축적
```

### Run the scheduler (daily automation)
```bash
python scheduler.py                   # 매일 09:00 자동 분석 (계속 실행)
python scheduler.py --now             # 즉시 1회 실행 후 종료
```

### Launch the web dashboard
```bash
python web_dashboard.py               # http://localhost:5001 (PORT 환경변수로 변경 가능)
```

Environment variables (recommended for anything public):
`JWT_SECRET_KEY`, `ADMIN_PASSWORD`, `ADMIN_EMAIL`, `SECURE_COOKIES=1` (HTTPS 배포),
`ALLOW_REGISTRATION=1` (로컬 계정 생성 시에만), `EXPORT_MY_PORTFOLIO=1` (개인 포트폴리오 공개 시에만),
`ACCOUNT_ADDRESS` (CI에서 config.json 대체).

## Security Considerations

1. **API Keys**: Store your API keys and wallet addresses securely. Never commit them to version control.

2. **Configuration**: Use environment variables or secure configuration management for sensitive data.

3. **Private Keys**: Never share or expose your private keys. The analyzer only requires read access to vault data.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for informational purposes only. Always conduct your own research and due diligence before making investment decisions. Past performance does not guarantee future results.
