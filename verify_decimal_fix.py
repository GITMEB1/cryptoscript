#!/usr/bin/env python3
"""
Decimal Fix Verification
=======================

This script verifies that the normalize_decimal function has been correctly 
implemented with ROUND_HALF_UP rounding mode and proper precision.
"""

import sys
import importlib.util
from decimal import Decimal, ROUND_HALF_UP
import traceback


def load_module(file_path, module_name="crypto_trading_bot"):
    """Load a module from a file path dynamically"""
    try:
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if not spec:
            print(f"Error: Could not load module spec from {file_path}")
            return None
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception as e:
        print(f"Error loading module: {e}")
        traceback.print_exc()
        return None


def test_function_exists(module):
    """Test that the normalize_decimal function exists"""
    if not hasattr(module, 'normalize_decimal'):
        print("❌ normalize_decimal function not found in module")
        return False
    
    print("✅ normalize_decimal function found")
    return True


def test_import_exists(module):
    """Test that ROUND_HALF_UP is imported in the module"""
    module_vars = dir(module)
    if 'ROUND_HALF_UP' not in module_vars:
        print("❌ ROUND_HALF_UP not found in module namespace")
        return False
    
    print("✅ ROUND_HALF_UP import found")
    return True


def test_basic_functionality(normalize_decimal_func):
    """Test basic functionality of normalize_decimal function"""
    print("\n=== Basic Functionality Tests ===")
    test_values = [
        (Decimal('0.12345678'), '0.12345678'),
        (Decimal('0.123456789'), '0.12345679'),
        (Decimal('0.000000001'), '0.00000000'),
        (42, '42.00000000'),
        (3.14159, '3.14159000'),
        ('9.87654321', '9.87654321'),
    ]
    
    all_passed = True
    for value, expected in test_values:
        try:
            result = normalize_decimal_func(value)
            result_str = str(result)
            
            if result_str == expected:
                print(f"✅ normalize_decimal({value}) = {result}")
            else:
                print(f"❌ normalize_decimal({value}) = {result}, expected {expected}")
                all_passed = False
        except Exception as e:
            print(f"❌ Error testing {value}: {e}")
            all_passed = False
    
    return all_passed


def test_rounding_behavior(normalize_decimal_func):
    """Test rounding behavior of normalize_decimal function"""
    print("\n=== Rounding Behavior Tests ===")
    test_cases = [
        (Decimal('0.123456785'), '0.12345679'),  # Round up at exactly 5
        (Decimal('0.123456784'), '0.12345678'),  # Round down below 5
        (Decimal('0.123456786'), '0.12345679'),  # Round up above 5
        (Decimal('0.12345678499'), '0.12345678'),  # Round down at just below 5
        (Decimal('0.12345678501'), '0.12345679'),  # Round up at just above 5
    ]
    
    all_passed = True
    for value, expected in test_cases:
        try:
            result = normalize_decimal_func(value)
            result_str = str(result)
            
            if result_str == expected:
                print(f"✅ normalize_decimal({value}) = {result}")
            else:
                print(f"❌ normalize_decimal({value}) = {result}, expected {expected}")
                print(f"   This indicates incorrect rounding behavior")
                all_passed = False
        except Exception as e:
            print(f"❌ Error testing {value}: {e}")
            all_passed = False
    
    if all_passed:
        print("✅ ROUND_HALF_UP rounding behavior verified")
    else:
        print("❌ ROUND_HALF_UP rounding behavior incorrect")
    
    return all_passed


def test_exponent_precision(normalize_decimal_func):
    """Test that results have the correct exponent (precision)"""
    print("\n=== Decimal Precision Tests ===")
    test_values = [
        Decimal('0.12345678'),
        Decimal('42'),
        Decimal('0.00000001'),
        Decimal('123456789.12345678'),
        Decimal('0'),
    ]
    
    all_passed = True
    for value in test_values:
        try:
            result = normalize_decimal_func(value)
            exponent = result.as_tuple().exponent
            
            if exponent == -8:
                print(f"✅ normalize_decimal({value}) has correct exponent: {exponent}")
            else:
                print(f"❌ normalize_decimal({value}) has wrong exponent: {exponent}, expected -8")
                all_passed = False
        except Exception as e:
            print(f"❌ Error testing {value}: {e}")
            all_passed = False
    
    return all_passed


def test_edge_cases(normalize_decimal_func):
    """Test edge cases"""
    print("\n=== Edge Case Tests ===")
    
    edge_cases = [
        (Decimal('0'), '0.00000000'),
        (Decimal('-0.12345678'), '-0.12345678'),
        (Decimal('999999999.99999999'), '999999999.99999999'),
        (Decimal('0.000000001'), '0.00000000'),  # Below precision
        ('NaN', None),  # Should either fail or handle special values
    ]
    
    all_passed = True
    for value, expected in edge_cases[:-1]:  # Skip NaN for now
        try:
            result = normalize_decimal_func(value)
            result_str = str(result)
            
            if result_str == expected:
                print(f"✅ Edge case normalize_decimal({value}) = {result}")
            else:
                print(f"❌ Edge case normalize_decimal({value}) = {result}, expected {expected}")
                all_passed = False
        except Exception as e:
            print(f"❌ Error testing edge case {value}: {e}")
            all_passed = False
    
    # Test NaN separately
    try:
        result = normalize_decimal_func('NaN')
        print(f"ℹ️ NaN handling: normalize_decimal('NaN') = {result}")
    except:
        print("ℹ️ NaN input throws an exception (this is acceptable behavior)")
    
    return all_passed


def verify_decimal_fix(bot_file_path):
    """Main verification function"""
    print(f"Verifying decimal fix in: {bot_file_path}")
    
    # Load the module
    module = load_module(bot_file_path)
    if not module:
        return False
    
    # Verify that the function exists
    if not test_function_exists(module):
        return False
    
    # Verify that ROUND_HALF_UP is imported
    if not test_import_exists(module):
        return False
    
    # Get the function
    normalize_decimal = module.normalize_decimal
    
    # Run tests
    basic_passed = test_basic_functionality(normalize_decimal)
    rounding_passed = test_rounding_behavior(normalize_decimal)
    precision_passed = test_exponent_precision(normalize_decimal)
    edge_passed = test_edge_cases(normalize_decimal)
    
    # Overall results
    print("\n=== Overall Results ===")
    print(f"Basic functionality: {'✅ PASS' if basic_passed else '❌ FAIL'}")
    print(f"Rounding behavior:   {'✅ PASS' if rounding_passed else '❌ FAIL'}")
    print(f"Decimal precision:   {'✅ PASS' if precision_passed else '❌ FAIL'}")
    print(f"Edge cases:          {'✅ PASS' if edge_passed else '❌ FAIL'}")
    
    all_passed = basic_passed and rounding_passed and precision_passed and edge_passed
    
    if all_passed:
        print("\n✅ OVERALL: normalize_decimal function implementation is CORRECT")
        return True
    else:
        print("\n❌ OVERALL: normalize_decimal function has ISSUES that need to be fixed")
        return False


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python verify_decimal_fix.py <path_to_trading_bot.py>")
        return 1
    
    bot_file_path = sys.argv[1]
    
    try:
        success = verify_decimal_fix(bot_file_path)
        return 0 if success else 1
    except Exception as e:
        print(f"Unhandled error: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main()) 