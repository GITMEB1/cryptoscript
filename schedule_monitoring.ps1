# PowerShell script to schedule regular monitoring of the trading bot
# This script sets up scheduled tasks to run the monitoring script at regular intervals

param (
    [switch]$Remote = $false,
    [string]$Interval = "daily", # Options: hourly, daily, weekly
    [int]$Duration = 7 # Number of days to run the monitoring
)

$ErrorActionPreference = "Stop"
$scriptPath = Join-Path $PSScriptRoot "monitor_trading_bot.py"
$logDir = Join-Path $PSScriptRoot "monitoring_logs"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"

# Create monitoring logs directory if it doesn't exist
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
    Write-Host "Created monitoring logs directory: $logDir" -ForegroundColor Green
}

# Function to run the monitoring script and save output to a log file
function Run-Monitoring {
    param (
        [switch]$Remote = $false
    )
    
    $currentTime = Get-Date -Format "yyyyMMdd_HHmmss"
    $logFile = Join-Path $logDir "monitor_$currentTime.log"
    
    Write-Host "Running monitoring script at $(Get-Date)" -ForegroundColor Cyan
    
    try {
        if ($Remote) {
            # Use Start-Process to capture output properly
            $process = Start-Process -FilePath "python" -ArgumentList "$scriptPath --remote" -NoNewWindow -Wait -PassThru -RedirectStandardOutput $logFile -RedirectStandardError "$logFile.err"
            $exitCode = $process.ExitCode
        } else {
            $process = Start-Process -FilePath "python" -ArgumentList "$scriptPath" -NoNewWindow -Wait -PassThru -RedirectStandardOutput $logFile -RedirectStandardError "$logFile.err"
            $exitCode = $process.ExitCode
        }
        
        # Combine error log with main log if it exists
        if (Test-Path "$logFile.err") {
            Add-Content -Path $logFile -Value (Get-Content -Path "$logFile.err")
            Remove-Item -Path "$logFile.err" -Force
        }
        
        if ($exitCode -eq 0) {
            Write-Host "Monitoring completed successfully. Log saved to: $logFile" -ForegroundColor Green
            
            # Display a summary of the monitoring results
            $logContent = Get-Content -Path $logFile -Raw
            if ($logContent -match "=== Monitoring Summary ===\s+(.*?)(?:\r?\n){2,}") {
                $summary = $matches[1]
                Write-Host "`nMonitoring Summary:" -ForegroundColor Yellow
                Write-Host $summary -ForegroundColor Gray
            }
        } else {
            Write-Host "Monitoring failed with exit code $exitCode. Check log: $logFile" -ForegroundColor Red
        }
    } catch {
        Write-Host "Error running monitoring script: $_" -ForegroundColor Red
    }
}

# Function to schedule tasks based on the interval
function Schedule-Monitoring {
    param (
        [string]$Interval,
        [int]$Duration,
        [switch]$Remote = $false
    )
    
    $remoteFlag = if ($Remote) { "--remote" } else { "" }
    $scriptCommand = "python `"$scriptPath`" $remoteFlag"
    $taskName = "CryptoBot_Monitor_$timestamp"
    
    Write-Host "Setting up scheduled monitoring with interval: $Interval for $Duration days" -ForegroundColor Cyan
    
    switch ($Interval) {
        "hourly" {
            # Schedule to run every 4 hours
            $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Hours 4) -RepetitionDuration (New-TimeSpan -Days $Duration)
        }
        "daily" {
            # Schedule to run daily
            $trigger = New-ScheduledTaskTrigger -Daily -At "12:00" -DaysInterval 1
        }
        "weekly" {
            # Schedule to run weekly
            $trigger = New-ScheduledTaskTrigger -Weekly -At "12:00" -DaysOfWeek Monday
        }
        default {
            Write-Host "Invalid interval specified. Using daily." -ForegroundColor Yellow
            $trigger = New-ScheduledTaskTrigger -Daily -At "12:00" -DaysInterval 1
        }
    }
    
    # Create a more robust action that handles output properly
    $actionScript = @"
# Run the monitoring script and save output to a log file
`$logDir = "$logDir"
`$currentTime = Get-Date -Format "yyyyMMdd_HHmmss"
`$logFile = Join-Path `$logDir "monitor_`$currentTime.log"

try {
    Start-Process -FilePath "python" -ArgumentList "$scriptPath $remoteFlag" -NoNewWindow -Wait -RedirectStandardOutput `$logFile -RedirectStandardError "`$logFile.err"
    
    # Combine error log with main log if it exists
    if (Test-Path "`$logFile.err") {
        Add-Content -Path `$logFile -Value (Get-Content -Path "`$logFile.err")
        Remove-Item -Path "`$logFile.err" -Force
    }
} catch {
    Add-Content -Path `$logFile -Value "Error running monitoring script: `$_"
}
"@
    
    $actionScriptPath = Join-Path $PSScriptRoot "monitor_task.ps1"
    Set-Content -Path $actionScriptPath -Value $actionScript
    
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$actionScriptPath`""
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd -AllowStartIfOnBatteries
    
    # Create the scheduled task
    try {
        Register-ScheduledTask -TaskName $taskName -Trigger $trigger -Action $action -Settings $settings -Force | Out-Null
        Write-Host "Scheduled task '$taskName' created successfully" -ForegroundColor Green
        Write-Host "Monitoring will run with $Interval interval for $Duration days" -ForegroundColor Green
        
        # If duration is specified, create an end task to remove the scheduled task
        if ($Duration -gt 0) {
            $endDate = (Get-Date).AddDays($Duration)
            $endTaskName = "CryptoBot_Monitor_End_$timestamp"
            $endTrigger = New-ScheduledTaskTrigger -Once -At $endDate
            $endAction = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -Command `"Unregister-ScheduledTask -TaskName '$taskName' -Confirm:`$false`""
            
            Register-ScheduledTask -TaskName $endTaskName -Trigger $endTrigger -Action $endAction -Settings $settings -Force | Out-Null
            Write-Host "End task '$endTaskName' created to remove monitoring on $(Get-Date -Date $endDate -Format 'yyyy-MM-dd')" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "Failed to create scheduled task: $_" -ForegroundColor Red
    }
}

# Run monitoring once immediately
Write-Host "Running initial monitoring..." -ForegroundColor Cyan
Run-Monitoring -Remote:$Remote

# Schedule future monitoring
Write-Host "`nSetting up scheduled monitoring..." -ForegroundColor Cyan
Schedule-Monitoring -Interval $Interval -Duration $Duration -Remote:$Remote

Write-Host "`nMonitoring setup complete!" -ForegroundColor Green
Write-Host "Initial monitoring results are saved in the $logDir directory" -ForegroundColor Green
Write-Host "Future monitoring will run with $Interval interval for $Duration days" -ForegroundColor Green
Write-Host "To view scheduled tasks, run: Get-ScheduledTask | Where-Object {`$_.TaskName -like 'CryptoBot_Monitor*'}" -ForegroundColor Cyan 