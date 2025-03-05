# fix_on_server.ps1
# This script uploads the fix script to the server and runs it on the trading bot file

# Configuration
$SERVER = "217.154.11.242"
$SSH_KEY = $env:SSH_KEY
$REMOTE_DIR = "/root/CryptoScript"
$BOT_FILE = "crypto_trading_bot.py"
$FIX_SCRIPT = "direct_replace_normalize_decimal.py"
$CONDA_ENV = "trading"

# Print header
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Crypto Trading Bot Decimal Precision Fix" -ForegroundColor Cyan  
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if the fix script exists
if (-not (Test-Path $FIX_SCRIPT)) {
    Write-Host "❌ Fix script not found: $FIX_SCRIPT" -ForegroundColor Red
    exit 1
}

# Check if the SSH key exists
if (-not $SSH_KEY) {
    Write-Host "❌ SSH key not found. Make sure the SSH_KEY environment variable is set." -ForegroundColor Red
    exit 1
}

Write-Host "1. Uploading fix script to server..." -ForegroundColor Yellow
$uploadResult = scp -i "$SSH_KEY" "$FIX_SCRIPT" "root@$SERVER`:$REMOTE_DIR/"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to upload fix script" -ForegroundColor Red
    Write-Host $uploadResult
    exit 1
}
Write-Host "✅ Fix script uploaded successfully" -ForegroundColor Green

Write-Host ""
Write-Host "2. Running fix script on server..." -ForegroundColor Yellow
$fixResult = ssh -i "$SSH_KEY" "root@$SERVER" "cd $REMOTE_DIR && source /root/miniconda3/bin/activate $CONDA_ENV && python $FIX_SCRIPT $BOT_FILE"
Write-Host $fixResult
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Fix script failed to run successfully" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Fix applied successfully on server" -ForegroundColor Green

Write-Host ""
Write-Host "3. Testing normalize_decimal function..." -ForegroundColor Yellow
$testCommand = @"
from crypto_trading_bot import normalize_decimal
from decimal import Decimal

# Test values
test_values = [
    Decimal('0.12345678'),
    Decimal('0.1234567850'),  # Should round up
    Decimal('0.1234567849')   # Should round down with ROUND_HALF_UP
]

print('Testing normalize_decimal function:')
for val in test_values:
    result = normalize_decimal(val)
    print(f'normalize_decimal({val}) = {result} (exp: {result.as_tuple().exponent})')
"@

$testCommand = $testCommand -replace "`n", "; "
$testResult = ssh -i "$SSH_KEY" "root@$SERVER" "cd $REMOTE_DIR && source /root/miniconda3/bin/activate $CONDA_ENV && python -c '$testCommand'"
Write-Host $testResult
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Function test failed" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Function tested successfully" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ All steps completed successfully!" -ForegroundColor Green
Write-Host "The decimal precision fix has been applied to the trading bot." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan 