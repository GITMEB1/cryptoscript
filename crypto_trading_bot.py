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
from dotenv import load_dotenv
from collections import Counter
import sys
from decimal import Decimal, ROUND_HALF_UP, getcontext, ROUND_DOWN, localcontext
from datetime import datetime, timedelta
import traceback
from typing import Optional, Dict, List, Any
# Load environment variables
load_dotenv()


# =========================
# Enhanced logging
# =========================
def setup_detailed_logging():
    """Configure detailed logging for both file and console output"""
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Generate timestamp for log file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f'logs/trading_bot_{timestamp}.log'
    
    # Configure logging with more detailed format
    logging.basicConfig(
        level=logging.DEBUG,  # Changed to DEBUG for more detailed logging
        format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Log system info
    logging.info("=== Trading Bot Started ===")
    logging.info(f"Python version: {sys.version}")
    logging.info(f"Operating System: {os.name}")
    logging.info(f"Trading Mode: {TRADING_MODE}")
    logging.info(f"Trading Pairs: {ALTCoin_LIST}")
    logging.info(f"Initial Balance: ${os.getenv('INITIAL_BALANCE', '40.00')}")

# =========================
# Global Configuration
# =========================
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
BTC_DOMINANCE_THRESHOLD = 55.0  # Percent threshold for alt season detection
ALTCoin_LIST = ['ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'ADA/USDT']  # Using correct CCXT symbol format
TRADING_MODE = os.getenv("TRADING_MODE", "backtest")  # "backtest" or "live"

# Exchange API credentials (set these in your environment)
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")

# Set global precision to 8 decimal places (one extra for rounding)
getcontext().prec = 8
getcontext().rounding = ROUND_DOWN


def normalize_decimal(value):
    """Convert a value to a Decimal with 8 decimal places."""
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    
    # Use quantize with ROUND_HALF_UP for proper rounding
    result = value.quantize(Decimal('0.00000001'), rounding=ROUND_HALF_UP)
    return result
# =========================
# Market Data Handler Module
# =========================
class MarketDataHandler:
    def __init__(self):
        # Initialize ccxt exchange instance with different configs based on mode
        if TRADING_MODE.lower() == "backtest":
            self.exchange = ccxt.binance({
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot'
                }
            })
        else:
            self.exchange = ccxt.binance({
                'apiKey': BINANCE_API_KEY,
                'secret': BINANCE_API_SECRET,
                'enableRateLimit': True,
            })
        # Price cache with 1-second expiry
        self.price_cache = {}
        self.cache_expiry = 1  # 1 second
    
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
    
    def fetch_altcoin_data(self, coin_id, timeframe='15m', days_back=30):
        """
        Fetch historical OHLCV data for a given altcoin from Binance.
        """
        try:
            logging.info(f"Fetching {days_back} days of {timeframe} data for {coin_id}")
            
            # Calculate millisecond timestamps
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days_back)
            end_ts = int(end_time.timestamp() * 1000)
            start_ts = int(start_time.timestamp() * 1000)
            
            # Initialize data storage
            all_candles = []
            current_ts = start_ts
            
            while current_ts < end_ts:
                try:
                    # Add rate limiting delay
                    time.sleep(0.5)  # 500ms delay between requests
                    
                    # Fetch batch of candles
                    candles = self.exchange.fetch_ohlcv(
                        coin_id,
                        timeframe,
                        since=current_ts,
                        limit=500  # Reduced from 1000 to be more conservative
                    )
                    
                    if not candles:
                        logging.warning(f"No data returned for {coin_id} at timestamp {current_ts}")
                        break
                        
                    all_candles.extend(candles)
                    
                    # Update timestamp for next batch
                    current_ts = candles[-1][0] + 1
                    
                except ccxt.RateLimitExceeded as e:
                    logging.warning(f"Rate limit hit, waiting 30 seconds... ({str(e)})")
                    time.sleep(30)
                    continue
                except Exception as e:
                    logging.error(f"Error fetching batch for {coin_id}: {str(e)}")
                    break
            
            if not all_candles:
                logging.error(f"No data collected for {coin_id}")
                return pd.DataFrame()  # Return empty DataFrame instead of None
                
            # Convert to DataFrame
            df = pd.DataFrame(all_candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('datetime', inplace=True)
            
            # Ensure numeric types and remove duplicates
            df = df.astype({
                'open': 'float',
                'high': 'float',
                'low': 'float',
                'close': 'float',
                'volume': 'float'
            })
            df = df.drop_duplicates()
            
            logging.info(f"Successfully fetched {len(df)} candles for {coin_id}")
            return df
            
        except Exception as e:
            logging.error(f"Error fetching OHLCV for {coin_id}: {str(e)}\n{traceback.format_exc()}")
            return pd.DataFrame()  # Return empty DataFrame instead of None

    def get_current_price(self, symbol):
        """
        Get the current price for a symbol with caching and error handling
        """
        try:
            current_time = time.time()
            
            # Check cache first
            if symbol in self.price_cache:
                cached_price, cache_time = self.price_cache[symbol]
                if current_time - cache_time < self.cache_expiry:
                    return cached_price
            
            # Fetch new price
            ticker = self.exchange.fetch_ticker(symbol)
            if not ticker or 'last' not in ticker:
                logging.error(f"Invalid ticker data for {symbol}")
                return None
                
            price = ticker['last']
            
            # Update cache
            self.price_cache[symbol] = (price, current_time)
            
            return price
            
        except ccxt.NetworkError as e:
            logging.error(f"Network error fetching price for {symbol}: {str(e)}")
            # Return cached price if available
            if symbol in self.price_cache:
                cached_price, _ = self.price_cache[symbol]
                logging.info(f"Using cached price for {symbol} due to network error")
                return cached_price
            return None
            
        except ccxt.ExchangeError as e:
            logging.error(f"Exchange error fetching price for {symbol}: {str(e)}")
            return None
            
        except Exception as e:
            logging.error(f"Unexpected error fetching price for {symbol}: {str(e)}")
            return None
# =========================
# QQE Indicator
# =========================
class QQEIndicator:
    def __init__(self):
        self.rsi_period = 14
        self.sf = 5          # Smoothing factor
        self.wilder = 0.33   # Volatility adjustment
        
    def calculate(self, close_prices):
        """Calculate QQE indicator values"""
        try:
            rsi = talib.RSI(close_prices, self.rsi_period)
            rsi_ma = talib.EMA(rsi, self.sf)
            delta = rsi - rsi_ma
            
            upper = rsi_ma + delta * self.wilder
            lower = rsi_ma - delta * self.wilder
            
            return {
                'upper': upper,
                'rsi_ma': rsi_ma,
                'lower': lower
            }
        except Exception as e:
            logging.error(f"Error calculating QQE: {str(e)}")
            return None


# =========================
# Volume Profile
# =========================
class VolumeProfile:
    def __init__(self):
        self.period = 14
        self.value_area_sd = 1.2
        self.bucket_size = 0.0025  # 0.25% price increments

    def calculate_profile(self, df):
        """Calculate volume profile and POC"""
        try:
            # Create a copy of the dataframe to avoid SettingWithCopyWarning
            df_copy = df.copy()
            
            # Calculate price buckets
            bucket_calc = (df_copy['close'] / (df_copy['close'] * self.bucket_size)).round() * (df_copy['close'] * self.bucket_size)
            df_copy = df_copy.assign(price_bucket=bucket_calc)
            
            # Calculate volume profile
            volume_by_price = df_copy.groupby('price_bucket')['volume'].sum()
            
            # Find POC (Point of Control)
            poc = volume_by_price.idxmax()
            
            # Calculate Value Area
            std_dev = df_copy['close'].std()
            value_area_high = poc + (std_dev * self.value_area_sd)
            value_area_low = poc - (std_dev * self.value_area_sd)
            
            return {
                'poc': poc,
                'value_area_high': value_area_high,
                'value_area_low': value_area_low,
                'volume_profile': volume_by_price
            }
        except Exception as e:
            logging.error(f"Error calculating volume profile: {str(e)}")
            return None
# =========================
# Signal Generator Module
# =========================
class SignalGenerator:
    def __init__(self):
        # Existing parameters
        self.ema_fast = 9
        self.ema_slow = 21
        self.rsi_period = 14
        self.rsi_min = 50
        
        # Position tracking
        self.in_position = False
        
        # New QQE indicator
        self.qqe = QQEIndicator()
        
        # Correlation settings
        self.corr_window = 24  # 24-hour correlation window
        self.corr_threshold = 0.7  # Maximum allowed correlation
        
        # Volume profile settings
        self.vp_period = 14  # 14-day volume profile
        self.value_area_sd = 1.2  # Standard deviations for value area
        self.volume_profile = VolumeProfile()
        
        # Signal deduplication
        self.last_signal_time = None
        self.cooldown_seconds = 30 * 60  # 30 minutes cooldown
        
    def check_correlation(self, sol_prices, btc_prices):
        """Check correlation between SOL and BTC"""
        try:
            if len(sol_prices) < self.corr_window or len(btc_prices) < self.corr_window:
                return True  # Allow trading if not enough data
                
            sol_returns = np.log(sol_prices[-self.corr_window:]).diff().dropna()
            btc_returns = np.log(btc_prices[-self.corr_window:]).diff().dropna()
            
            if len(sol_returns) < 2:  # Need at least 2 points for correlation
                return True
                
            correlation = np.corrcoef(sol_returns, btc_returns)[0,1]
            return abs(correlation) < self.corr_threshold
            
        except Exception as e:
            logging.error(f"Error checking correlation: {str(e)}")
            return True  # Allow trading on error
            
    def generate_signals(self, df):
        """Generate signals for all candles in the dataframe"""
        try:
            # Compute indicators if not already present
            df = self.compute_indicators(df)
            if df is None:
                return pd.Series(0, index=df.index)  # Return neutral signals
                
            signals = pd.Series(0, index=df.index)  # Initialize with neutral signals
            
            for i in range(len(df)):
                slice_df = df.iloc[:i+1]
                signals.iloc[i] = 1 if self.generate_signal(slice_df) == 'buy' else (-1 if self.generate_signal(slice_df) == 'sell' else 0)
                
            return signals
            
        except Exception as e:
            logging.error(f"Error generating signals: {str(e)}")
            return pd.Series(0, index=df.index)  # Return neutral signals on error

    def generate_signal(self, df):
        """Enhanced signal generation with QQE and correlation check"""
        if df is None or df.empty or len(df) < self.ema_slow:
            return 'hold'
            
        try:
            latest = df.iloc[-1]
            prev = df.iloc[-2]
            current_price = latest['close']
            
            # Calculate QQE
            qqe_values = self.qqe.calculate(df['close'])
            if qqe_values is None:
                return 'hold'
            
            # Check correlation if BTC data available
            if 'btc_close' in df.columns:
                if not self.check_correlation(df['close'], df['btc_close']):
                    logging.debug("Signal skipped: High BTC correlation")
                    return 'hold'
            
            # Check volume profile
            if not self.check_volume_profile(df):
                logging.debug("Signal skipped: Price outside value area")
                return 'hold'
                    
            # Entry conditions with buffer zone
            trend_up = latest['close'] > latest['ema_slow']
            qqe_bullish = qqe_values['rsi_ma'].iloc[-1] > 48  # More responsive threshold
            qqe_bearish = qqe_values['rsi_ma'].iloc[-1] < 52
            volume_active = latest['volume'] > latest['volume_ma'] * 1.15  # Adjusted multiplier
            
            # Log conditions
            logging.debug(
                f"Signal Conditions: QQE={qqe_values['rsi_ma'].iloc[-1]:.1f}, "
                f"VolRatio={latest['volume']/latest['volume_ma']:.2f}, "
                f"EMA_Fast={latest['ema_fast']:.2f}, "
                f"EMA_Slow={latest['ema_slow']:.2f}"
            )
            
            if not self.in_position:
                if (trend_up and qqe_bullish and volume_active):
                    # Validate signal (check cooldown)
                    if not self.validate_signal('buy', current_price):
                        return 'hold'
                        
                    logging.info("Buy signal generated: All conditions met")
                    return 'buy'
            else:
                if qqe_bearish or volume_active < 0.7:  # Exit on weak volume
                    # Validate signal (check cooldown)
                    if not self.validate_signal('sell', current_price):
                        return 'hold'
                        
                    logging.info("Sell signal generated: Exit conditions met")
                    return 'sell'
            
            return 'hold'
        
        except Exception as e:
            logging.error(f"Error generating signal: {str(e)}")
            return 'hold'
    
    def check_volume_profile(self, df):
        """Check if price is within valid volume profile area"""
        try:
            profile = self.volume_profile.calculate_profile(df)
            if profile is None:
                return True  # Allow trading if calculation fails
                
            current_price = df['close'].iloc[-1]
            return (current_price >= profile['value_area_low'] and 
                    current_price <= profile['value_area_high'])
        except Exception as e:
            logging.error(f"Error checking volume profile: {str(e)}")
            return True

    def compute_indicators(self, df):
        """Compute all technical indicators needed for signal generation"""
        try:
            # Calculate EMAs
            df['ema_fast'] = talib.EMA(df['close'], self.ema_fast)
            df['ema_slow'] = talib.EMA(df['close'], self.ema_slow)
            
            # Calculate ATR
            df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14)
            
            # Calculate volume moving average
            df['volume_ma'] = talib.SMA(df['volume'], timeperiod=20)
            
            # Calculate RSI
            df['rsi'] = talib.RSI(df['close'], timeperiod=self.rsi_period)
            
            return df
            
        except Exception as e:
            logging.error(f"Error computing indicators: {str(e)}")
            return None

    def validate_signal(self, signal_type, current_price):
        """Validate signal to prevent duplicates and respect cooldown periods"""
        current_time = time.time()  # Get current time here
        
        # Check if we're in cooldown period
        if self.last_signal_time is not None:
            time_since_last = current_time - self.last_signal_time
            if time_since_last < self.cooldown_seconds:
                logging.debug(f"Signal rejected: Cooldown active ({time_since_last:.0f}s < {self.cooldown_seconds}s)")
                return False
        
        # Signal is valid, update last signal time
        self.last_signal_time = current_time
        logging.debug(f"Signal validated: New {signal_type} signal at price ${current_price:.2f}")
        return True
