#!/usr/bin/env python3
"""
Line-Based Fix for Crypto Trading Bot
====================================

This script uses line numbers to identify and replace specific sections of the code.
"""

import sys
from decimal import Decimal, ROUND_HALF_UP

def read_file(path):
    with open(path, 'r') as f:
        return f.readlines()

def write_file(path, lines):
    with open(path, 'w') as f:
        f.writelines(lines)

# Define the fixed normalize_decimal function code
FIXED_NORMALIZE_DECIMAL = '''def normalize_decimal(value, precision=8):
    """
    Enforce exact decimal precision using quantization
    
    Args:
        value: The value to normalize (int, float, str, or Decimal)
        precision: Number of decimal places to maintain (default: 8)
        
    Returns:
        Decimal value with exactly 'precision' decimal places
    """
    if not isinstance(value, Decimal):
        # Convert all values to Decimal first (handling float precision issues)
        try:
            value = Decimal(str(value))
        except:
            raise TypeError(f"Cannot convert {value} to Decimal")
    
    # Create a quantizer with the exact number of decimal places
    quantizer = Decimal('1e-{}'.format(precision))
    return value.quantize(quantizer, rounding=ROUND_HALF_UP)
'''

# Define the fixed Position class code
FIXED_POSITION = '''class Position:
    """Tracks a single position with precise calculations"""
    def __init__(self, pair, entry_price, usdt_size, fee_rate):
        """Initialize a new position with proper decimal precision"""
        self.pair = pair
        
        # Convert all inputs to normalized Decimals immediately
        self.entry_price = normalize_decimal(entry_price)
        self.usdt_size = normalize_decimal(usdt_size)
        self.fee_rate = normalize_decimal(fee_rate)
        
        # Calculate entry details with normalization at each step
        self.entry_fee = normalize_decimal(self.usdt_size * self.fee_rate)
        self.quantity = normalize_decimal((self.usdt_size - self.entry_fee) / self.entry_price)
        self.entry_cost = self.usdt_size  # This is already normalized

        # Initialize other attributes
        self.atr = normalize_decimal(0)
        self.current_stop = None
        self.stop_loss = None
        self.take_profit = None
        self.trailing_stop = None
        self.trailing_activation = None

    def is_valid(self):
        """Check if position meets minimum requirements"""
        min_order_size = normalize_decimal(10.0)  # Minimum order size in USDT
        return self.usdt_size >= min_order_size

    def update_current_value(self, current_price):
        """Calculate current position value and unrealized PnL"""
        # Normalize the current price
        current_price = normalize_decimal(current_price)
        
        # Calculate with normalization at each step
        gross_value = normalize_decimal(self.quantity * current_price)
        exit_fee = normalize_decimal(gross_value * self.fee_rate)
        net_value = normalize_decimal(gross_value - exit_fee)
        unrealized_pnl = normalize_decimal(net_value - self.entry_cost)
        total_fees = normalize_decimal(self.entry_fee + exit_fee)

        return {
            'gross_value': gross_value,
            'net_value': net_value,
            'unrealized_pnl': unrealized_pnl,
            'exit_fee': exit_fee,
            'total_fees': total_fees
        }

    def close_position(self, exit_price):
        """Calculate final position value and realized PnL"""
        # Normalize the exit price
        exit_price = normalize_decimal(exit_price)
        
        # Calculate with normalization at each step
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
        # Normalize inputs
        exit_price = normalize_decimal(exit_price)
        close_ratio = normalize_decimal(close_ratio)
        
        # Validate close ratio
        zero = normalize_decimal(0)
        one = normalize_decimal(1)
        if not (zero < close_ratio <= one):
            raise ValueError("Close ratio must be between 0 and 1")

        # Calculate with normalization at each step
        close_quantity = normalize_decimal(self.quantity * close_ratio)
        remaining_quantity = normalize_decimal(self.quantity - close_quantity)
        gross_value = normalize_decimal(close_quantity * exit_price)
        exit_fee = normalize_decimal(gross_value * self.fee_rate)
        net_value = normalize_decimal(gross_value - exit_fee)
        
        # Update position values
        self.quantity = remaining_quantity
        self.entry_cost = normalize_decimal(self.entry_cost * (one - close_ratio))
        self.entry_fee = normalize_decimal(self.entry_fee * (one - close_ratio))

        return {
            'gross_value': gross_value,
            'net_value': net_value,
            'exit_fee': exit_fee,
            'remaining_quantity': remaining_quantity
        }
'''

