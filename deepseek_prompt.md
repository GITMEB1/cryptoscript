# Context and Challenge

We have implemented a cryptocurrency trading bot for alt season with the following specifications:
- Initial capital: $70
- Platform: Binance
- Current timeframe: 15-minute candles
- Trading pairs: ETH/USDT, BNB/USDT, SOL/USDT, ADA/USDT

## Current Implementation Issues
Our backtesting results show:
1. High number of trades (57-68 per coin) leading to excessive fees ($2.26-$2.74)
2. Low win rate (32-37%)
3. Consistent losses across all pairs (7-9% loss)
4. High drawdowns (9-12%)

## Core Requirements
1. Must work with $70 initial capital
2. Must respect Binance's minimum order size ($10)
3. Must handle trading fees (0.1% per trade)
4. Must be viable during alt season (BTC dominance < 55%)

# Strategic Questions to Address

## Market Analysis
1. What characteristics make an altcoin suitable for trading with such small capital?
   - Consider volatility vs stability
   - Consider volume requirements
   - Consider price range implications

2. How can we identify periods of increased probability for successful trades?
   - What market conditions signal higher probability setups?
   - What conditions should make us more conservative?
   - How can we validate these conditions programmatically?

## Strategy Development
1. How can we maximize the effectiveness of small capital?
   - What position sizing strategy minimizes risk while maintaining profit potential?
   - How many concurrent positions can we realistically manage?
   - What's the optimal trade frequency given our constraints?

2. What combination of indicators would be most effective?
   - Which indicators work best for altcoin volatility?
   - How can we reduce false signals?
   - How can we confirm trend direction reliably?

3. How should we handle position sizing?
   - What percentage of capital per trade is optimal?
   - How should position size change as capital grows/shrinks?
   - How do we handle the $10 minimum order size constraint?

## Risk Management
1. How can we protect against volatile price swings?
   - What stop-loss strategy minimizes unnecessary exits?
   - What take-profit strategy maximizes gains while ensuring profits are taken?
   - How can we use ATR or other volatility measures effectively?

2. What risk-reward ratio should we target?
   - How does the ratio affect our required win rate?
   - How can we ensure the ratio is realistic given altcoin volatility?
   - What minimum win rate do we need for profitability?

## Implementation Considerations
1. How do we handle partial fills and minimum order sizes?
   - What's the best order type to use (market vs limit)?
   - How do we ensure orders meet minimum size requirements?
   - How do we handle slippage?

2. How do we minimize the impact of fees?
   - What's the minimum profit target needed to overcome fees?
   - Should we use BNB for fee reduction?
   - How does fee structure affect our trading frequency?

# Success Criteria
A successful solution should demonstrate:
1. Positive returns in backtesting (minimum 5% monthly)
2. Win rate above 45%
3. Maximum drawdown under 15%
4. Average profit per trade > 3x average loss
5. Trading frequency that keeps fees under 5% of profits
6. Realistic handling of minimum order sizes
7. Clear entry/exit rules that can be programmatically implemented
8. Proper risk management suitable for small capital

# Required Output
Please provide:
1. Detailed strategy logic with clear entry/exit rules
2. Complete risk management framework
3. Position sizing formula that handles the $10 minimum
4. Specific indicator parameters and their rationale
5. Backtesting results showing:
   - Total return
   - Win rate
   - Average profit/loss per trade
   - Maximum drawdown
   - Total fees
   - Number of trades
6. Python code implementation of key strategy components
7. Explanation of how the strategy handles different market conditions

Focus on developing a conservative strategy that prioritizes capital preservation while still allowing for growth. The strategy should be specifically optimized for small capital trading during alt season. 