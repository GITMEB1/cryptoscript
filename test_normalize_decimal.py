#!/usr/bin/env python3
"""
Simple Test Script for normalize_decimal Function
================================================

This script checks if the normalize_decimal function works with the ROUND_HALF_UP rounding mode.
"""

from decimal import Decimal, ROUND_HALF_UP

def normalize_decimal(value, force_precision=8):
    """Helper function to normalize decimal values with forced precision"""
    if isinstance(value, (int, float, str)):
        value = Decimal(str(value))
    
    # Create a quantizer with the exact number of decimal places
    quantizer = Decimal('1e-{}'.format(force_precision))
    return value.quantize(quantizer, rounding=ROUND_HALF_UP)

def test_normalize_decimal():
    """Test the normalize_decimal function with different inputs"""
    test_values = [
        Decimal('0.12345678'), 
        0.12345678, 
        '0.12345678',
        Decimal('0.123456789'),  # More precision than needed
        0.123456789,
        '0.123456789',
        Decimal('0.1234567850'),  # Test rounding up
        0.1234567850,
        '0.1234567850',
        Decimal('0.1234567849'),  # Test rounding down
        0.1234567849,
        '0.1234567849',
    ]
    
    print("Testing normalize_decimal function with ROUND_HALF_UP:")
    print("-" * 50)
    
    for val in test_values:
        normalized = normalize_decimal(val)
        print(f"Original: {val} (type: {type(val).__name__})")
        print(f"Normalized: {normalized} (type: {type(normalized).__name__})")
        print(f"Exponent: {normalized.as_tuple().exponent}")
        print("-" * 50)
    
    print("All tests completed.")

if __name__ == "__main__":
    test_normalize_decimal() 