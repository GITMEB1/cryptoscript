## Getting Started

### Prerequisites
1. Python 3.10 or higher
2. pip (Python package manager)
3. Git
4. A Binance account with API access (for live trading)

### Installation

1. Clone the repository
```bash
git clone <your-repository-url>
cd CryptoScript
```

2. Create and activate a virtual environment (recommended)
```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. Install required packages
```bash
pip install -r requirements.txt
```

4. Install TA-Lib (Technical Analysis Library)
- Windows: Download and install from [here](https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib)
- Linux: `sudo apt-get install ta-lib`
- macOS: `brew install ta-lib`

5. Set up environment variables
- Copy `.env.example` to `.env`
```bash
cp .env.example .env
```
- Edit `.env` with your configuration:
```env
TRADING_MODE=backtest  # or 'live' for live trading
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
INITIAL_BALANCE=1000  # Starting balance for backtesting
UPDATE_INTERVAL=900   # Update interval in seconds (15 minutes)
```

### Running the Application

1. Backtesting Mode
```bash
python crypto_trading_bot.py
```
This will run the bot in backtesting mode using historical data.

2. Live Trading Mode
- Ensure your `.env` file has `TRADING_MODE=live`
- Verify your Binance API credentials are set
```bash
python crypto_trading_bot.py
```

### Configuration Options

1. Trading Pairs
Edit the `TRADING_PAIRS` list in `crypto_trading_bot.py`:
```python
TRADING_PAIRS = [
    'ETH/USDT',
    'BNB/USDT',
    'SOL/USDT',
    'ADA/USDT'
]
```

2. Risk Parameters
Adjust the risk parameters in the `RiskManager` class:
- `position_risk`: Risk per trade (default 2%)
- `max_position_size`: Maximum position size (default 25%)
- `min_trade_amount`: Minimum trade amount (default $10)
- `max_trades`: Maximum concurrent trades (default 2)
- `max_daily_loss`: Maximum daily loss limit (default 2%)

3. Technical Indicators
Modify the parameters in the `SignalGenerator` class:
- `ema_fast`: Fast EMA period (default 9)
- `ema_slow`: Slow EMA period (default 21)
- `rsi_period`: RSI period (default 14)
- `atr_period`: ATR period (default 14)

### Monitoring and Logging

- All trading activities are logged to `trading_bot.log`
- Console output shows real-time trading information
- Backtest results include:
  - Final balance
  - Total profit/loss
  - Number of trades
  - Win rate
  - Maximum drawdown

### Troubleshooting

1. TA-Lib Installation Issues
- Windows: Use the appropriate wheel file for your Python version
- Linux: Try `sudo apt-get install python3-dev` before installing ta-lib

2. API Connection Issues
- Verify your API keys are correct
- Check your internet connection
- Ensure you have sufficient permissions on your Binance account

3. Backtesting Performance
- Reduce the number of trading pairs for faster testing
- Adjust the date range for historical data
- Consider using a machine with more RAM for large datasets

### Safety Notes

1. Always test in backtesting mode first
2. Start with small amounts in live trading
3. Monitor the bot regularly when running in live mode
4. Keep your API keys secure and never share them
5. Set appropriate stop-loss and risk parameters
```

## Recent Updates

### Version 1.1.0 (or appropriate version number)
- Improved position management and risk calculations
- Fixed unrealized PnL calculations
- Reduced minimum ATR floor to 0.01%
- Enhanced decimal precision handling
- All test suites passing

### Known Limitations
- API rate limiting may affect real-time trading
- Large backtests require significant memory
- Some advanced features still in development

### Upcoming Features
- Advanced backtesting capabilities
- Enhanced market analysis tools
- Improved user interface
- Additional risk management features

## Contributing
Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## Testing
To run the test suite:
```bash
pytest test_trading_bot_enhanced.py -v
```

All tests should pass successfully. If you encounter any issues, please check the troubleshooting section or raise an issue on GitHub.
```