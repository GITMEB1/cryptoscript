import re
import sys
from pathlib import Path

def fix_unterminated_string_line_875(content):
    """Fix for the specific unterminated string issue at line 875"""
    pattern = r'(logging\.info\(f"Initial Balance: \${)class Position:'
    replacement = r'\1position_class}"'
    
    if re.search(pattern, content):
        fixed_content = re.sub(pattern, replacement, content)
        return fixed_content, True
    
    return content, False

def fix_line_611_syntax_error(content):
    """Fix for syntax error at line 611 with unexpected class RiskManager text"""
    pattern = r'(return self\.volatility_adjustment)class RiskManager:'
    replacement = r'\1'
    
    if re.search(pattern, content):
        fixed_content = re.sub(pattern, replacement, content)
        return fixed_content, True
    
    return content, False

def find_and_fix_syntax_errors(file_path):
    """Find and fix known syntax errors in the file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        changes_made = False
        
        # Fix unterminated string at line 875
        content, changed1 = fix_unterminated_string_line_875(content)
        if changed1:
            changes_made = True
            print(f"Fixed unterminated string issue at line 875")
        
        # Fix class RiskManager issue at line 611
        content, changed2 = fix_line_611_syntax_error(content)
        if changed2:
            changes_made = True
            print(f"Fixed unexpected class text issue at line 611")
        
        # Try to validate syntax to catch other errors
        try:
            compile(content, file_path, 'exec')
        except SyntaxError as e:
            print(f"Warning: Still has syntax error at line {e.lineno}: {e.msg}")
            return False
        
        # Write fixed content back if changes were made
        if changes_made:
            with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(content)
            print(f"Fixed syntax issues in {file_path}")
            return True
        else:
            print(f"No syntax errors found or couldn't fix issues in {file_path}")
            return True
        
    except Exception as e:
        print(f"Error fixing syntax: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_syntax.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    if not Path(file_path).exists():
        print(f"File not found: {file_path}")
        sys.exit(1)
    
    success = find_and_fix_syntax_errors(file_path)
    sys.exit(0 if success else 1)