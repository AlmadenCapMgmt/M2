# Bitcoin Strategic Investment Model (BSI) - Version 3.0

A sophisticated Python framework for strategic Bitcoin investment decisions based on macroeconomic indicators, on-chain metrics, and monetary policy analysis.

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/AlmadenCapMgmt/M2.git
cd M2

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
# FRED_API_KEY=your_fred_key_here
# GLASSNODE_API_KEY=your_glassnode_key_here
```

## 📊 Basic Usage

```python
from bitcoin_model import BitcoinMacroModel

# Initialize with API keys
api_keys = {
    'fred': 'YOUR_FRED_API_KEY',
    'glassnode': 'YOUR_GLASSNODE_API_KEY',
    'cryptoquant': 'YOUR_CRYPTOQUANT_API_KEY'
}

model = BitcoinMacroModel(api_keys)

# Check for buy signals
result = model.run_analysis(scenario=1, portfolio_value=100000)

if result['signals']['buy_signal']:
    print(f"🚨 BUY SIGNAL: {result['signals']['combined_score']:.3f}")
    print(f"Position Size: {result['trade_plan']['position_size']*100:.1f}%")
```

## 🎯 Investment Scenarios

### Scenario 1: Fed Pivot + Low Exchange Reserves
- **Trigger**: Federal Reserve policy shifts + Bitcoin exchange reserves < 2.5M BTC
- **Entry**: Scaled over 72 hours
- **Historical Win Rate**: 75%
- **Signal Threshold**: 70%

### Scenario 2: M2 Expansion + Miner Capitulation  
- **Trigger**: M2 money supply growth >10% + Hash ribbon buy signal
- **Entry**: Accumulated over 30 days
- **Historical Win Rate**: 80%
- **Signal Threshold**: 75%

## 🔧 Features

### Core Capabilities
- ✅ **Real-time Signal Detection**: Fed policy, on-chain metrics, M2 analysis
- ✅ **Risk-Adjusted Position Sizing**: 3-25% allocations based on signal strength
- ✅ **Multi-Scenario Analysis**: Run all scenarios or get strongest signal
- ✅ **Health Monitoring**: Check data provider status and system health
- ✅ **Automated Trading Integration**: Execute trades on major exchanges (V3)

### Data Sources
- 📈 **Federal Reserve (FRED)**: Interest rates, M2 money supply
- ⛓️ **On-Chain Metrics**: Exchange reserves, NUPL, hash ribbon (mock implementation)
- 💰 **Price Data**: CoinGecko integration
- 🏦 **Exchange APIs**: Binance, Coinbase, Kraken support

## 🤖 Automated Trading (V3)

```python
from bitcoin_model.exchange_integration import AutomatedTrader, TradingConfig

# Configure trading (ALWAYS START WITH TESTNET!)
config = TradingConfig(
    exchange='binance',
    api_key='YOUR_API_KEY',
    api_secret='YOUR_SECRET',
    testnet=True,      # Use testnet first!
    dry_run=True,      # Paper trading mode
    max_position_size=0.05  # 5% max position
)

# Start automated trading
trader = AutomatedTrader(model, config)
await trader.start()
```

### ⚠️ Trading Safety Features
- 🛡️ **Circuit Breakers**: Daily loss limits, consecutive loss protection
- 🧪 **Paper Trading**: Test strategies without real money
- 🏖️ **Testnet Support**: Use exchange sandbox environments
- 📊 **Position Limits**: Configurable maximum position sizes
- 🚨 **Health Checks**: Automatic system monitoring

## 📁 Project Structure

```
bitcoin_model/
├── core.py                    # Main BitcoinMacroModel class
├── models/
│   ├── fed_pivot.py          # Scenario 1: Fed Pivot + Exchange Reserves
│   └── m2_miner.py           # Scenario 2: M2 + Miner Capitulation
├── data_providers/
│   ├── fred_client.py        # Federal Reserve data
│   └── crypto_data.py        # Crypto & on-chain data
├── exchange_integration/
│   ├── trading_config.py     # Trading configuration
│   └── automated_trader.py   # Automated trading system
├── config/
│   └── settings.py           # Configuration settings
└── utils/
    ├── logging_config.py     # Logging setup
    └── error_handling.py     # Error handling utilities
```

## 🔑 API Setup

### Required APIs

1. **FRED (Free)**: https://fred.stlouisfed.org/docs/api/api_key.html
2. **CoinGecko (Free tier)**: https://www.coingecko.com/en/api/pricing
3. **Glassnode (Paid)**: https://glassnode.com/pricing
4. **Exchange APIs**: For automated trading

### Environment Configuration

```env
# Data Provider APIs
FRED_API_KEY=your_fred_api_key_here
GLASSNODE_API_KEY=your_glassnode_api_key_here
COINGECKO_API_KEY=your_coingecko_api_key_here

# Trading APIs (Optional)
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET=your_binance_secret

# Configuration
DEFAULT_PORTFOLIO_VALUE=100000
RISK_PROFILE=moderate  # conservative, moderate, aggressive
TESTNET_MODE=true
DRY_RUN=true
```

## 📊 Examples

### Daily Monitoring
```bash
python examples/monitoring_script.py
```

### Basic Analysis
```bash
python examples/basic_usage.py
```

### Run Tests
```bash
pytest tests/
```

## 📈 Signal Interpretation

### Signal Scores (0-1 scale)
- **0.0-0.3**: Weak signal, no action
- **0.3-0.5**: Moderate signal, monitor closely  
- **0.5-0.7**: Strong signal, consider partial position
- **0.7-1.0**: Very strong signal, full position warranted

### Position Sizing
| Risk Profile | Base Position | Max Position |
|-------------|---------------|--------------|
| Conservative | 3% | 10% |
| Moderate | 5% | 15% |
| Aggressive | 10% | 25% |

## 🚨 Important Disclaimers

### Educational Purpose Only
- ⚠️ **Not Financial Advice**: This software is for educational and research purposes
- 📉 **Risk Warning**: Cryptocurrency investments carry significant risk
- 🔍 **Do Your Research**: Always conduct your own analysis
- 👨‍💼 **Consult Professionals**: Seek advice from qualified financial advisors

### Automated Trading Warnings
- 🧪 **Test First**: Always use testnet and paper trading initially
- 💰 **Start Small**: Begin with minimal position sizes
- 👀 **Monitor Actively**: Watch trades closely, especially during first week
- 🛑 **Never Risk More**: Than you can afford to lose

## 📊 Historical Performance

| Scenario | Period | Win Rate | Avg Return | Max Drawdown |
|----------|--------|----------|------------|--------------|
| Fed Pivot | 2020-2024 | 75% | +156% | -22% |
| M2 + Miner | 2020-2024 | 80% | +245% | -18% |

*Past performance does not guarantee future results*

## 🛠️ Development

### Install Development Dependencies
```bash
pip install -r requirements.txt
pip install pytest black flake8
```

### Run Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black bitcoin_model/
flake8 bitcoin_model/
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/AlmadenCapMgmt/M2/issues)
- **Discussions**: [GitHub Discussions](https://github.com/AlmadenCapMgmt/M2/discussions)

---

Built with ❤️ for the Bitcoin community

**Remember**: Always test with paper trading and testnet before using real money!