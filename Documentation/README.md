# AI-Powered Crypto Trading Bot
Version 2.0.0 (February 2025)

## Overview
Advanced cryptocurrency trading bot optimized for alt season trading, featuring:
- Real-time market analysis
- ATR-based position sizing
- Multi-factor signal generation
- Comprehensive risk management

## Features
- **Smart Entry/Exit**: QQE-based signal generation with volume confirmation
- **Risk Management**: Dynamic position sizing with ATR volatility adjustment
- **Market Analysis**: Real-time correlation and volume profile analysis
- **Logging**: Detailed trade decision tracking and performance monitoring

## Requirements
- Python 3.11+
- ccxt
- TA-Lib
- pandas
- numpy
- requests
- logging

## Configuration
1. Environment Variables:
   ```env
   TRADING_MODE=live  # or "backtest"
   BINANCE_API_KEY=your_api_key
   BINANCE_API_SECRET=your_api_secret
   INITIAL_BALANCE=40.00
   ```

2. Risk Parameters:
   - Position Risk: 1.5%
   - Max Position Size: 30%
   - Min Trade Amount: $3.00
   - Max Daily Loss: 2%

3. Technical Indicators:
   - QQE (RSI: 14, Smooth: 5, Wilder: 0.33)
   - Volume Profile (14-day, 0.25% buckets)
   - EMA (Fast: 9, Slow: 21)

## Installation
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure environment variables
4. Run: `python crypto_trading_bot.py`

## Usage
```bash
# Live Trading
python crypto_trading_bot.py

# Backtesting
TRADING_MODE=backtest python crypto_trading_bot.py
```

## Monitoring
- Check logs in `logs/` directory
- Monitor positions and PnL in real-time output
- Review trade history in generated reports

## Safety Features
- Maximum position limits
- Daily loss limits
- Correlation-based risk management
- Volume-based entry validation

## Contributing
1. Fork the repository
2. Create feature branch
3. Submit pull request

## License
MIT License

## Disclaimer
Trading cryptocurrencies carries significant risk. This bot is for educational purposes only.


## Troubleshooting
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