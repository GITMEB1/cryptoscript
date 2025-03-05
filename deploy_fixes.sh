#!/bin/bash

# Deploy Decimal Precision Fixes to Server
# ========================================
#
# This script uploads the fixed implementations to the server
# and applies them to the crypto trading bot.

# Configuration
SERVER="root@217.154.11.242"
SSH_KEY="$HOME/.ssh/id_rsa_trading"
REMOTE_DIR="~/CryptoScript"

# Display banner
echo "====================================================="
echo "Deploying Decimal Precision Fixes to Crypto Trading Bot"
echo "====================================================="

# Check that the SSH key exists
if [ ! -f "$SSH_KEY" ]; then
    echo "Error: SSH key not found at $SSH_KEY"
    exit 1
fi

# Upload fixed implementation files
echo "Uploading fixed implementation files..."
scp -i "$SSH_KEY" fixed_decimal.py fixed_position.py fixed_risk_manager.py apply_fixes.py test_fixed_precision.py "$SERVER:$REMOTE_DIR/"

if [ $? -ne 0 ]; then
    echo "Error: Failed to upload files to server"
    exit 1
fi

# Apply fixes on the server
echo "Applying fixes on the server..."
ssh -i "$SSH_KEY" "$SERVER" "cd $REMOTE_DIR && source ~/miniconda3/bin/activate trading && python apply_fixes.py"

if [ $? -ne 0 ]; then
    echo "Error: Failed to apply fixes on the server"
    exit 1
fi

# Run tests to verify fixes
echo "Running tests to verify the fixes..."
ssh -i "$SSH_KEY" "$SERVER" "cd $REMOTE_DIR && source ~/miniconda3/bin/activate trading && python test_fixed_precision.py"

if [ $? -ne 0 ]; then
    echo "Warning: Tests failed. Fixes may not be working correctly."
else
    echo "Tests passed. Fixes are working correctly."
fi

# Apply the fixed file
echo "Applying the fixed version to the main bot file..."
ssh -i "$SSH_KEY" "$SERVER" "cd $REMOTE_DIR && mv crypto_trading_bot.py.fixed crypto_trading_bot.py"

if [ $? -ne 0 ]; then
    echo "Error: Failed to apply fixes to the main bot file"
    exit 1
fi

# Run original tests to verify everything works
echo "Running original tests to verify the fixed implementation..."
ssh -i "$SSH_KEY" "$SERVER" "cd $REMOTE_DIR && source ~/miniconda3/bin/activate trading && python -m pytest test_trading_bot.py -v"

echo "====================================================="
echo "Deployment completed!"
echo "=====================================================" 