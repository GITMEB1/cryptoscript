#!/usr/bin/env python3
"""
Syntax Error Fixer
=================

This script fixes the unterminated string literal in the trading bot file
before applying the AST-based modifications.
"""

import sys
import os
import re
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

def fix_unterminated_string(content):
    """Fix the unterminated string literal around line 875."""
    # Split the content into lines for easier processing
    lines = content.split('\n')
    
    # Look for the problematic line
    for i, line in enumerate(lines):
        if "Initial Balance: $" in line and "class Position:" in line:
            print(f"Found problematic line {i+1}: {line}")
            
            # Fix the line by properly terminating the string
            # This assumes the format is something like: logging.info(f"Initial Balance: ${class Position:
            # We'll replace it with: logging.info(f"Initial Balance: $")  # class Position:
            fixed_line = line.split("class Position:")[0] + '")'
            comment_part = "# class Position:"
            lines[i] = fixed_line
            lines.insert(i+1, comment_part)
            
            print(f"Fixed line {i+1}: {fixed_line}")
            print(f"Added line {i+2}: {comment_part}")
            break
    
    # Join the lines back into a single string
    fixed_content = '\n'.join(lines)
    return fixed_content

def main():
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print("Usage: python fix_syntax_error.py <path_to_trading_bot.py>")
        return 1
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist")
        return 1
    
    # Create a backup
    backup_path, content = create_backup(file_path)
    if not backup_path or not content:
        return 1
    
    # Fix the unterminated string
    fixed_content = fix_unterminated_string(content)
    
    # Save the fixed content
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print(f"Saved fixed content to: {file_path}")
        
        # Verify the syntax
        try:
            import ast
            ast.parse(fixed_content)
            print("✅ Syntax validation passed")
            return 0
        except SyntaxError as e:
            print(f"❌ Syntax validation failed: {e}")
            print(f"Error at line {e.lineno}, column {e.offset}")
            context_lines = fixed_content.splitlines()[max(0, e.lineno-3):e.lineno+2]
            for i, line in enumerate(context_lines):
                print(f"{e.lineno-2+i}: {line}")
            
            # Restore from backup
            print(f"Restoring from backup: {backup_path}")
            with open(backup_path, 'r', encoding='utf-8') as src:
                original_content = src.read()
            
            with open(file_path, 'w', encoding='utf-8') as dst:
                dst.write(original_content)
            
            print(f"Restored original file from backup")
            return 1
    except Exception as e:
        print(f"Error saving fixed content: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 