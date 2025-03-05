<PLAN>
1. **Alt Season Detection:**
   - **Bitcoin Dominance Monitoring:**  
     Retrieve global market data from CoinGecko (via its `/global` endpoint) to track Bitcoin’s market share. A fall in BTC dominance below a predefined threshold (e.g. 55%) is used to flag the start of alt season.
   - **Altcoin Performance Analysis:**  
     For each selected altcoin (e.g. Ethereum, Binance Coin, Solana, Cardano), fetch historical OHLCV data from an exchange (using ccxt, e.g. Binance) and compute technical indicators via TA-Lib.
   - **Confirmation Criteria:**  
     An altcoin is considered bullish if its price is above its moving averages (50-period and 200-period), RSI is below an overbought level (e.g. 70), and a positive MACD crossover is observed.

2. **Core Trading Logic:**
   - **Momentum-Based Strategy:**  
     - **Entry:**  
       When the altcoin’s price is above both the 50-period and 200-period moving averages, RSI is in a healthy range, and MACD is crossing above its signal line, generate a “buy” signal.
     - **Exit:**  
       Exit the position if the price falls below the moving averages, RSI exceeds a threshold (e.g. 80), or MACD shows a negative crossover.
   - **Alt Season Trigger:**  
     The bot trades altcoins only when Bitcoin’s dominance falls below a set threshold, suggesting that altcoins are in a favorable environment.

3. **Risk Management Techniques:**
   - **Stop-Loss and Take-Profit:**  
     Use fixed percentage thresholds (e.g. 5% stop-loss and 10% take-profit) to manage downside risk and lock in profits.
   - **Dynamic Position Sizing:**  
     Calculate the trade size as a fraction of the available balance based on a risk factor and current market volatility.
   - **Trailing Stops (Future Enhancement):**  
     Although not fully implemented in this version, the design allows for adding a trailing stop to adjust exit levels as price moves in favor of the trade.

4. **APIs and Libraries:**
   - **Market Data & Trading:**  
     - `ccxt` to connect with Binance (or other exchanges) for live OHLCV data and order execution.
     - `requests` to fetch global market data (e.g. Bitcoin dominance) from the CoinGecko API.
   - **Data Handling & Technical Analysis:**  
     - `pandas` for data manipulation.
     - `TA-Lib` to compute technical indicators (SMA, RSI, MACD).
   - **Other Utilities:**  
     - `logging` for activity logging.
     - `os` and `time` for configuration and scheduling.

5. **Modular Code Structure:**
   - **MarketDataHandler:**  
     Handles data retrieval from both CoinGecko (for global metrics) and ccxt (for altcoin OHLCV).
   - **SignalGenerator:**  
     Computes technical indicators and generates trading signals based on the momentum strategy.
   - **RiskManager:**  
     Implements risk controls such as stop-loss, take-profit, and dynamic position sizing.
   - **TradeExecutor:**  
     Manages order placement via ccxt.
   - **Backtester:**  
     Provides a simple backtesting framework using historical data.
   - **TradingBot (Main Controller):**  
     Orchestrates real-time monitoring and trade execution, switching between backtesting and live modes.
   
Please confirm if you would like any modifications before I proceed with the full Python script implementation.
</PLAN>

<CODE>
#!/usr/bin/env python3
"""
AI-Powered Alt Season Crypto Trading Agent
===========================================

This Python script implements an AI-powered trading agent optimized for alt season.
It monitors Bitcoin dominance and altcoin price trends, generates trading signals based on technical indicators,
executes trades using ccxt, and supports both backtesting and live trading modes.

Requirements:
- Python 3.10+
- Libraries: ccxt, TA-Lib, pandas, numpy, requests, logging
- API credentials for your chosen exchange (e.g., Binance)
- Environment variable TRADING_MODE: "backtest" or "live"

Before running, install required packages:
    pip install ccxt pandas numpy requests TA-Lib
"""

import os
import time
import math
import logging
import requests
import ccxt
import talib
import pandas as pd
import numpy as np
from datetime import datetime

