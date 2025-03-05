#!/usr/bin/env python3
"""
Verification Script for Decimal Precision Fix
============================================

This script verifies that the decimal precision fix was applied correctly
by testing the normalize_decimal function and the Position class.
"""

import sys
from decimal import Decimal, ROUND_HALF_UP

def test_normalize_decimal():
    """Test that normalize_decimal function works correctly"""
    try:
        # Import the function from the trading bot
        sys.path.append('.')
        from crypto_trading_bot import normalize_decimal
        
        # Test cases
        test_values = [
            (10, "10.00000000"),
            (10.12345, "10.12345000"),
            (10.123456789, "10.12345679"),  # Should round
            ("10.123456789", "10.12345679"),  # String input
            (Decimal("10.123456789"), "10.12345679"),  # Decimal input
            (0.00000001, "0.00000001"),  # Smallest value
            (0.000000001, "0.00000000"),  # Below smallest value, should round to zero
        ]
        
        # Run tests
        print("Testing normalize_decimal function...")
        for value, expected in test_values:
            result = normalize_decimal(value)
            if str(result) != expected:
                print(f"❌ FAIL: normalize_decimal({value}) returned {result}, expected {expected}")
                return False
            else:
                print(f"✅ PASS: normalize_decimal({value}) = {result}")
        
        # Test exponent
        result = normalize_decimal(10.5)
        if result.as_tuple().exponent != -8:
            print(f"❌ FAIL: normalize_decimal(10.5) has exponent {result.as_tuple().exponent}, expected -8")
            return False
        else:
            print(f"✅ PASS: normalize_decimal(10.5) has correct exponent {result.as_tuple().exponent}")
        
        return True
    except Exception as e:
        print(f"❌ ERROR testing normalize_decimal: {e}")
        return False

def test_position_class():
    """Test that Position class works correctly with decimal precision"""
    try:
        # Import the Position class from the trading bot
        sys.path.append('.')
        from crypto_trading_bot import Position
        
        # Create a test position
        print("\nTesting Position class...")
        position = Position("BTC/USDT", 50000.12345678, 1000, 0.001)
        
        # Check that all values have correct precision
        print(f"Entry price: {position.entry_price}")
        print(f"USDT size: {position.usdt_size}")
        print(f"Fee rate: {position.fee_rate}")
        print(f"Entry fee: {position.entry_fee}")
        print(f"Quantity: {position.quantity}")
        
        # Test update_current_value
        current_value = position.update_current_value(55000.12345678)
        print(f"Current value results: {current_value}")
        
        # Test close_position
        close_result = position.close_position(60000.12345678)
        print(f"Close position results: {close_result}")
        
        # Check exponents of all decimal values
        for attr_name in ['entry_price', 'usdt_size', 'fee_rate', 'entry_fee', 'quantity']:
            attr_value = getattr(position, attr_name)
            if not isinstance(attr_value, Decimal):
                print(f"❌ FAIL: Position.{attr_name} is not a Decimal: {type(attr_value)}")
                return False
            if attr_value.as_tuple().exponent != -8:
                print(f"❌ FAIL: Position.{attr_name} has exponent {attr_value.as_tuple().exponent}, expected -8")
                return False
            else:
                print(f"✅ PASS: Position.{attr_name} has correct exponent {attr_value.as_tuple().exponent}")
        
        # Check exponents of calculation results
        for key, value in close_result.items():
            if not isinstance(value, Decimal):
                print(f"❌ FAIL: close_result['{key}'] is not a Decimal: {type(value)}")
                return False
            if value.as_tuple().exponent != -8:
                print(f"❌ FAIL: close_result['{key}'] has exponent {value.as_tuple().exponent}, expected -8")
                return False
            else:
                print(f"✅ PASS: close_result['{key}'] has correct exponent {value.as_tuple().exponent}")
        
        return True
    except Exception as e:
        print(f"❌ ERROR testing Position class: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all verification tests"""
    print("=== Decimal Precision Fix Verification ===\n")
    
    normalize_decimal_ok = test_normalize_decimal()
    position_class_ok = test_position_class()
    
    print("\n=== Verification Summary ===")
    print(f"normalize_decimal function: {'✅ PASS' if normalize_decimal_ok else '❌ FAIL'}")
    print(f"Position class: {'✅ PASS' if position_class_ok else '❌ FAIL'}")
    
    if normalize_decimal_ok and position_class_ok:
        print("\n✅ SUCCESS: The decimal precision fix was applied correctly!")
        return 0
    else:
        print("\n❌ ERROR: The decimal precision fix was not applied correctly.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 