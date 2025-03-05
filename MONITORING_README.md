# CryptoScript Monitoring Tools

This directory contains tools for monitoring the CryptoScript trading bot after the decimal precision fix deployment.

## Available Tools

### 1. `monitor_trading_bot.py`

A Python script that monitors the trading bot's logs and performance, specifically checking for:
- Proper functioning of the `normalize_decimal` function
- Errors or warnings in the logs
- Trading activity metrics

#### Usage

**Local Monitoring:**
```bash
python monitor_trading_bot.py
```

**Remote Monitoring:**
```bash
python monitor_trading_bot.py --remote
```

### 2. `schedule_monitoring.ps1`

A PowerShell script that schedules regular monitoring of the trading bot using Windows Task Scheduler.

#### Usage

**Basic Usage (Daily monitoring for 7 days):**
```powershell
.\schedule_monitoring.ps1
```

**Custom Monitoring Schedule:**
```powershell
# Monitor the remote server hourly for 3 days
.\schedule_monitoring.ps1 -Remote -Interval hourly -Duration 3

# Monitor locally weekly for 30 days
.\schedule_monitoring.ps1 -Interval weekly -Duration 30
```

#### Parameters

- `-Remote`: Monitor the remote server instead of local environment
- `-Interval`: Frequency of monitoring (hourly, daily, weekly)
- `-Duration`: Number of days to run the monitoring

## Monitoring Logs

All monitoring logs are saved in the `monitoring_logs` directory with timestamps in the filename.

## Recommended Monitoring Schedule

1. **Initial Period (First 24 Hours)**
   ```powershell
   .\schedule_monitoring.ps1 -Remote -Interval hourly -Duration 1
   ```

2. **Stabilization Period (Next 7 Days)**
   ```powershell
   .\schedule_monitoring.ps1 -Remote -Interval daily -Duration 7
   ```

3. **Long-term Monitoring**
   ```powershell
   .\schedule_monitoring.ps1 -Remote -Interval weekly -Duration 30
   ```

## Interpreting Results

The monitoring script provides information about:

1. **Bot Status**: Whether the trading bot is currently running
2. **Log Analysis**: Statistics about errors, warnings, and trading activity
3. **Decimal Function Test**: Verification that the `normalize_decimal` function is working correctly

### Example Output

```
=== Trading Bot Monitor ===
Mode: Remote
Time: 2025-03-05 14:30:45
==============================

=== Bot Status ===
Bot Status: ✅ Running on remote server

Latest log file: /root/CryptoScript/logs/trading_bot_20250305_123456.log

=== Log Analysis ===
Log Statistics:
  Errors: 0
  Warnings: 12
  Buy Signals: 3
  Sell Signals: 2
  Decimal Operations: 45

=== Testing normalize_decimal Function ===
Testing on remote server...
  Value: 0.123456785
  Result: 0.12345679
  Expected: 0.12345679
  Match: ✅

  Value: 0.123456784
  Result: 0.12345678
  Expected: 0.12345678
  Match: ✅

  Value: 1.999999995
  Result: 2.00000000
  Expected: 2.00000000
  Match: ✅

  Value: 0.000000001
  Result: 0.00000000
  Expected: 0.00000000
  Match: ✅

=== Monitoring Summary ===
Bot Status: ✅ Running
Log File: trading_bot_20250305_123456.log
Decimal Function: ✅ Tested

Recommendation:
  - Continue monitoring for at least 24 hours to ensure stability
```

## Troubleshooting

### Common Issues

1. **PuTTY Tools Not Found**
   - Ensure PuTTY is installed and in your PATH
   - Or specify the full path to PuTTY tools in the script

2. **Authentication Failures**
   - Verify the correct password is being used
   - Try connecting manually to identify any issues

3. **Python Import Errors**
   - Ensure all required packages are installed:
     ```bash
     pip install pandas
     ```

## Next Steps

After monitoring confirms the fix is working correctly:

1. Review the complete monitoring logs
2. Update the project documentation
3. Consider implementing the security enhancements outlined in `NEXT_STEPS.md`

---

*Last Updated: March 5, 2025* 