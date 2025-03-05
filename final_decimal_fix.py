#!/usr/bin/env python3
"""
Final Decimal Precision Fix
==========================

This script provides a robust solution to fix the normalize_decimal function
in the crypto trading bot. It uses multiple strategies to ensure the function
is correctly replaced without introducing syntax errors.
"""

import sys
import os
import re
import ast
import shutil
from datetime import datetime
from pathlib import Path

# The fixed normalize_decimal function
FIXED_FUNCTION = '''def normalize_decimal(value, force_precision=8):
    """Helper function to normalize decimal values with forced precision"""
    if isinstance(value, (int, float, str)):
        value = Decimal(str(value))
    
    # Create a quantizer with the exact number of decimal places
    quantizer = Decimal('1e-{}'.format(force_precision))
    return value.quantize(quantizer, rounding=ROUND_HALF_UP)'''

class DecimalFixer:
    def __init__(self, file_path):
        self.file_path = Path(file_path)
        self.backup_path = None
        self.content = None
        self.modified_content = None
    
    def read_file(self):
        """Read the file with proper error handling"""
        try:
            # Try UTF-8 first
            self.content = self.file_path.read_text(encoding='utf-8')
            return True
        except UnicodeDecodeError:
            try:
                # Try with latin-1 as fallback
                self.content = self.file_path.read_text(encoding='latin-1')
                return True
            except Exception as e:
                print(f"Error reading file: {e}")
                return False
    
    def create_backup(self):
        """Create a timestamped backup of the file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_path = self.file_path.with_suffix(f'.py.bak.{timestamp}')
        try:
            shutil.copy2(self.file_path, self.backup_path)
            print(f"Created backup: {self.backup_path}")
            return True
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False
    
    def check_imports(self):
        """Check if ROUND_HALF_UP is imported"""
        if 'ROUND_HALF_UP' in self.content:
            print("ROUND_HALF_UP import already exists")
            return True
        return False
    
    def add_round_half_up_import(self):
        """Add ROUND_HALF_UP import to the file"""
        print("Adding ROUND_HALF_UP import...")
        
        # Check for existing decimal imports
        if 'from decimal import Decimal' in self.content:
            # Add ROUND_HALF_UP to existing import
            self.modified_content = re.sub(
                r'from\s+decimal\s+import\s+Decimal',
                'from decimal import Decimal, ROUND_HALF_UP',
                self.content
            )
        elif 'import decimal' in self.content:
            # Add specific import after existing import
            self.modified_content = re.sub(
                r'import\s+decimal',
                'import decimal\nfrom decimal import ROUND_HALF_UP',
                self.content
            )
        else:
            # Add new import at the beginning of the file
            self.modified_content = 'from decimal import Decimal, ROUND_HALF_UP\n\n' + self.content
    
    def find_function_ast(self):
        """Find the normalize_decimal function using AST"""
        try:
            tree = ast.parse(self.content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == 'normalize_decimal':
                    print(f"Found normalize_decimal function using AST at line {node.lineno}")
                    return node.lineno
            return None
        except SyntaxError:
            print("Warning: Could not parse file with AST due to syntax errors")
            return None
    
    def find_function_regex(self):
        """Find the normalize_decimal function using regex"""
        # Try to find the function with a precise pattern
        pattern = r'def\s+normalize_decimal\s*\([^)]*\).*?(?=\s*def|\s*class|$)'
        match = re.search(pattern, self.content, re.DOTALL)
        if match:
            # Count lines to get line number
            line_count = self.content[:match.start()].count('\n') + 1
            print(f"Found normalize_decimal function using regex at line {line_count}")
            return match.start(), match.end()
        return None
    
    def find_function_line_based(self):
        """Find the normalize_decimal function using line-based search"""
        lines = self.content.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith('def normalize_decimal('):
                print(f"Found normalize_decimal function using line-based search at line {i+1}")
                
                # Find the end of the function
                indent = len(line) - len(line.lstrip())
                j = i + 1
                while j < len(lines):
                    if not lines[j].strip():  # Skip empty lines
                        j += 1
                        continue
                    
                    curr_indent = len(lines[j]) - len(lines[j].lstrip())
                    if curr_indent <= indent and (lines[j].strip().startswith('def ') or lines[j].strip().startswith('class ')):
                        return i, j - 1
                    j += 1
                
                # If we couldn't find the end, assume it's 10 lines
                return i, min(i + 10, len(lines) - 1)
        
        return None
    
    def replace_function(self):
        """Replace the normalize_decimal function using the best available method"""
        if not self.modified_content:
            self.modified_content = self.content
        
        # Try AST-based approach first
        ast_line = self.find_function_ast()
        
        # Then try regex-based approach
        regex_match = self.find_function_regex()
        
        # Finally try line-based approach
        line_match = self.find_function_line_based()
        
        if regex_match:
            start, end = regex_match
            # Get indentation from the original function
            function_text = self.content[start:end]
            first_line = function_text.split('\n')[0]
            indent = len(first_line) - len(first_line.lstrip())
            
            # Apply indentation to the fixed function
            indented_function = '\n'.join(' ' * indent + line if line else '' for line in FIXED_FUNCTION.split('\n'))
            
            # Replace the function
            self.modified_content = self.content[:start] + indented_function + self.content[end:]
            print("Replaced function using regex match")
            return True
        
        elif line_match:
            start_line, end_line = line_match
            lines = self.content.split('\n')
            
            # Get indentation from the original function
            first_line = lines[start_line]
            indent = len(first_line) - len(first_line.lstrip())
            
            # Apply indentation to the fixed function
            indented_function = '\n'.join(' ' * indent + line if line else '' for line in FIXED_FUNCTION.split('\n'))
            
            # Replace the function
            new_lines = lines[:start_line] + [indented_function] + lines[end_line+1:]
            self.modified_content = '\n'.join(new_lines)
            print("Replaced function using line-based match")
            return True
        
        else:
            print("Could not find normalize_decimal function using any method")
            return False
    
    def validate_syntax(self):
        """Validate the syntax of the modified content"""
        try:
            ast.parse(self.modified_content)
            print("Syntax validation passed")
            return True
        except SyntaxError as e:
            print(f"Syntax error in modified content: {e}")
            print(f"Line {e.lineno}, column {e.offset}: {e.text}")
            return False
    
    def save_changes(self):
        """Save the modified content to the file"""
        try:
            self.file_path.write_text(self.modified_content, encoding='utf-8')
            print(f"Changes saved to {self.file_path}")
            return True
        except Exception as e:
            print(f"Error saving changes: {e}")
            return False
    
    def fix(self):
        """Apply all fixes to the file"""
        # Read the file
        if not self.read_file():
            return False
        
        # Create backup
        if not self.create_backup():
            return False
        
        # Add ROUND_HALF_UP import if needed
        if not self.check_imports():
            self.add_round_half_up_import()
        else:
            self.modified_content = self.content
        
        # Replace the normalize_decimal function
        if not self.replace_function():
            print("Failed to replace normalize_decimal function")
            return False
        
        # Validate syntax
        if not self.validate_syntax():
            print("Restoring from backup due to syntax errors")
            shutil.copy2(self.backup_path, self.file_path)
            return False
        
        # Save changes
        if not self.save_changes():
            print("Restoring from backup due to save error")
            shutil.copy2(self.backup_path, self.file_path)
            return False
        
        print("✅ All fixes applied successfully")
        return True

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python final_decimal_fix.py <crypto_trading_bot.py>")
        return 1
    
    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return 1
    
    fixer = DecimalFixer(file_path)
    success = fixer.fix()
    
    if success:
        print("\n=== Fix Applied Successfully ===")
        print("The normalize_decimal function has been updated to use Decimal.quantize with ROUND_HALF_UP.")
        print("\nNext steps:")
        print("1. Verify the changes by running tests")
        print("2. Check that decimal precision is maintained in calculations")
        return 0
    else:
        print("\n❌ Failed to apply fix")
        print("The original file has been restored from the backup.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 