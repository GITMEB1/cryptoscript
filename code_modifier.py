#!/usr/bin/env python3
"""
AST-Based Code Modifier for Trading Bot
======================================

This script safely modifies Python code using AST parsing to:
1. Find and replace the normalize_decimal function
2. Add the ROUND_HALF_UP import if needed
"""

import ast
import sys
import os
from pathlib import Path
import tempfile
import shutil


class CodeModifier:
    """
    AST-based code modifier that safely replaces Python code components
    while preserving the original structure.
    """
    
    def __init__(self, file_path):
        """Initialize with the path to the target Python file"""
        self.file_path = Path(file_path)
        self.code = None
        self.original_tree = None
        self.modified = False
        self.load_file()
    
    def load_file(self):
        """Load the file and parse its AST"""
        try:
            self.code = self.file_path.read_text(encoding='utf-8')
            self.original_tree = ast.parse(self.code)
            return True
        except UnicodeDecodeError:
            # Try with a different encoding if UTF-8 fails
            try:
                self.code = self.file_path.read_text(encoding='latin-1')
                self.original_tree = ast.parse(self.code)
                return True
            except Exception as e:
                print(f"Error reading file with latin-1 encoding: {e}")
                return False
        except Exception as e:
            print(f"Error loading file: {e}")
            return False
    
    def find_normalize_decimal_function(self):
        """
        Find the normalize_decimal function node in the AST
        Returns (node, lineno, end_lineno) or (None, None, None) if not found
        """
        for node in ast.walk(self.original_tree):
            if isinstance(node, ast.FunctionDef) and node.name == 'normalize_decimal':
                print(f"Found normalize_decimal function at line {node.lineno}")
                # Use getattr to handle cases where end_lineno might not be available
                end_lineno = getattr(node, 'end_lineno', None)
                if end_lineno is None:
                    # Fallback to estimate end_lineno
                    end_lineno = node.lineno + 10  # Assuming function is < 10 lines
                return node, node.lineno, end_lineno
        print("normalize_decimal function not found")
        return None, None, None
    
    def check_imports(self):
        """Check if ROUND_HALF_UP is already imported"""
        if 'ROUND_HALF_UP' in self.code:
            print("ROUND_HALF_UP import already exists")
            return True
        print("ROUND_HALF_UP import not found")
        return False
    
    def add_round_half_up_import(self):
        """Add ROUND_HALF_UP to imports"""
        # Check for different import patterns
        if 'from decimal import Decimal' in self.code:
            print("Adding ROUND_HALF_UP to existing Decimal import")
            self.code = self.code.replace(
                'from decimal import Decimal',
                'from decimal import Decimal, ROUND_HALF_UP',
                1
            )
            self.modified = True
            return True
        elif 'import decimal' in self.code:
            print("Adding ROUND_HALF_UP import after decimal import")
            self.code = self.code.replace(
                'import decimal',
                'import decimal\nfrom decimal import ROUND_HALF_UP',
                1
            )
            self.modified = True
            return True
        else:
            # Add import at the beginning
            print("Adding decimal and ROUND_HALF_UP imports")
            self.code = 'from decimal import Decimal, ROUND_HALF_UP\n\n' + self.code
            self.modified = True
            return True
    
    def replace_normalize_decimal(self):
        """Replace the normalize_decimal function"""
        # Find the function in the AST
        node, start_line, end_line = self.find_normalize_decimal_function()
        if not node:
            return False
        
        # Get the indentation from the original function
        lines = self.code.split('\n')
        if start_line <= 0 or start_line > len(lines):
            print(f"Invalid start line: {start_line}")
            return False
        
        first_line = lines[start_line - 1]  # AST line numbers are 1-based
        indent = len(first_line) - len(first_line.lstrip())
        indent_str = ' ' * indent
        
        # Define the new function with proper indentation
        new_function = f'''{indent_str}def normalize_decimal(value, force_precision=8):
{indent_str}    """Helper function to normalize decimal values with forced precision"""
{indent_str}    if isinstance(value, (int, float, str)):
{indent_str}        value = Decimal(str(value))
{indent_str}    
{indent_str}    # Create a quantizer with the exact number of decimal places
{indent_str}    quantizer = Decimal('1e-{{}}'.format(force_precision))
{indent_str}    return value.quantize(quantizer, rounding=ROUND_HALF_UP)'''
        
        # Replace the function
        new_lines = lines[:start_line - 1] + [new_function] + lines[end_line:]
        self.code = '\n'.join(new_lines)
        self.modified = True
        print("Replaced normalize_decimal function")
        return True
    
    def validate_syntax(self):
        """Validate that the modified code has valid syntax"""
        try:
            ast.parse(self.code)
            print("Syntax validation passed")
            return True
        except SyntaxError as e:
            print(f"Syntax error in modified code: {e}")
            print(f"Line {e.lineno}, column {e.offset}: {e.text}")
            return False
    
    def create_backup(self):
        """Create a backup of the original file"""
        import datetime
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = self.file_path.with_suffix(f'.py.bak.{timestamp}')
        try:
            shutil.copy2(self.file_path, backup_path)
            print(f"Created backup: {backup_path}")
            return backup_path
        except Exception as e:
            print(f"Error creating backup: {e}")
            return None
    
    def save_changes(self, output_path=None):
        """Save the modified code"""
        if not self.modified:
            print("No changes were made")
            return False
        
        if not output_path:
            output_path = self.file_path
        
        try:
            Path(output_path).write_text(self.code, encoding='utf-8')
            print(f"Changes saved to {output_path}")
            return True
        except Exception as e:
            print(f"Error saving changes: {e}")
            return False
    
    def modify(self, make_backup=True, validate=True):
        """Perform all modifications and validations"""
        # Create backup if requested
        backup_path = None
        if make_backup:
            backup_path = self.create_backup()
            if not backup_path:
                print("Failed to create backup, aborting")
                return False
        
        # Check and add imports if needed
        if not self.check_imports():
            self.add_round_half_up_import()
        
        # Replace the function
        if not self.replace_normalize_decimal():
            print("Failed to replace function, aborting")
            return False
        
        # Validate syntax if requested
        if validate and not self.validate_syntax():
            print("Syntax validation failed, aborting")
            if backup_path:
                print(f"You can restore from backup: {backup_path}")
            return False
        
        # Save changes
        return self.save_changes()


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python code_modifier.py <file_path> [output_path]")
        return 1
    
    file_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    modifier = CodeModifier(file_path)
    success = modifier.modify()
    
    if success:
        print("\n✅ Code modification successful!")
        return 0
    else:
        print("\n❌ Code modification failed")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 