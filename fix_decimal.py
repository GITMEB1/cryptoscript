#!/usr/bin/env python
import re

def create_fixed_function():
    """
    Creates a fixed normalize_decimal function that handles both the original function signature
    and the one with decimal_places parameter.
    """
    fixed_function = '''def normalize_decimal(value, decimal_places=8):
    """
    Normalize a decimal value to a specified number of decimal places.
    Uses Decimal.quantize with ROUND_HALF_UP for proper rounding.
    """
    from decimal import Decimal, ROUND_HALF_UP
    
    # Convert value to Decimal if it's not already
    if not isinstance(value, Decimal):
        try:
            value = Decimal(str(value))
        except:
            # Handle invalid input
            return Decimal('0')
    
    # Create the quantization format based on decimal_places
    quantize_format = Decimal('0.' + '0' * decimal_places)
    
    # Perform the quantization with proper rounding
    result = value.quantize(quantize_format, rounding=ROUND_HALF_UP)
    
    return result'''
    
    return fixed_function

print("# Script to fix normalize_decimal function in crypto_trading_bot.py")
print("# This script updates the function to handle different input types and parameter signatures")
print(create_fixed_function())
print("\n# Usage on remote server:")
print("# 1. Save this content to a file")
print("# 2. Use regex to replace the old function with this improved version")
print("# 3. Restart the trading bot") 