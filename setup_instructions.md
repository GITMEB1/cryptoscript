# Crypto Trading Bot Setup Instructions

## Environment Setup

1. **Conda Environment**
   ```bash
   conda create -n trading python=3.10
   conda activate trading
   ```

2. **Required Packages**
   ```bash
   conda install -c conda-forge ccxt pandas numpy requests python-dotenv
   conda install -c conda-forge ta-lib
   ```

3. **Environment Variables**
   Create a `.env` file in the project root with:
   ```
   # Trading Mode: "backtest" or "live"
   TRADING_MODE=backtest

   # Binance API Credentials
   BINANCE_API_KEY=your_api_key
   BINANCE_API_SECRET=your_api_secret

   # Trading Parameters
   INITIAL_BALANCE=100
   UPDATE_INTERVAL=900  # 15 minutes in seconds
   ```

## Important Notes for LLMs

1. **Decimal Precision**
   - All monetary calculations use Python's Decimal class for precision
   - Convert all float inputs to Decimal using `Decimal(str(value))`
   - Convert Decimal outputs to float for display using `float(value)`

2. **Position Tracking**
   - Positions are tracked using the Position class
   - Each position maintains its own quantity, entry price, and stop levels
   - All position calculations use Decimal arithmetic

3. **Risk Management**
   - Position sizing is ATR-based with a 2% risk per trade
   - Maximum position size is 25% of balance
   - Minimum trade amount is $12
   - Daily loss limit is 5%

4. **Trading Parameters**
   - Timeframe: 15 minutes
   - Maximum concurrent trades: 2
   - Fee rate: 0.075% (with BNB discount)
   - Slippage buffer: 0.3%

## Running the Bot

1. **Backtesting Mode**
   ```bash
   conda activate trading
   python crypto_trading_bot.py
   ```

2. **Live Trading Mode**
   - Set `TRADING_MODE=live` in `.env`
   - Ensure valid API credentials
   - Run the same command as backtesting

## Debugging Tips

1. **Common Issues**
   - If getting ccxt errors, check API credentials
   - If getting calculation errors, check for float/Decimal conversion
   - If no trades execute, check minimum position size requirements

2. **Logging**
   - All trades are logged to console and trading_bot.log
   - Check daily statistics in live mode
   - Monitor position updates and trailing stops

## Exchange-Specific Notes

1. **Binance Requirements**
   - Minimum order size varies by trading pair
   - BNB required for reduced fees
   - API rate limits apply in live mode

## Project Structure
```
trading_bot/
├── .env                  # Environment variables
├── crypto_trading_bot.py # Main script
├── setup_instructions.md # This file
└── trading_bot.log      # Will be created when running
```

## Environment Verification

Check if you're in the correct environment:
```bash
# Check current environment
conda info --envs

# Check installed packages
conda list | grep ta-lib
```

## Troubleshooting TA-Lib

If you encounter installation issues:

1. Make sure you're in the correct conda environment
2. Try removing and reinstalling TA-Lib:
```bash
conda remove ta-lib
conda install -c conda-forge ta-lib
```

3. Verify the installation:
```bash
python -c "import talib; print(talib.__version__)"
```

If you still encounter issues:
- Check if your Python version is compatible (3.10 recommended)
- Ensure all system dependencies are installed
- Try creating a new conda environment and starting fresh

## Common Issues

1. **"No module named 'talib'"**
   - Verify you're in the correct conda environment
   - Reinstall TA-Lib using conda

2. **TA-Lib installation fails**
   - Install system dependencies first
   - Use conda instead of pip for TA-Lib
   - Check system architecture compatibility

3. **Import errors after installation**
   - Restart your Python session
   - Verify PATH environment variables
   - Check for conflicting installations

## Additional Notes

- The bot is configured for a $70 initial balance
- Backtesting mode is enabled by default
- Minimum trade amount is set to $10 (Binance requirement)
- Trading fees are set to 0.1% per trade 