# AI-Powered Alt Season Crypto Trading Bot

This is an AI-powered trading bot optimized for cryptocurrency alt season. It monitors Bitcoin dominance and altcoin price trends, generates trading signals based on technical indicators, and executes trades automatically.

## Features

- Bitcoin dominance monitoring to detect alt season
- Technical analysis using multiple indicators (SMA, RSI, MACD)
- Risk management with stop-loss and take-profit
- Support for both backtesting and live trading
- Detailed logging of all operations
- Modular design for easy customization

## Prerequisites

- Python 3.10 or higher
- Binance account with API access (for live trading)
- TA-Lib library installed

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd <repository-directory>
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

3. Install TA-Lib:
   - Windows: Download and install from [here](https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib)
   - Linux: `sudo apt-get install ta-lib`
   - macOS: `brew install ta-lib`

4. Copy `.env.example` to `.env` and configure your settings:
```bash
cp .env.example .env
```

5. Edit `.env` file with your Binance API credentials and preferred trading mode.

## Configuration

The bot can be configured through the following environment variables in the `.env` file:

- `TRADING_MODE`: Set to either "backtest" or "live"
- `BINANCE_API_KEY`: Your Binance API key
- `BINANCE_API_SECRET`: Your Binance API secret

Additional configuration parameters can be found at the top of `crypto_trading_bot.py`:

- `BTC_DOMINANCE_THRESHOLD`: Bitcoin dominance threshold for alt season detection
- `ALTCoin_LIST`: List of altcoins to trade
- Risk parameters in the `RiskManager` class

## Usage

### Backtesting Mode

To run the bot in backtesting mode:

1. Set `TRADING_MODE=backtest` in your `.env` file
2. Run the bot:
```bash
python crypto_trading_bot.py
```

### Live Trading Mode

To run the bot in live trading mode:

1. Set `TRADING_MODE=live` in your `.env` file
2. Ensure your Binance API credentials are correctly set
3. Run the bot:
```bash
python crypto_trading_bot.py
```

## Trading Strategy

The bot implements a momentum-based strategy with the following components:

1. **Alt Season Detection**:
   - Monitors Bitcoin dominance
   - Trades only when BTC dominance is below threshold (default: 55%)

2. **Entry Criteria**:
   - Price above both 50 and 200-period moving averages
   - RSI below 70 (not overbought)
   - MACD crossing above signal line

3. **Exit Criteria**:
   - Price falls below 50-period moving average
   - RSI above 80 (overbought)
   - MACD crosses below signal line
   - Stop-loss or take-profit hit

4. **Risk Management**:
   - 5% stop-loss
   - 10% take-profit
   - Position sizing based on account balance and risk factor

## Logging

The bot logs all activities to both console and `trading_bot.log` file. The log includes:
- Market conditions
- Trading signals
- Order execution details
- Errors and warnings

## Disclaimer

This bot is for educational purposes only. Cryptocurrency trading carries significant risks. Always test thoroughly in backtesting mode before running with real money. The authors are not responsible for any financial losses incurred using this software.

## License

MIT License 