# =========================
# Risk Management Module
# =========================
class RiskManager:
    def __init__(self):
        """Initialize risk management parameters"""
        self.max_position_size = normalize_decimal('0.1')  # 10% of balance per position
        self.max_portfolio_allocation = normalize_decimal('0.5')  # 50% max total allocation
        self.max_daily_loss = normalize_decimal('0.02')  # 2% max daily loss
        self.max_trades = 10  # Maximum trades per day
        self.atr_trail_mult = normalize_decimal('2.0')  # ATR multiplier for trailing stops
        self.atr_sl_mult = normalize_decimal('1.5')  # ATR multiplier for stop loss
        self.atr_tp_mult = normalize_decimal('3.0')  # ATR multiplier for take profit
        self.min_trade_amount = normalize_decimal('10.0')  # Minimum trade size in USDT
        
        # Daily tracking
        self.daily_pnl = normalize_decimal('0')
        self.daily_trades = 0
        self.last_reset = datetime.now().date()

    def can_trade(self, daily_pnl=None, initial_balance=None):
        """Check if trading is allowed based on daily limits"""
        # Reset daily counters if it's a new day
        current_date = datetime.now().date()
        if current_date > self.last_reset:
            self.daily_pnl = normalize_decimal('0')
            self.daily_trades = 0
            self.last_reset = current_date
        
        # Handle both single param and dual param versions for test compatibility
        if initial_balance is not None and daily_pnl is not None:
            # Test case is passing daily_pnl and initial_balance directly
            daily_pnl_dec = normalize_decimal(daily_pnl)
            initial_balance_dec = normalize_decimal(initial_balance)
            
            # Check daily loss limit
            if daily_pnl_dec <= -initial_balance_dec * self.max_daily_loss:
                return False
        else:
            # Using internal tracking (daily_pnl is actually balance in this case)
            balance = normalize_decimal(daily_pnl) if daily_pnl is not None else normalize_decimal('0')
            
            # Check daily loss limit
            if self.daily_pnl < -balance * self.max_daily_loss:
                return False
        
        # Check maximum trades per day
        if self.daily_trades >= self.max_trades:
            return False
            
        return True

    def calculate_stop_levels(self, entry_price, atr):
        """Calculate initial and trailing stop levels based on ATR"""
        entry = normalize_decimal(entry_price)
        atr_dec = normalize_decimal(atr)
        
        stop_loss = entry - (atr_dec * self.atr_sl_mult)
        take_profit = entry + (atr_dec * self.atr_tp_mult)
        trailing_stop = stop_loss
        trailing_activation = entry + (atr_dec * self.atr_trail_mult)
        
        return {
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'trailing_stop': trailing_stop,
            'trailing_activation': trailing_activation,
            'atr': atr_dec
        }

    def compute_position_size(self, balance, price, volatility):
        """Calculate position size based on balance, price, and volatility"""
        balance_dec = normalize_decimal(balance)
        max_position = balance_dec * self.max_position_size
        
        # Adjust position size based on volatility
        volatility_dec = normalize_decimal(volatility)
        vol_adj = normalize_decimal('1') - (volatility_dec * normalize_decimal('5'))  # Reduce size as volatility increases
        vol_adj = max(vol_adj, normalize_decimal('0.2'))  # Minimum 20% of standard size
        
        position_size = max(min(max_position * vol_adj, max_position), self.min_trade_amount)
        return position_size

    def calculate_dynamic_position_size(self, balance, price, volatility):
        """Legacy method for backward compatibility"""
        return self.compute_position_size(balance, price, volatility)

    def update_daily_stats(self, pnl):
        """Update daily statistics after a trade"""
        self.daily_pnl += normalize_decimal(pnl)
        self.daily_trades += 1

    def update_trailing_stop(self, position, current_price):
        """Update trailing stop if price moves above activation level"""
        current_price_dec = normalize_decimal(current_price)
        
        if hasattr(position, 'trailing_activation') and current_price_dec >= position.trailing_activation:
            new_stop = current_price_dec - (position.atr * self.atr_trail_mult)
            if position.current_stop is None or new_stop > position.current_stop:
                return new_stop
        elif hasattr(position, 'trailing_stop') and current_price_dec >= position.trailing_stop:
            new_stop = current_price_dec - (position.atr * self.atr_trail_mult)
            if position.current_stop is None or new_stop > position.current_stop:
                return new_stop
        
        return position.current_stop

    def evaluate_trade(self, position, current_price):
        """Evaluate if the current price has triggered any exit conditions"""
        current_price_dec = normalize_decimal(current_price)
        
        if position.current_stop is not None and current_price_dec <= position.current_stop:
            return 'stop_loss'
        elif position.take_profit is not None and current_price_dec >= position.take_profit:
            return 'take_profit'
        
        return 'hold'

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

    def place_limit_order(self, symbol, side, amount, price, offset=0.0003):
        """Place a limit order with specified offset from current price"""
        try:
            if side == 'buy':
                limit_price = price * (1 - offset)  # Buy slightly below market
            else:
                limit_price = price * (1 + offset)  # Sell slightly above market
                
            order = self.exchange.create_limit_order(
                symbol,
                side,
                amount,
                limit_price
            )
            
            logging.info(f"Placed {side} limit order for {symbol} at {limit_price}: {order}")
            return order
        except Exception as e:
            logging.error(f"Error placing limit order: {str(e)}")
            return None
