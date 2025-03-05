# Decimal Precision Fix - Setup & Deployment Instructions

This document provides detailed instructions for setting up and deploying the decimal precision fix for the CryptoScript trading bot.

## Current Status

✅ **Local Fix Applied**: The decimal precision fix has been successfully applied to the local copy of the trading bot.
⚠️ **Remote Deployment Pending**: The fix needs to be deployed to the remote server.

## Local Fix Summary

The following changes have been applied locally:

1. **Syntax Errors Fixed**:
   - Fixed unterminated f-string at line 875
   - Fixed invalid code insertion at line 611

2. **normalize_decimal Function Replaced**:
   - Implemented proper decimal rounding using `Decimal.quantize()` with `ROUND_HALF_UP`
   - Added required imports (`ROUND_HALF_UP`)

3. **Validation Completed**:
   - Python compilation check passed
   - Function tests with various decimal values confirmed correct rounding behavior

## Remote Deployment Options

### Option 1: Using PuTTY Tools (Recommended for Windows)

#### Prerequisites

1. **Install PuTTY**:
   - Download from [https://www.putty.org/](https://www.putty.org/)
   - Install and add the installation directory to your PATH environment variable

2. **Verify Installation**:
   ```powershell
   Get-Command plink.exe
   Get-Command pscp.exe
   ```

#### Deployment Steps

1. **Run the Windows Deployment Script**:
   ```powershell
   .\deploy_windows.ps1
   ```

2. **What the Script Does**:
   - Creates a backup of the original file on the server
   - Uploads the fixed local file to the server
   - Validates the changes on the server
   - Provides rollback capability if needed

### Option 2: Manual SCP/SSH Deployment

If the automated scripts are not working, you can manually deploy the fix:

1. **Create a Backup on the Server**:
   ```bash
   ssh root@217.154.11.242 "cp /root/CryptoScript/crypto_trading_bot.py /root/CryptoScript/backup/crypto_trading_bot.$(date +%Y%m%d_%H%M%S).bak"
   ```

2. **Upload the Fixed File**:
   ```bash
   scp crypto_trading_bot.py root@217.154.11.242:/root/CryptoScript/
   ```

3. **Verify the Fix on the Server**:
   ```bash
   ssh root@217.154.11.242 "cd /root/CryptoScript && python -m py_compile crypto_trading_bot.py"
   ```

4. **Test the Function on the Server**:
   ```bash
   ssh root@217.154.11.242 "cd /root/CryptoScript && python -c 'from crypto_trading_bot import normalize_decimal; print(normalize_decimal(\"0.123456785\"))'"
   ```

### Option 3: Using WinSCP (GUI Alternative)

For those who prefer a graphical interface:

1. **Install WinSCP**:
   - Download from [https://winscp.net/](https://winscp.net/)
   - Install and run the application

2. **Connect to the Server**:
   - Host: 217.154.11.242
   - Username: root
   - Password: 4O9gNnSt

3. **Upload the File**:
   - Navigate to /root/CryptoScript/ on the remote server
   - Create a backup of crypto_trading_bot.py
   - Upload the local crypto_trading_bot.py to replace the remote file

## Verification After Deployment

After deploying the fix to the remote server, verify that:

1. **The file compiles without errors**:
   ```bash
   ssh root@217.154.11.242 "cd /root/CryptoScript && python -m py_compile crypto_trading_bot.py"
   ```

2. **The normalize_decimal function works correctly**:
   ```bash
   ssh root@217.154.11.242 "cd /root/CryptoScript && python -c 'from crypto_trading_bot import normalize_decimal; print(normalize_decimal(\"0.123456785\"))'"
   ```
   Expected output: `0.12345679`

3. **The trading bot runs without errors**:
   ```bash
   ssh root@217.154.11.242 "cd /root/CryptoScript && source /root/miniconda3/etc/profile.d/conda.sh && conda activate trading && python crypto_trading_bot.py --test"
   ```

## Troubleshooting

### Common Issues

1. **SSH Authentication Failures**:
   - Verify the correct password is being used
   - Try connecting manually to identify any issues

2. **File Permission Issues**:
   - Ensure the uploaded file has the correct permissions:
     ```bash
     ssh root@217.154.11.242 "chmod 644 /root/CryptoScript/crypto_trading_bot.py"
     ```

3. **Import Errors**:
   - If there are import errors, ensure the trading environment has all required packages:
     ```bash
     ssh root@217.154.11.242 "source /root/miniconda3/etc/profile.d/conda.sh && conda activate trading && pip install -r /root/CryptoScript/requirements.txt"
     ```

### Rollback Procedure

If you need to restore the original file:

```bash
ssh root@217.154.11.242 "cp /root/CryptoScript/backup/crypto_trading_bot.[TIMESTAMP].bak /root/CryptoScript/crypto_trading_bot.py"
```

Replace `[TIMESTAMP]` with the actual timestamp of your backup file.

## Security Considerations

- The current instructions contain hardcoded passwords for convenience
- For production environments, consider more secure authentication methods
- Remove or secure any files containing passwords after deployment

---

*Last Updated: March 5, 2025* 