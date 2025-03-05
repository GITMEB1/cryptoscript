# PowerShell script to deploy decimal precision fix
# This script uploads the necessary files to the server and applies the fix

# Configuration
$SERVER = "217.154.11.242"
$USERNAME = "root"
$SSH_KEY = "$env:USERPROFILE\.ssh\id_rsa_trading"
$REMOTE_DIR = "/root/CryptoScript"
$CONDA_ENV = "trading"

Write-Host "=== Decimal Precision Fix Deployment ===" -ForegroundColor Cyan
Write-Host "Server: $SERVER"
Write-Host "Remote directory: $REMOTE_DIR"
Write-Host "Conda environment: $CONDA_ENV"

# Check if SSH key exists
if (-not (Test-Path $SSH_KEY)) {
    Write-Host "Error: SSH key not found at $SSH_KEY" -ForegroundColor Red
    exit 1
}

# Step 1: Upload the decimal precision fixer and verification scripts
Write-Host "`n[1/5] Uploading scripts..." -ForegroundColor Cyan
scp -i $SSH_KEY "decimal_precision_fixer.py" "${USERNAME}@${SERVER}:${REMOTE_DIR}/decimal_precision_fixer.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to upload decimal_precision_fixer.py" -ForegroundColor Red
    exit 1
}

scp -i $SSH_KEY "verify_decimal_fix.py" "${USERNAME}@${SERVER}:${REMOTE_DIR}/verify_decimal_fix.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to upload verify_decimal_fix.py" -ForegroundColor Red
    exit 1
}
Write-Host "Upload successful!" -ForegroundColor Green

# Step 2: Create a backup of the original file
Write-Host "`n[2/5] Creating backup of original trading bot file..." -ForegroundColor Cyan
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
ssh -i $SSH_KEY "${USERNAME}@${SERVER}" "cd ${REMOTE_DIR} && cp crypto_trading_bot.py crypto_trading_bot.py.backup_${timestamp}"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to create backup" -ForegroundColor Red
    exit 1
}
Write-Host "Backup created successfully!" -ForegroundColor Green

# Step 3: Run the decimal precision fixer script
Write-Host "`n[3/5] Applying decimal precision fix..." -ForegroundColor Cyan
ssh -i $SSH_KEY "${USERNAME}@${SERVER}" "cd ${REMOTE_DIR} && source /root/miniconda3/bin/activate ${CONDA_ENV} && python decimal_precision_fixer.py crypto_trading_bot.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to apply decimal precision fix" -ForegroundColor Red
    exit 1
}
Write-Host "Fix script executed successfully!" -ForegroundColor Green

# Step 4: Apply the fixed version
Write-Host "`n[4/5] Applying the fixed version..." -ForegroundColor Cyan
ssh -i $SSH_KEY "${USERNAME}@${SERVER}" "cd ${REMOTE_DIR} && cp crypto_trading_bot.py.fixed crypto_trading_bot.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to apply fixed version" -ForegroundColor Red
    exit 1
}
Write-Host "Fixed version applied successfully!" -ForegroundColor Green

# Step 5: Verify the fix
Write-Host "`n[5/5] Verifying the fix..." -ForegroundColor Cyan
ssh -i $SSH_KEY "${USERNAME}@${SERVER}" "cd ${REMOTE_DIR} && source /root/miniconda3/bin/activate ${CONDA_ENV} && python verify_decimal_fix.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Warning: Verification reported issues. Please check the verification output above." -ForegroundColor Yellow
    Write-Host "You may need to restore the backup and try again." -ForegroundColor Yellow
} else {
    Write-Host "Verification successful! The fix was applied correctly." -ForegroundColor Green
    
    # Run the test suite
    Write-Host "`nRunning the test suite..." -ForegroundColor Cyan
    ssh -i $SSH_KEY "${USERNAME}@${SERVER}" "cd ${REMOTE_DIR} && source /root/miniconda3/bin/activate ${CONDA_ENV} && python -m pytest test_trading_bot.py -v"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Warning: Some tests failed. Please check the test output above." -ForegroundColor Yellow
    } else {
        Write-Host "All tests passed successfully!" -ForegroundColor Green
    }
}

Write-Host "`n=== Deployment Complete ===" -ForegroundColor Cyan
Write-Host "The decimal precision fix has been applied to the trading bot." -ForegroundColor Green
Write-Host "If you encounter any issues, you can restore the backup with:" -ForegroundColor Yellow
Write-Host "ssh -i $SSH_KEY ${USERNAME}@${SERVER} ""cd ${REMOTE_DIR} && cp crypto_trading_bot.py.backup_${timestamp} crypto_trading_bot.py""" -ForegroundColor Yellow 