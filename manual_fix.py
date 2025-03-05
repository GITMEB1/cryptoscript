#!/usr/bin/env python3
"""
Manual Fix Script
===============

This script manually fixes the trading bot file by:
1. Removing the problematic line at line 875
2. Adding the correct normalize_decimal function
3. Adding the ROUND_HALF_UP import
"""

import sys
import os
import datetime

def create_backup(file_path):
    """Create a backup of the original file."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.{timestamp}.bak"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as src:
            content = src.read()
        
        with open(backup_path, 'w', encoding='utf-8') as dst:
            dst.write(content)
        
        print(f"Created backup at: {backup_path}")
        return backup_path
    except Exception as e:
        print(f"Error creating backup: {e}")
        return None

def manual_fix(file_path):
    """Manually fix the file."""
    try:
        # Read the file line by line
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Fix the problematic line at line 875
        if len(lines) >= 875:
            problematic_line = lines[874]  # 0-indexed, so line 875 is at index 874
            if "Initial Balance: $" in problematic_line and "class Position:" in problematic_line:
                print(f"Found problematic line: {problematic_line.strip()}")
                lines[874] = '        logging.info(f"Initial Balance: $")\n'
                print(f"Fixed line: {lines[874].strip()}")
            else:
                print(f"Line 875 does not match the expected pattern: {problematic_line.strip()}")
        else:
            print(f"File has only {len(lines)} lines, but we expected at least 875.")
        
        # Add ROUND_HALF_UP import
        for i, line in enumerate(lines):
            if "from decimal import Decimal" in line and "ROUND_HALF_UP" not in line:
                lines[i] = line.replace("from decimal import Decimal", "from decimal import Decimal, ROUND_HALF_UP")
                print(f"Added ROUND_HALF_UP to import: {lines[i].strip()}")
                break
        else:
            # If we didn't find the import, add it at the beginning
            for i, line in enumerate(lines):
                if line.startswith("import ") or line.startswith("from "):
                    lines.insert(i, "from decimal import Decimal, ROUND_HALF_UP\n")
                    print(f"Added new import line: from decimal import Decimal, ROUND_HALF_UP")
                    break
        
        # Find and replace the normalize_decimal function
        new_function = '''
def normalize_decimal(value):
    """Convert a value to a Decimal with 8 decimal places."""
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    
    # Use quantize with ROUND_HALF_UP for proper rounding
    result = value.quantize(Decimal('0.00000001'), rounding=ROUND_HALF_UP)
    return result
'''
        
        # Look for the function
        found = False
        for i, line in enumerate(lines):
            if line.strip().startswith("def normalize_decimal"):
                # Find the end of the function
                j = i + 1
                while j < len(lines) and (lines[j].startswith(" ") or lines[j].strip() == ""):
                    j += 1
                
                # Replace the function
                lines[i:j] = new_function.splitlines(True)
                print(f"Replaced normalize_decimal function at line {i+1}")
                found = True
                break
        
        if not found:
            # Add the function at the end
            lines.append("\n" + new_function)
            print("Added normalize_decimal function at the end of the file")
        
        # Write the fixed content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        print("File has been fixed successfully.")
        return True
    
    except Exception as e:
        print(f"Error fixing the file: {e}")
        return False

def main():
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print("Usage: python manual_fix.py <path_to_trading_bot.py>")
        return 1
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist")
        return 1
    
    # Create a backup
    backup_path = create_backup(file_path)
    if not backup_path:
        return 1
    
    # Manually fix the file
    if not manual_fix(file_path):
        print("Failed to fix the file.")
        print(f"You can restore the backup from: {backup_path}")
        return 1
    
    print("The file has been fixed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 