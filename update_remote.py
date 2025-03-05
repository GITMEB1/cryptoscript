#!/usr/bin/env python
import re

def fix_normalize_decimal():
    # Define the fixed function with proper error handling
    fixed_function = '''def normalize_decimal(value, decimal_places=8):
    """
    Normalize a decimal value to a specified number of decimal places.
    Uses Decimal.quantize with ROUND_HALF_UP for proper rounding.
    """
    from decimal import Decimal, ROUND_HALF_UP
    
    # Convert value to Decimal if it's not already
    if not isinstance(value, Decimal):
        try:
            value = Decimal(str(value))
        except:
            # Handle invalid input
            return Decimal('0')
    
    # Create the quantization format based on decimal_places
    quantize_format = Decimal('0.' + '0' * decimal_places)
    
    # Perform the quantization with proper rounding
    result = value.quantize(quantize_format, rounding=ROUND_HALF_UP)
    
    return result'''
    
    return fixed_function

# Execute remote commands to update the function
def generate_powershell_commands():
    commands = []
    
    # 1. Create a temporary Python script on the remote server
    remote_script = f'''cat > /root/CryptoScript/fix_function.py << 'EOF'
#!/usr/bin/env python
import re

# Read the original file
with open('/root/CryptoScript/crypto_trading_bot.py', 'r') as f:
    content = f.read()

# The fixed normalize_decimal function
fixed_function = """{fix_normalize_decimal()}"""

# Create a pattern that matches the current normalize_decimal function
pattern = r'def normalize_decimal\\([^)]*\\):.*?return result'

# Replace the function in the content, handling multiline with DOTALL flag
new_content = re.sub(pattern, fixed_function, content, flags=re.DOTALL)

# Write the updated content back to the file
with open('/root/CryptoScript/crypto_trading_bot.py', 'w') as f:
    f.write(new_content)

print("normalize_decimal function updated successfully")
EOF'''
    
    remote_script = remote_script.replace('"', '\\"')
    commands.append(f'& "C:\\Program Files\\PuTTY\\plink.exe" -ssh root@217.154.11.242 -pw 4O9gNnSt "{remote_script}"')
    
    # 2. Run the script
    commands.append('& "C:\\Program Files\\PuTTY\\plink.exe" -ssh root@217.154.11.242 -pw 4O9gNnSt "source /root/miniconda3/etc/profile.d/conda.sh && conda activate trading && python /root/CryptoScript/fix_function.py"')
    
    # 3. Test the fixed function
    test_script = '''cat > /root/CryptoScript/test_fixed.py << 'EOF'
#!/usr/bin/env python
from crypto_trading_bot import normalize_decimal
from decimal import Decimal

# Test cases
test_inputs = [
    '2.0',
    2.0,
    Decimal('2.0'),
    '0.123456789',
    123.456789
]

print("Testing normalize_decimal function with various inputs:")
for input_val in test_inputs:
    try:
        result = normalize_decimal(input_val)
        print(f"Input: {input_val} ({type(input_val).__name__}) -> Result: {result}")
    except Exception as e:
        print(f"Input: {input_val} -> Error: {str(e)}")
EOF'''
    
    commands.append(f'& "C:\\Program Files\\PuTTY\\plink.exe" -ssh root@217.154.11.242 -pw 4O9gNnSt "{test_script}"')
    commands.append('& "C:\\Program Files\\PuTTY\\plink.exe" -ssh root@217.154.11.242 -pw 4O9gNnSt "source /root/miniconda3/etc/profile.d/conda.sh && conda activate trading && python /root/CryptoScript/test_fixed.py"')
    
    # 4. Start the trading bot
    commands.append('& "C:\\Program Files\\PuTTY\\plink.exe" -ssh root@217.154.11.242 -pw 4O9gNnSt "cd /root/CryptoScript && source /root/miniconda3/etc/profile.d/conda.sh && conda activate trading && nohup python crypto_trading_bot.py > /root/CryptoScript/logs/trading_bot.log 2>&1 &"')
    
    return commands

if __name__ == "__main__":
    commands = generate_powershell_commands()
    
    print("# PowerShell commands to update normalize_decimal function on remote server")
    print("# Copy and run these commands in PowerShell one at a time")
    print()
    
    for i, cmd in enumerate(commands, 1):
        print(f"# Step {i}:")
        print(cmd)
        print() 