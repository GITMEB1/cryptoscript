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

class Position:
    """Tracks a single position with precise calculations"""
    def __init__(self, pair, entry_price, usdt_size, fee_rate):
        """Initialize a new position with proper decimal precision"""
        self.pair = pair
        
        # Convert all inputs to normalized Decimals immediately
        self.entry_price = normalize_decimal(entry_price)
        self.usdt_size = normalize_decimal(usdt_size)
        self.fee_rate = normalize_decimal(fee_rate)
        
        # Calculate entry details with normalization at each step
        self.entry_fee = normalize_decimal(self.usdt_size * self.fee_rate)
        self.quantity = normalize_decimal((self.usdt_size - self.entry_fee) / self.entry_price)
        self.entry_cost = self.usdt_size  # This is already normalized

        # Initialize other attributes
        self.atr = normalize_decimal(0)
        self.current_stop = None
        self.stop_loss = None
        self.take_profit = None
        self.trailing_stop = None
        self.trailing_activation = None

    def is_valid(self):
        """Check if position meets minimum requirements"""
        min_order_size = normalize_decimal(10.0)  # Minimum order size in USDT
        return self.usdt_size >= min_order_size

    def update_current_value(self, current_price):
        """Calculate current position value and unrealized PnL"""
        # Normalize the current price
        current_price = normalize_decimal(current_price)
        
        # Calculate with normalization at each step
        gross_value = normalize_decimal(self.quantity * current_price)
        exit_fee = normalize_decimal(gross_value * self.fee_rate)
        net_value = normalize_decimal(gross_value - exit_fee)
        unrealized_pnl = normalize_decimal(net_value - self.entry_cost)
        total_fees = normalize_decimal(self.entry_fee + exit_fee)

        return {
            'gross_value': gross_value,
            'net_value': net_value,
            'unrealized_pnl': unrealized_pnl,
            'exit_fee': exit_fee,
            'total_fees': total_fees
        }

    def close_position(self, exit_price):
        """Calculate final position value and realized PnL"""
        # Normalize the exit price
        exit_price = normalize_decimal(exit_price)
        
        # Calculate with normalization at each step
        gross_value = normalize_decimal(self.quantity * exit_price)
        exit_fee = normalize_decimal(gross_value * self.fee_rate)
        net_value = normalize_decimal(gross_value - exit_fee)
        realized_pnl = normalize_decimal(net_value - self.entry_cost)
        total_fees = normalize_decimal(self.entry_fee + exit_fee)

        return {
            'gross_value': gross_value,
            'net_value': net_value,
            'realized_pnl': realized_pnl,
            'exit_fee': exit_fee,
            'total_fees': total_fees
        }

    def close_partial_position(self, exit_price, close_ratio):
        """Close a portion of the position"""
        # Normalize inputs
        exit_price = normalize_decimal(exit_price)
        close_ratio = normalize_decimal(close_ratio)
        
        # Validate close ratio
        zero = normalize_decimal(0)
        one = normalize_decimal(1)
        if not (zero < close_ratio <= one):
            raise ValueError("Close ratio must be between 0 and 1")

        # Calculate with normalization at each step
        close_quantity = normalize_decimal(self.quantity * close_ratio)
        remaining_quantity = normalize_decimal(self.quantity - close_quantity)
        gross_value = normalize_decimal(close_quantity * exit_price)
        exit_fee = normalize_decimal(gross_value * self.fee_rate)
        net_value = normalize_decimal(gross_value - exit_fee)
        
        # Update position values
        self.quantity = remaining_quantity
        self.entry_cost = normalize_decimal(self.entry_cost * (one - close_ratio))
        self.entry_fee = normalize_decimal(self.entry_fee * (one - close_ratio))

        return {
            'gross_value': gross_value,
            'net_value': net_value,
            'exit_fee': exit_fee,
            'remaining_quantity': remaining_quantity
        } 