# =========================
# Backtesting Module
# =========================
class Backtester:
    def __init__(self, data_handler, signal_generator, risk_manager):
        self.data_handler = data_handler
        self.signal_generator = signal_generator
        self.risk_manager = risk_manager
        self.fee_rate = 0.001  # 0.1% trading fee

    def run_backtest(self, coin_id, initial_balance=70, days_back=30):
        """
        Run a backtest for a given coin using historical data.
        
        Args:
            coin_id (str): Trading pair to backtest
            initial_balance (float): Starting balance in USDT
            days_back (int): Number of days to backtest
        """
        logging.info(f"\nStarting backtest for {coin_id}")
        logging.info(f"Initial balance: ${initial_balance:.2f}")
        logging.info(f"Backtest period: {days_back} days")
        
        # Fetch historical data
        df = self.data_handler.fetch_altcoin_data(coin_id, days_back=days_back)
        if df is None or df.empty:
            logging.error(f"No data available for backtesting {coin_id}.")
            return None
            
        logging.info(f"Loaded {len(df)} candles from {df.index[0]} to {df.index[-1]}")
        
        # Compute indicators
        df = self.signal_generator.compute_indicators(df)
        logging.info("Computed technical indicators")
        
        # Initialize tracking variables
        balance = initial_balance
        position = 0
        entry_price = 0
        trades = []
        max_balance = initial_balance
        max_drawdown = 0
        daily_pnl = 0
        last_trade_day = None
        
        # Log initial conditions
        logging.info(f"Starting balance: ${balance:.2f}")
        logging.info("Beginning trade simulation...")
        
        # Start backtesting after sufficient data is available
        for i in range(self.signal_generator.ema_slow, len(df)):
            slice_df = df.iloc[:i+1]
            current_price = slice_df.iloc[-1]['close']
            current_atr = slice_df.iloc[-1]['atr']
            current_day = slice_df.index[-1].date()
            
            # Rest of your existing code...
            # Add logging statements at key points:
            
            if position == 0 and signal == 'buy':
                logging.info(f"Buy signal detected at ${current_price:.2f}")
                logging.info(f"ATR: {current_atr:.4f}, Volatility adjustment applied")
                
            if position > 0 and (decision != 'hold' or signal == 'sell'):
                logging.info(f"Sell signal detected at ${current_price:.2f}")
                logging.info(f"Exit reason: {decision if decision != 'hold' else 'signal'}")
                logging.info(f"Trade PnL: ${trade_pnl:.2f} ({(trade_pnl/initial_balance)*100:.2f}%)")
        
        # Enhanced results logging
        logging.info("\n=== Backtest Results ===")
        logging.info(f"Initial Balance: ${initial_balance:.2f}")
        logging.info(f"Final Balance: ${balance:.2f}")
        logging.info(f"Total Profit/Loss: ${total_pnl:.2f} ({total_pnl_pct:.2f}%)")
        logging.info(f"Maximum Drawdown: {max_drawdown*100:.2f}%")
        logging.info(f"Number of Trades: {num_trades}")
        logging.info(f"Win Rate: {win_rate:.2f}%")
        logging.info(f"Total Fees Paid: ${total_fees:.2f}")
        logging.info(f"Average Trade P/L: ${avg_trade_pnl:.2f}")
        
        # Log trade distribution
        logging.info("\nExit Reasons Distribution:")
        for reason, count in exit_reasons.items():
            logging.info(f"{reason}: {count} trades ({(count/num_trades)*100:.1f}%)")
        
        return results

