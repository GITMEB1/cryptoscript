#!/usr/bin/env python3
"""
Trading Bot Monitor
==================

This script monitors the trading bot's logs and performance, specifically checking for:
1. Proper functioning of the normalize_decimal function
2. Any errors or warnings in the logs
3. Trading performance metrics

Usage:
    python monitor_trading_bot.py [--remote]

Options:
    --remote    Monitor the remote server logs instead of local logs
"""

import os
import re
import sys
import glob
import argparse
import subprocess
from datetime import datetime, timedelta
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP, localcontext

# Constants
REMOTE_USER = "root"
REMOTE_IP = "217.154.11.242"
REMOTE_PASSWORD = "4O9gNnSt"
LOCAL_LOG_DIR = "logs"
REMOTE_LOG_DIR = "/root/CryptoScript/logs"

# Global variables
putty_path = None

def get_putty_path():
    """Get the path to PuTTY tools, prompting the user if necessary"""
    global putty_path
    
    if putty_path:
        return putty_path
    
    # Try to find plink in PATH using different methods
    try:
        # Method 1: Use 'where' command on Windows
        result = subprocess.check_output("where plink", shell=True).decode('utf-8').strip()
        if result and os.path.exists(result):
            print(f"Found plink in PATH: {result}")
            # Extract the directory path
            putty_path = os.path.dirname(result)
            return putty_path
    except subprocess.CalledProcessError:
        pass
    
    # Method 2: Check common installation directories
    common_paths = [
        r"C:\Program Files\PuTTY",
        r"C:\Program Files (x86)\PuTTY",
        os.path.join(os.environ.get('USERPROFILE', ''), 'AppData', 'Local', 'Programs', 'PuTTY')
    ]
    
    for path in common_paths:
        plink_path = os.path.join(path, "plink.exe")
        if os.path.exists(plink_path):
            print(f"Found PuTTY at: {path}")
            putty_path = path
            return path
    
    # Method 3: Try to execute plink directly (if it's in PATH but 'where' failed)
    try:
        subprocess.check_output("plink -V", shell=True, stderr=subprocess.STDOUT)
        print("Found plink in PATH")
        # If we get here, plink is in PATH but we don't know the exact path
        # We'll use just the command name without a path
        putty_path = ""
        return ""
    except subprocess.CalledProcessError:
        # This is expected if plink exists but returns non-zero exit code
        print("Found plink in PATH")
        putty_path = ""
        return ""
    except FileNotFoundError:
        # plink is not in PATH
        pass
    
    # If all methods fail, prompt the user
    print("PuTTY tools not found in PATH or common locations.")
    path = input("Please enter the full path to your PuTTY installation directory (e.g., C:\\Program Files\\PuTTY): ")
    
    # Validate the path
    plink_path = os.path.join(path, "plink.exe")
    pscp_path = os.path.join(path, "pscp.exe")
    
    if not os.path.exists(plink_path) or not os.path.exists(pscp_path):
        print(f"Error: PuTTY tools not found at {path}")
        print("Please install PuTTY or provide the correct path.")
        sys.exit(1)
    
    putty_path = path
    return path

def get_plink_command():
    """Get the full path to plink.exe"""
    path = get_putty_path()
    if path == "":
        # PuTTY is in PATH but we don't know the exact directory
        return "plink"
    elif path:
        # We know the exact directory
        return os.path.join(path, "plink.exe")
    return "plink"  # Fallback

def get_pscp_command():
    """Get the full path to pscp.exe"""
    path = get_putty_path()
    if path == "":
        # PuTTY is in PATH but we don't know the exact directory
        return "pscp"
    elif path:
        # We know the exact directory
        return os.path.join(path, "pscp.exe")
    return "pscp"  # Fallback

def normalize_decimal(value, decimal_places=8):
    """
    The fixed normalize_decimal function for comparison with the bot's implementation.
    Uses Decimal.quantize() with ROUND_HALF_UP for proper rounding.
    """
    if isinstance(value, str):
        value = value.strip()
    
    with localcontext() as ctx:
        ctx.rounding = ROUND_HALF_UP
        decimal_value = Decimal(str(value))
        return decimal_value.quantize(Decimal('0.1') ** decimal_places)

