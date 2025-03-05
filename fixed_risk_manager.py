from decimal import Decimal, ROUND_HALF_UP

def normalize_decimal(value, precision=8):
    """
    Enforce exact decimal precision using quantization
    
    Args:
        value: The value to normalize (int, float, str, or Decimal)
        precision: Number of decimal places to maintain (default: 8)
        
    Returns:
        Decimal value with exactly 'precision' decimal places
    """
    if not isinstance(value, Decimal):
        # Convert all values to Decimal first (handling float precision issues)
        try:
            value = Decimal(str(value))
        except:
            raise TypeError(f"Cannot convert {value} to Decimal")
    
    # Create a quantizer with the exact number of decimal places
    quantizer = Decimal('1e-{}'.format(precision))
    return value.quantize(quantizer, rounding=ROUND_HALF_UP)

class RiskManager:
    """Manages risk for trading positions"""
    def __init__(self, account_balance, risk_per_trade=0.01, daily_loss_limit=0.05):
        """Initialize risk manager with account balance and risk parameters"""
        self.account_balance = normalize_decimal(account_balance)
        self.risk_per_trade = normalize_decimal(risk_per_trade)
        self.daily_loss_limit = normalize_decimal(daily_loss_limit)
        self.daily_loss = normalize_decimal(0)
        self.positions = []
        self.volatility_adjustment = normalize_decimal(1.0)

    def calculate_position_size(self, entry_price, stop_loss, fee_rate=0.001):
        """Calculate position size based on risk parameters and price levels"""
        # Normalize all inputs
        entry_price = normalize_decimal(entry_price)
        stop_loss = normalize_decimal(stop_loss)
        fee_rate = normalize_decimal(fee_rate)
        
        # Calculate risk amount in USDT
        risk_amount = normalize_decimal(self.account_balance * self.risk_per_trade * self.volatility_adjustment)
        
        # Calculate price difference as a percentage
        price_diff_pct = normalize_decimal(abs((entry_price - stop_loss) / entry_price))
        
        # Account for fees in both directions
        total_fee_impact = normalize_decimal(fee_rate * normalize_decimal(2))
        
        # Calculate position size with fee consideration
        position_size = normalize_decimal(risk_amount / (price_diff_pct + total_fee_impact))
        
        # Ensure position size doesn't exceed account balance
        max_position = normalize_decimal(self.account_balance * normalize_decimal(0.95))  # 95% of balance max
        position_size = normalize_decimal(min(position_size, max_position))
        
        return position_size

    def calculate_stop_levels(self, entry_price, atr, direction='long'):
        """Calculate stop loss and take profit levels based on ATR"""
        # Normalize inputs
        entry_price = normalize_decimal(entry_price)
        atr = normalize_decimal(atr)
        
        # Different multipliers for stop loss and take profit
        stop_multiplier = normalize_decimal(2.0)
        tp_multiplier = normalize_decimal(3.0)
        
        if direction.lower() == 'long':
            stop_loss = normalize_decimal(entry_price - (atr * stop_multiplier))
            take_profit = normalize_decimal(entry_price + (atr * tp_multiplier))
        else:  # short
            stop_loss = normalize_decimal(entry_price + (atr * stop_multiplier))
            take_profit = normalize_decimal(entry_price - (atr * tp_multiplier))
        
        return {
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'atr': atr
        }

    def update_trailing_stop(self, position, current_price):
        """Update trailing stop if price moves favorably"""
        current_price = normalize_decimal(current_price)
        
        # Initialize trailing stop if not set
        if position.trailing_stop is None:
            position.trailing_stop = position.stop_loss
            position.trailing_activation = normalize_decimal(position.entry_price * normalize_decimal(1.01))  # 1% above entry
            return position.trailing_stop
        
        # For long positions
        if current_price > position.entry_price:
            # Check if price has reached activation level
            if current_price >= position.trailing_activation:
                # Calculate new trailing stop
                new_stop = normalize_decimal(current_price - (position.atr * normalize_decimal(2.0)))
                
                # Only update if new stop is higher than current stop
                if new_stop > position.trailing_stop:
                    position.trailing_stop = new_stop
        
        # For short positions (not implemented in this example)
        # else:
        #     if current_price <= position.trailing_activation:
        #         new_stop = normalize_decimal(current_price + (position.atr * normalize_decimal(2.0)))
        #         if new_stop < position.trailing_stop:
        #             position.trailing_stop = new_stop
        
        return position.trailing_stop

    def check_daily_loss_limit(self, new_loss=0):
        """Check if daily loss limit has been reached"""
        new_loss = normalize_decimal(new_loss)
        self.daily_loss = normalize_decimal(self.daily_loss + new_loss)
        max_loss = normalize_decimal(self.account_balance * self.daily_loss_limit)
        
        return self.daily_loss >= max_loss

    def adjust_for_volatility(self, current_volatility, baseline_volatility):
        """Adjust position sizing based on current market volatility"""
        current_volatility = normalize_decimal(current_volatility)
        baseline_volatility = normalize_decimal(baseline_volatility)
        
        # Calculate volatility ratio
        zero = normalize_decimal(0)
        if baseline_volatility > zero:
            volatility_ratio = normalize_decimal(baseline_volatility / current_volatility)
            
            # Adjust position sizing (lower for higher volatility)
            min_adjustment = normalize_decimal(0.5)  # Min 50% of normal size
            max_adjustment = normalize_decimal(1.5)  # Max 150% of normal size
            
            self.volatility_adjustment = normalize_decimal(
                min(max(volatility_ratio, min_adjustment), max_adjustment)
            )
        else:
            self.volatility_adjustment = normalize_decimal(1.0)
        
        return self.volatility_adjustment 