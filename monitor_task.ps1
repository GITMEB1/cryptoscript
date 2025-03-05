# Run the monitoring script and save output to a log file
$logDir = "C:\Users\abbey\OneDrive\Documents\Danny\OneDrive\Desktop\CryptoScript\monitoring_logs"
$currentTime = Get-Date -Format "yyyyMMdd_HHmmss"
$logFile = Join-Path $logDir "monitor_$currentTime.log"

try {
    Start-Process -FilePath "python" -ArgumentList "C:\Users\abbey\OneDrive\Documents\Danny\OneDrive\Desktop\CryptoScript\monitor_trading_bot.py --remote" -NoNewWindow -Wait -RedirectStandardOutput $logFile -RedirectStandardError "$logFile.err"
    
    # Combine error log with main log if it exists
    if (Test-Path "$logFile.err") {
        Add-Content -Path $logFile -Value (Get-Content -Path "$logFile.err")
        Remove-Item -Path "$logFile.err" -Force
    }
} catch {
    Add-Content -Path $logFile -Value "Error running monitoring script: $_"
}