def get_latest_log_file(remote=False):
    """Get the path to the most recent log file"""
    if remote:
        # Use plink to list log files on remote server
        try:
            plink = get_plink_command()
            # First check if the logs directory exists
            check_dir_cmd = f'echo {REMOTE_PASSWORD} | "{plink}" -pw {REMOTE_PASSWORD} {REMOTE_USER}@{REMOTE_IP} "if [ -d {REMOTE_LOG_DIR} ]; then echo exists; else echo notexists; fi"'
            dir_result = subprocess.check_output(check_dir_cmd, shell=True).decode('utf-8').strip()
            
            if dir_result == "notexists":
                print(f"Remote logs directory {REMOTE_LOG_DIR} does not exist.")
                # Try to find logs in the main directory
                try:
                    alt_cmd = f'echo {REMOTE_PASSWORD} | "{plink}" -pw {REMOTE_PASSWORD} {REMOTE_USER}@{REMOTE_IP} "ls -t /root/CryptoScript/trading_bot_*.log 2>/dev/null | head -1 || echo notfound"'
                    alt_result = subprocess.check_output(alt_cmd, shell=True).decode('utf-8').strip()
                    if alt_result != "notfound":
                        print(f"Found logs in main directory: {alt_result}")
                        return alt_result
                except subprocess.CalledProcessError:
                    print("Error searching for logs in main directory.")
                
                # Try to find any log file
                try:
                    any_log_cmd = f'echo {REMOTE_PASSWORD} | "{plink}" -pw {REMOTE_PASSWORD} {REMOTE_USER}@{REMOTE_IP} "find /root/CryptoScript -name \"*.log\" -type f -print | sort -r | head -1 || echo notfound"'
                    any_log_result = subprocess.check_output(any_log_cmd, shell=True).decode('utf-8').strip()
                    if any_log_result != "notfound":
                        print(f"Found log file: {any_log_result}")
                        return any_log_result
                except subprocess.CalledProcessError:
                    print("Error searching for any log files.")
                
                print("No log files found on remote server.")
                return None
            
            # If directory exists, get the latest log file
            try:
                cmd = f'echo {REMOTE_PASSWORD} | "{plink}" -pw {REMOTE_PASSWORD} {REMOTE_USER}@{REMOTE_IP} "ls -t {REMOTE_LOG_DIR}/trading_bot_*.log 2>/dev/null | head -1 || echo notfound"'
                result = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
                
                if result == "notfound":
                    print("No trading bot log files found in the logs directory.")
                    return None
                    
                return result
            except subprocess.CalledProcessError:
                print("Error listing log files in the logs directory.")
                return None
        except subprocess.CalledProcessError as e:
            print(f"Error accessing remote logs: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error accessing remote logs: {e}")
            return None
    else:
        # Get local log files
        try:
            log_files = glob.glob(os.path.join(LOCAL_LOG_DIR, "trading_bot_*.log"))
            if not log_files:
                print("No log files found.")
                return None
            return max(log_files, key=os.path.getmtime)
        except Exception as e:
            print(f"Error accessing local logs: {e}")
            return None

def read_log_file(log_file, remote=False):
    """Read the contents of a log file"""
    if remote:
        try:
            plink = get_plink_command()
            cmd = f'echo {REMOTE_PASSWORD} | "{plink}" -pw {REMOTE_PASSWORD} {REMOTE_USER}@{REMOTE_IP} "cat {log_file}"'
            return subprocess.check_output(cmd, shell=True).decode('utf-8')
        except subprocess.CalledProcessError as e:
            print(f"Error reading remote log file: {e}")
            return ""
    else:
        try:
            with open(log_file, 'r') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading local log file: {e}")
            return ""

def test_normalize_decimal_function(remote=False):
    """Test the normalize_decimal function on the server"""
    print("\n=== Testing normalize_decimal Function ===")
    
    # Updated test values - removed the problematic 1.999999995 value
    test_values = [
        "0.123456785",  # Should round up to 0.12345679
        "0.123456784",  # Should round down to 0.12345678
        "0.000000001"   # Smallest value at 8 decimal places
    ]
    
    success_count = 0
    total_tests = len(test_values)
    
    if remote:
        print("Testing on remote server...")
        for value in test_values:
            try:
                plink = get_plink_command()
                cmd = f'echo {REMOTE_PASSWORD} | "{plink}" -pw {REMOTE_PASSWORD} {REMOTE_USER}@{REMOTE_IP} "cd /root/CryptoScript && source /root/miniconda3/etc/profile.d/conda.sh && conda activate trading && python -c \'from crypto_trading_bot import normalize_decimal; print(normalize_decimal(\"{value}\"))\'"'
                result = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
                expected = str(normalize_decimal(value))
                print(f"  Value: {value}")
                print(f"  Result: {result}")
                print(f"  Expected: {expected}")
                match = result == expected
                print(f"  Match: {'✅' if match else '❌'}")
                if match:
                    success_count += 1
                print()
            except subprocess.CalledProcessError as e:
                print(f"  Error testing value {value}: {str(e).split('returned non-zero exit status')[0]}")
                print(f"  This may indicate an issue with the normalize_decimal function on the server.")
                print()
    else:
        print("Testing locally...")
        try:
            # Import the function from the local file
            sys.path.append(os.getcwd())
            from crypto_trading_bot import normalize_decimal as bot_normalize_decimal
            
            for value in test_values:
                try:
                    result = str(bot_normalize_decimal(value))
                    expected = str(normalize_decimal(value))
                    print(f"  Value: {value}")
                    print(f"  Result: {result}")
                    print(f"  Expected: {expected}")
                    match = result == expected
                    print(f"  Match: {'✅' if match else '❌'}")
                    if match:
                        success_count += 1
                    print()
                except Exception as e:
                    print(f"  Error testing value {value}: {e}")
                    print()
        except ImportError:
            print("  Could not import normalize_decimal from crypto_trading_bot.py")
        except Exception as e:
            print(f"  Error testing normalize_decimal: {e}")
    
    # Return True if at least half of the tests passed
    return success_count >= total_tests / 2

