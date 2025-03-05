#!/usr/bin/env python3
"""
Direct replacement script to update the crypto_trading_bot.py file
"""
import re
import sys
from decimal import Decimal, localcontext

def update_file(filename):
    """Update the crypto_trading_bot.py file with fixed classes"""
    print(f"Reading {filename}...")
    with open(filename, 'r') as f:
        content = f.read()
    
    # Read the fixed classes
    with open('fix_position.py', 'r') as f:
        position_content = f.read()
    
    with open('fix_risk_manager.py', 'r') as f:
        risk_manager_content = f.read()
    
    # Extract the normalize_decimal function from fix_position.py
    normalize_match = re.search(r'def normalize_decimal\(.*?\):.*?return value\.normalize\(\)', 
                               position_content, re.DOTALL)
    if normalize_match:
        normalize_function = normalize_match.group(0)
    else:
        print("Error: Could not find normalize_decimal function in fix_position.py")
        return
    
    # Extract the Position class from fix_position.py
    position_match = re.search(r'class Position:.*?def close_partial_position\(.*?\):.*?return \{.*?\'remaining_quantity\': remaining_quantity.*?\}', 
                              position_content, re.DOTALL)
    if position_match:
        position_class = position_match.group(0)
    else:
        print("Error: Could not find Position class in fix_position.py")
        return
    
    # Extract the RiskManager class from fix_risk_manager.py
    risk_manager_match = re.search(r'class RiskManager:.*?def evaluate_trade\(.*?\):.*?return \'hold\'', 
                                  risk_manager_content, re.DOTALL)
    if risk_manager_match:
        risk_manager_class = risk_manager_match.group(0)
    else:
        print("Error: Could not find RiskManager class in fix_risk_manager.py")
        return
    
    # Replace the normalize_decimal function in the content
    print("Replacing normalize_decimal function...")
    content = re.sub(r'def normalize_decimal\(.*?\):.*?return value\.normalize\(\)', 
                    normalize_function, content, flags=re.DOTALL)
    
    # Replace the Position class in the content
    print("Replacing Position class...")
    content = re.sub(r'class Position:.*?def close_partial_position\(.*?\):.*?return \{.*?\'remaining_quantity\': remaining_quantity.*?\}', 
                    position_class, content, flags=re.DOTALL)
    
    # Replace the RiskManager class in the content
    print("Replacing RiskManager class...")
    content = re.sub(r'class RiskManager:.*?def evaluate_trade\(.*?\):.*?return \'hold\'', 
                    risk_manager_class, content, flags=re.DOTALL)
    
    # Write the updated content to a new file
    new_filename = f"{filename}.new"
    print(f"Writing updated content to {new_filename}...")
    with open(new_filename, 'w') as f:
        f.write(content)
    
    print(f"Update completed successfully! New file: {new_filename}")
    print(f"To apply the changes, run: mv {new_filename} {filename}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        update_file(sys.argv[1])
    else:
        update_file("crypto_trading_bot.py") 