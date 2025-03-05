#!/usr/bin/env python3
"""
Complete Fix for Crypto Trading Bot
==================================

This script reads the original trading bot file and creates a complete replacement
with the fixed decimal precision implementations.
"""

import sys
import re
from decimal import Decimal, ROUND_HALF_UP

def read_file(path):
    with open(path, 'r') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w') as f:
        f.write(content)

# Read the original trading bot code
try:
    print("Reading the original trading bot file...")
    original_content = read_file('crypto_trading_bot.py')
    # Make backup
    write_file('crypto_trading_bot.py.bak', original_content)
    print("Created backup at crypto_trading_bot.py.bak")
except Exception as e:
    print(f"Error reading original file: {e}")
    sys.exit(1)

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
    return value.quantize(quantizer, rounding=ROUND_HALF_UP)'''

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
        }'''

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
        
        return self.volatility_adjustment'''

try:
    # Use more precise pattern matching to find class definitions
    # Look for class definition followed by the entire class body until the next class definition
    position_class_pattern = r'class\s+Position:.*?(?=\n\s*class\s+\w+:|$)'
    risk_manager_class_pattern = r'class\s+RiskManager:.*?(?=\n\s*class\s+\w+:|$)'
    
    # Find the position of important sections in the original file using re.DOTALL to match across lines
    position_class_match = re.search(position_class_pattern, original_content, re.DOTALL)
    risk_manager_class_match = re.search(risk_manager_class_pattern, original_content, re.DOTALL)
    
    # Find where to insert the decimal import
    decimal_import_match = re.search(r'from\s+decimal\s+import\s+Decimal', original_content)
    
    # Verify that we found the classes before proceeding
    if not position_class_match:
        raise ValueError("Could not find Position class in the original file")
    if not risk_manager_class_match:
        raise ValueError("Could not find RiskManager class in the original file")
    
    # Create a copy of the original content to modify
    modified_content = original_content
    
    # Add or update decimal import
    if decimal_import_match:
        # Check if ROUND_HALF_UP is already imported
        if 'ROUND_HALF_UP' not in modified_content[:decimal_import_match.end() + 50]:
            modified_content = modified_content.replace(
                'from decimal import Decimal', 
                'from decimal import Decimal, ROUND_HALF_UP'
            )
    else:
        # Add import after other imports
        import_section = re.search(r'import\s+[a-zA-Z0-9_]+(?:\s*,\s*[a-zA-Z0-9_]+)*(?:\s+as\s+[a-zA-Z0-9_]+)?\s*$', original_content, re.MULTILINE)
        if import_section:
            import_end = import_section.end()
            modified_content = (
                modified_content[:import_end] + 
                '\nfrom decimal import Decimal, ROUND_HALF_UP' + 
                modified_content[import_end:]
            )
    
    # Replace the normalize_decimal function
    normalize_decimal_pattern = r'def\s+normalize_decimal\s*\(.*?\).*?(?=\n\s*def|\n\s*class|$)'
    normalize_decimal_match = re.search(normalize_decimal_pattern, original_content, re.DOTALL)
    
    if normalize_decimal_match:
        modified_content = modified_content.replace(
            normalize_decimal_match.group(0),
            FIXED_NORMALIZE_DECIMAL
        )
    else:
        # If not found, add it after imports
        import_section = re.search(r'from\s+decimal\s+import', modified_content)
        if import_section:
            import_line_end = modified_content.find('\n', import_section.end())
            if import_line_end > 0:
                modified_content = (
                    modified_content[:import_line_end+1] + 
                    '\n' + FIXED_NORMALIZE_DECIMAL + '\n\n' + 
                    modified_content[import_line_end+1:]
                )
    
    # Replace Position class - use the exact match we found
    if position_class_match:
        modified_content = modified_content.replace(
            position_class_match.group(0),
            FIXED_POSITION
        )
    
    # Replace RiskManager class - use the exact match we found
    if risk_manager_class_match:
        modified_content = modified_content.replace(
            risk_manager_class_match.group(0),
            FIXED_RISK_MANAGER
        )
    
    # Validate the modified content before writing
    # Check for unterminated string literals or other syntax errors
    try:
        # Simple validation - check for balanced quotes and parentheses
        open_quotes = modified_content.count('"') - modified_content.count('\\"')
        if open_quotes % 2 != 0:
            print("Warning: Unbalanced double quotes in modified content")
        
        open_quotes = modified_content.count("'") - modified_content.count("\\'")
        if open_quotes % 2 != 0:
            print("Warning: Unbalanced single quotes in modified content")
        
        # Write the modified content to a new file
        write_file('crypto_trading_bot.py.fixed', modified_content)
        print("Successfully wrote modified content to crypto_trading_bot.py.fixed")
        print("To apply the fix, run: mv crypto_trading_bot.py.fixed crypto_trading_bot.py")
    except Exception as e:
        print(f"Error validating modified content: {e}")
        sys.exit(1)
    
except Exception as e:
    print(f"Error applying fixes: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("Complete fix script completed!") 