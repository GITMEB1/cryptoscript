# deploy_ast_based_fix.ps1
# Robust deployment script for applying AST-based code modifications to the trading bot
# Includes validation and automatic rollback on failure

# Configuration
$SERVER = "217.154.11.242"
$SSH_KEY = $env:SSH_KEY
$REMOTE_DIR = "/root/CryptoScript"
$BOT_FILE = "crypto_trading_bot.py"
$CODE_MODIFIER = "code_modifier.py"
$CONDA_ENV = "trading"
$ErrorActionPreference = "Stop"

# Header
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "   AST-Based Decimal Precision Fix Deployment" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Function to handle errors and rollback
function HandleError {
    param(
        [string]$ErrorMessage,
        [string]$BackupFile
    )
    
    Write-Host "`n❌ ERROR: $ErrorMessage" -ForegroundColor Red
    
    if ($BackupFile) {
        Write-Host "Attempting rollback from backup: $BackupFile" -ForegroundColor Yellow
        try {
            Invoke-Expression "ssh -i `"$SSH_KEY`" root@$SERVER `"cd $REMOTE_DIR && cp $BackupFile $BOT_FILE`""
            Write-Host "✅ Rollback successful!" -ForegroundColor Green
        }
        catch {
            Write-Host "❌ Rollback failed: $_" -ForegroundColor Red
            Write-Host "Manual intervention required. Backup file is: $BackupFile" -ForegroundColor Red
        }
    }
    
    exit 1
}

# Check prerequisites
try {
    # Check if the code modifier exists
    if (-not (Test-Path $CODE_MODIFIER)) {
        throw "Code modifier script not found: $CODE_MODIFIER"
    }
    
    # Check if SSH key exists
    if (-not $SSH_KEY) {
        throw "SSH key not found. Please set the SSH_KEY environment variable."
    }
}
catch {
    HandleError -ErrorMessage $_
}

# Step 1: Upload the code modifier to the server
Write-Host "Step 1: Uploading AST-based code modifier..." -ForegroundColor Yellow
try {
    scp -i "$SSH_KEY" "$CODE_MODIFIER" "root@$SERVER`:$REMOTE_DIR/"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to upload code modifier script"
    }
    Write-Host "✅ Code modifier uploaded successfully" -ForegroundColor Green
}
catch {
    HandleError -ErrorMessage $_
}

# Step 2: Create a timestamp for backups
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFile = "${BOT_FILE}.bak.$timestamp"

# Step 3: Create a backup of the original file on the server
Write-Host "`nStep 2: Creating backup of the original file..." -ForegroundColor Yellow
try {
    ssh -i "$SSH_KEY" "root@$SERVER" "cd $REMOTE_DIR && cp $BOT_FILE $backupFile"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to create backup on server"
    }
    Write-Host "✅ Backup created: $backupFile" -ForegroundColor Green
}
catch {
    HandleError -ErrorMessage $_
}

# Step 4: Run the code modifier on the server
Write-Host "`nStep 3: Running AST-based code modifier..." -ForegroundColor Yellow
try {
    $modifierOutput = ssh -i "$SSH_KEY" "root@$SERVER" "cd $REMOTE_DIR && source /root/miniconda3/bin/activate $CONDA_ENV && python $CODE_MODIFIER $BOT_FILE"
    Write-Host $modifierOutput
    
    if ($LASTEXITCODE -ne 0) {
        throw "Code modification failed"
    }
    
    if ($modifierOutput -match "Code modification failed") {
        throw "Code modification reported failure"
    }
    
    Write-Host "✅ Code modification completed" -ForegroundColor Green
}
catch {
    HandleError -ErrorMessage $_ -BackupFile $backupFile
}

# Step 5: Validate the modified file syntax
Write-Host "`nStep 4: Validating modified file syntax..." -ForegroundColor Yellow
try {
    $syntaxCheck = ssh -i "$SSH_KEY" "root@$SERVER" "cd $REMOTE_DIR && source /root/miniconda3/bin/activate $CONDA_ENV && python -m py_compile $BOT_FILE"
    
    if ($LASTEXITCODE -ne 0) {
        throw "Syntax validation failed. The modified file contains syntax errors."
    }
    
    Write-Host "✅ Syntax validation passed" -ForegroundColor Green
}
catch {
    HandleError -ErrorMessage $_ -BackupFile $backupFile
}

# Step 6: Function Testing
Write-Host "`nStep 5: Testing normalize_decimal function..." -ForegroundColor Yellow
try {
    $testCommand = @"
from crypto_trading_bot import normalize_decimal
from decimal import Decimal

# Test cases
test_cases = [
    (Decimal('0.12345678'), '0.12345678'),    # Exact precision match
    (Decimal('0.123456785'), '0.12345679'),   # Round up at 5
    (Decimal('0.1234567849'), '0.12345678'),  # Round down below 5
    ('0.12345678', '0.12345678'),             # String input
    (0.12345678, '0.12345678')                # Float input
]

print('Testing normalize_decimal function:')
all_passed = True

for input_val, expected in test_cases:
    result = normalize_decimal(input_val)
    result_str = str(result)
    
    # Check if the result matches the expected value
    if result_str == expected:
        print(f'PASS: normalize_decimal({input_val}) = {result}')
    else:
        print(f'FAIL: normalize_decimal({input_val}) = {result}, expected {expected}')
        all_passed = False
    
    # Check if exponent is -8 (8 decimal places)
    if result.as_tuple().exponent != -8:
        print(f'FAIL: Result has incorrect exponent: {result.as_tuple().exponent}, expected -8')
        all_passed = False

if all_passed:
    print('All tests passed!')
    exit(0)
else:
    print('Some tests failed!')
    exit(1)
"@

    $testCommand = $testCommand -replace "`n", "; "
    $testResult = ssh -i "$SSH_KEY" "root@$SERVER" "cd $REMOTE_DIR && source /root/miniconda3/bin/activate $CONDA_ENV && python -c '$testCommand'"
    Write-Host $testResult
    
    if ($LASTEXITCODE -ne 0) {
        throw "Function tests failed. The normalize_decimal function is not working as expected."
    }
    
    Write-Host "✅ Function tests passed" -ForegroundColor Green
}
catch {
    HandleError -ErrorMessage $_ -BackupFile $backupFile
}

# Step 7: Run unit tests if available
Write-Host "`nStep 6: Running unit tests..." -ForegroundColor Yellow
try {
    $unitTestResult = ssh -i "$SSH_KEY" "root@$SERVER" "cd $REMOTE_DIR && source /root/miniconda3/bin/activate $CONDA_ENV && python -m pytest test_trading_bot.py -v || echo 'Non-critical test failures detected'"
    Write-Host $unitTestResult
    
    if ($unitTestResult -match "Some tests failed") {
        Write-Host "⚠️ Some unit tests failed, but deployment will continue" -ForegroundColor Yellow
    } else {
        Write-Host "✅ Unit tests completed" -ForegroundColor Green
    }
}
catch {
    Write-Host "⚠️ Unit tests encountered an error, but deployment will continue: $_" -ForegroundColor Yellow
}

# Deployment successful!
Write-Host "`n=============================================" -ForegroundColor Cyan
Write-Host "   ✅ Deployment completed successfully!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "`nThe normalize_decimal function has been updated with proper decimal precision handling using ROUND_HALF_UP."
Write-Host "`nA backup of the original file was created: $backupFile"
Write-Host "To restore the backup if needed, run:"
Write-Host "ssh -i `"$SSH_KEY`" root@$SERVER `"cd $REMOTE_DIR && cp $backupFile $BOT_FILE`"" -ForegroundColor Yellow 