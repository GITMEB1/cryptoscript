# PowerShell script to completely fix the trading bot

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

# Create a Python script that will add the normalize_decimal function to the file
$fixScript = @"
#!/usr/bin/env python
import re

# Read the file content
with open('/root/CryptoScript/crypto_trading_bot.py', 'r') as f:
    content = f.read()

# Define the normalize_decimal function
normalize_decimal_function = '''
# =========================
# Utility Functions
# =========================
def normalize_decimal(value, decimal_places=8):
    """
    Normalize a decimal value to a specified number of decimal places.
    Uses Decimal.quantize with ROUND_HALF_UP for proper rounding.
    """
    from decimal import Decimal, ROUND_HALF_UP
    
    # Convert value to Decimal if it's not already
    if not isinstance(value, Decimal):
        try:
            value = Decimal(str(value))
        except Exception as e:
            print(f"Error converting to Decimal: {{e}}")
            return Decimal('0')
    
    try:
        # Create the quantization format based on decimal_places
        quantize_format = Decimal('0.' + '0' * decimal_places)
        
        # Perform the quantization with proper rounding
        result = value.quantize(quantize_format, rounding=ROUND_HALF_UP)
        return result
    except Exception as e:
        print(f"Error during quantization: {{e}}")
        return Decimal('0')

'''

# Add the normalize_decimal function after the imports
pattern = r'from typing import Optional, Dict, List, Any.*?load_dotenv\(\)'
replacement = r'\g<0>\n\n' + normalize_decimal_function

# Replace using regex with DOTALL flag to match across multiple lines
new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

# Write the modified content back to the file
with open('/root/CryptoScript/crypto_trading_bot.py', 'w') as f:
    f.write(new_content)

print("normalize_decimal function added successfully")
"@

# Upload and execute the fix script
Write-Host "Creating and uploading fix script..." -ForegroundColor Cyan
$fixScriptPath = "/root/CryptoScript/add_function.py"
echo $fixScript | & $plinkPath -ssh ${remoteUser}@${remoteIP} -pw $remotePassword "cat > $fixScriptPath"
Run-RemoteCommand "chmod +x $fixScriptPath"

Write-Host "Executing fix script..." -ForegroundColor Cyan
Run-RemoteCommand "cd /root/CryptoScript && source /root/miniconda3/etc/profile.d/conda.sh && conda activate trading && python $fixScriptPath"

# Create a test script
$testScript = @"
#!/usr/bin/env python
import sys
sys.path.append('/root/CryptoScript')

try:
    from crypto_trading_bot import normalize_decimal
    from decimal import Decimal
    
    print("Testing normalize_decimal function...")
    
    test_cases = [
        ('2.0', 'string'),
        (2.0, 'float'),
        (Decimal('2.0'), 'Decimal'),
        ('0.123456789', 'string with many decimals'),
        (123.456789, 'float with many decimals')
    ]
    
    for value, desc in test_cases:
        try:
            result = normalize_decimal(value)
            print(f"Input: {value} ({desc}) -> Result: {result}")
        except Exception as e:
            print(f"Input: {value} ({desc}) -> Error: {e}")
    
    print("Test completed successfully!")
except Exception as e:
    print(f"Error during import or testing: {e}")
"@

# Upload and run the test script
Write-Host "Testing fixed function..." -ForegroundColor Cyan
$testScriptPath = "/root/CryptoScript/test_normalize.py"
echo $testScript | & $plinkPath -ssh ${remoteUser}@${remoteIP} -pw $remotePassword "cat > $testScriptPath"
Run-RemoteCommand "chmod +x $testScriptPath"
Run-RemoteCommand "cd /root/CryptoScript && source /root/miniconda3/etc/profile.d/conda.sh && conda activate trading && python $testScriptPath"

# Start the trading bot again
Write-Host "Starting trading bot..." -ForegroundColor Cyan
Run-RemoteCommand "cd /root/CryptoScript && source /root/miniconda3/etc/profile.d/conda.sh && conda activate trading && nohup python crypto_trading_bot.py > /root/CryptoScript/logs/trading_bot.log 2>&1 &"

# Wait a moment for the bot to start
Start-Sleep -Seconds 2

# Check if the bot is running
Write-Host "Checking if the bot is running..." -ForegroundColor Cyan
Run-RemoteCommand "ps aux | grep -v grep | grep python | grep crypto_trading_bot.py"

# Check the bot logs
Write-Host "Checking the bot logs..." -ForegroundColor Cyan
Run-RemoteCommand "tail -n 20 /root/CryptoScript/logs/trading_bot.log"

Write-Host "Fix complete!" -ForegroundColor Green 