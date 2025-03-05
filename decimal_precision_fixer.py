#!/usr/bin/env python3
"""
Decimal Precision Fixer
=======================

A robust implementation to fix decimal precision issues in the trading bot.
Uses AST-based validation and context-aware regex patterns to safely modify code.
"""

import ast
import re
import sys
from pathlib import Path
import io
from tokenize import detect_encoding

class DecimalPrecisionFixer:
    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self.original_code = self._read_file_with_proper_encoding()
        self.modified_code = self.original_code
        self.imports_modified = False
        
    def _read_file_with_proper_encoding(self):
        """Read file with proper encoding detection"""
        with open(self.file_path, 'rb') as f:
            encoding, _ = detect_encoding(f.readline)
        
        with open(self.file_path, 'r', encoding=encoding) as f:
            return f.read()

    def _add_rounding_import(self):
        """Add ROUND_HALF_UP to decimal imports if not already present"""
        print("Checking and updating decimal imports...")
        
        # Check if import already exists
        if 'ROUND_HALF_UP' not in self.modified_code:
            # Try to find decimal import line
            pattern = r'(from\s+decimal\s+import\s+)([^\n]+)'
            
            def add_round_half_up(match):
                imports = match.group(2)
                if 'ROUND_HALF_UP' not in imports:
                    return f"{match.group(1)}{imports}, ROUND_HALF_UP"
                return match.group(0)
            
            updated_code = re.sub(pattern, add_round_half_up, self.modified_code, count=1)
            
            if updated_code != self.modified_code:
                self.modified_code = updated_code
                self.imports_modified = True
                print("✅ Added ROUND_HALF_UP to decimal imports")
            else:
                print("⚠️ Decimal import line not found, manual verification needed")
        else:
            print("✅ ROUND_HALF_UP already imported")

    def _replace_normalize_decimal(self):
        """Safely replace the normalize_decimal function using precise regex"""
        print("Replacing normalize_decimal function...")
        
        # The new function implementation
        new_function = '''def normalize_decimal(value, precision=8):
    """
    Enforce exact decimal precision using quantization
    
    Args:
        value: The value to normalize (int, float, str, or Decimal)
        precision: Number of decimal places to maintain (default: 8)
        
    Returns:
        Decimal value with exactly 'precision' decimal places
    """
    if not isinstance(value, Decimal):
        # Convert all values to Decimal first (handling float precision issues)
        try:
            value = Decimal(str(value))
        except:
            raise TypeError(f"Cannot convert {value} to Decimal")
    
    # Create a quantizer with the exact number of decimal places
    quantizer = Decimal('1e-{}'.format(precision))
    return value.quantize(quantizer, rounding=ROUND_HALF_UP)'''
        
        # Find the existing function using multi-line regex
        pattern = r'def\s+normalize_decimal\s*\([^)]*\):.*?(?=\n\s*def|\n\s*class|\Z)'
        
        match = re.search(pattern, self.modified_code, re.DOTALL)
        if not match:
            print("❌ Could not find normalize_decimal function. Aborting.")
            return False
            
        print(f"Found normalize_decimal function at position {match.start()}-{match.end()}")
        
        # Replace the function
        old_function = match.group(0)
        indent = re.match(r'^(\s*)', old_function).group(1)
        indented_new_function = '\n'.join(indent + line if line else '' for line in new_function.split('\n'))
        
        self.modified_code = self.modified_code.replace(old_function, indented_new_function)
        print("✅ Replaced normalize_decimal function")
        return True

    def _validate_changes(self):
        """Perform AST validation of modified code"""
        print("Validating syntax of modified code...")
        try:
            ast.parse(self.modified_code)
            print("✅ Syntax validation passed")
            return True
        except SyntaxError as e:
            line_num = e.lineno
            context_start = max(0, line_num - 2)
            context_end = min(len(self.modified_code.split('\n')), line_num + 3)
            
            print(f"❌ Syntax error at line {line_num}: {e}")
            print("Context:")
            for i, line in enumerate(self.modified_code.split('\n')[context_start:context_end], context_start + 1):
                indicator = ">>> " if i == line_num else "    "
                print(f"{indicator}Line {i}: {line}")
            
            return False

    def apply_fixes(self):
        """Main entry point for applying all fixes"""
        print(f"Starting fixes on {self.file_path}")
        
        # Step 1: Add ROUND_HALF_UP import
        self._add_rounding_import()
        
        # Step 2: Replace normalize_decimal function
        if not self._replace_normalize_decimal():
            return False
        
        # Step 3: Validate changes
        if not self._validate_changes():
            return False
            
        return True

    def create_backup(self):
        """Create a backup of the original file"""
        backup_path = self.file_path.with_suffix('.py.bak')
        print(f"Creating backup at {backup_path}")
        
        try:
            with open(backup_path, 'w', encoding='utf-8') as f:
                f.write(self.original_code)
            print(f"✅ Backup created at {backup_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to create backup: {e}")
            return False

    def save_changes(self, output_path=None):
        """Save modified code to file"""
        output_path = output_path or self.file_path
        print(f"Saving changes to {output_path}")
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(self.modified_code)
            print(f"✅ Changes saved to {output_path}")
            return True
        except Exception as e:
            print(f"❌ Failed to save changes: {e}")
            return False

def main():
    """Main entry point for the script"""
    if len(sys.argv) < 2:
        print("Usage: python decimal_precision_fixer.py <path_to_trading_bot.py> [output_path]")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    fixer = DecimalPrecisionFixer(input_path)
    
    # Create backup first
    if not fixer.create_backup():
        print("Aborting due to backup failure")
        sys.exit(1)
    
    # Apply fixes
    if not fixer.apply_fixes():
        print("Fixes could not be applied completely. Check errors above.")
        sys.exit(1)
    
    # Save changes
    output_file = output_path or input_path + '.fixed'
    if not fixer.save_changes(output_file):
        print("Failed to save changes")
        sys.exit(1)
    
    print("\n=== Decimal Precision Fix Complete ===")
    print(f"Original file: {input_path}")
    print(f"Backup file: {input_path}.bak")
    print(f"Fixed file: {output_file}")
    print("\nNext steps:")
    print("1. Review the changes to ensure correctness")
    print("2. Run tests to verify functionality")
    print("3. If tests pass, replace the original file with the fixed version")
    print("   cp " + output_file + " " + input_path)

if __name__ == "__main__":
    main() 