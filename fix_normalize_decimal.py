#!/usr/bin/env python3
"""
Fix for normalize_decimal function
=================================

This script only fixes the normalize_decimal function, which is the core of the decimal precision issue.
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

try:
    print("Reading the original trading bot file...")
    original_content = read_file('crypto_trading_bot.py')
    
    # Make backup
    write_file('crypto_trading_bot.py.bak', original_content)
    print("Created backup at crypto_trading_bot.py.bak")
    
    # Find the normalize_decimal function
    normalize_decimal_pattern = r'def\s+normalize_decimal\s*\([^)]*\):[^}]*?(?=\n\s*def|\n\s*class)'
    normalize_decimal_match = re.search(normalize_decimal_pattern, original_content, re.DOTALL)
    
    if not normalize_decimal_match:
        raise ValueError("Could not find normalize_decimal function")
    
    print(f"Found normalize_decimal function")
    
    # Check if we need to add ROUND_HALF_UP to imports
    if 'from decimal import Decimal' in original_content and 'ROUND_HALF_UP' not in original_content:
        modified_content = original_content.replace(
            'from decimal import Decimal', 
            'from decimal import Decimal, ROUND_HALF_UP'
        )
        print("Updated decimal import to include ROUND_HALF_UP")
    else:
        modified_content = original_content
    
    # Replace the normalize_decimal function
    modified_content = modified_content.replace(
        normalize_decimal_match.group(0),
        FIXED_NORMALIZE_DECIMAL
    )
    
    # Write the modified content to a new file
    write_file('crypto_trading_bot.py.fixed', modified_content)
    print("Successfully wrote modified content to crypto_trading_bot.py.fixed")
    print("To apply the fix, run: cp crypto_trading_bot.py.fixed crypto_trading_bot.py")
    
except Exception as e:
    print(f"Error applying fixes: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("normalize_decimal fix script completed!") 