#!/usr/bin/env python3
"""
Script to update the crypto_trading_bot.py file with fixed Position and RiskManager classes
"""
import re
import sys

# Import the fixed classes
from fix_position import Position
from fix_risk_manager import RiskManager, normalize_decimal

def update_file(filename):
    """Update the crypto_trading_bot.py file with fixed classes"""
    print(f"Reading {filename}...")
    with open(filename, 'r') as f:
        content = f.read()
    
    # Replace the normalize_decimal function
    normalize_pattern = r'def normalize_decimal\(.*?\):\s+""".*?""".*?return value\.normalize\(\)'
    normalize_replacement = """def normalize_decimal(value, force_precision=8):
    \"\"\"Helper function to normalize decimal values with forced precision\"\"\"
    if isinstance(value, (int, float, str)):
        value = Decimal(str(value))
    if force_precision is not None:
        # Create a context with higher precision for intermediate calculations
        with localcontext() as ctx:
            ctx.prec = force_precision + 10  # Add extra precision for rounding
            # Format string with exact number of decimal places
            format_str = f'{{:.{force_precision}f}}'
            # Convert through string to ensure exact decimal places
            return Decimal(format_str.format(value))
    return value.normalize()"""
    
    # Replace the Position class
    position_pattern = r'class Position:.*?def close_partial_position\(.*?\).*?return \{.*?\'remaining_quantity\': remaining_quantity.*?\}'
    
    # Get the Position class source code
    position_source = ""
    with open('fix_position.py', 'r') as f:
        position_content = f.read()
        position_match = re.search(r'class Position:.*?def close_partial_position\(.*?\).*?return \{.*?\'remaining_quantity\': remaining_quantity.*?\}', 
                                  position_content, re.DOTALL)
        if position_match:
            position_source = position_match.group(0)
        else:
            print("Error: Could not find Position class in fix_position.py")
            sys.exit(1)
    
    # Replace the RiskManager class
    risk_manager_pattern = r'class RiskManager:.*?def evaluate_trade\(.*?\).*?return \'hold\''
    
    # Get the RiskManager class source code
    risk_manager_source = ""
    with open('fix_risk_manager.py', 'r') as f:
        risk_manager_content = f.read()
        risk_manager_match = re.search(r'class RiskManager:.*?def evaluate_trade\(.*?\).*?return \'hold\'', 
                                      risk_manager_content, re.DOTALL)
        if risk_manager_match:
            risk_manager_source = risk_manager_match.group(0)
        else:
            print("Error: Could not find RiskManager class in fix_risk_manager.py")
            sys.exit(1)
    
    # Replace the classes in the content
    print("Replacing normalize_decimal function...")
    content = re.sub(normalize_pattern, normalize_replacement, content, flags=re.DOTALL)
    
    print("Replacing Position class...")
    content = re.sub(position_pattern, position_source, content, flags=re.DOTALL)
    
    print("Replacing RiskManager class...")
    content = re.sub(risk_manager_pattern, risk_manager_source, content, flags=re.DOTALL)
    
    # Write the updated content back to the file
    print(f"Writing updated content to {filename}...")
    with open(filename, 'w') as f:
        f.write(content)
    
    print("Update completed successfully!")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        update_file(sys.argv[1])
    else:
        update_file("crypto_trading_bot.py") 