# =========================
# Global Configuration
# =========================
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
BTC_DOMINANCE_THRESHOLD = 55.0  # Percent threshold for alt season detection
ALTCoin_LIST = ['ethereum', 'binancecoin', 'solana', 'cardano']  # List of altcoins to trade
TRADING_MODE = os.getenv("TRADING_MODE", "backtest")  # "backtest" or "live"

# Exchange API credentials (set these in your environment)
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")

# =========================
# Market Data Handler Module
# =========================
class MarketDataHandler:
    def __init__(self):
        # Initialize ccxt exchange instance (Binance example)
        self.exchange = ccxt.binance({
            'apiKey': BINANCE_API_KEY,
            'secret': BINANCE_API_SECRET,
            'enableRateLimit': True,
        })
    
    def fetch_global_data(self):
        """
        Fetch global market data from CoinGecko to obtain Bitcoin dominance.
        """
        try:
            response = requests.get(f"{COINGECKO_API_URL}/global")
            if response.status_code == 200:
                data = response.json()
                btc_dominance = data["data"]["market_cap_percentage"]["btc"]
                return btc_dominance
            else:
                logging.error("Failed to fetch global data from CoinGecko")
                return None
        except Exception as e:
            logging.error(f"Error fetching global data: {e}")
            return None
    
    def fetch_altcoin_data(self, coin_id, timeframe='1h'):
        """
        Fetch historical OHLCV data for a given altcoin from Binance.
        Returns a pandas DataFrame.
        """
        symbol = f"{coin_id.upper()}/USDT"  # Simplistic symbol mapping
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('datetime', inplace=True)
            # Ensure numeric types
            df = df.astype({'open': 'float', 'high': 'float', 'low': 'float', 'close': 'float', 'volume': 'float'})
            return df
        except Exception as e:
            logging.error(f"Error fetching OHLCV for {coin_id}: {e}")
            return None

# =========================
# Signal Generator Module
# =========================
class SignalGenerator:
    def __init__(self):
        pass

    def compute_indicators(self, df):
        """
        Compute technical indicators: 50-period and 200-period SMA, RSI, and MACD.
        """
        if df is None or df.empty:
            return df
        df['ma50'] = talib.SMA(df['close'], timeperiod=50)
        df['ma200'] = talib.SMA(df['close'], timeperiod=200)
        df['rsi'] = talib.RSI(df['close'], timeperiod=14)
        macd, macdsignal, _ = talib.MACD(df['close'], fastperiod=12, slowperiod=26, signalperiod=9)
        df['macd'] = macd
        df['macdsignal'] = macdsignal
        return df

    def generate_signal(self, df):
        """
        Generate trading signal based on the latest data point.
        Returns 'buy', 'sell', or 'hold'.
        """
        if df is None or df.empty:
            return None
        latest = df.iloc[-1]
        # Entry criteria: Price above both MAs, RSI healthy, MACD crossover positive
        if (latest['close'] > latest['ma50'] and latest['close'] > latest['ma200'] and
            latest['rsi'] < 70 and latest['macd'] > latest['macdsignal']):
            return 'buy'
        # Exit criteria: Price falls below MA50, RSI overbought, or MACD negative crossover
        elif (latest['close'] < latest['ma50'] or latest['rsi'] > 80 or
              latest['macd'] < latest['macdsignal']):
            return 'sell'
        else:
            return 'hold'

# =========================
# Risk Management Module
# =========================
class RiskManager:
    def __init__(self):
        self.stop_loss_pct = 0.05    # 5% stop-loss
        self.take_profit_pct = 0.10  # 10% take-profit

    def evaluate_trade(self, entry_price, current_price):
        """
        Evaluate if the current price has reached stop-loss or take-profit levels.
        Returns 'stop_loss', 'take_profit', or 'hold'.
        """
        if current_price <= entry_price * (1 - self.stop_loss_pct):
            return 'stop_loss'
        elif current_price >= entry_price * (1 + self.take_profit_pct):
            return 'take_profit'
        else:
            return 'hold'

    def compute_position_size(self, balance, risk_factor=0.02):
        """
        Compute the position size based on available balance and a risk factor.
        Returns the dollar amount to use for the trade.
        """
        return balance * risk_factor