# =========================
# Trading Bot Module
# =========================
class Position:
    """Tracks a single position with precise calculations"""
    def __init__(self, pair, entry_price, usdt_size, fee_rate):
        """Initialize a new position with proper decimal precision"""
        self.pair = pair
        self.entry_price = normalize_decimal(entry_price)
        self.usdt_size = normalize_decimal(usdt_size)
        self.fee_rate = normalize_decimal(fee_rate)
        
        # Calculate entry details with consistent precision
        self.entry_fee = normalize_decimal(self.usdt_size * self.fee_rate)
        self.quantity = normalize_decimal((self.usdt_size - self.entry_fee) / self.entry_price)
        self.entry_cost = normalize_decimal(self.usdt_size)
        
        # Initialize other attributes
        self.atr = normalize_decimal('0')
        self.current_stop = None
        self.stop_loss = None
        self.take_profit = None
        self.trailing_stop = None

    def is_valid(self):
        """Check if position meets minimum requirements"""
        min_order_size = normalize_decimal('10.0')  # Minimum order size in USDT
        return self.usdt_size >= min_order_size

    def update_current_value(self, current_price):
        """Calculate current position value and unrealized PnL"""
        current_price = normalize_decimal(current_price)
        gross_value = normalize_decimal(self.quantity * current_price)
        exit_fee = normalize_decimal(gross_value * self.fee_rate)
        net_value = normalize_decimal(gross_value - exit_fee)
        unrealized_pnl = normalize_decimal(net_value - self.entry_cost)
        
        return {
            'gross_value': gross_value,
            'net_value': net_value,
            'unrealized_pnl': unrealized_pnl,
            'exit_fee': exit_fee
        }

    def close_position(self, exit_price):
        """Close the position and calculate realized PnL"""
        exit_price = normalize_decimal(exit_price)
        gross_value = normalize_decimal(self.quantity * exit_price)
        exit_fee = normalize_decimal(gross_value * self.fee_rate)
        net_value = normalize_decimal(gross_value - exit_fee)
        realized_pnl = normalize_decimal(net_value - self.entry_cost)
        total_fees = normalize_decimal(self.entry_fee + exit_fee)
        
        return {
            'gross_value': gross_value,
            'net_value': net_value,
            'realized_pnl': realized_pnl,
            'exit_fee': exit_fee,
            'total_fees': total_fees
        }

    def close_partial_position(self, exit_price, close_ratio):
        """Close a portion of the position"""
        close_ratio = normalize_decimal(close_ratio)
        if not Decimal('0') < close_ratio <= Decimal('1'):
            raise ValueError("Close ratio must be between 0 and 1")
        
        # Calculate partial quantities
        close_quantity = normalize_decimal(self.quantity * close_ratio)
        remaining_quantity = normalize_decimal(self.quantity - close_quantity)
        
        # Calculate partial values
        exit_price = normalize_decimal(exit_price)
        gross_value = normalize_decimal(close_quantity * exit_price)
        exit_fee = normalize_decimal(gross_value * self.fee_rate)
        net_value = normalize_decimal(gross_value - exit_fee)
        
        # Update position
        self.quantity = remaining_quantity
        self.entry_cost = normalize_decimal(self.entry_cost * (Decimal('1') - close_ratio))
        self.entry_fee = normalize_decimal(self.entry_fee * (Decimal('1') - close_ratio))
        
        return {
            'gross_value': gross_value,
            'net_value': net_value,
            'exit_fee': exit_fee,
            'remaining_quantity': remaining_quantity
        }

