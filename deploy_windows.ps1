$ErrorActionPreference = "Stop"
$remoteUser = "root"
$remoteIP = "217.154.11.242"
$remotePath = "/root/CryptoScript/crypto_trading_bot.py"
$backupPath = "/root/CryptoScript/backup"
$remotePassword = "4O9gNnSt"

# Check if plink and pscp are available
$plinkExists = Get-Command plink -ErrorAction SilentlyContinue
$pscpExists = Get-Command pscp -ErrorAction SilentlyContinue

if (-not $plinkExists -or -not $pscpExists) {
    Write-Host "PuTTY tools (plink/pscp) not found in PATH" -ForegroundColor Red
    Write-Host "Please install PuTTY and ensure plink.exe and pscp.exe are in your PATH" -ForegroundColor Yellow
    exit 1
}

# First-time connection to accept host key (with auto answer yes)
Write-Host "Setting up initial connection..." -ForegroundColor Cyan
echo y | plink -pw $remotePassword ${remoteUser}@${remoteIP} "exit" 2>&1 | Out-Null

# Create backup directory if it doesn't exist
try {
    Write-Host "Creating backup directory..." -ForegroundColor Cyan
    echo $remotePassword | plink -pw $remotePassword ${remoteUser}@${remoteIP} "mkdir -p ${backupPath}"
} catch {
    Write-Host "Backup directory already exists or couldn't be created" -ForegroundColor Yellow
}

# Step 1: Create remote backup with timestamp
try {
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupFile = "${backupPath}/crypto_trading_bot.${timestamp}.bak"
    Write-Host "Creating remote backup at ${backupFile}..." -ForegroundColor Cyan
    echo $remotePassword | plink -pw $remotePassword ${remoteUser}@${remoteIP} "cp ${remotePath} ${backupFile}"
    
    # Step 2: Download file for local editing
    Write-Host "Downloading file for syntax fix..." -ForegroundColor Cyan
    echo $remotePassword | pscp -pw $remotePassword ${remoteUser}@${remoteIP}:${remotePath} .\temp_file.py
    
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
    echo $remotePassword | pscp -pw $remotePassword $tempFile ${remoteUser}@${remoteIP}:${remotePath}
    
    # Step 5: Remote validation
    Write-Host "Validating remote file..." -ForegroundColor Cyan
    
    # Verify syntax 
    $validation = echo $remotePassword | plink -pw $remotePassword ${remoteUser}@${remoteIP} "cd /root/CryptoScript && source /root/miniconda3/etc/profile.d/conda.sh && conda activate trading && python -m py_compile ${remotePath}"
    
    if ($LASTEXITCODE -ne 0) {
        throw "Remote validation failed: $validation"
    }
    
    # Verify imports
    Write-Host "Verifying imports..." -ForegroundColor Cyan
    $importCheck = echo $remotePassword | plink -pw $remotePassword ${remoteUser}@${remoteIP} "cd /root/CryptoScript && source /root/miniconda3/etc/profile.d/conda.sh && conda activate trading && python -c 'from crypto_trading_bot import normalize_decimal; from decimal import ROUND_HALF_UP; print(\"Import verification successful\")'"
    
    if ($LASTEXITCODE -ne 0) {
        throw "Import verification failed: $importCheck"
    }
    
    Write-Host $importCheck -ForegroundColor Gray
    
    # Test function
    Write-Host "Testing normalize_decimal function..." -ForegroundColor Cyan
    $functionTest = echo $remotePassword | plink -pw $remotePassword ${remoteUser}@${remoteIP} "cd /root/CryptoScript && source /root/miniconda3/etc/profile.d/conda.sh && conda activate trading && python -c 'from crypto_trading_bot import normalize_decimal; from decimal import Decimal; result = normalize_decimal(\"0.123456785\"); print(f\"Test result: {result}\"); assert str(result) == \"0.12345679\", f\"Expected 0.12345679, got {result}\"'"
    
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
        echo $remotePassword | plink -pw $remotePassword ${remoteUser}@${remoteIP} "cp ${backupFile} ${remotePath}"
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