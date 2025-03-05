import re

def read_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def write_file(file_path, content):
    with open(file_path, 'w') as file:
        file.write(content)

def replace_function_or_class(content, pattern, replacement):
    """Replace a function or class in the content using regex pattern matching"""
    return re.sub(pattern, replacement, content, flags=re.DOTALL)

# Read the original trading bot file
original_content = read_file('crypto_trading_bot.py')

# Read the fixed implementations
position_class = read_file('final_position.py')
risk_manager_class = read_file('final_risk_manager.py')

# Extract the normalize_decimal function from the Position class file
normalize_decimal_pattern = r'def normalize_decimal\(.*?\):.*?return value\.normalize\(\)'
normalize_decimal_match = re.search(normalize_decimal_pattern, position_class, re.DOTALL)
normalize_decimal_function = normalize_decimal_match.group(0) if normalize_decimal_match else None

# Extract the Position class from the file
position_class_pattern = r'class Position:.*?def close_partial_position\(.*?\}$'
position_class_match = re.search(position_class_pattern, position_class, re.DOTALL)
position_class_code = position_class_match.group(0) if position_class_match else None

# Extract the RiskManager class from the file
risk_manager_class_pattern = r'class RiskManager:.*?return self\.volatility_adjustment$'
risk_manager_class_match = re.search(risk_manager_class_pattern, risk_manager_class, re.DOTALL)
risk_manager_class_code = risk_manager_class_match.group(0) if risk_manager_class_match else None

# Replace the normalize_decimal function in the original content
if normalize_decimal_function:
    normalize_decimal_pattern_in_original = r'def normalize_decimal\(.*?\):.*?return value\.normalize\(\)'
    original_content = replace_function_or_class(original_content, normalize_decimal_pattern_in_original, normalize_decimal_function)
    print("Replaced normalize_decimal function")

# Replace the Position class in the original content
if position_class_code:
    position_class_pattern_in_original = r'class Position:.*?def close_partial_position\(.*?\}$'
    original_content = replace_function_or_class(original_content, position_class_pattern_in_original, position_class_code)
    print("Replaced Position class")

# Replace the RiskManager class in the original content
if risk_manager_class_code:
    risk_manager_class_pattern_in_original = r'class RiskManager:.*?return self\.volatility_adjustment$'
    original_content = replace_function_or_class(original_content, risk_manager_class_pattern_in_original, risk_manager_class_code)
    print("Replaced RiskManager class")

# Write the updated content to a new file
write_file('crypto_trading_bot.py.new', original_content)
print("Update completed successfully. The updated file is saved as 'crypto_trading_bot.py.new'.")
print("To apply the changes, rename 'crypto_trading_bot.py.new' to 'crypto_trading_bot.py'.") 