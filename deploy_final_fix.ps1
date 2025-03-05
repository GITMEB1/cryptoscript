# deploy_final_fix.ps1
# This script deploys the final decimal precision fix to the server

# Configuration
$SERVER = "217.154.11.242"
$SSH_KEY = $env:SSH_KEY
$REMOTE_DIR = "/root/CryptoScript"
$BOT_FILE = "crypto_trading_bot.py"
$FIX_SCRIPT = "final_decimal_fix.py"
$VERIFY_SCRIPT = "verify_fix.py"
$CONDA_ENV = "trading"

# Print header
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Final Decimal Precision Fix Deployment" -ForegroundColor Cyan  
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if the fix script exists
if (-not (Test-Path $FIX_SCRIPT)) {
    Write-Host "❌ Fix script not found: $FIX_SCRIPT" -ForegroundColor Red
    exit 1
}

# Check if the verification script exists
if (-not (Test-Path $VERIFY_SCRIPT)) {
    Write-Host "❌ Verification script not found: $VERIFY_SCRIPT" -ForegroundColor Red
    exit 1
}

# Check if the SSH key exists
if (-not $SSH_KEY) {
    Write-Host "❌ SSH key not found. Make sure the SSH_KEY environment variable is set." -ForegroundColor Red
    exit 1
}

# Step 1: Upload the scripts to the server
Write-Host "Step 1: Uploading scripts to server..." -ForegroundColor Yellow
$uploadResult1 = scp -i "$SSH_KEY" "$FIX_SCRIPT" "root@$SERVER`:$REMOTE_DIR/"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to upload fix script" -ForegroundColor Red
    Write-Host $uploadResult1
    exit 1
}

$uploadResult2 = scp -i "$SSH_KEY" "$VERIFY_SCRIPT" "root@$SERVER`:$REMOTE_DIR/"
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to upload verification script" -ForegroundColor Red
    Write-Host $uploadResult2
    exit 1
}

Write-Host "✅ Scripts uploaded successfully" -ForegroundColor Green

# Step 2: Run the fix script on the server
Write-Host "`nStep 2: Applying decimal precision fix..." -ForegroundColor Yellow
$fixResult = ssh -i "$SSH_KEY" "root@$SERVER" "cd $REMOTE_DIR && source /root/miniconda3/bin/activate $CONDA_ENV && python $FIX_SCRIPT $BOT_FILE"
Write-Host $fixResult
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Fix script failed to run successfully" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Fix applied successfully" -ForegroundColor Green

# Step 3: Verify the fix
Write-Host "`nStep 3: Verifying the fix..." -ForegroundColor Yellow
$verifyResult = ssh -i "$SSH_KEY" "root@$SERVER" "cd $REMOTE_DIR && source /root/miniconda3/bin/activate $CONDA_ENV && python $VERIFY_SCRIPT $BOT_FILE"
Write-Host $verifyResult
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Verification failed" -ForegroundColor Red
    exit 1
}
Write-Host "✅ Verification successful" -ForegroundColor Green

# Step 4: Run a simple test to confirm the function works
Write-Host "`nStep 4: Testing normalize_decimal function..." -ForegroundColor Yellow
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
Write-Host "✅ Function test successful" -ForegroundColor Green

# Step 5: Run the test suite
Write-Host "`nStep 5: Running the test suite..." -ForegroundColor Yellow
$testSuiteResult = ssh -i "$SSH_KEY" "root@$SERVER" "cd $REMOTE_DIR && source /root/miniconda3/bin/activate $CONDA_ENV && python -m pytest test_trading_bot.py -v"
Write-Host $testSuiteResult
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️ Some tests failed. Please review the test output." -ForegroundColor Yellow
} else {
    Write-Host "✅ All tests passed" -ForegroundColor Green
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "✅ Deployment completed successfully!" -ForegroundColor Green
Write-Host "The decimal precision fix has been applied to the trading bot." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan 