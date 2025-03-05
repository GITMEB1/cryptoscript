# PowerShell script to directly fix the normalize_decimal function on the remote server

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

# Create a temporary file with the modified function
$tempFile = Join-Path $env:TEMP "fixed_function.py"

@"
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
            print(f"Error converting to Decimal: {e}")
            return Decimal('0')
    
    try:
        # Create the quantization format based on decimal_places
        quantize_format = Decimal('0.' + '0' * decimal_places)
        
        # Perform the quantization with proper rounding
        result = value.quantize(quantize_format, rounding=ROUND_HALF_UP)
        return result
    except Exception as e:
        print(f"Error during quantization: {e}")
        return Decimal('0')
"@ | Out-File -FilePath $tempFile -Encoding ASCII

# Direct approach - replace the function completely
Write-Host "Uploading fixed function directly..." -ForegroundColor Cyan

$remotePath = "/root/CryptoScript/fixed_function.py"
& "C:\Program Files\PuTTY\pscp.exe" -pw $remotePassword $tempFile ${remoteUser}@${remoteIP}:$remotePath

# Apply the fix directly with sed
$sedCommand = "sed -i '/def normalize_decimal/,/return result/c\\$(cat $remotePath)' /root/CryptoScript/crypto_trading_bot.py"
Run-RemoteCommand $sedCommand

# Create a simple test
$testCode = @"
#!/usr/bin/env python
print('Testing fixed normalize_decimal')
from decimal import Decimal
import sys
sys.path.append('/root/CryptoScript')
from crypto_trading_bot import normalize_decimal

test_cases = [
    ('2.0', 'string'),
    (2.0, 'float'),
    (Decimal('2.0'), 'Decimal')
]

for value, desc in test_cases:
    try:
        result = normalize_decimal(value)
        print(f'Input: {value} ({desc}) -> Result: {result}')
    except Exception as e:
        print(f'Input: {value} ({desc}) -> Error: {str(e)}')
"@

# Upload and run the test
Write-Host "Testing fixed function..." -ForegroundColor Cyan
$testPath = "/root/CryptoScript/quick_test.py"
echo $testCode | & $plinkPath -ssh ${remoteUser}@${remoteIP} -pw $remotePassword "cat > $testPath"
Run-RemoteCommand "chmod +x $testPath"
Run-RemoteCommand "cd /root/CryptoScript && source /root/miniconda3/etc/profile.d/conda.sh && conda activate trading && python $testPath"

# Start the trading bot again
Write-Host "Starting trading bot..." -ForegroundColor Cyan
Run-RemoteCommand "cd /root/CryptoScript && source /root/miniconda3/etc/profile.d/conda.sh && conda activate trading && nohup python crypto_trading_bot.py > /root/CryptoScript/logs/trading_bot.log 2>&1 &"

# Wait a moment for the bot to start
Start-Sleep -Seconds 2

# Check if the bot is running and check the logs
Write-Host "Checking if the bot is running..." -ForegroundColor Cyan
Run-RemoteCommand "ps aux | grep -v grep | grep python | grep crypto_trading_bot.py"
Write-Host "Checking the bot logs..." -ForegroundColor Cyan
Run-RemoteCommand "tail /root/CryptoScript/logs/trading_bot.log"

Write-Host "Fix complete!" -ForegroundColor Green 