# Define the fixed RiskManager class code
FIXED_RISK_MANAGER = '''class RiskManager:
    """Manages risk for trading positions"""
    def __init__(self, account_balance, risk_per_trade=0.01, daily_loss_limit=0.05):
        """Initialize risk manager with account balance and risk parameters"""
        self.account_balance = normalize_decimal(account_balance)
        self.risk_per_trade = normalize_decimal(risk_per_trade)
        self.daily_loss_limit = normalize_decimal(daily_loss_limit)
        self.daily_loss = normalize_decimal(0)
        self.positions = []
        self.volatility_adjustment = normalize_decimal(1.0)

    def calculate_position_size(self, entry_price, stop_loss, fee_rate=0.001):
        """Calculate position size based on risk parameters and price levels"""
        # Normalize all inputs
        entry_price = normalize_decimal(entry_price)
        stop_loss = normalize_decimal(stop_loss)
        fee_rate = normalize_decimal(fee_rate)
        
        # Calculate risk amount in USDT
        risk_amount = normalize_decimal(self.account_balance * self.risk_per_trade * self.volatility_adjustment)
        
        # Calculate price difference as a percentage
        price_diff_pct = normalize_decimal(abs((entry_price - stop_loss) / entry_price))
        
        # Account for fees in both directions
        total_fee_impact = normalize_decimal(fee_rate * normalize_decimal(2))
        
        # Calculate position size with fee consideration
        position_size = normalize_decimal(risk_amount / (price_diff_pct + total_fee_impact))
        
        # Ensure position size doesn't exceed account balance
        max_position = normalize_decimal(self.account_balance * normalize_decimal(0.95))  # 95% of balance max
        position_size = normalize_decimal(min(position_size, max_position))
        
        return position_size

    def calculate_stop_levels(self, entry_price, atr, direction='long'):
        """Calculate stop loss and take profit levels based on ATR"""
        # Normalize inputs
        entry_price = normalize_decimal(entry_price)
        atr = normalize_decimal(atr)
        
        # Different multipliers for stop loss and take profit
        stop_multiplier = normalize_decimal(2.0)
        tp_multiplier = normalize_decimal(3.0)
        
        if direction.lower() == 'long':
            stop_loss = normalize_decimal(entry_price - (atr * stop_multiplier))
            take_profit = normalize_decimal(entry_price + (atr * tp_multiplier))
        else:  # short
            stop_loss = normalize_decimal(entry_price + (atr * stop_multiplier))
            take_profit = normalize_decimal(entry_price - (atr * tp_multiplier))
        
        return {
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'atr': atr
        }

    def update_trailing_stop(self, position, current_price):
        """Update trailing stop if price moves favorably"""
        current_price = normalize_decimal(current_price)
        
        # Initialize trailing stop if not set
        if position.trailing_stop is None:
            position.trailing_stop = position.stop_loss
            position.trailing_activation = normalize_decimal(position.entry_price * normalize_decimal(1.01))  # 1% above entry
            return position.trailing_stop
        
        # For long positions
        if current_price > position.entry_price:
            # Check if price has reached activation level
            if current_price >= position.trailing_activation:
                # Calculate new trailing stop
                new_stop = normalize_decimal(current_price - (position.atr * normalize_decimal(2.0)))
                
                # Only update if new stop is higher than current stop
                if new_stop > position.trailing_stop:
                    position.trailing_stop = new_stop
        
        return position.trailing_stop

    def check_daily_loss_limit(self, new_loss=0):
        """Check if daily loss limit has been reached"""
        new_loss = normalize_decimal(new_loss)
        self.daily_loss = normalize_decimal(self.daily_loss + new_loss)
        max_loss = normalize_decimal(self.account_balance * self.daily_loss_limit)
        
        return self.daily_loss >= max_loss

    def adjust_for_volatility(self, current_volatility, baseline_volatility):
        """Adjust position sizing based on current market volatility"""
        current_volatility = normalize_decimal(current_volatility)
        baseline_volatility = normalize_decimal(baseline_volatility)
        
        # Calculate volatility ratio
        zero = normalize_decimal(0)
        if baseline_volatility > zero:
            volatility_ratio = normalize_decimal(baseline_volatility / current_volatility)
            
            # Adjust position sizing (lower for higher volatility)
            min_adjustment = normalize_decimal(0.5)  # Min 50% of normal size
            max_adjustment = normalize_decimal(1.5)  # Max 150% of normal size
            
            self.volatility_adjustment = normalize_decimal(
                min(max(volatility_ratio, min_adjustment), max_adjustment)
            )
        else:
            self.volatility_adjustment = normalize_decimal(1.0)
        
        return self.volatility_adjustment
'''

