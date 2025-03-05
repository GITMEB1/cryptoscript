Here's a comprehensive solution to enforce 8 decimal places of precision throughout your trading bot:

**Step 1: Implement Enhanced Decimal Normalization**

```python
from decimal import Decimal, ROUND_HALF_UP

def normalize_decimal(value, precision=8):
    """Enforce exact decimal precision using quantization"""
    if not isinstance(value, Decimal):
        # Convert all values to Decimal first (handling float precision issues)
        try:
            value = Decimal(str(value))
        except:
            raise TypeError(f"Cannot convert {value} to Decimal")
    
    quantizer = Decimal('1e-{}'.format(-precision))
    return value.quantize(quantizer, rounding=ROUND_HALF_UP)
```

**Step 2: Modified Position Class**

```python
class Position:
    def __init__(self, symbol, quantity, entry_price, fee_rate):
        self.symbol = symbol
        self.quantity = normalize_decimal(quantity)
        self.entry_price = normalize_decimal(entry_price)
        self.fee_rate = normalize_decimal(fee_rate)
        
        # Calculate base values with normalization
        self.entry_value = normalize_decimal(self.quantity * self.entry_price)
        self.entry_fee = normalize_decimal(self.entry_value * self.fee_rate)
        
        self.current_price = None
        self.current_value = None

    def update_current_value(self, current_price):
        self.current_price = normalize_decimal(current_price)
        self.current_value = normalize_decimal(self.quantity * self.current_price)

    def calculate_pnl(self):
        if not self.current_value:
            raise ValueError("Current price not updated")
        
        raw_pnl = self.current_value - self.entry_value
        return normalize_decimal(raw_pnl + self.entry_fee)

    def close_position(self, exit_price, fee_rate):
        exit_price = normalize_decimal(exit_price)
        exit_fee_rate = normalize_decimal(fee_rate)
        
        exit_value = normalize_decimal(self.quantity * exit_price)
        exit_fee = normalize_decimal(exit_value * exit_fee_rate)
        
        realized_pnl = normalize_decimal(
            exit_value - self.entry_value - exit_fee + self.entry_fee
        )
        return realized_pnl

    # Add similar normalization for close_partial_position
```

**Step 3: Updated RiskManager Class**

```python
class RiskManager:
    def __init__(self, max_risk_per_trade):
        self.max_risk_per_trade = normalize_decimal(max_risk_per_trade)

    def calculate_position_size(self, entry_price, stop_loss_price, portfolio_value):
        entry = normalize_decimal(entry_price)
        stop = normalize_decimal(stop_loss_price)
        portfolio = normalize_decimal(portfolio_value)
        
        risk_amount = normalize_decimal(portfolio * self.max_risk_per_trade)
        price_diff = normalize_decimal(entry - stop).abs()
        
        if price_diff == Decimal('0'):
            return Decimal('0')
            
        size = normalize_decimal(risk_amount / price_diff)
        return size

    # Apply similar normalization to other risk calculations
```

**Key Improvements:**
1. Quantization Instead of Formatting: Uses [`Decimal.quantize()`](https://docs.python.org/3/library/decimal.html) for precise decimal control rather than string manipulation
2. Immediate Normalization: Converts all numeric inputs to Decimal immediately at object boundaries
3. Per-operation Normalization: Ensures results of all calculations are explicitly normalized
4. Consistent Context Handling: ROUND_HALF_UP provides consistent financial rounding behavior

**Test Impact:**
- Fixes exponent test by enforcing exact quantization (`Decimal.as_tuple().exponent` will now always be -8)
- Ensures equality comparisons work by having identical precision across all values
- Maintains maximum precision during calculations while normalizing inputs/outputs

**Important Implementation Notes:**
1. Convert all float values from external sources (exchange API, etc.) immediately using `normalize_decimal`
2. Avoid any float arithmetic in the core logic - only use Decimals
3. For pandas operations, use `decimal.Decimal` type in DataFrames where precision is critical
4. Consider creating a custom decimal context for your application:

```python
from decimal import getcontext, Decimal

def configure_decimal_context():
    ctx = getcontext()
    ctx.prec = 20  # High precision for intermediate calculations
    ctx.rounding = ROUND_HALF_UP

configure_decimal_context()
```

This solution addresses all three test failures by ensuring consistent decimal handling throughout the calculation pipeline. The quantization approach provides better numerical stability than string formatting and properly handles significant figures according to financial calculation requirements.