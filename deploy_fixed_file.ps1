$ErrorActionPreference = "Stop"
$remoteUser = "root"
$remoteIP = "217.154.11.242"
$remotePath = "/root/CryptoScript/crypto_trading_bot.py"
$backupPath = "/root/CryptoScript/backup"
$remotePassword = "4O9gNnSt"
$localFixedFile = "crypto_trading_bot.py"  # Our already fixed local file

# Ask for PuTTY installation directory
$puttyPath = Read-Host "Please enter the full path to your PuTTY installation directory (e.g., C:\Program Files\PuTTY)"
$plinkPath = Join-Path $puttyPath "plink.exe"
$pscpPath = Join-Path $puttyPath "pscp.exe"

# Check if plink and pscp exist at the specified paths
if (-not (Test-Path $plinkPath) -or -not (Test-Path $pscpPath)) {
    Write-Host "PuTTY tools not found at the specified path" -ForegroundColor Red
    Write-Host "Please verify the path and try again" -ForegroundColor Yellow
    exit 1
}

# First-time connection to accept host key (with auto answer yes)
Write-Host "Setting up initial connection..." -ForegroundColor Cyan
echo y | & $plinkPath -pw $remotePassword ${remoteUser}@${remoteIP} "exit" 2>&1 | Out-Null

# Create backup directory if it doesn't exist
try {
    Write-Host "Creating backup directory..." -ForegroundColor Cyan
    echo $remotePassword | & $plinkPath -pw $remotePassword ${remoteUser}@${remoteIP} "mkdir -p ${backupPath}"
} catch {
    Write-Host "Backup directory already exists or couldn't be created" -ForegroundColor Yellow
}

# Step 1: Create remote backup with timestamp
try {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupFile = "${backupPath}/crypto_trading_bot.${timestamp}.bak"
    Write-Host "Creating remote backup at ${backupFile}..." -ForegroundColor Cyan
    echo $remotePassword | & $plinkPath -pw $remotePassword ${remoteUser}@${remoteIP} "cp ${remotePath} ${backupFile}"
    
    # Step 2: Upload our already fixed file
    Write-Host "Uploading fixed file..." -ForegroundColor Cyan
    echo $remotePassword | & $pscpPath -pw $remotePassword $localFixedFile ${remoteUser}@${remoteIP}:${remotePath}
    
    # Step 3: Remote validation
    Write-Host "Validating remote file..." -ForegroundColor Cyan
    
    # Verify syntax 
    Write-Host "Verifying syntax..." -ForegroundColor Cyan
    $validation = echo $remotePassword | & $plinkPath -pw $remotePassword ${remoteUser}@${remoteIP} "cd /root/CryptoScript && source /root/miniconda3/etc/profile.d/conda.sh && conda activate trading && python -m py_compile ${remotePath}"
    
    if ($LASTEXITCODE -ne 0) {
        throw "Remote validation failed: $validation"
    }
    
    # Create a temporary verification script on the server
    Write-Host "Creating verification script..." -ForegroundColor Cyan
    $verifyScript = @"
#!/usr/bin/env python
from decimal import Decimal, ROUND_HALF_UP

# Import the module directly
import sys
sys.path.append('/root/CryptoScript')
from crypto_trading_bot import normalize_decimal

print("Import verification successful")

# Test the function
result = normalize_decimal("0.123456785")
print(f"Test result: {result}")
assert str(result) == "0.12345679", f"Expected 0.12345679, got {result}"
print("Function test successful")
"@

    # Upload the verification script to the CryptoScript directory
    $verifyScriptPath = "/root/CryptoScript/verify_decimal.py"
    echo $verifyScript | & $plinkPath -pw $remotePassword ${remoteUser}@${remoteIP} "cat > ${verifyScriptPath}"
    echo $remotePassword | & $plinkPath -pw $remotePassword ${remoteUser}@${remoteIP} "chmod +x ${verifyScriptPath}"
    
    # Run the verification script
    Write-Host "Running verification script..." -ForegroundColor Cyan
    $verifyResult = echo $remotePassword | & $plinkPath -pw $remotePassword ${remoteUser}@${remoteIP} "cd /root/CryptoScript && source /root/miniconda3/etc/profile.d/conda.sh && conda activate trading && python ${verifyScriptPath}"
    
    if ($LASTEXITCODE -ne 0) {
        throw "Verification failed: $verifyResult"
    }
    
    Write-Host $verifyResult -ForegroundColor Gray
    
    # Clean up
    echo $remotePassword | & $plinkPath -pw $remotePassword ${remoteUser}@${remoteIP} "rm -f ${verifyScriptPath}"
    
    # Step 4: Complete
    Write-Host "`nDeployment successful!" -ForegroundColor Green
    Write-Host "The normalize_decimal function has been updated with proper decimal rounding." -ForegroundColor Green
    Write-Host "Backup created at: $backupFile" -ForegroundColor Green
}
catch {
    Write-Host "`nDeployment failed: $_" -ForegroundColor Red
    
    # Ask if user wants to restore from backup
    $restore = Read-Host "Do you want to restore from the latest backup? (y/n)"
    if ($restore -eq "y") {
        Write-Host "Restoring from backup..." -ForegroundColor Yellow
        echo $remotePassword | & $plinkPath -pw $remotePassword ${remoteUser}@${remoteIP} "cp ${backupFile} ${remotePath}"
        Write-Host "Restored from backup $backupFile" -ForegroundColor Green
    }
    exit 1
} 