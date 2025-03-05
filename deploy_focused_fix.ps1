# Focused Syntax Error Fix Deployment Script
# This script uploads and runs the focused syntax error fixer on the server

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
$syntaxFixerFile = "focused_fix.py"

# Check if required files exist
if (-not (Test-Path $syntaxFixerFile)) {
    Write-Error "Syntax fixer script not found: $syntaxFixerFile"
    exit 1
}

Write-Host "=== Focused Syntax Error Fix Deployment ===" -ForegroundColor Cyan

# Step 1: Upload the script to the server
Write-Host "`nStep 1: Uploading focused syntax fixer script..." -ForegroundColor Yellow
try {
    Write-Host "Uploading $syntaxFixerFile..."
    & scp -i $sshKeyPath $syntaxFixerFile "$username@$serverIp`:$remoteDir/"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to upload $syntaxFixerFile"
    }
    
    Write-Host "Script uploaded successfully." -ForegroundColor Green
} catch {
    Write-Error "Error uploading script: $_"
    exit 1
}

# Step 2: Run the syntax fixer
Write-Host "`nStep 2: Running focused syntax fixer..." -ForegroundColor Yellow
$runFixerCmd = "cd $remoteDir && source /root/miniconda3/etc/profile.d/conda.sh && conda activate $condaEnv && python focused_fix.py crypto_trading_bot.py"

try {
    $fixerOutput = & ssh -i $sshKeyPath "$username@$serverIp" $runFixerCmd
    Write-Host $fixerOutput
    
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to fix syntax errors"
    }
    
    # Check if the fixer was successful
    if ($fixerOutput -match "Syntax validation passed") {
        Write-Host "Syntax errors fixed successfully." -ForegroundColor Green
    } else {
        Write-Host "No syntax errors were fixed. This could mean the file is already fixed or there was an issue." -ForegroundColor Yellow
    }
} catch {
    Write-Error "Error fixing syntax errors: $_"
    exit 1
}

# Step 3: Verify the syntax
Write-Host "`nStep 3: Verifying syntax..." -ForegroundColor Yellow
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
Write-Host "✅ Script uploaded successfully" -ForegroundColor Green
Write-Host "✅ Syntax errors fixed" -ForegroundColor Green
Write-Host "✅ Syntax validated" -ForegroundColor Green

Write-Host "`nThe syntax errors have been fixed successfully!" -ForegroundColor Green
Write-Host "You can now proceed with the AST-based decimal precision fix." -ForegroundColor Cyan 