class TradingBot:
    def __init__(self, trading_pairs, initial_balance=100):
        self.market_data = MarketDataHandler()
        self.signal_generator = SignalGenerator()
        self.risk_manager = RiskManager()
        self.trading_pairs = trading_pairs
        self.initial_balance = normalize_decimal(initial_balance)
        self.balance = self.initial_balance
        self.positions = {}  # Dictionary to track open positions
        self.trade_history = []
        self.daily_pnl = normalize_decimal('0')
        self.last_trade_day = None
        self.max_balance = self.initial_balance
        self.max_drawdown = normalize_decimal('0')

    def execute_trade(self, pair, signal, current_price, current_atr):
        """Execute a trade based on the signal and current market conditions"""
        if signal == 0:  # No signal
            return
            
        # Reset daily PnL if it's a new day
        current_day = datetime.now().date()
        if self.last_trade_day != current_day:
            self.daily_pnl = normalize_decimal('0')
            self.last_trade_day = current_day
        
            
        # Check daily loss limit
        if self.daily_pnl <= -self.balance * self.risk_manager.max_daily_loss:
            logging.info(f"Daily loss limit reached. No new trades for {pair}")
            return
            
        # Handle entry signals
        if signal == 1 and pair not in self.positions:
            logging.debug(f"[EXECUTION] Processing buy signal for {pair} at ${current_price:.2f}")
            
            # Calculate position size
            position_size = normalize_decimal(self.risk_manager.calculate_dynamic_position_size(
                float(self.balance), current_price, current_atr
            ))
        
            # Detailed execution logging
            position_size_usdt = float(position_size) * current_price
            logging.debug(f"""
    [EXECUTION] Trade Evaluation:
    - Signal: BUY
    - Pair: {pair}
    - Price: ${current_price:.2f}
    - ATR: ${current_atr:.4f}
    - Calculated Size: {float(position_size):.4f} ({pair.split('/')[0]}) = ${position_size_usdt:.2f}
    - Min Required: ${float(self.risk_manager.min_trade_amount):.2f}
    - Available Balance: ${float(self.balance):.2f}
    - Max Position: ${float(self.balance) * float(self.risk_manager.max_position_size):.2f}
    - Decision: {"EXECUTING" if position_size > 0 else "REJECTED"}
    """)
        
            if position_size == normalize_decimal('0'):
                logging.info(f"[EXECUTION] Trade rejected: Invalid position size for {pair}")
                return
                
            # Calculate stop levels
            stop_levels = self.risk_manager.calculate_stop_levels(
                current_price, current_atr
            )
            
            # Create new position
            position = Position(pair, current_price, position_size, self.risk_manager.fee_rate)
            position.current_stop = normalize_decimal(str(stop_levels['stop_loss']))
            position.take_profit = normalize_decimal(str(stop_levels['take_profit']))
            position.trailing_stop = normalize_decimal(str(stop_levels['trailing_stop']))
            position.atr = normalize_decimal(str(current_atr))
            
            # Update balance
            self.balance -= position.entry_cost
            
            # Store position
            self.positions[pair] = position
            
            logging.info(f"[EXECUTION] Opened {pair} position: Size=${float(position_size_usdt):.2f}, Entry=${current_price:.2f}")
            logging.info(f"[EXECUTION] SL=${float(position.current_stop):.2f}, TP=${float(position.take_profit):.2f}")
            
        # Handle exit signals and stop conditions
        elif pair in self.positions:
            position = self.positions[pair]
            
            # Update trailing stop if applicable
            new_stop = self.risk_manager.update_trailing_stop(position, current_price)
            if new_stop:
                position.current_stop = normalize_decimal(str(new_stop))
            
            # Check exit conditions
            exit_signal = self.risk_manager.evaluate_trade(position, current_price)
            
            if signal == -1 or exit_signal != 'hold':
                # Close position and calculate final values
                close_results = position.close_position(current_price)
                
                # Update balance and track metrics
                self.balance += normalize_decimal(str(close_results['net_value']))
                self.daily_pnl += normalize_decimal(str(close_results['realized_pnl']))
                
                # Record trade
                self.trade_history.append({
                    'pair': pair,
                    'entry_price': float(position.entry_price),
                    'exit_price': current_price,
                    'position_size': float(position.usdt_size),
                    'quantity': float(position.quantity),
                    'pnl': float(close_results['realized_pnl']),
                    'fees': float(close_results['total_fees']),
                    'exit_reason': exit_signal if exit_signal != 'hold' else 'signal'
                })
                
                print(f"Closing {pair} position: Exit=${current_price:.2f}, PnL=${float(close_results['realized_pnl']):.2f}")
                
                # Remove position
                del self.positions[pair]
                
                # Update max balance and drawdown
                self.max_balance = max(self.max_balance, self.balance)
                current_drawdown = (self.max_balance - self.balance) / self.max_balance
                self.max_drawdown = max(self.max_drawdown, current_drawdown)

    def run_backtest(self, start_date=None, end_date=None):
        """Run backtest with the specified parameters"""
        print(f"Starting backtest with initial balance: ${float(self.balance):.2f}")
        
        for pair in self.trading_pairs:
            print(f"\nBacktesting {pair}...")
            
            # Fetch historical data
            df = self.market_data.fetch_altcoin_data(pair)
            if df.empty:
                print(f"No data available for {pair}")
                continue
                
            # Generate signals
            signals = self.signal_generator.generate_signals(df)
            
            # Simulate trading
            for i in range(len(df)):
                current_price = df['close'].iloc[i]
                current_atr = df['atr'].iloc[i]
                signal = signals.iloc[i]
                
                self.execute_trade(pair, signal, current_price, current_atr)
                
        # Print final results
        print("\nBacktest Results:")
        print(f"Final Balance: ${float(self.balance):.2f}")
        total_pnl = self.balance - self.initial_balance
        print(f"Total Profit/Loss: ${float(total_pnl):.2f} ({float(total_pnl/self.initial_balance)*100:.2f}%)")
        print(f"Max Drawdown: {float(self.max_drawdown)*100:.2f}%")
        
        total_trades = len(self.trade_history)
        if total_trades > 0:
            winning_trades = sum(1 for trade in self.trade_history if trade['pnl'] > 0)
            win_rate = (winning_trades / total_trades) * 100
            total_fees = sum(trade['fees'] for trade in self.trade_history)
            avg_profit = sum(trade['pnl'] for trade in self.trade_history) / total_trades
            
            print(f"Number of Trades: {total_trades}")
            print(f"Win Rate: {win_rate:.2f}%")
            print(f"Average Trade Profit: ${avg_profit:.2f}")
            print(f"Total Fees Paid: ${total_fees:.2f}")
            
            # Print exit reasons distribution
            exit_reasons = Counter(trade['exit_reason'] for trade in self.trade_history)
            print("\nExit Reasons Distribution:")
            for reason, count in exit_reasons.items():
                print(f"{reason}: {count} trades ({(count/total_trades)*100:.1f}%)")

    def run_iteration(self):
        """Execute one iteration of the trading loop for live trading"""
        current_time = datetime.now()
        
        # Log current state
        print(f"\nIteration at {current_time}")
        print(f"Current Balance: ${float(self.balance):.2f}")
        print(f"Open Positions: {len(self.positions)}")
        
        for pair in self.trading_pairs:
            try:
                # Skip if we already have maximum positions
                if len(self.positions) >= self.risk_manager.max_trades:
                    print(f"Maximum positions ({self.risk_manager.max_trades}) reached. Skipping {pair}")
                    continue
                
                # Fetch latest data (1 day of 15-minute candles should be enough for indicators)
                df = self.market_data.fetch_altcoin_data(pair, timeframe='15m', days_back=1)
                if df is None or df.empty:
                    print(f"No data available for {pair}")
                    continue
                
                # Generate signal
                signals = self.signal_generator.generate_signals(df)
                current_signal = signals.iloc[-1]
                
                # Get current price and ATR
                current_price = df['close'].iloc[-1]
                current_atr = df['atr'].iloc[-1]
                
                # Execute trade based on signal
                self.execute_trade(pair, current_signal, current_price, current_atr)
                
                # Update trailing stops for open position
                if pair in self.positions:
                    position = self.positions[pair]
                    new_stop = self.risk_manager.update_trailing_stop(position, current_price)
                    if new_stop and new_stop != position.current_stop:
                        position.current_stop = normalize_decimal(str(new_stop))
                        print(f"Updated trailing stop for {pair} to ${float(new_stop):.2f}")
                
            except Exception as e:
                logging.error(f"Error processing {pair}: {str(e)}")
                continue
        
        # Print current positions status
        if self.positions:
            print("\nCurrent Positions:")
            for pair, position in self.positions.items():
                current_price = self.market_data.get_current_price(pair)
                if current_price:
                    position_value = position.update_current_value(current_price)
                print(f"{pair}: Entry=${float(position.entry_price):.2f}, "
                        f"Current=${current_price:.2f}, "
                      f"Size=${float(position.usdt_size):.2f}, "
                        f"PnL=${float(position_value['unrealized_pnl']):.2f}")
        
        # Print daily statistics
        if self.trade_history:
            today_trades = [t for t in self.trade_history 
                          if datetime.now().date() == datetime.now().date()]
            if today_trades:
                print("\nToday's Trading Statistics:")
                print(f"Number of Trades: {len(today_trades)}")
                print(f"Profit/Loss: ${sum(t['pnl'] for t in today_trades):.2f}")
                print(f"Win Rate: {(sum(1 for t in today_trades if t['pnl'] > 0) / len(today_trades)) * 100:.1f}%")