try:
    print("Reading the original trading bot file...")
    lines = read_file('crypto_trading_bot.py')
    
    # Make backup
    write_file('crypto_trading_bot.py.bak', lines)
    print("Created backup at crypto_trading_bot.py.bak")
    
    # Find line numbers for important sections
    normalize_decimal_start = None
    normalize_decimal_end = None
    position_class_start = None
    position_class_end = None
    risk_manager_class_start = None
    risk_manager_class_end = None
    
    # Find the normalize_decimal function
    for i, line in enumerate(lines):
        if 'def normalize_decimal(' in line:
            normalize_decimal_start = i
            # Find the end of the function (next def or class)
            for j in range(i + 1, len(lines)):
                if 'def ' in lines[j] or 'class ' in lines[j]:
                    normalize_decimal_end = j - 1
                    break
            break
    
    # Find the Position class
    for i, line in enumerate(lines):
        if 'class Position:' in line:
            position_class_start = i
            # Find the end of the class (next class)
            for j in range(i + 1, len(lines)):
                if 'class ' in lines[j]:
                    position_class_end = j - 1
                    break
            break
    
    # Find the RiskManager class
    for i, line in enumerate(lines):
        if 'class RiskManager:' in line:
            risk_manager_class_start = i
            # Find the end of the class (next class or end of file)
            for j in range(i + 1, len(lines)):
                if 'class ' in lines[j]:
                    risk_manager_class_end = j - 1
                    break
            if not risk_manager_class_end:
                # If no next class, use end of file
                risk_manager_class_end = len(lines) - 1
            break
    
    # Verify that we found all sections
    if not normalize_decimal_start or not normalize_decimal_end:
        raise ValueError("Could not find normalize_decimal function")
    if not position_class_start or not position_class_end:
        raise ValueError("Could not find Position class")
    if not risk_manager_class_start or not risk_manager_class_end:
        raise ValueError("Could not find RiskManager class")
    
    print(f"Found normalize_decimal function at lines {normalize_decimal_start+1}-{normalize_decimal_end+1}")
    print(f"Found Position class at lines {position_class_start+1}-{position_class_end+1}")
    print(f"Found RiskManager class at lines {risk_manager_class_start+1}-{risk_manager_class_end+1}")
    
    # Check if we need to add ROUND_HALF_UP to imports
    decimal_import_line = None
    for i, line in enumerate(lines):
        if 'from decimal import Decimal' in line and 'ROUND_HALF_UP' not in line:
            decimal_import_line = i
            lines[i] = 'from decimal import Decimal, ROUND_HALF_UP\n'
            print(f"Updated decimal import at line {i+1}")
            break
    
    # Replace the normalize_decimal function
    new_lines = lines[:normalize_decimal_start]
    new_lines.append(FIXED_NORMALIZE_DECIMAL)
    new_lines.extend(lines[normalize_decimal_end+1:position_class_start])
    
    # Replace the Position class
    new_lines.append(FIXED_POSITION)
    new_lines.extend(lines[position_class_end+1:risk_manager_class_start])
    
    # Replace the RiskManager class
    new_lines.append(FIXED_RISK_MANAGER)
    new_lines.extend(lines[risk_manager_class_end+1:])
    
    # Write the modified content to a new file
    write_file('crypto_trading_bot.py.fixed', new_lines)
    print("Successfully wrote modified content to crypto_trading_bot.py.fixed")
    print("To apply the fix, run: cp crypto_trading_bot.py.fixed crypto_trading_bot.py")
    
except Exception as e:
    print(f"Error applying fixes: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("Line-based fix script completed!") 