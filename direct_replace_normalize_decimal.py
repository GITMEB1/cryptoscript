#!/usr/bin/env python3
"""
Direct String Replacement for normalize_decimal function
=======================================================

This script uses a very direct string replacement to fix the normalize_decimal function.
It avoids complex parsing and just uses direct string matching to minimize potential problems.
"""

import sys
import os
import re
from datetime import datetime

# Define the search pattern for the normalize_decimal function (as loose as possible)
SEARCH_PATTERN = r'def\s+normalize_decimal\s*\([^)]*\).*?(?=\s*def|\s*class|$)'

# Define the replacement with the fixed function
REPLACEMENT = '''def normalize_decimal(value, force_precision=8):
    """Helper function to normalize decimal values with forced precision"""
    if isinstance(value, (int, float, str)):
        value = Decimal(str(value))
    
    # Create a quantizer with the exact number of decimal places
    quantizer = Decimal('1e-{}'.format(force_precision))
    return value.quantize(quantizer, rounding=ROUND_HALF_UP)'''

def create_backup(file_path):
    """Create a backup of the file with timestamp"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = f"{file_path}.bak.{timestamp}"
    try:
        with open(file_path, 'rb') as src, open(backup_path, 'wb') as dst:
            dst.write(src.read())
        print(f"Created backup: {backup_path}")
        return True
    except Exception as e:
        print(f"Failed to create backup: {e}")
        return False

def check_for_round_half_up(content):
    """Check if ROUND_HALF_UP is imported in the file"""
    if 'ROUND_HALF_UP' in content:
        return True
    return False

def add_round_half_up_import(content):
    """Add ROUND_HALF_UP import to the file if needed"""
    if 'from decimal import Decimal' in content:
        if 'from decimal import Decimal, ROUND_HALF_UP' not in content:
            content = content.replace(
                'from decimal import Decimal', 
                'from decimal import Decimal, ROUND_HALF_UP'
            )
    elif 'import decimal' in content:
        content = content.replace(
            'import decimal', 
            'import decimal\nfrom decimal import ROUND_HALF_UP'
        )
    else:
        # Add at the beginning of the file
        content = 'from decimal import Decimal, ROUND_HALF_UP\n\n' + content
    
    return content

def fix_file(file_path):
    """Apply the direct fix to the file"""
    try:
        # Read the file as binary first to ensure we can read it regardless of encoding
        with open(file_path, 'rb') as f:
            binary_content = f.read()
        
        # Try to decode as UTF-8 with replacement
        content = binary_content.decode('utf-8', errors='replace')
        
        # Create backup
        if not create_backup(file_path):
            return False
        
        # Check if we need to add ROUND_HALF_UP import
        has_round_half_up = check_for_round_half_up(content)
        if not has_round_half_up:
            print("Adding ROUND_HALF_UP import...")
            content = add_round_half_up_import(content)
        
        # Look for the normalize_decimal function using very broad pattern
        # This uses the re.DOTALL flag to match across multiple lines
        print("Searching for normalize_decimal function...")
        
        # Try with flags=re.DOTALL for multi-line matching
        match = re.search(SEARCH_PATTERN, content, flags=re.DOTALL)
        if not match:
            print("Could not find normalize_decimal function using pattern search.")
            
            # Try a simpler approach - find the function start and guess the end
            function_start = None
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'def normalize_decimal(' in line:
                    function_start = i
                    break
            
            if function_start is None:
                print("Could not find normalize_decimal function.")
                return False
            
            # Get the indentation level of the function
            original_line = lines[function_start]
            indent = len(original_line) - len(original_line.lstrip())
            indent_str = ' ' * indent
            
            # Apply indentation to the replacement function
            indented_replacement = '\n'.join(indent_str + line if line else '' for line in REPLACEMENT.split('\n'))
            
            # Assume the function is 10 lines long (should be enough)
            function_end = min(function_start + 10, len(lines) - 1)
            
            # Create the new content
            new_lines = lines[:function_start] + [indented_replacement] + lines[function_end+1:]
            new_content = '\n'.join(new_lines)
        else:
            print(f"Found normalize_decimal function at position {match.start()} to {match.end()}")
            
            # Get the indentation of the original function
            match_text = match.group(0)
            indent = len(match_text) - len(match_text.lstrip())
            indent_str = ' ' * indent
            
            # Apply indentation to the replacement function
            indented_replacement = '\n'.join(indent_str + line if line else '' for line in REPLACEMENT.split('\n'))
            
            # Replace the function
            new_content = content[:match.start()] + indented_replacement + content[match.end():]
        
        # Write the modified content back to the file
        with open(file_path, 'w', encoding='utf-8', errors='replace') as f:
            f.write(new_content)
        
        print("✅ Fixed normalize_decimal function successfully.")
        return True
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python direct_replace_normalize_decimal.py <file_path>")
        return 1
    
    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return 1
    
    success = fix_file(file_path)
    if success:
        print("✅ Fix completed successfully.")
        return 0
    else:
        print("❌ Fix failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 