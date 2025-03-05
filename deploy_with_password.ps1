$ErrorActionPreference = "Stop"
$remoteUser = "root"
$remoteIP = "217.154.11.242"
$remotePath = "/root/CryptoScript/crypto_trading_bot.py"
$backupPath = "/root/CryptoScript/backup"
$remotePassword = "4O9gNnSt"

# Verify sshpass is installed
$sshpassCheck = Get-Command sshpass -ErrorAction SilentlyContinue
if (-not $sshpassCheck) {
    Write-Host "sshpass is not installed. You'll need to install it for this script to work." -ForegroundColor Red
    Write-Host "For Windows, you can install it via WSL or Git Bash with: apt-get install sshpass" -ForegroundColor Yellow
    exit 1
}

# Common SSH/SCP commands with password
$sshCmd = "sshpass -p '$remotePassword' ssh -o StrictHostKeyChecking=no ${remoteUser}@${remoteIP}"
$scpToCmd = "sshpass -p '$remotePassword' scp -o StrictHostKeyChecking=no"
$scpFromCmd = "sshpass -p '$remotePassword' scp -o StrictHostKeyChecking=no ${remoteUser}@${remoteIP}:${remotePath}"

# Create backup directory if it doesn't exist
try {
    Invoke-Expression "$sshCmd 'mkdir -p ${backupPath}'"
} catch {
    Write-Host "Backup directory already exists or couldn't be created" -ForegroundColor Yellow
}

# Step 1: Create remote backup with timestamp
try {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupFile = "${backupPath}/crypto_trading_bot.${timestamp}.bak"
    Write-Host "Creating remote backup at ${backupFile}..." -ForegroundColor Cyan
    Invoke-Expression "$sshCmd 'cp ${remotePath} ${backupFile}'"
    
    # Step 2: Download file for local editing
    Write-Host "Downloading file for syntax fix..." -ForegroundColor Cyan
    Invoke-Expression "$scpFromCmd .\temp_file.py"
    
    # Fix line endings locally
    Write-Host "Normalizing line endings..." -ForegroundColor Cyan
    (Get-Content .\temp_file.py -Raw) | ForEach-Object { $_ -replace "`r`n","`n" } | Set-Content .\temp_file.py -Encoding utf8 -NoNewline
    
    # Apply syntax fix
    Write-Host "Applying syntax fix..." -ForegroundColor Cyan
    $syntaxResult = python .\fix_syntax.py .\temp_file.py
    Write-Host $syntaxResult -ForegroundColor Gray
    
    # Step 3: Deploy function replacement
    Write-Host "Applying function replacement..." -ForegroundColor Cyan
    $result = python .\deploy_fix.py .\temp_file.py
    
    if ($result -match "^ERROR:") {
        throw $result
    }
    
    $tempFile = $result -replace "^SUCCESS:", ""
    
    # Step 4: Deploy fixed file
    Write-Host "Uploading fixed file..." -ForegroundColor Cyan
    Invoke-Expression "$scpToCmd $tempFile ${remoteUser}@${remoteIP}:${remotePath}"
    
    # Step 5: Remote validation
    Write-Host "Validating remote file..." -ForegroundColor Cyan
    
    # Verify syntax 
    $validation = Invoke-Expression "$sshCmd 'cd /root/CryptoScript && source /root/miniconda3/etc/profile.d/conda.sh && conda activate trading && python -m py_compile ${remotePath}'"
    
    if ($LASTEXITCODE -ne 0) {
        throw "Remote validation failed: $validation"
    }
    
    # Verify imports
    Write-Host "Verifying imports..." -ForegroundColor Cyan
    $importCheck = Invoke-Expression "$sshCmd 'cd /root/CryptoScript && source /root/miniconda3/etc/profile.d/conda.sh && conda activate trading && python -c \"from crypto_trading_bot import normalize_decimal; from decimal import ROUND_HALF_UP; print(\\\"Import verification successful\\\")\"'"
    
    if ($LASTEXITCODE -ne 0) {
        throw "Import verification failed: $importCheck"
    }
    
    Write-Host $importCheck -ForegroundColor Gray
    
    # Test function
    Write-Host "Testing normalize_decimal function..." -ForegroundColor Cyan
    $functionTest = Invoke-Expression "$sshCmd 'cd /root/CryptoScript && source /root/miniconda3/etc/profile.d/conda.sh && conda activate trading && python -c \"from crypto_trading_bot import normalize_decimal; from decimal import Decimal; result = normalize_decimal(\\\"0.123456785\\\"); print(f\\\"Test result: {result}\\\"); assert str(result) == \\\"0.12345679\\\", f\\\"Expected 0.12345679, got {result}\\\"\"'"
    
    if ($LASTEXITCODE -ne 0) {
        throw "Function test failed: $functionTest"
    }
    
    Write-Host $functionTest -ForegroundColor Gray
    
    # Step 6: Complete
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
        Invoke-Expression "$sshCmd 'cp ${backupFile} ${remotePath}'"
        Write-Host "Restored from backup $backupFile" -ForegroundColor Green
    }
    exit 1
}
finally {
    # Clean up temporary files
    if (Test-Path .\temp_file.py) {
        Remove-Item .\temp_file.py -ErrorAction SilentlyContinue
    }
    if (Test-Path .\temp_file.py.fixed) {
        Remove-Item .\temp_file.py.fixed -ErrorAction SilentlyContinue
    }
} 