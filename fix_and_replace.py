#!/usr/bin/env python3
"""
Fix and Replace Script
=====================

This script first fixes syntax errors in the trading bot file,
then replaces the normalize_decimal function with the improved version.
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

def fix_syntax_errors(lines):
    """Fix syntax errors in the lines."""
    fixed = False
    
    # Look for the problematic line with "Initial Balance: $" and "class Position:"
    for i, line in enumerate(lines):
        if "Initial Balance: $" in line and "class Position:" in line:
            print(f"Found problematic line {i+1}: {line.strip()}")
            
            # Fix the line by splitting it into two parts
            parts = line.split("class Position:", 1)
            fixed_line = parts[0] + '")\n'
            class_line = "# class Position:" + (parts[1] if len(parts) > 1 else "") + "\n"
            
            # Replace the problematic line
            lines[i] = fixed_line
            
            # Insert the class line after the fixed line
            lines.insert(i+1, class_line)
            
            print(f"Fixed line {i+1}: {fixed_line.strip()}")
            print(f"Added line {i+2}: {class_line.strip()}")
            fixed = True
            break
    
    return lines, fixed

def ensure_round_half_up_import(content):
    """Ensure that ROUND_HALF_UP is imported from decimal."""
    # Check if ROUND_HALF_UP is already imported
    if "from decimal import" in content and "ROUND_HALF_UP" in content:
        print("ROUND_HALF_UP is already imported.")
        return content
    
    # Find the decimal import line
    decimal_import_pattern = r"from\s+decimal\s+import\s+([^\n]+)"
    decimal_import_match = re.search(decimal_import_pattern, content)
    
    if decimal_import_match:
        # Add ROUND_HALF_UP to the existing import
        imports = decimal_import_match.group(1)
        if "Decimal" in imports and "ROUND_HALF_UP" not in imports:
            new_imports = imports + ", ROUND_HALF_UP"
            new_import_line = f"from decimal import {new_imports}"
            content = content.replace(decimal_import_match.group(0), new_import_line)
            print(f"Added ROUND_HALF_UP to existing import: {new_import_line}")
    else:
        # Add a new import line
        new_import_line = "from decimal import Decimal, ROUND_HALF_UP"
        # Find a good place to add the import (after other imports)
        import_section_end = 0
        for match in re.finditer(r"^import\s+|^from\s+", content, re.MULTILINE):
            import_line_end = content.find("\n", match.start())
            if import_line_end > import_section_end:
                import_section_end = import_line_end
        
        if import_section_end > 0:
            content = content[:import_section_end+1] + new_import_line + "\n" + content[import_section_end+1:]
            print(f"Added new import line: {new_import_line}")
        else:
            # If no imports found, add at the beginning after any comments or docstrings
            first_non_comment = re.search(r"^[^#\"\'\n]", content, re.MULTILINE)
            if first_non_comment:
                content = content[:first_non_comment.start()] + new_import_line + "\n\n" + content[first_non_comment.start():]
                print(f"Added new import line at the beginning: {new_import_line}")
            else:
                content = new_import_line + "\n\n" + content
                print(f"Added new import line at the very beginning: {new_import_line}")
    
    return content

def replace_normalize_decimal(content):
    """Replace the normalize_decimal function with the improved version."""
    # Define the new function
    new_function = '''
def normalize_decimal(value):
    """Convert a value to a Decimal with 8 decimal places."""
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    
    # Use quantize with ROUND_HALF_UP for proper rounding
    result = value.quantize(Decimal('0.00000001'), rounding=ROUND_HALF_UP)
    return result
'''
    
    # Try to find the existing function using a regex pattern
    function_pattern = r"def\s+normalize_decimal\s*\([^)]*\):[^}]*?(?=\n\S)"
    function_match = re.search(function_pattern, content, re.DOTALL)
    
    if function_match:
        # Replace the function
        content = content[:function_match.start()] + new_function + content[function_match.end():]
        print("Replaced normalize_decimal function.")
    else:
        # Try a simpler pattern
        simple_pattern = r"def\s+normalize_decimal\s*\([^)]*\):.*?(?=\n\s*def|\Z)"
        simple_match = re.search(simple_pattern, content, re.DOTALL)
        
        if simple_match:
            content = content[:simple_match.start()] + new_function + content[simple_match.end():]
            print("Replaced normalize_decimal function (using simple pattern).")
        else:
            # If we can't find the function, add it at the end
            content += "\n\n" + new_function
            print("Could not find normalize_decimal function. Added it at the end of the file.")
    
    return content

def validate_syntax(content):
    """Validate the syntax of the content."""
    try:
        import ast
        ast.parse(content)
        print("✅ Syntax validation passed")
        return True
    except SyntaxError as e:
        print(f"❌ Syntax validation failed: {e}")
        print(f"Error at line {e.lineno}, column {e.offset}")
        return False

def main():
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print("Usage: python fix_and_replace.py <path_to_trading_bot.py>")
        return 1
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist")
        return 1
    
    # Create a backup
    backup_path, content = create_backup(file_path)
    if not backup_path or not content:
        return 1
    
    # Step 1: Fix syntax errors
    print("\n=== Step 1: Fixing Syntax Errors ===")
    lines = content.split('\n')
    lines, fixed_syntax = fix_syntax_errors(lines)
    
    if fixed_syntax:
        # Join the lines back into a single string
        content = '\n'.join(lines)
        
        # Validate the syntax
        if not validate_syntax(content):
            print("Failed to fix all syntax errors.")
            print(f"You can restore the backup from: {backup_path}")
            return 1
        
        print("Syntax errors fixed successfully.")
    else:
        print("No syntax errors were fixed. The file may already be fixed or have different issues.")
    
    # Step 2: Ensure ROUND_HALF_UP is imported
    print("\n=== Step 2: Ensuring ROUND_HALF_UP Import ===")
    content = ensure_round_half_up_import(content)
    
    # Step 3: Replace the normalize_decimal function
    print("\n=== Step 3: Replacing normalize_decimal Function ===")
    content = replace_normalize_decimal(content)
    
    # Save the modified content
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"\nSaved modified content to: {file_path}")
        
        # Final validation
        if validate_syntax(content):
            print("\n✅ All changes applied successfully!")
            return 0
        else:
            print("\n❌ Final validation failed. The file may have other syntax errors.")
            print(f"You can restore the backup from: {backup_path}")
            return 1
    except Exception as e:
        print(f"\nError saving modified content: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main()) 