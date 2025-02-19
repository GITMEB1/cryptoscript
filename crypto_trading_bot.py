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
from decimal import Decimal, getcontext, ROUND_DOWN, localcontext

# Load environment variables
load_dotenv()

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

def normalize_decimal(value, force_precision=7):
    """Helper function to normalize decimal values with forced precision"""
    if isinstance(value, (int, float, str)):
        value = Decimal(str(value))
    if force_precision is not None:
        return value.quantize(Decimal('0.' + '0' * force_precision))
    return value.normalize()

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
    
    def fetch_altcoin_data(self, coin_id, timeframe='15m'):
        """
        Fetch historical OHLCV data for a given altcoin from Binance.
        Returns a pandas DataFrame.
        """
        try:
            # Load more historical data for better backtesting
            limit = 1000 if TRADING_MODE.lower() == "backtest" else 100
            ohlcv = self.exchange.fetch_ohlcv(coin_id, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('datetime', inplace=True)
            # Ensure numeric types
            df = df.astype({'open': 'float', 'high': 'float', 'low': 'float', 'close': 'float', 'volume': 'float'})
            return df
        except Exception as e:
            logging.error(f"Error fetching OHLCV for {coin_id}: {e}")
            return None

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
# Signal Generator Module
# =========================
class SignalGenerator:
    def __init__(self):
        self.ema_fast = 9
        self.ema_slow = 21
        self.rsi_period = 14
        self.rsi_min = 50  # More conservative RSI threshold
        self.bb_period = 20
        self.bb_std = 2
        self.atr_period = 14
        self.volume_ma_period = 20
        self.volume_mult = 1.2  # Volume confirmation threshold
        self.min_price = 15  # Minimum price filter for coins

    def compute_indicators(self, df):
        """
        Compute technical indicators with ATR-based volatility measures
        """
        if df is None or df.empty:
            return df
            
        # EMAs for trend
        df['ema_fast'] = talib.EMA(df['close'], timeperiod=self.ema_fast)
        df['ema_slow'] = talib.EMA(df['close'], timeperiod=self.ema_slow)
        
        # RSI for momentum
        df['rsi'] = talib.RSI(df['close'], timeperiod=self.rsi_period)
        
        # ATR for volatility
        df['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=self.atr_period)
        df['atr_pct'] = df['atr'] / df['close'] * 100  # ATR as percentage of price
        
        # Dynamic ATR floor (1% of price)
        df['min_atr'] = df['close'] * 0.01
        df['effective_atr'] = df[['atr', 'min_atr']].max(axis=1)
        
        # Bollinger Bands for volatility
        df['bb_upper'], df['bb_middle'], df['bb_lower'] = talib.BBANDS(
            df['close'], 
            timeperiod=self.bb_period,
            nbdevup=self.bb_std,
            nbdevdn=self.bb_std
        )
        
        # Volume analysis
        df['volume_ma'] = talib.SMA(df['volume'], timeperiod=self.volume_ma_period)
        df['volume_ratio'] = df['volume'] / df['volume_ma']
        
        # Price momentum
        df['price_change'] = df['close'].pct_change()
        df['price_ma'] = talib.SMA(df['close'], timeperiod=self.ema_slow)
        df['trend_strength'] = (df['close'] - df['price_ma']) / df['price_ma'] * 100
        
        return df

    def generate_signal(self, df):
        """
        Generate trading signals with improved filtering
        """
        if df is None or df.empty or len(df) < self.ema_slow:
            return None
            
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        # Price filter
        if latest['close'] < self.min_price:
            return 'hold'
        
        # Volatility check
        hour_range = df[-12:]['high'].max() - df[-12:]['low'].min()  # 1-hour range (12 * 5min)
        if hour_range > 3 * latest['atr']:
            return 'hold'  # Too volatile
            
        # Volume conditions
        volume_active = latest['volume_ratio'] > self.volume_mult
        
        # Trend conditions
        trend_up = latest['close'] > latest['price_ma']
        ema_crossover_up = (prev['ema_fast'] <= prev['ema_slow']) and (latest['ema_fast'] > latest['ema_slow'])
        ema_crossover_down = (prev['ema_fast'] >= prev['ema_slow']) and (latest['ema_fast'] < latest['ema_slow'])
        
        # Momentum conditions
        rsi_bullish = latest['rsi'] > self.rsi_min
        trend_strong = abs(latest['trend_strength']) > 1.0  # 1% minimum trend strength
        
        # Entry conditions
        if (not self.in_position and 
            ema_crossover_up and 
            rsi_bullish and 
            volume_active and 
            trend_up and 
            trend_strong):
            return 'buy'
            
        # Exit conditions
        elif (self.in_position and 
              (ema_crossover_down or 
               latest['close'] < latest['ema_slow'] or
               latest['volume_ratio'] < 0.7)):  # Volume drying up
            return 'sell'
            
        return 'hold'

    @property
    def in_position(self):
        """Track if we're currently in a position"""
        return hasattr(self, '_in_position') and self._in_position

    @in_position.setter
    def in_position(self, value):
        self._in_position = value

    def generate_signals(self, df):
        """
        Generate signals for the entire DataFrame
        """
        if df is None or df.empty:
            return pd.Series(index=df.index)
            
        # Compute indicators
        df = self.compute_indicators(df)
        
        # Initialize signal series
        signals = pd.Series(0, index=df.index)
        
        # Track position state
        self.in_position = False
        
        # Generate signals for each candle
        for i in range(1, len(df)):
            # Create a slice of data up to current point
            current_slice = df.iloc[:i+1]
            
            # Get signal for current candle
            signal = self.generate_signal(current_slice)
            
            # Convert signal to numeric value
            if signal == 'buy':
                signals.iloc[i] = 1
                self.in_position = True
            elif signal == 'sell':
                signals.iloc[i] = -1
                self.in_position = False
            else:
                signals.iloc[i] = 0
                
        return signals

# =========================
# Risk Management Module
# =========================
class RiskManager:
    def __init__(self):
        # Risk parameters
        self.position_risk = normalize_decimal('0.02')    # Risk 2% per trade
        self.max_position_size = normalize_decimal('0.25')  # Maximum 25% of balance per trade
        self.min_trade_amount = normalize_decimal('10.0')  # Minimum $10 to account for slippage
        self.max_trades = 2  # Maximum concurrent trades
        self.max_daily_loss = normalize_decimal('0.02')  # 2% maximum daily loss
        self.max_portfolio_allocation = normalize_decimal('0.5')  # 50% max portfolio allocation
        
        # ATR-based stops
        self.atr_sl_mult = normalize_decimal('1.5')  # Stop loss at 1.5x ATR
        self.atr_tp_mult = normalize_decimal('3.0')  # Take profit at 3x ATR (3:1 ratio)
        self.atr_trail_mult = normalize_decimal('2.0')  # Start trailing at 2x ATR profit
        
        # Slippage and fees
        self.slippage_buffer = normalize_decimal('0.003')  # 0.3% slippage buffer
        self.fee_rate = normalize_decimal('0.00075')  # 0.075% with BNB discount

    def compute_position_size(self, balance, current_price, atr=None):
        """
        Compute position size based on ATR and account for minimum order size
        Returns position size in USDT
        """
        balance = normalize_decimal(balance)
        current_price = normalize_decimal(current_price)
        
        if balance < self.min_trade_amount:
            return normalize_decimal('0')
            
        # Calculate maximum position size
        max_position = min(balance * self.max_position_size, balance - normalize_decimal('1'))  # Keep 1 USDT for fees
        
        if atr and current_price:
            atr = normalize_decimal(atr)
            # Enforce minimum viable ATR (1% of price)
            min_atr = normalize_decimal(current_price * normalize_decimal('0.01'))
            effective_atr = max(atr, min_atr)
            
            # Calculate volatility-adjusted position size
            volatility_ratio = effective_atr / current_price
            risk_amount = balance * self.position_risk
            
            # Higher volatility = smaller position size
            # Use exponential scaling for more pronounced effect
            volatility_factor = normalize_decimal('1') / (volatility_ratio ** normalize_decimal('2'))
            position_size = risk_amount * volatility_factor * normalize_decimal('0.01')  # Scale factor
            
            # Apply slippage buffer
            position_size = position_size * (normalize_decimal('1') - self.slippage_buffer)
        else:
            # Fallback to simple position sizing if no ATR
            position_size = balance * normalize_decimal('0.2')  # 20% of balance
        
        # Ensure position meets minimum and maximum constraints
        if position_size < self.min_trade_amount:
            return normalize_decimal('0')
        return normalize_decimal(min(position_size, max_position))

    def calculate_stop_levels(self, entry_price, atr):
        """
        Calculate stop loss and take profit levels based on ATR
        """
        entry_price = normalize_decimal(entry_price)
        atr = normalize_decimal(atr)
        
        # Enforce minimum ATR
        min_atr = normalize_decimal(entry_price * normalize_decimal('0.01'))
        effective_atr = max(atr, min_atr)
        
        stop_loss = entry_price - (self.atr_sl_mult * effective_atr)
        take_profit = entry_price + (self.atr_tp_mult * effective_atr)
        trailing_activation = entry_price + (self.atr_trail_mult * effective_atr)
        
        return {
            'stop_loss': float(stop_loss),
            'take_profit': float(take_profit),
            'trailing_activation': float(trailing_activation),
            'atr': float(effective_atr)
        }

    def update_trailing_stop(self, position, current_price):
        """
        Update trailing stop if price has moved in our favor
        """
        if not position:
            return None
            
        current_price = normalize_decimal(current_price)
        
        if current_price >= position.trailing_activation:
            # Calculate new stop level
            new_stop = current_price - normalize_decimal(str(position.atr))
            
            # Only update if new stop is higher than current
            if position.current_stop is None or new_stop > normalize_decimal(str(position.current_stop)):
                return float(new_stop)
                
        return position.current_stop

    def evaluate_trade(self, position, current_price):
        """
        Evaluate if the current price has reached stop-loss or take-profit levels
        """
        if not position:
            return 'hold'
            
        current_price = normalize_decimal(current_price)
        
        if current_price <= normalize_decimal(str(position.current_stop)):
            return 'stop_loss'
        elif current_price >= normalize_decimal(str(position.take_profit)):
            return 'take_profit'
            
        return 'hold'

    def can_trade(self, daily_pnl, initial_balance):
        """Check if trading is allowed based on daily loss limit"""
        max_loss = normalize_decimal(initial_balance) * self.max_daily_loss
        return normalize_decimal(daily_pnl) > -max_loss

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
        self.fee_rate = 0.001  # 0.1% trading fee

    def run_backtest(self, coin_id, initial_balance=70):  # $70 initial balance
        """
        Run a backtest for a given coin using historical data.
        Implements the complete strategy with proper position sizing and risk management.
        """
        df = self.data_handler.fetch_altcoin_data(coin_id)
        if df is None or df.empty:
            logging.error(f"No data available for backtesting {coin_id}.")
            return None
            
        df = self.signal_generator.compute_indicators(df)
        
        # Initialize tracking variables
        balance = initial_balance
        position = 0
        entry_price = 0
        trades = []
        max_balance = initial_balance
        max_drawdown = 0
        daily_pnl = 0
        last_trade_day = None
        
        # Start backtesting after sufficient data is available for indicators
        for i in range(self.signal_generator.ema_slow, len(df)):
            slice_df = df.iloc[:i+1]
            current_price = slice_df.iloc[-1]['close']
            current_atr = slice_df.iloc[-1]['atr']
            current_day = slice_df.index[-1].date()
            
            # Reset daily PnL on new day
            if last_trade_day is None:
                last_trade_day = current_day
            elif current_day != last_trade_day:
                daily_pnl = 0
                last_trade_day = current_day
            
            # Update maximum balance and drawdown
            current_value = balance + (position * current_price)
            if current_value > max_balance:
                max_balance = current_value
            current_drawdown = (max_balance - current_value) / max_balance
            max_drawdown = max(max_drawdown, current_drawdown)
            
            if position == 0:  # Not in a position
                # Check if we've hit daily loss limit
                if daily_pnl <= -initial_balance * self.risk_manager.max_daily_loss:
                    continue
                    
                signal = self.signal_generator.generate_signal(slice_df)
                if signal == 'buy':
                    # Calculate position size
                    position_size = self.risk_manager.compute_position_size(
                        balance, 
                        current_price,
                        current_atr
                    )
                    
                    if position_size >= self.risk_manager.min_trade_amount:
                        # Account for fees
                        position = (position_size * (1 - self.fee_rate)) / current_price
                        entry_price = current_price
                        balance -= position_size
                        trades.append({
                            'type': 'buy',
                            'time': slice_df.index[-1],
                            'price': current_price,
                            'position_size': position_size,
                            'balance': balance,
                            'fees': position_size * self.fee_rate
                        })
            
            elif position > 0:  # In a position
                # Check stop loss and take profit
                decision = self.risk_manager.evaluate_trade(
                    self.risk_manager.calculate_stop_levels(entry_price, current_atr),
                    current_price
                )
                
                signal = self.signal_generator.generate_signal(slice_df)
                
                if decision != 'hold' or signal == 'sell':
                    # Close position
                    exit_value = position * current_price * (1 - self.fee_rate)
                    trade_pnl = exit_value - (position * entry_price)
                    daily_pnl += trade_pnl
                    balance += exit_value
                    
                    trades.append({
                        'type': 'sell',
                        'time': slice_df.index[-1],
                        'price': current_price,
                        'position_size': exit_value,
                        'balance': balance,
                        'pnl': trade_pnl,
                        'pnl_pct': (trade_pnl / (position * entry_price)) * 100,
                        'exit_reason': decision if decision != 'hold' else 'signal',
                        'fees': exit_value * self.fee_rate
                    })
                    position = 0
                    
        # Close any remaining position at the end
        if position > 0:
            final_price = df.iloc[-1]['close']
            exit_value = position * final_price * (1 - self.fee_rate)
            trade_pnl = exit_value - (position * entry_price)
            balance += exit_value
            
            trades.append({
                'type': 'sell',
                'time': df.index[-1],
                'price': final_price,
                'position_size': exit_value,
                'balance': balance,
                'pnl': trade_pnl,
                'pnl_pct': (trade_pnl / (position * entry_price)) * 100,
                'exit_reason': 'backtest_end',
                'fees': exit_value * self.fee_rate
            })
            
        # Calculate performance metrics
        total_pnl = balance - initial_balance
        total_pnl_pct = (total_pnl / initial_balance) * 100
        num_trades = len([t for t in trades if t['type'] == 'buy'])
        win_trades = len([t for t in trades if t['type'] == 'sell' and t.get('pnl', 0) > 0])
        win_rate = (win_trades / num_trades * 100) if num_trades > 0 else 0
        total_fees = sum(t.get('fees', 0) for t in trades)
        avg_trade_pnl = sum(t.get('pnl', 0) for t in trades if t['type'] == 'sell') / num_trades if num_trades > 0 else 0
        
        results = {
            'coin': coin_id,
            'initial_balance': initial_balance,
            'final_balance': balance,
            'total_pnl': total_pnl,
            'total_pnl_pct': total_pnl_pct,
            'max_drawdown_pct': max_drawdown * 100,
            'num_trades': num_trades,
            'win_rate': win_rate,
            'total_fees': total_fees,
            'avg_trade_pnl': avg_trade_pnl,
            'trades': trades
        }
        
        logging.info(f"\nBacktest Results for {coin_id}:")
        logging.info(f"Profit/Loss: ${total_pnl:.2f} ({total_pnl_pct:.2f}%)")
        logging.info(f"Max Drawdown: {(max_drawdown * 100):.2f}%")
        logging.info(f"Number of Trades: {num_trades}")
        logging.info(f"Win Rate: {win_rate:.2f}%")
        logging.info(f"Total Fees: ${total_fees:.2f}")
        logging.info(f"Average Trade P/L: ${avg_trade_pnl:.2f}")
        
        return results

# =========================
# Trading Bot Module
# =========================
class Position:
    """Tracks a single position with precise calculations"""
    def __init__(self, pair, entry_price, usdt_size, fee_rate):
        self.pair = pair
        # Convert all inputs to Decimal with proper precision
        self.entry_price = normalize_decimal(entry_price)
        self.usdt_size = normalize_decimal(usdt_size)
        self.fee_rate = normalize_decimal(fee_rate)
        
        # Calculate values with proper precision
        with localcontext() as ctx:
            ctx.prec = 10  # Use higher precision for intermediate calculations
            self.entry_fee = normalize_decimal(self.usdt_size * self.fee_rate)
            self.entry_cost = normalize_decimal(self.usdt_size)
            self.quantity = normalize_decimal((self.usdt_size - self.entry_fee) / self.entry_price)
        
        self.current_stop = None
        self.trailing_activation = None
        self.atr = None

    def is_valid(self):
        """Check if position meets minimum order size requirements"""
        min_order_size = normalize_decimal('10.0')  # $10 minimum order
        return self.usdt_size >= min_order_size

    def update_current_value(self, current_price):
        """Calculate current position value and unrealized PnL"""
        current_price = normalize_decimal(current_price)
        gross_value = self.quantity * current_price
        exit_fee = gross_value * self.fee_rate
        net_value = gross_value - exit_fee
        unrealized_pnl = net_value - self.entry_cost
        return {
            'gross_value': float(gross_value),
            'net_value': float(net_value),
            'unrealized_pnl': float(unrealized_pnl),
            'fees': float(self.entry_fee + exit_fee)
        }
        
    def close_position(self, exit_price):
        """Calculate final position value and realized PnL"""
        exit_price = normalize_decimal(exit_price)
        gross_value = self.quantity * exit_price
        exit_fee = gross_value * self.fee_rate
        net_value = gross_value - exit_fee
        realized_pnl = net_value - self.entry_cost
        return {
            'gross_value': float(gross_value),
            'net_value': float(net_value),
            'realized_pnl': float(realized_pnl),
            'total_fees': float(self.entry_fee + exit_fee)
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
            print(f"Daily loss limit reached. No new trades for {pair}")
            return
            
        # Handle entry signals
        if signal == 1 and pair not in self.positions:
            # Calculate position size
            position_size = normalize_decimal(self.risk_manager.compute_position_size(
                float(self.balance), current_price, current_atr
            ))
            
            if position_size == normalize_decimal('0'):
                return
                
            # Calculate stop levels
            stop_levels = self.risk_manager.calculate_stop_levels(
                current_price, current_atr
            )
            
            # Create new position
            position = Position(pair, current_price, position_size, self.risk_manager.fee_rate)
            position.current_stop = normalize_decimal(str(stop_levels['stop_loss']))
            position.take_profit = normalize_decimal(str(stop_levels['take_profit']))
            position.trailing_activation = normalize_decimal(str(stop_levels['trailing_activation']))
            position.atr = normalize_decimal(str(stop_levels['atr']))
            
            # Update balance
            self.balance -= position.entry_cost
            
            # Store position
            self.positions[pair] = position
            
            print(f"Opening {pair} position: Size=${float(position_size):.2f}, Entry=${current_price:.2f}")
            print(f"SL=${float(position.current_stop):.2f}, TP=${float(position.take_profit):.2f}")
            
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
                
                # Fetch latest data
                df = self.market_data.fetch_altcoin_data(pair, limit=100)  # Get enough data for indicators
                if df.empty:
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
                unrealized_pnl = (float(position.usdt_size) * 
                    (self.market_data.get_current_price(pair) - float(position.entry_price)))
                print(f"{pair}: Entry=${float(position.entry_price):.2f}, "
                      f"Current=${self.market_data.get_current_price(pair):.2f}, "
                      f"Size=${float(position.usdt_size):.2f}, "
                      f"PnL=${unrealized_pnl:.2f}")
        
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

# =========================
# Main Controller
# =========================
def main():
    # Load environment variables
    load_dotenv()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Trading pairs to monitor
    TRADING_PAIRS = [
        'ETH/USDT',
        'BNB/USDT',
        'SOL/USDT',
        'ADA/USDT'
    ]
    
    # Get trading mode from environment
    TRADING_MODE = os.getenv('TRADING_MODE', 'backtest')
    
    try:
        if TRADING_MODE.lower() == "backtest":
            # Initialize bot with trading pairs
            bot = TradingBot(TRADING_PAIRS, initial_balance=100)
            
            # Run backtest
            bot.run_backtest()
            
        elif TRADING_MODE.lower() == "live":
            # Verify API credentials are available
            if not os.getenv('BINANCE_API_KEY') or not os.getenv('BINANCE_SECRET_KEY'):
                raise ValueError("API credentials not found. Please set BINANCE_API_KEY and BINANCE_SECRET_KEY in .env file")
            
            # Initialize bot with trading pairs
            bot = TradingBot(TRADING_PAIRS, initial_balance=float(os.getenv('INITIAL_BALANCE', '1000')))
            
            print("Starting live trading...")
            print(f"Monitoring pairs: {', '.join(TRADING_PAIRS)}")
            
            while True:
                try:
                    # Run one iteration of the trading loop
                    bot.run_iteration()
                    
                    # Sleep for the specified interval
                    time.sleep(int(os.getenv('UPDATE_INTERVAL', '900')))  # Default 15 minutes
                    
                except Exception as e:
                    logging.error(f"Error in trading loop: {str(e)}")
                    time.sleep(60)  # Wait before retrying
                    
        else:
            raise ValueError(f"Invalid TRADING_MODE: {TRADING_MODE}. Must be 'backtest' or 'live'")
            
    except Exception as e:
        logging.error(f"Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 