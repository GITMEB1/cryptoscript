#!/usr/bin/env python3
"""
Direct Fix Script for Crypto Trading Bot
========================================

This script directly replaces the problematic classes in the crypto_trading_bot.py file
with fixed versions that handle decimal precision correctly.
"""

import re

# Read the original file
with open('crypto_trading_bot.py', 'r') as file:
    content = file.read()

# Define the fixed normalize_decimal function
normalize_decimal_function = '''
def normalize_decimal(value, force_precision=8):
    """Helper function to normalize decimal values with forced precision"""
    if isinstance(value, (int, float, str)):
        value = Decimal(str(value))
    if force_precision is not None:
        # Create a context with higher precision for intermediate calculations
        with localcontext() as ctx:
            ctx.prec = 28  # High precision for intermediate calculations
            # Format string with exact number of decimal places
            format_str = f'{{:.{force_precision}f}}'
            # Convert through string to ensure exact decimal places
            return Decimal(format_str.format(value))
    return value.normalize()
'''

# Define the fixed Position class
position_class = '''
class Position:
    """Tracks a single position with precise calculations"""
    def __init__(self, pair, entry_price, usdt_size, fee_rate):
        """Initialize a new position with proper decimal precision"""
        self.pair = pair
        
        # Store original values for exact calculations
        self._entry_price_raw = Decimal(str(entry_price))
        self._usdt_size_raw = Decimal(str(usdt_size))
        self._fee_rate_raw = Decimal(str(fee_rate))
        
        # Calculate entry details with exact precision
        with localcontext() as ctx:
            ctx.prec = 28  # High precision for intermediate calculations
            self._entry_fee_raw = self._usdt_size_raw * self._fee_rate_raw
            self._quantity_raw = (self._usdt_size_raw - self._entry_fee_raw) / self._entry_price_raw
        
        # Store normalized values for display and consistency
        self.entry_price = self._entry_price_raw
        self.usdt_size = self._usdt_size_raw
        self.fee_rate = self._fee_rate_raw
        self.entry_fee = self._entry_fee_raw
        self.quantity = self._quantity_raw
        self.entry_cost = self._usdt_size_raw

        # Initialize other attributes
        self.atr = Decimal('0')
        self.current_stop = None
        self.stop_loss = None
        self.take_profit = None
        self.trailing_stop = None
        self.trailing_activation = None

    def is_valid(self):
        """Check if position meets minimum requirements"""
        min_order_size = Decimal('10.0')  # Minimum order size in USDT
        return self.usdt_size >= min_order_size

    def update_current_value(self, current_price):
        """Calculate current position value and unrealized PnL"""
        # Store raw value for exact calculations
        _current_price_raw = Decimal(str(current_price))
        
        # Calculate with exact precision
        with localcontext() as ctx:
            ctx.prec = 28  # High precision for intermediate calculations
            _gross_value_raw = self.quantity * _current_price_raw
            _exit_fee_raw = _gross_value_raw * self.fee_rate
            _net_value_raw = _gross_value_raw - _exit_fee_raw
            _unrealized_pnl_raw = _net_value_raw - self.entry_cost
            _total_fees_raw = self.entry_fee + _exit_fee_raw

        return {
            'gross_value': _gross_value_raw,
            'net_value': _net_value_raw,
            'unrealized_pnl': _unrealized_pnl_raw,
            'exit_fee': _exit_fee_raw,
            'total_fees': _total_fees_raw
        }

    def close_position(self, exit_price):
        """Calculate final position value and realized PnL"""
        # Store raw value for exact calculations
        _exit_price_raw = Decimal(str(exit_price))
        
        # Calculate with exact precision
        with localcontext() as ctx:
            ctx.prec = 28  # High precision for intermediate calculations
            _gross_value_raw = self.quantity * _exit_price_raw
            _exit_fee_raw = _gross_value_raw * self.fee_rate
            _net_value_raw = _gross_value_raw - _exit_fee_raw
            _realized_pnl_raw = _net_value_raw - self.entry_cost
            _total_fees_raw = self.entry_fee + _exit_fee_raw

        return {
            'gross_value': _gross_value_raw,
            'net_value': _net_value_raw,
            'realized_pnl': _realized_pnl_raw,
            'exit_fee': _exit_fee_raw,
            'total_fees': _total_fees_raw
        }

    def close_partial_position(self, exit_price, close_ratio):
        """Close a portion of the position"""
        # Store raw values for exact calculations
        _exit_price_raw = Decimal(str(exit_price))
        _close_ratio_raw = Decimal(str(close_ratio))
        
        if not Decimal('0') < _close_ratio_raw <= Decimal('1'):
            raise ValueError("Close ratio must be between 0 and 1")

        # Calculate with exact precision
        with localcontext() as ctx:
            ctx.prec = 28  # High precision for intermediate calculations
            _close_quantity_raw = self.quantity * _close_ratio_raw
            _remaining_quantity_raw = self.quantity - _close_quantity_raw
            _gross_value_raw = _close_quantity_raw * _exit_price_raw
            _exit_fee_raw = _gross_value_raw * self.fee_rate
            _net_value_raw = _gross_value_raw - _exit_fee_raw
        
        # Update values
        self.quantity = _remaining_quantity_raw
        self.entry_cost = self.entry_cost * (Decimal('1') - _close_ratio_raw)
        self.entry_fee = self.entry_fee * (Decimal('1') - _close_ratio_raw)

        return {
            'gross_value': _gross_value_raw,
            'net_value': _net_value_raw,
            'exit_fee': _exit_fee_raw,
            'remaining_quantity': _remaining_quantity_raw
        }
'''

