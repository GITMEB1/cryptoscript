# PowerShell script to fix the normalize_decimal function on the remote server

# Step 1: Create a Python script to fix the function
$fixScript = @'
#!/usr/bin/env python
import re

# Read the original file
with open('/root/CryptoScript/crypto_trading_bot.py', 'r') as f:
    content = f.read()

# The fixed normalize_decimal function
fixed_function = """def normalize_decimal(value, decimal_places=8):
    \"\"\"
    Normalize a decimal value to a specified number of decimal places.
    Uses Decimal.quantize with ROUND_HALF_UP for proper rounding.
    \"\"\"
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
    
    return result"""

# Create a pattern that matches the current normalize_decimal function
pattern = r'def normalize_decimal\([^)]*\):.*?return result'

# Replace the function in the content, handling multiline with DOTALL flag
new_content = re.sub(pattern, fixed_function, content, flags=re.DOTALL)

# Write the updated content back to the file
with open('/root/CryptoScript/crypto_trading_bot.py', 'w') as f:
    f.write(new_content)

print("normalize_decimal function updated successfully")
'@

# Step 2: Create a test script for the fixed function
$testScript = @'
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
'@

# Remote server details
$remoteUser = "root"
$remoteIP = "217.154.11.242"
$remotePassword = "4O9gNnSt"
$puttyPath = "C:\Program Files\PuTTY"
$plinkPath = Join-Path $puttyPath "plink.exe"

# Function to run a command on the remote server
function Run-RemoteCommand {
    param(
        [string]$command
    )
    
    & $plinkPath -ssh ${remoteUser}@${remoteIP} -pw $remotePassword $command
}

# Upload the fix script
$fixScriptPath = "/root/CryptoScript/fix_function.py"
Write-Host "Creating fix script on remote server..." -ForegroundColor Cyan
echo $fixScript | & $plinkPath -ssh ${remoteUser}@${remoteIP} -pw $remotePassword "cat > $fixScriptPath"
Run-RemoteCommand "chmod +x $fixScriptPath"

# Run the fix script
Write-Host "Running fix script..." -ForegroundColor Cyan
Run-RemoteCommand "cd /root/CryptoScript && source /root/miniconda3/etc/profile.d/conda.sh && conda activate trading && python $fixScriptPath"

# Upload the test script
$testScriptPath = "/root/CryptoScript/test_fixed.py"
Write-Host "Creating test script on remote server..." -ForegroundColor Cyan
echo $testScript | & $plinkPath -ssh ${remoteUser}@${remoteIP} -pw $remotePassword "cat > $testScriptPath"
Run-RemoteCommand "chmod +x $testScriptPath"

# Run the test script
Write-Host "Testing fixed function..." -ForegroundColor Cyan
Run-RemoteCommand "cd /root/CryptoScript && source /root/miniconda3/etc/profile.d/conda.sh && conda activate trading && python $testScriptPath"

# Start the trading bot
Write-Host "Starting trading bot..." -ForegroundColor Cyan
Run-RemoteCommand "cd /root/CryptoScript && source /root/miniconda3/etc/profile.d/conda.sh && conda activate trading && nohup python crypto_trading_bot.py > /root/CryptoScript/logs/trading_bot.log 2>&1 &"

# Check if the bot is running
Write-Host "Verifying bot is running..." -ForegroundColor Cyan
Run-RemoteCommand "ps aux | grep -v grep | grep python | grep crypto_trading_bot.py"

Write-Host "Fix complete!" -ForegroundColor Green 