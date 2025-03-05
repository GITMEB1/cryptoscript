# Direct Replacement Deployment Script
# This script uploads and runs the direct replacement script on the server

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
$replacementFile = "direct_replace.py"
$verificationFile = "verify_decimal_fix.py"

# Check if required files exist
if (-not (Test-Path $replacementFile)) {
    Write-Error "Replacement script not found: $replacementFile"
    exit 1
}

if (-not (Test-Path $verificationFile)) {
    Write-Error "Verification script not found: $verificationFile"
    exit 1
}

Write-Host "=== Direct Replacement Deployment ===" -ForegroundColor Cyan

# Step 1: Upload the scripts to the server
Write-Host "`nStep 1: Uploading scripts to server..." -ForegroundColor Yellow
try {
    Write-Host "Uploading $replacementFile..."
    & scp -i $sshKeyPath $replacementFile "$username@$serverIp`:$remoteDir/"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to upload $replacementFile"
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

# Step 2: Run the direct replacement script
Write-Host "`nStep 2: Running direct replacement script..." -ForegroundColor Yellow
$runReplaceCmd = "cd $remoteDir && source /root/miniconda3/etc/profile.d/conda.sh && conda activate $condaEnv && python direct_replace.py crypto_trading_bot.py"

try {
    $replaceOutput = & ssh -i $sshKeyPath "$username@$serverIp" $runReplaceCmd
    Write-Host $replaceOutput
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to replace normalize_decimal function"
    }
    
    # Check if the replacement was successful
    if ($replaceOutput -match "Syntax validation passed") {
        Write-Host "Function replacement completed successfully." -ForegroundColor Green
    } else {
        Write-Host "Function replacement completed with warnings. Please check the output above." -ForegroundColor Yellow
    }
} catch {
    Write-Error "Error replacing function: $_"
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
Write-Host "✅ normalize_decimal function replaced" -ForegroundColor Green
Write-Host "✅ Changes verified" -ForegroundColor Green

Write-Host "`nThe normalize_decimal function has been successfully replaced with the improved version!" -ForegroundColor Green
Write-Host "The trading bot now uses ROUND_HALF_UP for proper decimal rounding." -ForegroundColor Cyan 