from decimal import Decimal, localcontext

def normalize_decimal(value, force_precision=8):
    """Helper function to normalize decimal values with forced precision"""
    if isinstance(value, (int, float, str)):
        value = Decimal(str(value))
    if force_precision is not None:
        # Create a context with higher precision for intermediate calculations
        with localcontext() as ctx:
            ctx.prec = 28  # High precision for intermediate calculations
            # Format string with exact number of decimal places
            format_str = f'{{:.{force_precision}f}}'
            # Convert through string to ensure exact decimal places
            return Decimal(format_str.format(value))
    return value.normalize()

class Position:
    """Tracks a single position with precise calculations"""
    def __init__(self, pair, entry_price, usdt_size, fee_rate):
        """Initialize a new position with proper decimal precision"""
        self.pair = pair
        
        # Store original values for exact calculations
        self._entry_price_raw = Decimal(str(entry_price))
        self._usdt_size_raw = Decimal(str(usdt_size))
        self._fee_rate_raw = Decimal(str(fee_rate))
        
        # Calculate entry details with exact precision
        with localcontext() as ctx:
            ctx.prec = 28  # High precision for intermediate calculations
            self._entry_fee_raw = self._usdt_size_raw * self._fee_rate_raw
            self._quantity_raw = (self._usdt_size_raw - self._entry_fee_raw) / self._entry_price_raw
        
        # Store normalized values for display and consistency
        self.entry_price = self._entry_price_raw
        self.usdt_size = self._usdt_size_raw
        self.fee_rate = self._fee_rate_raw
        self.entry_fee = self._entry_fee_raw
        self.quantity = self._quantity_raw
        self.entry_cost = self._usdt_size_raw

        # Initialize other attributes
        self.atr = Decimal('0')
        self.current_stop = None
        self.stop_loss = None
        self.take_profit = None
        self.trailing_stop = None
        self.trailing_activation = None

    def is_valid(self):
        """Check if position meets minimum requirements"""
        min_order_size = Decimal('10.0')  # Minimum order size in USDT
        return self.usdt_size >= min_order_size

    def update_current_value(self, current_price):
        """Calculate current position value and unrealized PnL"""
        # Store raw value for exact calculations
        _current_price_raw = Decimal(str(current_price))
        
        # Calculate with exact precision
        with localcontext() as ctx:
            ctx.prec = 28  # High precision for intermediate calculations
            _gross_value_raw = self.quantity * _current_price_raw
            _exit_fee_raw = _gross_value_raw * self.fee_rate
            _net_value_raw = _gross_value_raw - _exit_fee_raw
            _unrealized_pnl_raw = _net_value_raw - self.entry_cost
            _total_fees_raw = self.entry_fee + _exit_fee_raw

        return {
            'gross_value': _gross_value_raw,
            'net_value': _net_value_raw,
            'unrealized_pnl': _unrealized_pnl_raw,
            'exit_fee': _exit_fee_raw,
            'total_fees': _total_fees_raw
        }

    def close_position(self, exit_price):
        """Calculate final position value and realized PnL"""
        # Store raw value for exact calculations
        _exit_price_raw = Decimal(str(exit_price))
        
        # Calculate with exact precision
        with localcontext() as ctx:
            ctx.prec = 28  # High precision for intermediate calculations
            _gross_value_raw = self.quantity * _exit_price_raw
            _exit_fee_raw = _gross_value_raw * self.fee_rate
            _net_value_raw = _gross_value_raw - _exit_fee_raw
            _realized_pnl_raw = _net_value_raw - self.entry_cost
            _total_fees_raw = self.entry_fee + _exit_fee_raw

        return {
            'gross_value': _gross_value_raw,
            'net_value': _net_value_raw,
            'realized_pnl': _realized_pnl_raw,
            'exit_fee': _exit_fee_raw,
            'total_fees': _total_fees_raw
        }

    def close_partial_position(self, exit_price, close_ratio):
        """Close a portion of the position"""
        # Store raw values for exact calculations
        _exit_price_raw = Decimal(str(exit_price))
        _close_ratio_raw = Decimal(str(close_ratio))
        
        if not Decimal('0') < _close_ratio_raw <= Decimal('1'):
            raise ValueError("Close ratio must be between 0 and 1")

        # Calculate with exact precision
        with localcontext() as ctx:
            ctx.prec = 28  # High precision for intermediate calculations
            _close_quantity_raw = self.quantity * _close_ratio_raw
            _remaining_quantity_raw = self.quantity - _close_quantity_raw
            _gross_value_raw = _close_quantity_raw * _exit_price_raw
            _exit_fee_raw = _gross_value_raw * self.fee_rate
            _net_value_raw = _gross_value_raw - _exit_fee_raw
        
        # Update values
        self.quantity = _remaining_quantity_raw
        self.entry_cost = self.entry_cost * (Decimal('1') - _close_ratio_raw)
        self.entry_fee = self.entry_fee * (Decimal('1') - _close_ratio_raw)

        return {
            'gross_value': _gross_value_raw,
            'net_value': _net_value_raw,
            'exit_fee': _exit_fee_raw,
            'remaining_quantity': _remaining_quantity_raw
        } 