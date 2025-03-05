# Crypto Trading Bot Server Setup Guide

## Server Information
- **IP Address**: 217.154.11.242
- **Username**: root
- **Password**: 4O9gNnSt

## Project Overview
This document outlines the setup process for a cryptocurrency trading bot on an Ubuntu VPS. The bot requires specific technical analysis libraries and Python packages to function correctly.

## System Requirements
- Ubuntu Server (Latest LTS recommended)
- Minimum 2GB RAM (4GB recommended for compilation tasks)
- 20GB+ storage
- Python 3.8+

## Pre-Installation Steps

1. Update System Packages
```bash
apt update && apt upgrade -y
apt install build-essential wget git python3-pip -y
```

2. Install Miniconda (Recommended over plain venv)
```bash
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh
```

## Environment Setup

1. Create Conda Environment
```bash
conda create -n trading python=3.10
conda activate trading
```

2. Install TA-Lib Dependencies
```bash
# Install system dependencies
apt install build-essential wget -y

# Download and install TA-Lib
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
make install
```

3. Install Python Packages
```bash
# Install numpy first as it's a dependency
pip install numpy

# Install TA-Lib Python wrapper
pip install ta-lib

# Verify installation
python -c "import talib; print(talib.__version__)"
```

## Common Issues and Solutions

### TA-Lib Installation Failures
1. Memory Issues
   - Solution: Ensure at least 2GB RAM is available during compilation
   - Use swap if needed: `sudo fallocate -l 2G /swapfile && sudo chmod 600 /swapfile && sudo mkswap /swapfile && sudo swapon /swapfile`

2. Library Path Issues
   If you see "libta_lib.so.0: cannot open shared object file":
   ```bash
   echo "/usr/local/lib" | sudo tee /etc/ld.so.conf.d/talib.conf
   sudo ldconfig
   ```

3. Compilation Failures
   - Ensure all build dependencies are installed
   - Try installing from conda-forge as alternative:
     ```bash
     conda install -c conda-forge ta-lib
     ```

## Project Deployment

1. Clone Repository
```bash
git clone [your-repo-url]
cd [project-directory]
```

2. Install Project Dependencies
```bash
pip install -r requirements.txt
```

3. Configuration
- Copy example config: `cp config.example.py config.py`
- Edit configuration with your API keys and settings

## Monitoring and Maintenance

1. Use Screen or tmux for persistent sessions
```bash
apt install screen
screen -S trading_bot
```

2. Basic Monitoring
```bash
# Monitor CPU and Memory
htop

# Check logs
tail -f bot.log
```

## Security Recommendations

1. Change root password after initial login
2. Set up SSH key authentication
3. Configure firewall (UFW)
```bash
ufw allow OpenSSH
ufw enable
```

## Backup Procedures

1. Regular config backups
2. Database backups if applicable
3. Trading history exports

## Support and Resources

- TA-Lib Documentation: https://ta-lib.org/
- Python TA-Lib Wrapper: https://github.com/mrjbq7/ta-lib
- Conda Documentation: https://docs.conda.io/

## Troubleshooting Checklist

1. Verify system resources
2. Check Python environment activation
3. Confirm TA-Lib installation
4. Review log files
5. Check network connectivity
6. Verify API credentials

Remember to keep this document updated with any changes or improvements to the setup process. 