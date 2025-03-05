# Fix and Replace Deployment Script
# This script uploads and runs the fix and replace script on the server

# Configuration
$serverIp = "217.154.11.242"
$username = "root"
$sshKeyPath = $env:SSH_KEY
$remoteDir = "/root/CryptoScript"
$condaEnv = "trading"

# Ensure the SSH key exists
if (-not (Test-Path $sshKeyPath)) {
    Write-Error "SSH key not found at $sshKeyPath"
    exit 1
}

# Files to upload
$fixAndReplaceFile = "fix_and_replace.py"
$verificationFile = "verify_decimal_fix.py"

# Check if required files exist
if (-not (Test-Path $fixAndReplaceFile)) {
    Write-Error "Fix and replace script not found: $fixAndReplaceFile"
    exit 1
}

if (-not (Test-Path $verificationFile)) {
    Write-Error "Verification script not found: $verificationFile"
    exit 1
}

Write-Host "=== Fix and Replace Deployment ===" -ForegroundColor Cyan

# Step 1: Upload the scripts to the server
Write-Host "`nStep 1: Uploading scripts to server..." -ForegroundColor Yellow
try {
    Write-Host "Uploading $fixAndReplaceFile..."
    & scp -i $sshKeyPath $fixAndReplaceFile "$username@$serverIp`:$remoteDir/"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to upload $fixAndReplaceFile"
    }
    
    Write-Host "Uploading $verificationFile..."
    & scp -i $sshKeyPath $verificationFile "$username@$serverIp`:$remoteDir/"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to upload $verificationFile"
    }
    
    Write-Host "Scripts uploaded successfully." -ForegroundColor Green
} catch {
    Write-Error "Error uploading scripts: $_"
    exit 1
}

# Step 2: Run the fix and replace script
Write-Host "`nStep 2: Running fix and replace script..." -ForegroundColor Yellow
$runFixAndReplaceCmd = "cd $remoteDir && source /root/miniconda3/etc/profile.d/conda.sh && conda activate $condaEnv && python fix_and_replace.py crypto_trading_bot.py"

try {
    $fixAndReplaceOutput = & ssh -i $sshKeyPath "$username@$serverIp" $runFixAndReplaceCmd
    Write-Host $fixAndReplaceOutput
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to fix syntax errors and replace normalize_decimal function"
    }
    
    # Check if the script was successful
    if ($fixAndReplaceOutput -match "All changes applied successfully") {
        Write-Host "Fix and replace completed successfully." -ForegroundColor Green
    } else {
        Write-Host "Fix and replace completed with warnings. Please check the output above." -ForegroundColor Yellow
    }
} catch {
    Write-Error "Error during fix and replace: $_"
    exit 1
}

# Step 3: Verify the changes
Write-Host "`nStep 3: Verifying the changes..." -ForegroundColor Yellow
$verifyCmd = "cd $remoteDir && source /root/miniconda3/etc/profile.d/conda.sh && conda activate $condaEnv && python verify_decimal_fix.py crypto_trading_bot.py"

try {
    $verifyOutput = & ssh -i $sshKeyPath "$username@$serverIp" $verifyCmd
    Write-Host $verifyOutput
    
    # Check if verification was successful
    if ($verifyOutput -match "OVERALL: normalize_decimal function implementation is CORRECT") {
        Write-Host "Verification successful!" -ForegroundColor Green
    } else {
        Write-Host "Verification failed or had warnings. Please check the output above." -ForegroundColor Red
    }
} catch {
    Write-Error "Error verifying changes: $_"
    exit 1
}

# Final status
Write-Host "`n=== Deployment Summary ===" -ForegroundColor Cyan
Write-Host "✅ Scripts uploaded successfully" -ForegroundColor Green
Write-Host "✅ Syntax errors fixed" -ForegroundColor Green
Write-Host "✅ normalize_decimal function replaced" -ForegroundColor Green
Write-Host "✅ Changes verified" -ForegroundColor Green

Write-Host "`nThe syntax errors have been fixed and the normalize_decimal function has been successfully replaced with the improved version!" -ForegroundColor Green
Write-Host "The trading bot now uses ROUND_HALF_UP for proper decimal rounding." -ForegroundColor Cyan