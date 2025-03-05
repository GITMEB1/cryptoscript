#!/usr/bin/env python3
"""
Robust Syntax Error Fixer
========================

This script fixes various syntax errors in the trading bot file,
focusing on unterminated string literals and other common issues.
"""

import sys
import os
import re
import datetime
import traceback

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

def fix_syntax_errors(content):
    """Fix various syntax errors in the content."""
    # Split the content into lines for easier processing
    lines = content.split('\n')
    fixed = False
    
    # First pass: Look for unterminated string literals
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check for unterminated string literals with class definitions
        if ('class ' in line and ('"' in line or "'" in line) and 
            (line.count('"') % 2 != 0 or line.count("'") % 2 != 0)):
            
            print(f"Found potential unterminated string at line {i+1}: {line}")
            
            # Case 1: String literal followed by class definition
            if 'class ' in line and ('"' in line[:line.find('class')] or "'" in line[:line.find('class')]):
                # Split at 'class' and terminate the string
                parts = line.split('class ', 1)
                
                # Determine which quote character is used
                quote_char = '"' if '"' in parts[0] else "'"
                
                # Find the last occurrence of the quote character before 'class'
                if quote_char in parts[0]:
                    # Terminate the string and add a comment for the class part
                    fixed_line = parts[0] + quote_char + ')'
                    comment_line = '# class ' + parts[1]
                    
                    lines[i] = fixed_line
                    lines.insert(i+1, comment_line)
                    
                    print(f"Fixed line {i+1}: {fixed_line}")
                    print(f"Added line {i+2}: {comment_line}")
                    fixed = True
                    i += 2  # Skip the newly inserted line
                    continue
            
            # Case 2: Generic unterminated string
            elif line.count('"') % 2 != 0 or line.count("'") % 2 != 0:
                # Determine which quote character is unbalanced
                if line.count('"') % 2 != 0:
                    quote_char = '"'
                else:
                    quote_char = "'"
                
                # Add the missing quote at the end
                fixed_line = line + quote_char
                lines[i] = fixed_line
                
                print(f"Fixed line {i+1}: {fixed_line}")
                fixed = True
        
        i += 1
    
    # Second pass: Look for indentation errors and other syntax issues
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check for mismatched parentheses, brackets, or braces
        if line.count('(') != line.count(')') or line.count('[') != line.count(']') or line.count('{') != line.count('}'):
            print(f"Found mismatched brackets at line {i+1}: {line}")
            
            # Simple fix: Add missing closing brackets at the end
            missing_parens = line.count('(') - line.count(')')
            missing_brackets = line.count('[') - line.count(']')
            missing_braces = line.count('{') - line.count('}')
            
            if missing_parens > 0 or missing_brackets > 0 or missing_braces > 0:
                fixed_line = line
                fixed_line += ')' * missing_parens if missing_parens > 0 else ''
                fixed_line += ']' * missing_brackets if missing_brackets > 0 else ''
                fixed_line += '}' * missing_braces if missing_braces > 0 else ''
                
                lines[i] = fixed_line
                print(f"Fixed line {i+1}: {fixed_line}")
                fixed = True
        
        i += 1
    
    # Join the lines back into a single string
    fixed_content = '\n'.join(lines)
    
    return fixed_content, fixed

def validate_syntax(content):
    """Validate the syntax of the content."""
    try:
        import ast
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        return False, e

def main():
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print("Usage: python robust_syntax_fixer.py <path_to_trading_bot.py>")
        return 1
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist")
        return 1
    
    # Create a backup
    backup_path, content = create_backup(file_path)
    if not backup_path or not content:
        return 1
    
    # Initial syntax check
    is_valid, error = validate_syntax(content)
    if is_valid:
        print("File already has valid syntax. No fixes needed.")
        return 0
    else:
        print(f"Initial syntax error: {error}")
        print(f"Error at line {error.lineno}, column {error.offset}")
        context_lines = content.splitlines()[max(0, error.lineno-3):error.lineno+2]
        for i, line in enumerate(context_lines):
            print(f"{error.lineno-2+i}: {line}")
    
    # Fix syntax errors
    fixed_content, fixed = fix_syntax_errors(content)
    
    if not fixed:
        print("No syntax errors were fixed. The file may have complex issues.")
        return 1
    
    # Validate the fixed content
    is_valid, error = validate_syntax(fixed_content)
    
    if not is_valid:
        print(f"Syntax errors still present after fixing: {error}")
        print(f"Error at line {error.lineno}, column {error.offset}")
        context_lines = fixed_content.splitlines()[max(0, error.lineno-3):error.lineno+2]
        for i, line in enumerate(context_lines):
            print(f"{error.lineno-2+i}: {line}")
        
        # Try a more aggressive approach: comment out the problematic line
        lines = fixed_content.split('\n')
        if 0 <= error.lineno-1 < len(lines):
            print(f"Commenting out problematic line {error.lineno}: {lines[error.lineno-1]}")
            lines[error.lineno-1] = f"# {lines[error.lineno-1]} # AUTO-COMMENTED DUE TO SYNTAX ERROR"
            fixed_content = '\n'.join(lines)
            
            # Check if commenting out fixed the issue
            is_valid, error = validate_syntax(fixed_content)
            if not is_valid:
                print(f"Commenting out the line did not fix the syntax error: {error}")
                return 1
            else:
                print("Commenting out the line fixed the syntax error.")
                fixed = True
        else:
            print(f"Could not comment out line {error.lineno} as it's out of range.")
            return 1
    
    # Save the fixed content
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print(f"Saved fixed content to: {file_path}")
        print("✅ Syntax validation passed")
        return 0
    except Exception as e:
        print(f"Error saving fixed content: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 