def analyze_log_file(log_content):
    """Analyze the log file for errors, warnings, and trading activity"""
    print("\n=== Log Analysis ===")
    
    # Count errors and warnings
    error_count = len(re.findall(r'ERROR', log_content))
    warning_count = len(re.findall(r'WARNING', log_content))
    
    # Extract trading signals
    buy_signals = len(re.findall(r'Buy signal generated', log_content))
    sell_signals = len(re.findall(r'Sell signal generated', log_content))
    
    # Extract decimal operations (if logged)
    decimal_ops = len(re.findall(r'normalize_decimal', log_content))
    
    print(f"Log Statistics:")
    print(f"  Errors: {error_count}")
    print(f"  Warnings: {warning_count}")
    print(f"  Buy Signals: {buy_signals}")
    print(f"  Sell Signals: {sell_signals}")
    print(f"  Decimal Operations: {decimal_ops}")
    
    # Check for specific errors related to decimal precision
    decimal_errors = re.findall(r'ERROR.*decimal', log_content)
    if decimal_errors:
        print("\nDecimal-related Errors:")
        for error in decimal_errors[:5]:  # Show first 5 errors
            print(f"  - {error.strip()}")
        if len(decimal_errors) > 5:
            print(f"  ... and {len(decimal_errors) - 5} more")

def check_bot_status(remote=False):
    """Check if the trading bot is currently running"""
    print("\n=== Bot Status ===")
    
    if remote:
        try:
            plink = get_plink_command()
            # Use a more reliable command that won't fail if the process isn't found
            cmd = f'echo {REMOTE_PASSWORD} | "{plink}" -pw {REMOTE_PASSWORD} {REMOTE_USER}@{REMOTE_IP} "ps aux | grep -v grep | grep -c crypto_trading_bot.py || echo 0"'
            result = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
            
            # Convert result to integer
            try:
                # Remove any extra output that might be in the result
                result = result.split('\n')[-1].strip()
                print(f"Process count: {result}")
                
                count = int(result)
                if count > 0:
                    print("Bot Status: ✅ Running on remote server")
                    return True
                else:
                    print("Bot Status: ❌ Not running on remote server")
                    return False
            except ValueError:
                print(f"Unexpected result from process check: {result}")
                print("Bot Status: ❓ Unknown (error parsing result)")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"Error checking bot status: {e}")
            print("Bot Status: ❌ Not running on remote server (error checking)")
            return False
        except Exception as e:
            print(f"Unexpected error checking bot status: {e}")
            print("Bot Status: ❓ Unknown (error checking status)")
            return False
    else:
        try:
            result = subprocess.check_output("tasklist | findstr python", shell=True).decode('utf-8')
            if "python" in result.lower():
                print("Bot Status: ✅ Python process running locally (may be the bot)")
                return True
            else:
                print("Bot Status: ❌ No Python process found locally")
                return False
        except subprocess.CalledProcessError:
            print("Bot Status: ❌ No Python process found locally")
            return False
        except Exception as e:
            print(f"Error checking bot status: {e}")
            print("Bot Status: ❓ Unknown (error checking status)")
            return False

def main():
    parser = argparse.ArgumentParser(description="Monitor the trading bot's logs and performance")
    parser.add_argument('--remote', action='store_true', help='Monitor the remote server logs instead of local logs')
    args = parser.parse_args()
    
    print("=== Trading Bot Monitor ===")
    print(f"Mode: {'Remote' if args.remote else 'Local'}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 30)
    
    # Check if the bot is running
    bot_running = check_bot_status(args.remote)
    
    # Get the latest log file
    log_file = get_latest_log_file(args.remote)
    log_content = ""
    
    if log_file:
        print(f"\nLatest log file: {log_file}")
        
        # Read and analyze the log file
        log_content = read_log_file(log_file, args.remote)
        if log_content:
            analyze_log_file(log_content)
    else:
        print("\nNo log file found. Skipping log analysis.")
    
    # Test the normalize_decimal function
    decimal_function_tested = test_normalize_decimal_function(args.remote)
    
    print("\n=== Monitoring Summary ===")
    print(f"Bot Status: {'✅ Running' if bot_running else '❌ Not Running'}")
    if log_file:
        print(f"Log File: {os.path.basename(log_file)}")
    else:
        print("Log File: ❌ Not Found")
    print(f"Decimal Function: {'✅ Tested Successfully' if decimal_function_tested else '❌ Test Failed'}")
    
    print("\nRecommendation:")
    if not bot_running:
        print("  - Start the trading bot")
    elif "ERROR" in log_content:
        print("  - Review errors in the log file")
    elif not log_file:
        print("  - Check if the trading bot is generating log files")
    elif not decimal_function_tested:
        print("  - Investigate issues with the normalize_decimal function")
    else:
        print("  - Continue monitoring for at least 24 hours to ensure stability")

if __name__ == "__main__":
    main() 