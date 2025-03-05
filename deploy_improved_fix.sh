#!/bin/bash
# Improved deployment script for fixing decimal precision issues in the trading bot
# This script uploads the improved fix script to the server and applies the changes

# Configuration
SERVER="217.154.11.242"
USERNAME="root"
SSH_KEY="$HOME/.ssh/id_rsa_trading"
REMOTE_DIR="/root/trading_bot"
CONDA_ENV="trading"

echo "=== Decimal Precision Fix Deployment ==="
echo "Server: $SERVER"
echo "Remote directory: $REMOTE_DIR"
echo "Conda environment: $CONDA_ENV"

# Step 1: Upload the improved fix script and verification script
echo -e "\n[1/6] Uploading scripts..."
scp -i "$SSH_KEY" complete_fix.py "$USERNAME@$SERVER:$REMOTE_DIR/improved_fix.py"
scp -i "$SSH_KEY" verify_fix.py "$USERNAME@$SERVER:$REMOTE_DIR/verify_fix.py"
if [ $? -ne 0 ]; then
    echo "Error: Failed to upload scripts"
    exit 1
fi
echo "Upload successful!"

# Step 2: Create a backup of the original file
echo -e "\n[2/6] Creating backup of original trading bot file..."
ssh -i "$SSH_KEY" "$USERNAME@$SERVER" "cd $REMOTE_DIR && cp crypto_trading_bot.py crypto_trading_bot.py.backup_$(date +%Y%m%d_%H%M%S)"
if [ $? -ne 0 ]; then
    echo "Error: Failed to create backup"
    exit 1
fi
echo "Backup created successfully!"

# Step 3: Run the improved fix script
echo -e "\n[3/6] Applying decimal precision fixes..."
ssh -i "$SSH_KEY" "$USERNAME@$SERVER" "cd $REMOTE_DIR && python improved_fix.py"
if [ $? -ne 0 ]; then
    echo "Error: Failed to apply fixes"
    exit 1
fi
echo "Fix script executed successfully!"

# Step 4: Apply the fixed version
echo -e "\n[4/6] Applying the fixed version..."
ssh -i "$SSH_KEY" "$USERNAME@$SERVER" "cd $REMOTE_DIR && cp crypto_trading_bot.py.fixed crypto_trading_bot.py"
if [ $? -ne 0 ]; then
    echo "Error: Failed to apply fixed version"
    exit 1
fi
echo "Fixed version applied successfully!"

# Step 5: Verify the fix
echo -e "\n[5/6] Verifying the fix..."
ssh -i "$SSH_KEY" "$USERNAME@$SERVER" "cd $REMOTE_DIR && source /root/miniconda3/bin/activate $CONDA_ENV && python verify_fix.py"
if [ $? -ne 0 ]; then
    echo "Warning: Verification failed. The fix may not have been applied correctly."
    echo "Please check the verification output above."
    echo "You may need to restore the backup and try again."
else
    echo "Verification successful! The fix was applied correctly."
fi

# Step 6: Run tests to verify the fix
echo -e "\n[6/6] Running tests to verify the fix..."
ssh -i "$SSH_KEY" "$USERNAME@$SERVER" "cd $REMOTE_DIR && source /root/miniconda3/bin/activate $CONDA_ENV && python -m pytest test_trading_bot.py -v"
if [ $? -ne 0 ]; then
    echo "Warning: Some tests failed. Please check the test output above."
else
    echo "All tests passed successfully!"
fi

echo -e "\n=== Deployment Complete ==="
echo "The decimal precision fixes have been applied to the trading bot."
echo "If you encounter any issues, you can restore the backup with:"
echo "ssh -i $SSH_KEY $USERNAME@$SERVER \"cd $REMOTE_DIR && cp crypto_trading_bot.py.backup_* crypto_trading_bot.py\"" 