import re
import sys
from pathlib import Path

def normalize_line_endings(text):
    return text.replace('\r\n', '\n').replace('\r', '\n')

def modify_decimal_imports(content):
    """Add ROUND_HALF_UP to imports"""
    if 'ROUND_HALF_UP' not in content:
        return re.sub(
            r'(from\s+decimal\s+import\s+)(Decimal)(\s*|,|$)',
            r'\1Decimal, ROUND_HALF_UP',
            content,
            count=1
        )
    return content

def replace_normalize_decimal(content):
    """Precise function replacement using signature matching"""
    old_pattern = re.compile(
        r'def normalize_decimal\(.*?\).*?return value\.normalize\(\)',
        re.DOTALL
    )
    
    new_function = '''\
def normalize_decimal(value):
    """Convert a value to a Decimal with 8 decimal places."""
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    
    # Use quantize with ROUND_HALF_UP for proper rounding
    result = value.quantize(Decimal('0.00000001'), rounding=ROUND_HALF_UP)
    return result'''
    
    return old_pattern.sub(new_function, content, count=1)

def main(file_path):
    original = Path(file_path).read_text(encoding='utf-8')
    modified = normalize_line_endings(original)
    
    # Apply changes in sequence
    modified = modify_decimal_imports(modified)
    modified = replace_normalize_decimal(modified)
    
    # Write to temporary file
    temp_path = file_path + '.fixed'
    Path(temp_path).write_text(modified, encoding='utf-8')
    
    # Validate changes
    validation = Path(temp_path).read_text(encoding='utf-8')
    if 'ROUND_HALF_UP' not in validation:
        raise ValueError("Import modification failed")
    if 'quantize' not in validation:
        raise ValueError("Function replacement failed")
    
    return temp_path

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python deploy_fix.py <filepath>")
        sys.exit(1)
    
    try:
        result = main(sys.argv[1])
        print(f"SUCCESS:{result}")
    except Exception as e:
        print(f"ERROR:{str(e)}")
        sys.exit(2) 