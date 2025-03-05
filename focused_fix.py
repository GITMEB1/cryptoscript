#!/usr/bin/env python3
"""
Focused Syntax Error Fix
======================

This script focuses specifically on fixing the unterminated string literal
at line 875 in the trading bot file.
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
        return backup_path, content
    except Exception as e:
        print(f"Error creating backup: {e}")
        return None, None

def fix_specific_error(file_path):
    """Fix the specific error at line 875."""
    try:
        # Read the file line by line
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Check if we have enough lines
        if len(lines) < 875:
            print(f"File has only {len(lines)} lines, but we need to fix line 875.")
            return False
        
        # Get the problematic line
        problematic_line = lines[874]  # 0-indexed, so line 875 is at index 874
        print(f"Problematic line: {problematic_line.strip()}")
        
        # Check if this is the line we expect
        if "Initial Balance: $" in problematic_line and "class Position:" in problematic_line:
            # Fix the line by splitting it into two parts
            parts = problematic_line.split("class Position:", 1)
            fixed_line = parts[0] + '")\n'
            class_line = "# class Position:" + (parts[1] if len(parts) > 1 else "") + "\n"
            
            # Replace the problematic line
            lines[874] = fixed_line
            
            # Insert the class line after the fixed line
            lines.insert(875, class_line)
            
            print(f"Fixed line: {fixed_line.strip()}")
            print(f"Added line: {class_line.strip()}")
            
            # Write the fixed content back to the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
            
            print("File has been fixed successfully.")
            return True
        else:
            print("The line does not match the expected pattern.")
            print("Expected a line containing 'Initial Balance: $' and 'class Position:'")
            return False
    
    except Exception as e:
        print(f"Error fixing the file: {e}")
        return False

def validate_syntax(file_path):
    """Validate the syntax of the file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        import ast
        ast.parse(content)
        print("✅ Syntax validation passed")
        return True
    except SyntaxError as e:
        print(f"❌ Syntax validation failed: {e}")
        print(f"Error at line {e.lineno}, column {e.offset}")
        return False
    except Exception as e:
        print(f"❌ Error during validation: {e}")
        return False

def main():
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print("Usage: python focused_fix.py <path_to_trading_bot.py>")
        return 1
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist")
        return 1
    
    # Create a backup
    backup_path, _ = create_backup(file_path)
    if not backup_path:
        return 1
    
    # Fix the specific error
    if not fix_specific_error(file_path):
        print("Failed to fix the specific error.")
        return 1
    
    # Validate the syntax
    if not validate_syntax(file_path):
        print("Syntax validation failed after fixing.")
        print(f"You can restore the backup from: {backup_path}")
        return 1
    
    print("The file has been fixed and validated successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 