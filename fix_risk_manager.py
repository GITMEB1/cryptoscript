from decimal import Decimal, localcontext

def normalize_decimal(value, force_precision=8):
    """Helper function to normalize decimal values with forced precision"""
    if isinstance(value, (int, float, str)):
        value = Decimal(str(value))
    if force_precision is not None:
        # Create a context with higher precision for intermediate calculations
        with localcontext() as ctx:
            ctx.prec = force_precision + 10  # Add extra precision for rounding
            # Format string with exact number of decimal places
            format_str = f'{{:.{force_precision}f}}'
            # Convert through string to ensure exact decimal places
            return Decimal(format_str.format(value))
    return value.normalize()

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
        self.last_reset = None  # Will be set to datetime.now().date() in first call

    def can_trade(self, daily_pnl=None, initial_balance=None):
        """Check if trading is allowed based on daily limits"""
        from datetime import datetime
        
        # Reset daily counters if it's a new day
        current_date = datetime.now().date()
        if self.last_reset is None or current_date > self.last_reset:
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

        with localcontext() as ctx:
            ctx.prec = 28  # High precision for intermediate calculations
            stop_loss = normalize_decimal(entry - (atr_dec * self.atr_sl_mult))
            take_profit = normalize_decimal(entry + (atr_dec * self.atr_tp_mult))
            trailing_stop = normalize_decimal(stop_loss)
            trailing_activation = normalize_decimal(entry + (atr_dec * self.atr_trail_mult))

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
        price_dec = normalize_decimal(price)
        volatility_dec = normalize_decimal(volatility)
        
        with localcontext() as ctx:
            ctx.prec = 28  # High precision for intermediate calculations
            
            # Calculate maximum position size based on balance
            max_position = normalize_decimal(balance_dec * self.max_position_size)
            
            # Adjust position size based on volatility - higher volatility = smaller position
            vol_adj = normalize_decimal(Decimal('1.0') - (volatility_dec * Decimal('0.05')))
            vol_adj = max(vol_adj, normalize_decimal('0.2'))  # Minimum 20% of standard size
            
            # Calculate final position size with volatility adjustment
            position_size = normalize_decimal(max_position * vol_adj)
            
            # Ensure position size is within limits
            position_size = max(min(position_size, max_position), self.min_trade_amount)
            
        return position_size

    def update_daily_stats(self, pnl):
        """Update daily statistics after a trade"""
        self.daily_pnl += normalize_decimal(pnl)
        self.daily_trades += 1

    def update_trailing_stop(self, position, current_price):
        """Update trailing stop if price moves above activation level"""
        current_price_dec = normalize_decimal(current_price)
        
        with localcontext() as ctx:
            ctx.prec = 28  # High precision for intermediate calculations
            
            if hasattr(position, 'trailing_activation') and position.trailing_activation is not None:
                if current_price_dec >= position.trailing_activation:
                    # Calculate new stop based on current price
                    new_stop = normalize_decimal(current_price_dec - position.atr)
                    
                    # Only update if new stop is higher than current stop
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