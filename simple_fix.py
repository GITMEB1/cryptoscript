#!/usr/bin/env python3
"""
Direct Fix for normalize_decimal function
=========================================

This script directly modifies the crypto_trading_bot.py file to fix the normalize_decimal function.
It uses a simple string replacement approach to minimize the chance of errors.
"""

import sys
import os
import shutil
import re
import ast
import traceback
from datetime import datetime

def backup_file(file_path):
    """Create a timestamped backup of the file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.bak.{timestamp}"
    shutil.copy2(file_path, backup_path)
    print(f"Created backup: {backup_path}")
    return backup_path

def validate_syntax(file_path):
    """Check if the file has valid Python syntax"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        return False, f"Syntax error at line {e.lineno}, column {e.offset}: {e.msg}"
    except Exception as e:
        return False, str(e)

def find_function_boundaries(content, function_name):
    """Find the start and end positions of a function in the content"""
    lines = content.split('\n')
    
    # Find function start
    start_line = None
    for i, line in enumerate(lines):
        if line.strip().startswith(f"def {function_name}("):
            start_line = i
            break
    
    if start_line is None:
        return None, None
    
    # Determine indentation level of the function
    indent = len(lines[start_line]) - len(lines[start_line].lstrip())
    
    # Find function end
    end_line = None
    for i in range(start_line + 1, len(lines)):
        # Skip empty lines
        if not lines[i].strip():
            continue
        
        # If we find a line at the same or lower indentation level that's not a comment or docstring
        # and not a continuation of the previous line, that's the end of the function
        curr_indent = len(lines[i]) - len(lines[i].lstrip())
        line_stripped = lines[i].strip()
        
        if curr_indent <= indent and not line_stripped.startswith('#'):
            end_line = i - 1
            break
    
    # If we couldn't find the end, assume it's the end of the file
    if end_line is None:
        end_line = len(lines) - 1
    
    return start_line, end_line

def has_round_half_up_import(content):
    """Check if ROUND_HALF_UP is imported in the content"""
    return 'ROUND_HALF_UP' in content

def add_round_half_up_import(content):
    """Add ROUND_HALF_UP import to the content"""
    if 'from decimal import Decimal' in content:
        # Add ROUND_HALF_UP to existing Decimal import
        content = content.replace('from decimal import Decimal', 'from decimal import Decimal, ROUND_HALF_UP')
    elif 'import decimal' in content:
        # Add specific import for ROUND_HALF_UP
        content = content.replace('import decimal', 'import decimal\nfrom decimal import ROUND_HALF_UP')
    else:
        # Add new import
        import_lines = re.findall(r'^.*import.*$', content, re.MULTILINE)
        if import_lines:
            last_import = import_lines[-1]
            content = content.replace(last_import, last_import + '\nfrom decimal import Decimal, ROUND_HALF_UP')
        else:
            content = 'from decimal import Decimal, ROUND_HALF_UP\n\n' + content
    
    return content

def replace_normalize_decimal(file_path):
    """Replace the normalize_decimal function with the fixed version"""
    # Fixed version of the function
    fixed_function = '''def normalize_decimal(value, force_precision=8):
    """Helper function to normalize decimal values with forced precision"""
    if isinstance(value, (int, float, str)):
        value = Decimal(str(value))
    
    # Create a quantizer with the exact number of decimal places
    quantizer = Decimal('1e-{}'.format(force_precision))
    return value.quantize(quantizer, rounding=ROUND_HALF_UP)'''
    
    try:
        # Read the file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with a different encoding if UTF-8 fails
            with open(file_path, 'r', encoding='latin-1', errors='replace') as f:
                content = f.read()
        
        # Create backup
        backup_file(file_path)
        
        # Check for syntax errors
        is_valid, error = validate_syntax(file_path)
        if not is_valid:
            print(f"⚠️ Original file has syntax errors: {error}")
            print("Proceeding with caution...")
        
        # Find the normalize_decimal function
        start_line, end_line = find_function_boundaries(content, 'normalize_decimal')
        if start_line is None:
            print("❌ Could not find normalize_decimal function.")
            print("Searching for function definition pattern...")
            # Try a simpler pattern matching approach
            pattern = r'def\s+normalize_decimal\s*\([^)]*\)[\s\S]*?(?=\n\s*def|\n\s*class|$)'
            match = re.search(pattern, content)
            if match:
                print(f"Found function using pattern matching at position {match.start()} to {match.end()}")
                # Replace the function
                before = content[:match.start()]
                after = content[match.end():]
                
                # Get the indentation from the first line
                indentation = ""
                match_text = match.group(0)
                for char in match_text:
                    if char.isspace():
                        indentation += char
                    else:
                        break
                
                # Apply the indentation to the fixed function
                indented_function = '\n'.join(indentation + line if line else '' for line in fixed_function.split('\n'))
                new_content = before + indented_function + after
                
                # Check if ROUND_HALF_UP is imported
                if not has_round_half_up_import(new_content):
                    print("Adding ROUND_HALF_UP import...")
                    new_content = add_round_half_up_import(new_content)
                
                # Write the modified content back to the file
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                except UnicodeEncodeError:
                    # Fallback to a safe encoding
                    with open(file_path, 'w', encoding='utf-8', errors='replace') as f:
                        f.write(new_content)
                
                # Verify the file syntax
                is_valid, error = validate_syntax(file_path)
                if not is_valid:
                    print(f"❌ Modified file has syntax errors: {error}")
                    # Restore backup
                    shutil.copy2(backup_path, file_path)
                    print(f"Restored original file from backup.")
                    return False
                
                print("✅ normalize_decimal function successfully replaced using pattern matching.")
                return True
            else:
                print("❌ Could not find normalize_decimal function pattern.")
                return False
        
        print(f"Found normalize_decimal function at lines {start_line+1} to {end_line+1}")
        
        # Get the original indentation
        lines = content.split('\n')
        orig_line = lines[start_line]
        indent = ""
        for char in orig_line:
            if char.isspace():
                indent += char
            else:
                break
        
        # Apply indentation to the fixed function
        indented_function = '\n'.join(indent + line if line else '' for line in fixed_function.split('\n'))
        
        # Replace the function in the content
        new_lines = lines[:start_line] + [indented_function] + lines[end_line+1:]
        new_content = '\n'.join(new_lines)
        
        # Check if ROUND_HALF_UP is imported
        if not has_round_half_up_import(new_content):
            print("Adding ROUND_HALF_UP import...")
            new_content = add_round_half_up_import(new_content)
        
        # Write the modified content back to the file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
        except UnicodeEncodeError:
            # Fallback to a safe encoding
            with open(file_path, 'w', encoding='utf-8', errors='replace') as f:
                f.write(new_content)
        
        # Verify the file syntax
        is_valid, error = validate_syntax(file_path)
        if not is_valid:
            print(f"❌ Modified file has syntax errors: {error}")
            return False
        
        print("✅ normalize_decimal function successfully replaced.")
        return True
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("Error details:")
        traceback.print_exc()
        return False

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python simple_fix.py <crypto_trading_bot.py>")
        return 1
    
    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return 1
    
    success = replace_normalize_decimal(file_path)
    if success:
        print("✅ Fixed normalize_decimal function successfully!")
        return 0
    else:
        print("❌ Failed to fix normalize_decimal function.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 