# =========================
# Trade Execution Module
# =========================
class TradeExecutor:
    def __init__(self, exchange):
        self.exchange = exchange

    def place_order(self, symbol, order_type, side, amount, price=None):
        """
        Place an order on the exchange.
        Supports 'market' and 'limit' orders.
        """
        try:
            if order_type == 'limit':
                order = self.exchange.create_limit_order(symbol, side, amount, price)
            elif order_type == 'market':
                order = self.exchange.create_market_order(symbol, side, amount)
            else:
                order = None
            logging.info(f"Placed {side} {order_type} order for {symbol}: {order}")
            return order
        except Exception as e:
            logging.error(f"Error placing order for {symbol}: {e}")
            return None

# =========================
# Backtesting Module
# =========================
class Backtester:
    def __init__(self, data_handler, signal_generator, risk_manager):
        self.data_handler = data_handler
        self.signal_generator = signal_generator
        self.risk_manager = risk_manager

    def run_backtest(self, coin_id, initial_balance=1000):
        """
        Run a simple backtest for a given coin using historical data.
        """
        df = self.data_handler.fetch_altcoin_data(coin_id)
        if df is None or df.empty:
            logging.error(f"No data available for backtesting {coin_id}.")
            return None
        df = self.signal_generator.compute_indicators(df)
        balance = initial_balance
        position = 0
        entry_price = 0
        trades = []
        # Start backtesting after sufficient data is available for indicators
        for i in range(200, len(df)):
            slice_df = df.iloc[:i+1]
            signal = self.signal_generator.generate_signal(slice_df)
            current_price = slice_df.iloc[-1]['close']
            if signal == 'buy' and position == 0:
                # Enter position: invest full balance
                position = balance / current_price
                entry_price = current_price
                balance = 0
                trades.append(('buy', slice_df.index[-1], current_price))
            elif position > 0:
                decision = self.risk_manager.evaluate_trade(entry_price, current_price)
                if decision in ['stop_loss', 'take_profit'] or signal == 'sell':
                    # Exit position: liquidate full position
                    balance = position * current_price
                    trades.append(('sell', slice_df.index[-1], current_price))
                    position = 0
        profit = balance - initial_balance
        logging.info(f"Backtest {coin_id}: Profit = ${profit:.2f}, Trades: {trades}")
        return profit, trades

# =========================
# Trading Bot Module
# =========================
class TradingBot:
    def __init__(self, data_handler, signal_generator, risk_manager, trade_executor):
        self.data_handler = data_handler
        self.signal_generator = signal_generator
        self.risk_manager = risk_manager
        self.trade_executor = trade_executor
        self.active_positions = {}  # Tracks active positions: coin_id -> entry_price

    def run(self, altcoin_list):
        """
        Main loop for live trading.
        Monitors BTC dominance and, if alt season is detected, scans altcoins for buy/sell signals.
        """
        logging.info("Starting live Trading Bot...")
        while True:
            btc_dominance = self.data_handler.fetch_global_data()
            if btc_dominance is None:
                time.sleep(10)
                continue
            logging.info(f"BTC Dominance: {btc_dominance:.2f}%")
            # Check if alt season is active
            if btc_dominance < BTC_DOMINANCE_THRESHOLD:
                logging.info("Alt season detected!")
                for coin in altcoin_list:
                    df = self.data_handler.fetch_altcoin_data(coin)
                    if df is None or df.empty:
                        continue
                    df = self.signal_generator.compute_indicators(df)
                    signal = self.signal_generator.generate_signal(df)
                    symbol = f"{coin.upper()}/USDT"
                    # Fetch available USDT balance
                    balance_info = self.trade_executor.exchange.fetch_balance()
                    usdt_balance = balance_info['free'].get('USDT', 0)
                    if signal == 'buy' and coin not in self.active_positions and usdt_balance > 10:
                        # Calculate position size
                        position_value = self.risk_manager.compute_position_size(usdt_balance)
                        current_price = df.iloc[-1]['close']
                        amount = position_value / current_price
                        order = self.trade_executor.place_order(symbol, order_type='market', side='buy', amount=amount)
                        if order:
                            self.active_positions[coin] = current_price
                    elif signal == 'sell' and coin in self.active_positions:
                        # Sell entire position
                        balance_info = self.trade_executor.exchange.fetch_balance()
                        coin_balance = balance_info['free'].get(coin.upper(), 0)
                        if coin_balance > 0:
                            order = self.trade_executor.place_order(symbol, order_type='market', side='sell', amount=coin_balance)
                            if order:
                                del self.active_positions[coin]
            else:
                logging.info("BTC dominance high; waiting for alt season conditions...")
            time.sleep(60)  # Pause for 60 seconds before next check

