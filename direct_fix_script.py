#!/usr/bin/env python3
"""
Direct Fix Script for Crypto Trading Bot
========================================

This script directly applies the fixed decimal precision implementation
to the crypto trading bot by replacing specific functions and classes.
"""

import re
import sys
from decimal import Decimal, ROUND_HALF_UP

def read_file(path):
    with open(path, 'r') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w') as f:
        f.write(content)

# Define the fixed normalize_decimal function
FIXED_NORMALIZE_DECIMAL_FUNCTION = '''
def normalize_decimal(value, precision=8):
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

# Define the fixed Position class
FIXED_POSITION_CLASS = '''
class Position:
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

# Define the fixed RiskManager class
FIXED_RISK_MANAGER_CLASS = '''
class RiskManager:
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
        
        # For short positions (not implemented in this example)
        # else:
        #     if current_price <= position.trailing_activation:
        #         new_stop = normalize_decimal(current_price + (position.atr * normalize_decimal(2.0)))
        #         if new_stop < position.trailing_stop:
        #             position.trailing_stop = new_stop
        
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

def main():
    print("Applying decimal precision fixes to crypto trading bot...")
    
    try:
        original_content = read_file('crypto_trading_bot.py')
    except FileNotFoundError:
        print("Error: crypto_trading_bot.py not found.")
        sys.exit(1)
    
    # Create backup of original file
    backup_path = 'crypto_trading_bot.py.bak'
    try:
        write_file(backup_path, original_content)
        print(f"Created backup of original file at {backup_path}")
    except Exception as e:
        print(f"Warning: Failed to create backup: {e}")
    
    # Replace the normalize_decimal function
    try:
        # Find the normalize_decimal function in the original file
        normalize_pattern = r'def\s+normalize_decimal\s*\([^)]*\):[^}]*?return\s+value\.normalize\(\)'
        if re.search(normalize_pattern, original_content, re.DOTALL):
            print("Replacing normalize_decimal function...")
            original_content = re.sub(normalize_pattern, FIXED_NORMALIZE_DECIMAL_FUNCTION.strip(), original_content, flags=re.DOTALL)
        else:
            print("Warning: normalize_decimal function not found in original file")
    except Exception as e:
        print(f"Error replacing normalize_decimal function: {e}")
    
    # Replace the Position class
    try:
        # Find the Position class in the original file
        position_pattern = r'class\s+Position:[^}]*?def\s+close_partial_position\s*\([^)]*\):[^}]*?\{[^}]*?\'remaining_quantity\'[^}]*?\}'
        if re.search(position_pattern, original_content, re.DOTALL):
            print("Replacing Position class...")
            original_content = re.sub(position_pattern, FIXED_POSITION_CLASS.strip(), original_content, flags=re.DOTALL)
        else:
            print("Warning: Position class not found in original file")
    except Exception as e:
        print(f"Error replacing Position class: {e}")
    
    # Replace the RiskManager class
    try:
        # Find the RiskManager class in the original file
        risk_manager_pattern = r'class\s+RiskManager:[^}]*?def\s+adjust_for_volatility\s*\([^)]*\):[^}]*?return\s+self\.volatility_adjustment'
        if re.search(risk_manager_pattern, original_content, re.DOTALL):
            print("Replacing RiskManager class...")
            original_content = re.sub(risk_manager_pattern, FIXED_RISK_MANAGER_CLASS.strip(), original_content, flags=re.DOTALL)
        else:
            print("Warning: RiskManager class not found in original file")
    except Exception as e:
        print(f"Error replacing RiskManager class: {e}")
    
    # Write the updated content to a new file
    try:
        output_path = 'crypto_trading_bot.py.fixed'
        write_file(output_path, original_content)
        print(f"Successfully wrote updated bot code to {output_path}")
        print(f"To apply the fixes, run: mv {output_path} crypto_trading_bot.py")
    except Exception as e:
        print(f"Error writing fixed file: {e}")
        sys.exit(1)
    
    print("Fix application completed!")

if __name__ == "__main__":
    main() 