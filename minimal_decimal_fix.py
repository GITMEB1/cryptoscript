#!/usr/bin/env python3
"""
Minimal Decimal Precision Fix
===========================

This script only fixes the normalize_decimal function, avoiding any modification to other parts of the code.
It searches for and replaces the exact function without affecting any other code areas.
"""

import sys
import re
import ast
import tempfile
from pathlib import Path

# The fixed normalize_decimal function
FIXED_NORMALIZE_DECIMAL = '''def normalize_decimal(value, force_precision=8):
    """Helper function to normalize decimal values with forced precision"""
    if isinstance(value, (int, float, str)):
        value = Decimal(str(value))
    
    # Create a quantizer with the exact number of decimal places
    quantizer = Decimal('1e-{}'.format(force_precision))
    return value.quantize(quantizer, rounding=ROUND_HALF_UP)'''

def read_file(path):
    """Read file with proper encoding"""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

def write_file(path, content):
    """Write content to file with proper encoding"""
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def validate_syntax(content):
    """Validate that the content is valid Python syntax"""
    try:
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        # Create a more helpful error message
        return False, f"Syntax error at line {e.lineno}, column {e.offset}: {e.msg}"

def ensure_rounding_import(content):
    """Ensure that ROUND_HALF_UP is imported from decimal"""
    if 'ROUND_HALF_UP' not in content:
        # If Decimal is already imported directly
        if re.search(r'from\s+decimal\s+import\s+.*Decimal', content):
            # Add ROUND_HALF_UP to the existing import
            content = re.sub(
                r'(from\s+decimal\s+import\s+.*)(\bDecimal\b)(.*)', 
                r'\1\2, ROUND_HALF_UP\3', 
                content
            )
        # If "from decimal import *" exists
        elif 'from decimal import *' in content:
            # ROUND_HALF_UP should already be included
            pass
        # If "import decimal" exists
        elif re.search(r'import\s+decimal', content):
            # Add specific import for ROUND_HALF_UP
            import_match = re.search(r'(import\s+decimal.*?)(\n)', content)
            if import_match:
                content = content[:import_match.end()] + "from decimal import ROUND_HALF_UP\n" + content[import_match.end():]
        # If no decimal import exists, add both imports
        else:
            # Find the last import line
            import_lines = re.findall(r'^.*import.*$', content, re.MULTILINE)
            if import_lines:
                last_import = import_lines[-1]
                last_import_pos = content.rfind(last_import) + len(last_import)
                content = (
                    content[:last_import_pos] + 
                    "\nfrom decimal import Decimal, ROUND_HALF_UP" + 
                    content[last_import_pos:]
                )
            else:
                # If no imports found, add it at the beginning
                content = "from decimal import Decimal, ROUND_HALF_UP\n\n" + content
                
    return content

def fix_trading_bot(input_file, output_file=None):
    """Apply minimal decimal precision fix to trading bot file"""
    if output_file is None:
        output_file = input_file + '.fixed'
    
    print(f"Reading input file: {input_file}")
    try:
        content = read_file(input_file)
    except Exception as e:
        print(f"Error reading file: {e}")
        return False
    
    # Validate original file syntax
    print("Validating original file syntax...")
    is_valid, error = validate_syntax(content)
    if not is_valid:
        print(f"⚠️ Original file has syntax errors: {error}")
        print("Proceeding with caution...")
    
    # Create backup
    backup_file = input_file + '.bak'
    try:
        print(f"Creating backup: {backup_file}")
        write_file(backup_file, content)
    except Exception as e:
        print(f"Error creating backup: {e}")
        return False
    
    # Find the normalize_decimal function using line-based search
    lines = content.split('\n')
    function_start = None
    function_end = None
    
    print("Searching for normalize_decimal function...")
    for i, line in enumerate(lines):
        if line.strip().startswith('def normalize_decimal('):
            function_start = i
            print(f"Found function start at line {function_start + 1}")
            
            # Find function end by looking for the next def/class at the same indentation level
            base_indent = len(line) - len(line.lstrip())
            j = i + 1
            while j < len(lines):
                curr_line = lines[j]
                # Skip empty lines
                if not curr_line.strip():
                    j += 1
                    continue
                
                curr_indent = len(curr_line) - len(curr_line.lstrip())
                # If we're back at the same or lower indentation level and it's a def or class, that's the end
                if curr_indent <= base_indent and (curr_line.strip().startswith('def ') or curr_line.strip().startswith('class ')):
                    function_end = j - 1
                    print(f"Found function end at line {function_end + 1}")
                    break
                j += 1
            
            # If we didn't find the end explicitly, use a reasonable number of lines
            if function_end is None:
                # Look for 15 lines after start - should be enough for normalize_decimal
                function_end = min(i + 15, len(lines) - 1)
                print(f"Function end not explicitly found, using line {function_end + 1}")
            
            break
    
    if function_start is None:
        print("Error: Could not find normalize_decimal function")
        return False
    
    # Get indentation of original function
    original_indent = ""
    for char in lines[function_start]:
        if char.isspace():
            original_indent += char
        else:
            break
    
    # Apply indentation to the fixed function
    indented_fix = '\n'.join(original_indent + line if line else '' for line in FIXED_NORMALIZE_DECIMAL.split('\n'))
    
    # Replace the function
    new_lines = lines[:function_start] + [indented_fix] + lines[function_end + 1:]
    new_content = '\n'.join(new_lines)
    
    # Ensure ROUND_HALF_UP is imported
    print("Checking for ROUND_HALF_UP import...")
    new_content = ensure_rounding_import(new_content)
    
    # Validate syntax of modified file
    print("Validating modified file syntax...")
    is_valid, error = validate_syntax(new_content)
    if not is_valid:
        print(f"❌ Modified file has syntax errors: {error}")
        print("Fix was NOT applied. Please check the code and try again.")
        return False
    
    # Save the modified content
    try:
        print(f"Writing modified content to {output_file}")
        write_file(output_file, new_content)
        print("✅ Decimal precision fix applied successfully")
        return True
    except Exception as e:
        print(f"Error writing output file: {e}")
        return False

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python minimal_decimal_fix.py <trading_bot_file> [output_file]")
        return 1
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    success = fix_trading_bot(input_file, output_file)
    
    if success:
        print("\n=== Fix Applied Successfully ===")
        print("Next steps:")
        print("1. Review the changes")
        print("2. Apply the fixed version with:")
        print(f"   cp {input_file}.fixed {input_file}")
        return 0
    else:
        print("\n❌ Failed to apply fix. See errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 