# =========================
# Utility Functions
# =========================
def setup_logging():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s %(levelname)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

# =========================
# Main Controller
# =========================
def main():
    setup_logging()
    logging.info(f"Trading Mode: {TRADING_MODE}")
    
    data_handler = MarketDataHandler()
    signal_generator = SignalGenerator()
    risk_manager = RiskManager()
    exchange = ccxt.binance({
        'apiKey': BINANCE_API_KEY,
        'secret': BINANCE_API_SECRET,
        'enableRateLimit': True,
    })
    trade_executor = TradeExecutor(exchange)
    
    if TRADING_MODE.lower() == "backtest":
        backtester = Backtester(data_handler, signal_generator, risk_manager)
        for coin in ALTCoin_LIST:
            backtester.run_backtest(coin)
    elif TRADING_MODE.lower() == "live":
        bot = TradingBot(data_handler, signal_generator, risk_manager, trade_executor)
        bot.run(ALTCoin_LIST)
    else:
        logging.error("Invalid TRADING_MODE. Set environment variable TRADING_MODE to 'backtest' or 'live'.")

if __name__ == "__main__":
    main()
</CODE>

<EXPLANATION>
This script implements an AI-powered crypto trading agent optimized for alt season. Its key components are:
- **MarketDataHandler:** Retrieves global market data from CoinGecko (to check BTC dominance) and altcoin OHLCV data from Binance using ccxt.
- **SignalGenerator:** Calculates technical indicators (50-period and 200-period SMAs, RSI, and MACD) using TA-Lib and generates simple buy/sell signals based on momentum.
- **RiskManager:** Applies risk controls by evaluating stop-loss and take-profit thresholds and determining position sizing.
- **TradeExecutor:** Uses ccxt to place market or limit orders on the exchange.
- **Backtester:** Runs a simple backtest on historical altcoin data to simulate the strategy.
- **TradingBot (Main Controller):** In live mode, it continuously monitors BTC dominance. When alt season is detected (BTC dominance below 55%), it scans each altcoin for trading signals and executes buy or sell orders accordingly.
The script supports both backtesting (to simulate performance) and live trading modes based on the environment variable TRADING_MODE.
</EXPLANATION>

<SELF-REVIEW>
- **Structure Optimality:**  
  The modular design divides responsibilities into clear components (data handling, signal generation, risk management, order execution, and backtesting), which simplifies maintenance and further development. This structure is particularly well-suited for alt season trading because it enables focused improvements (e.g., refining signal criteria or risk controls) without impacting other parts of the system.

- **Adaptability:**  
  The design supports both backtesting and live trading modes, allowing traders to simulate strategies on historical data and then transition to live markets. Additionally, by isolating market data retrieval and technical analysis into separate modules, the bot can easily be adapted to work with different data sources, altcoin selections, or even alternative trading strategies.

- **Potential Enhancements:**  
  Future improvements could include:
  - Integrating machine learning models to refine entry/exit signals.
  - Implementing more advanced risk management (e.g., trailing stops, dynamic rebalancing).
  - Adding support for additional exchanges and more robust error handling.
  - Enhancing the backtesting framework to simulate slippage, fees, and latency.
  
Overall, the design lays a solid foundation for an extensible, data-driven alt season trading bot.
</SELF-REVIEW>