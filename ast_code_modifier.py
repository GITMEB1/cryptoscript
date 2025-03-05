#!/usr/bin/env python3
"""
AST-based Code Modifier
======================

This script safely modifies Python code using AST parsing to:
1. Replace the normalize_decimal function with an improved version
2. Add the necessary ROUND_HALF_UP import if not present

This approach is more reliable than regex-based replacements as it understands
the code structure and can make precise modifications without affecting code in 
string literals or comments.
"""

import ast
import astor
import sys
import re
import os
from typing import List, Tuple, Optional
import inspect
import traceback


class ASTCodeModifier:
    """
    A class that uses AST to safely modify Python code.
    """
    
    def __init__(self, file_path: str):
        """Initialize with the path to the file to modify."""
        self.file_path = file_path
        self.tree = None
        self.modified = False
        self.backup_path = None
        self.original_content = None
        self.modified_content = None
    
    def read_file(self) -> str:
        """Read the file content with proper encoding detection."""
        encodings = ['utf-8', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                with open(self.file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                print(f"Successfully read file with {encoding} encoding")
                self.original_content = content
                return content
            except UnicodeDecodeError:
                continue
        
        raise ValueError(f"Could not read file with any of the encodings: {encodings}")
    
    def parse_ast(self, content: str) -> ast.Module:
        """Parse the content into an AST."""
        try:
            self.tree = ast.parse(content)
            return self.tree
        except SyntaxError as e:
            print(f"SyntaxError parsing file: {e}")
            print(f"Error at line {e.lineno}, column {e.offset}")
            context_lines = content.splitlines()[max(0, e.lineno-3):e.lineno+2]
            for i, line in enumerate(context_lines):
                print(f"{e.lineno-2+i}: {line}")
            raise
    
    def create_backup(self) -> str:
        """Create a backup of the original file."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"{self.file_path}.{timestamp}.bak"
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(self.original_content)
        
        print(f"Created backup at: {backup_path}")
        self.backup_path = backup_path
        return backup_path
    
    def has_round_half_up_import(self) -> bool:
        """Check if the ROUND_HALF_UP import is already present."""
        if not self.tree:
            raise ValueError("AST not parsed yet. Call parse_ast first.")
        
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ImportFrom) and node.module == 'decimal':
                for name in node.names:
                    if name.name == 'ROUND_HALF_UP':
                        return True
        
        return False
    
    def add_round_half_up_import(self) -> bool:
        """Add the ROUND_HALF_UP import if not present."""
        if self.has_round_half_up_import():
            print("ROUND_HALF_UP import already exists")
            return False
        
        # Find existing decimal import
        decimal_import = None
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ImportFrom) and node.module == 'decimal':
                decimal_import = node
                break
        
        # Modify existing decimal import or create a new one
        if decimal_import:
            # Check if Decimal is already imported
            has_decimal = any(name.name == 'Decimal' for name in decimal_import.names)
            
            # Add ROUND_HALF_UP to the existing import
            if has_decimal:
                decimal_import.names.append(ast.alias(name='ROUND_HALF_UP', asname=None))
            else:
                decimal_import.names.extend([
                    ast.alias(name='Decimal', asname=None),
                    ast.alias(name='ROUND_HALF_UP', asname=None)
                ])
        else:
            # Create a new import statement
            new_import = ast.ImportFrom(
                module='decimal',
                names=[
                    ast.alias(name='Decimal', asname=None),
                    ast.alias(name='ROUND_HALF_UP', asname=None)
                ],
                level=0
            )
            
            # Add the import near the top of the file
            self.tree.body.insert(0, new_import)
        
        self.modified = True
        print("Added ROUND_HALF_UP import")
        return True
    
    def find_normalize_decimal_function(self) -> Optional[ast.FunctionDef]:
        """Find the normalize_decimal function in the AST."""
        if not self.tree:
            raise ValueError("AST not parsed yet. Call parse_ast first.")
        
        for node in self.tree.body:
            if isinstance(node, ast.FunctionDef) and node.name == 'normalize_decimal':
                return node
        
        return None
    
    def replace_normalize_decimal_function(self) -> bool:
        """Replace the normalize_decimal function with the improved version."""
        old_function = self.find_normalize_decimal_function()
        if not old_function:
            print("normalize_decimal function not found")
            return False
        
        # The improved normalize_decimal function - using single quotes to avoid docstring issues
        new_function_source = '''
def normalize_decimal(value):
    """Convert a value to a Decimal with 8 decimal places."""
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    
    # Use quantize with ROUND_HALF_UP for proper rounding
    result = value.quantize(Decimal('0.00000001'), rounding=ROUND_HALF_UP)
    return result
'''
        
        # Parse the new function
        new_function_ast = ast.parse(new_function_source).body[0]
        
        # Replace the old function with the new one
        for i, node in enumerate(self.tree.body):
            if node is old_function:
                self.tree.body[i] = new_function_ast
                self.modified = True
                print("Replaced normalize_decimal function")
                return True
        
        return False
    
    def generate_modified_code(self) -> str:
        """Generate the modified code from the AST."""
        if not self.tree:
            raise ValueError("AST not parsed yet. Call parse_ast first.")
        
        # Convert the AST back to source code
        modified_content = astor.to_source(self.tree)
        
        # Add necessary imports if using astor
        if "import astor" not in self.original_content and "from astor import" not in self.original_content:
            modified_content = modified_content.replace("import astor\n", "")
        
        self.modified_content = modified_content
        return modified_content
    
    def validate_modified_code(self) -> bool:
        """Validate that the modified code is valid Python syntax."""
        if not self.modified_content:
            raise ValueError("Modified content not generated yet. Call generate_modified_code first.")
        
        try:
            ast.parse(self.modified_content)
            print("Modified code validation passed")
            return True
        except SyntaxError as e:
            print(f"Modified code validation failed: {e}")
            print(f"Error at line {e.lineno}, column {e.offset}")
            context_lines = self.modified_content.splitlines()[max(0, e.lineno-3):e.lineno+2]
            for i, line in enumerate(context_lines):
                print(f"{e.lineno-2+i}: {line}")
            return False
    
    def save_modified_code(self, output_path=None) -> str:
        """Save the modified code to a file."""
        if not self.modified_content:
            raise ValueError("Modified content not generated yet. Call generate_modified_code first.")
        
        if output_path is None:
            output_path = self.file_path
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(self.modified_content)
        
        print(f"Saved modified code to: {output_path}")
        return output_path
    
    def apply_changes(self) -> bool:
        """Apply all changes to the file."""
        try:
            # Read the file
            content = self.read_file()
            
            # Parse the AST
            self.parse_ast(content)
            
            # Create a backup
            self.create_backup()
            
            # Add the ROUND_HALF_UP import if needed
            import_added = self.add_round_half_up_import()
            
            # Replace the normalize_decimal function
            function_replaced = self.replace_normalize_decimal_function()
            
            # If nothing was changed, we're done
            if not import_added and not function_replaced:
                print("No changes were needed")
                return False
            
            # Generate the modified code
            self.generate_modified_code()
            
            # Validate the modified code
            if not self.validate_modified_code():
                print("Validation failed, not saving changes")
                return False
            
            # Save the modified code
            self.save_modified_code()
            
            return True
        
        except Exception as e:
            print(f"Error applying changes: {e}")
            traceback.print_exc()
            return False


def main():
    """Main entry point for the script."""
    if len(sys.argv) < 2:
        print("Usage: python ast_code_modifier.py <path_to_trading_bot.py>")
        return 1
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist")
        return 1
    
    modifier = ASTCodeModifier(file_path)
    
    try:
        success = modifier.apply_changes()
        if success:
            print("\n✅ Successfully modified the code!")
            print(f"Original file backed up to: {modifier.backup_path}")
            
            # Verify the changes
            print("\nVerifying changes...")
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location("modified_module", file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Check if the function exists and ROUND_HALF_UP is imported
                if hasattr(module, 'normalize_decimal') and hasattr(module, 'ROUND_HALF_UP'):
                    print("✅ Verification passed: normalize_decimal function and ROUND_HALF_UP import exist")
                    
                    # Test the function with a sample value
                    from decimal import Decimal
                    test_value = Decimal('0.123456785')
                    result = module.normalize_decimal(test_value)
                    print(f"Test: normalize_decimal({test_value}) = {result}")
                    
                    if str(result) == '0.12345679':
                        print("✅ Function behaves correctly")
                    else:
                        print(f"⚠️ Function behavior check: expected '0.12345679', got '{result}'")
                else:
                    print("⚠️ Verification warning: Could not verify function or import")
            except Exception as e:
                print(f"⚠️ Verification warning: {e}")
        else:
            print("\n⚠️ No changes were made to the file")
        
        return 0 if success else 1
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main()) 