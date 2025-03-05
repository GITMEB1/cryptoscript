#!/usr/bin/env python3
"""
Apply Decimal Precision Fixes to Crypto Trading Bot
==================================================

This script applies the fixed version of the normalize_decimal function,
Position class, and RiskManager class to the original crypto_trading_bot.py file.

The fixes ensure consistent 8-decimal place precision throughout all calculations
using Decimal.quantize() with ROUND_HALF_UP rounding.
"""

import re
import sys

def read_file(path):
    """Read file content"""
    with open(path, 'r') as f:
        return f.read()
    
def write_file(path, content):
    """Write content to file"""
    with open(path, 'w') as f:
        f.write(content)

def extract_code_section(content, pattern):
    """Extract a section of code using regex pattern"""
    match = re.search(pattern, content, re.DOTALL)
    if match:
        return match.group(0)
    return None

def replace_section(original, pattern, replacement):
    """Replace a section in the original code with a new implementation"""
    return re.sub(pattern, replacement, original, flags=re.DOTALL)

def main():
    print("Applying decimal precision fixes to crypto trading bot...")
    
    # Check if source files exist
    source_files = ['fixed_decimal.py', 'fixed_position.py', 'fixed_risk_manager.py']
    for file in source_files:
        try:
            read_file(file)
        except FileNotFoundError:
            print(f"Error: {file} not found. Please ensure all fixed implementation files exist.")
            sys.exit(1)
    
    # Read the original trading bot file
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
    
    # Extract the fixed normalize_decimal function
    normalize_decimal_code = extract_code_section(
        read_file('fixed_decimal.py'),
        r'def normalize_decimal\(.*?\):.*?return value\.quantize\(.*?\)'
    )
    
    # Extract the fixed Position class
    position_class_code = extract_code_section(
        read_file('fixed_position.py'),
        r'class Position:.*?def close_partial_position\(.*?\}\s*\}'
    )
    
    # Extract the fixed RiskManager class
    risk_manager_class_code = extract_code_section(
        read_file('fixed_risk_manager.py'),
        r'class RiskManager:.*?def adjust_for_volatility\(.*?return self\.volatility_adjustment'
    )
    
    # Replace normalize_decimal function in original content
    if normalize_decimal_code:
        print("Replacing normalize_decimal function...")
        original_content = replace_section(
            original_content,
            r'def normalize_decimal\(.*?\):.*?return value\.normalize\(\)',
            normalize_decimal_code
        )
    else:
        print("Warning: Could not extract normalize_decimal function")
    
    # Replace Position class in original content
    if position_class_code:
        print("Replacing Position class...")
        original_content = replace_section(
            original_content, 
            r'class Position:.*?def close_partial_position\(.*?\}\s*\}',
            position_class_code
        )
    else:
        print("Warning: Could not extract Position class")
    
    # Replace RiskManager class in original content
    if risk_manager_class_code:
        print("Replacing RiskManager class...")
        original_content = replace_section(
            original_content,
            r'class RiskManager:.*?def adjust_for_volatility\(.*?return self\.volatility_adjustment',
            risk_manager_class_code
        )
    else:
        print("Warning: Could not extract RiskManager class")
    
    # Write updated content to a new file
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