# =========================
# Utility Functions
# =========================
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('trading_bot.log')
        ]
    )

def setup_detailed_logging():
    """Configure detailed logging for both file and console output"""
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Generate timestamp for log file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f'logs/trading_bot_{timestamp}.log'
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Log system info
    logging.info("=== Trading Bot Started ===")
    logging.info(f"Python version: {sys.version}")
    logging.info(f"Operating System: {os.name}")
    logging.info(f"Trading Mode: {TRADING_MODE}")
    logging.info(f"Trading Pairs: {ALTCoin_LIST}")

# =========================
# Main Controller
# =========================
def main():
    print("Starting main function...")  # Debug print
    
    # Load environment variables
    load_dotenv()
    print("Loaded environment variables")  # Debug print
    
    # Configure detailed logging
    setup_detailed_logging()
    print("Set up logging")  # Debug print
    
    # Trading pairs to monitor
    TRADING_PAIRS = [
    'SOL/USDT'  # Only trade SOL since that's what we have
    ]
    print(f"Trading pairs: {TRADING_PAIRS}")  # Debug print
    
    # Get trading mode from environment
    TRADING_MODE = os.getenv('TRADING_MODE', 'backtest')
    print(f"Trading mode: {TRADING_MODE}")  # Debug print
    
    try:
        if TRADING_MODE.lower() == "backtest":
            print("Starting backtesting mode")  # Debug print
            logging.info("Starting backtesting mode")
            # Initialize bot with trading pairs
            bot = TradingBot(TRADING_PAIRS, initial_balance=100)
            print("Bot initialized")  # Debug print
            
            # Run backtest without days_back parameter
            bot.run_backtest()
            print("Backtest completed")  # Debug print
            
        elif TRADING_MODE.lower() == "live":
            print("Starting live trading mode")  # Debug print
            logging.info("Starting live trading mode")
            bot = TradingBot(TRADING_PAIRS, initial_balance=float(os.getenv('INITIAL_BALANCE', '1000')))
            
            while True:
                try:
                    bot.run_iteration()
                    update_interval = os.getenv('UPDATE_INTERVAL', '900').strip()
                    update_interval = update_interval.split('#')[0].strip()  # Remove any comments
                    time.sleep(int(update_interval))  # Convert to integer and sleep
                except Exception as e:
                    logging.error(f"Trading loop error: {str(e)}")
                    time.sleep(60)  # Wait 1 minute on error before retrying
            
    except Exception as e:
        print(f"Error in main: {str(e)}")  # Debug print
        logging.error(f"Fatal error: {str(e)}\n{traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    print("Script starting...")  # Debug print
    main() 