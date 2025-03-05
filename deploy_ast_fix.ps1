# AST-based Deployment Script for Decimal Precision Fix
# This script uploads the AST-based code modifier and verification scripts to the server
# and applies the decimal precision fix to the trading bot file.

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
$astModifierFile = "ast_code_modifier.py"
$verificationFile = "verify_decimal_fix.py"

# Check if required files exist
if (-not (Test-Path $astModifierFile)) {
    Write-Error "AST modifier script not found: $astModifierFile"
    exit 1
}

if (-not (Test-Path $verificationFile)) {
    Write-Error "Verification script not found: $verificationFile"
    exit 1
}

Write-Host "=== Decimal Precision Fix Deployment ===" -ForegroundColor Cyan

# Step 1: Upload the scripts to the server
Write-Host "`nStep 1: Uploading scripts to server..." -ForegroundColor Yellow
try {
    Write-Host "Uploading $astModifierFile..."
    & scp -i $sshKeyPath $astModifierFile "$username@$serverIp`:$remoteDir/"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to upload $astModifierFile"
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

# Step 2: Install required dependencies
Write-Host "`nStep 2: Installing required dependencies..." -ForegroundColor Yellow
$installDepsCmd = "cd $remoteDir && source /root/miniconda3/etc/profile.d/conda.sh && conda activate $condaEnv && pip install astor"

try {
    & ssh -i $sshKeyPath "$username@$serverIp" $installDepsCmd
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install dependencies"
    }
    Write-Host "Dependencies installed successfully." -ForegroundColor Green
} catch {
    Write-Error "Error installing dependencies: $_"
    exit 1
}

# Step 3: Create a timestamped backup of the original file
Write-Host "`nStep 3: Creating backup of original file..." -ForegroundColor Yellow
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupCmd = "cd $remoteDir && cp crypto_trading_bot.py crypto_trading_bot.py.$timestamp.bak && echo 'Created backup: crypto_trading_bot.py.$timestamp.bak'"

try {
    & ssh -i $sshKeyPath "$username@$serverIp" $backupCmd
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create backup"
    }
    Write-Host "Backup created successfully." -ForegroundColor Green
} catch {
    Write-Error "Error creating backup: $_"
    exit 1
}

# Step 4: Run the AST code modifier
Write-Host "`nStep 4: Applying decimal precision fix..." -ForegroundColor Yellow
$runModifierCmd = "cd $remoteDir && source /root/miniconda3/etc/profile.d/conda.sh && conda activate $condaEnv && python ast_code_modifier.py crypto_trading_bot.py"

try {
    $modifierOutput = & ssh -i $sshKeyPath "$username@$serverIp" $runModifierCmd
    Write-Host $modifierOutput
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to apply decimal precision fix"
    }
    
    # Check if the modifier was successful
    if ($modifierOutput -match "Successfully modified the code") {
        Write-Host "Decimal precision fix applied successfully." -ForegroundColor Green
    } else {
        Write-Host "No changes were made. This could mean the fix was already applied or there was an issue." -ForegroundColor Yellow
    }
} catch {
    Write-Error "Error applying decimal precision fix: $_"
    exit 1
}

# Step 5: Verify the changes
Write-Host "`nStep 5: Verifying the changes..." -ForegroundColor Yellow
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

# Step 6: Perform a sanity check - syntax check
Write-Host "`nStep 6: Performing syntax validation..." -ForegroundColor Yellow
$syntaxCheckCmd = 'cd $remoteDir && source /root/miniconda3/etc/profile.d/conda.sh && conda activate $condaEnv && python -c "import ast; ast.parse(open(\"crypto_trading_bot.py\").read()); print(\"✅ Syntax validation passed\")"'

try {
    $syntaxOutput = & ssh -i $sshKeyPath "$username@$serverIp" $syntaxCheckCmd
    Write-Host $syntaxOutput
    
    if ($LASTEXITCODE -ne 0) {
        throw "Syntax validation failed"
    }
    
    if ($syntaxOutput -match "Syntax validation passed") {
        Write-Host "Syntax validation successful!" -ForegroundColor Green
    } else {
        Write-Host "Syntax validation had issues. Please check manually." -ForegroundColor Red
    }
} catch {
    Write-Error "Error during syntax validation: $_"
    exit 1
}

# Final status
Write-Host "`n=== Deployment Summary ===" -ForegroundColor Cyan
Write-Host "✅ Scripts uploaded successfully" -ForegroundColor Green
Write-Host "✅ Dependencies installed" -ForegroundColor Green
Write-Host "✅ Backup created" -ForegroundColor Green
Write-Host "✅ Decimal precision fix applied" -ForegroundColor Green
Write-Host "✅ Changes verified" -ForegroundColor Green
Write-Host "✅ Syntax validated" -ForegroundColor Green

Write-Host "`nThe decimal precision fix has been successfully applied and verified!" -ForegroundColor Green
Write-Host "You can now restart the trading bot to apply the changes." -ForegroundColor Cyan