# Define the fixed RiskManager class
risk_manager_class = '''
class RiskManager:
    """Manages risk for trading positions"""
    def __init__(self, account_balance, risk_per_trade=0.01, daily_loss_limit=0.05):
        """Initialize risk manager with account balance and risk parameters"""
        self.account_balance = Decimal(str(account_balance))
        self.risk_per_trade = Decimal(str(risk_per_trade))
        self.daily_loss_limit = Decimal(str(daily_loss_limit))
        self.daily_loss = Decimal('0')
        self.positions = []
        self.volatility_adjustment = Decimal('1.0')

    def calculate_position_size(self, entry_price, stop_loss, fee_rate=Decimal('0.001')):
        """Calculate position size based on risk parameters and price levels"""
        # Ensure all inputs are Decimal
        entry_price = Decimal(str(entry_price))
        stop_loss = Decimal(str(stop_loss))
        fee_rate = Decimal(str(fee_rate))
        
        # Calculate risk amount in USDT
        risk_amount = self.account_balance * self.risk_per_trade * self.volatility_adjustment
        
        # Calculate price difference as a percentage
        with localcontext() as ctx:
            ctx.prec = 28  # High precision for intermediate calculations
            price_diff_pct = abs((entry_price - stop_loss) / entry_price)
            
            # Account for fees in both directions
            total_fee_impact = fee_rate * Decimal('2')
            
            # Calculate position size with fee consideration
            position_size = risk_amount / (price_diff_pct + total_fee_impact)
            
            # Ensure position size doesn't exceed account balance
            max_position = self.account_balance * Decimal('0.95')  # 95% of balance max
            position_size = min(position_size, max_position)
        
        return position_size

    def calculate_stop_levels(self, entry_price, atr, direction='long'):
        """Calculate stop loss and take profit levels based on ATR"""
        entry_price = Decimal(str(entry_price))
        atr = Decimal(str(atr))
        
        # Different multipliers for stop loss and take profit
        stop_multiplier = Decimal('2.0')
        tp_multiplier = Decimal('3.0')
        
        with localcontext() as ctx:
            ctx.prec = 28  # High precision for intermediate calculations
            
            if direction.lower() == 'long':
                stop_loss = entry_price - (atr * stop_multiplier)
                take_profit = entry_price + (atr * tp_multiplier)
            else:  # short
                stop_loss = entry_price + (atr * stop_multiplier)
                take_profit = entry_price - (atr * tp_multiplier)
        
        return {
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'atr': atr
        }

    def update_trailing_stop(self, position, current_price):
        """Update trailing stop if price moves favorably"""
        current_price = Decimal(str(current_price))
        
        # Initialize trailing stop if not set
        if position.trailing_stop is None:
            position.trailing_stop = position.stop_loss
            position.trailing_activation = position.entry_price * Decimal('1.01')  # 1% above entry
            return position.trailing_stop
        
        with localcontext() as ctx:
            ctx.prec = 28  # High precision for intermediate calculations
            
            # For long positions
            if current_price > position.entry_price:
                # Check if price has reached activation level
                if current_price >= position.trailing_activation:
                    # Calculate new trailing stop
                    new_stop = current_price - (position.atr * Decimal('2.0'))
                    
                    # Only update if new stop is higher than current stop
                    if new_stop > position.trailing_stop:
                        position.trailing_stop = new_stop
            
            # For short positions (not implemented in this example)
            # else:
            #     if current_price <= position.trailing_activation:
            #         new_stop = current_price + (position.atr * Decimal('2.0'))
            #         if new_stop < position.trailing_stop:
            #             position.trailing_stop = new_stop
        
        return position.trailing_stop

    def check_daily_loss_limit(self, new_loss=Decimal('0')):
        """Check if daily loss limit has been reached"""
        self.daily_loss += Decimal(str(new_loss))
        max_loss = self.account_balance * self.daily_loss_limit
        
        return self.daily_loss >= max_loss

    def adjust_for_volatility(self, current_volatility, baseline_volatility):
        """Adjust position sizing based on current market volatility"""
        current_volatility = Decimal(str(current_volatility))
        baseline_volatility = Decimal(str(baseline_volatility))
        
        with localcontext() as ctx:
            ctx.prec = 28  # High precision for intermediate calculations
            
            # Calculate volatility ratio
            if baseline_volatility > Decimal('0'):
                volatility_ratio = baseline_volatility / current_volatility
                
                # Adjust position sizing (lower for higher volatility)
                self.volatility_adjustment = min(
                    max(volatility_ratio, Decimal('0.5')),  # Min 50% of normal size
                    Decimal('1.5')  # Max 150% of normal size
                )
            else:
                self.volatility_adjustment = Decimal('1.0')
        
        return self.volatility_adjustment
'''

# Find and replace the normalize_decimal function
normalize_decimal_pattern = r'def normalize_decimal\([^)]*\):.*?return value\.normalize\(\)'
content = re.sub(normalize_decimal_pattern, normalize_decimal_function.strip(), content, flags=re.DOTALL)
print("Replaced normalize_decimal function")

# Find and replace the Position class
position_pattern = r'class Position:.*?def close_partial_position\([^)]*\):.*?return \{[^}]*\}'
content = re.sub(position_pattern, position_class.strip(), content, flags=re.DOTALL)
print("Replaced Position class")

# Find and replace the RiskManager class
risk_manager_pattern = r'class RiskManager:.*?def adjust_for_volatility\([^)]*\):.*?return self\.volatility_adjustment'
content = re.sub(risk_manager_pattern, risk_manager_class.strip(), content, flags=re.DOTALL)
print("Replaced RiskManager class")

# Write the updated content to a new file
with open('crypto_trading_bot.py.fixed', 'w') as file:
    file.write(content)

print("Update completed successfully. The updated file is saved as 'crypto_trading_bot.py.fixed'.")
print("To apply the changes, run: mv crypto_trading_bot.py.fixed crypto_trading_bot.py") 