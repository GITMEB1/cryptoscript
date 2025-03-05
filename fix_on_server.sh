#!/bin/bash
# fix_on_server.sh
# This script uploads the fix script to the server and runs it on the trading bot file

# Configuration
SERVER="217.154.11.242"
SSH_KEY="$SSH_KEY"
REMOTE_DIR="/root/CryptoScript"
BOT_FILE="crypto_trading_bot.py"
FIX_SCRIPT="simple_fix.py"

# Print header
echo "========================================"
echo "Crypto Trading Bot Decimal Precision Fix"
echo "========================================"
echo

# Check if the fix script exists
if [ ! -f "$FIX_SCRIPT" ]; then
  echo "❌ Fix script not found: $FIX_SCRIPT"
  exit 1
fi

echo "1. Uploading fix script to server..."
scp -i "$SSH_KEY" "$FIX_SCRIPT" "root@$SERVER:$REMOTE_DIR/"
if [ $? -ne 0 ]; then
  echo "❌ Failed to upload fix script"
  exit 1
fi
echo "✅ Fix script uploaded successfully"

echo
echo "2. Running fix script on server..."
ssh -i "$SSH_KEY" "root@$SERVER" "cd $REMOTE_DIR && python $FIX_SCRIPT $BOT_FILE"
if [ $? -ne 0 ]; then
  echo "❌ Fix script failed to run successfully"
  exit 1
fi
echo "✅ Fix applied successfully on server"

echo
echo "3. Testing normalize_decimal function..."
ssh -i "$SSH_KEY" "root@$SERVER" "cd $REMOTE_DIR && python -c \"
from crypto_trading_bot import normalize_decimal
from decimal import Decimal

# Test values
test_values = [
    Decimal('0.12345678'),
    Decimal('0.1234567850'),  # Should round up
    Decimal('0.1234567849')   # Should round down with ROUND_HALF_UP
]

print('Testing normalize_decimal function:')
for val in test_values:
    result = normalize_decimal(val)
    print(f'normalize_decimal({val}) = {result} (exp: {result.as_tuple().exponent})')
\""

if [ $? -ne 0 ]; then
  echo "❌ Function test failed"
  exit 1
fi
echo "✅ Function tested successfully"

echo
echo "========================================"
echo "✅ All steps completed successfully!"
echo "The decimal precision fix has been applied to the trading bot."
echo "========================================" 