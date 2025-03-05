#!/usr/bin/env python3
"""
Test script to verify our fixes for the Position and RiskManager classes
"""
from decimal import Decimal
from fix_position import Position
from fix_risk_manager import RiskManager

def test_position():
    """Test the Position class"""
    print("Testing Position class...")
    
    # Test with the values from the test_decimal_precision test
    entry_price = Decimal('1234.56789')
    usdt_size = Decimal('123.45678')
    fee_rate = Decimal('0.00075')

    position = Position('BTC/USDT', entry_price, usdt_size, fee_rate)
    
    # Verify precision in calculations
    expected_fee = usdt_size * fee_rate
    expected_quantity = (usdt_size - expected_fee) / entry_price
    
    print(f"Entry fee: {position.entry_fee} (expected: {expected_fee})")
    print(f"Quantity: {position.quantity} (expected: {expected_quantity})")
    print(f"Entry fee exponent: {position.entry_fee.as_tuple().exponent}")
    print(f"Quantity exponent: {position.quantity.as_tuple().exponent}")
    
    # Test close_position
    exit_price = Decimal('1300')
    result = position.close_position(exit_price)
    
    # Calculate expected values
    gross_value = position._quantity_raw * exit_price
    exit_fee = gross_value * fee_rate
    expected_net_value = gross_value - exit_fee
    expected_realized_pnl = expected_net_value - usdt_size
    
    print(f"Gross value: {result['gross_value']} (expected: {gross_value})")
    print(f"Net value: {result['net_value']} (expected: {expected_net_value})")
    print(f"Realized PnL: {result['realized_pnl']} (expected: {expected_realized_pnl})")

def test_risk_manager():
    """Test the RiskManager class"""
    print("\nTesting RiskManager class...")
    
    risk_manager = RiskManager()
    
    # Test dynamic position sizing
    balance = Decimal('1000')
    price = Decimal('100')
    
    # Test with different volatility scenarios
    low_atr = Decimal('1')  # 1% volatility
    high_atr = Decimal('10')  # 10% volatility
    
    low_vol_size = risk_manager.compute_position_size(float(balance), float(price), float(low_atr))
    high_vol_size = risk_manager.compute_position_size(float(balance), float(price), float(high_atr))
    
    print(f"Low volatility position size: {low_vol_size}")
    print(f"High volatility position size: {high_vol_size}")
    print(f"Low > High: {Decimal(str(low_vol_size)) > Decimal(str(high_vol_size))}")
    
    # Test trailing stop update
    entry_price = Decimal('100')
    atr = Decimal('5')
    current_price = Decimal('110')
    
    # Create a position for testing
    position = Position('BTC/USDT', entry_price, Decimal('1000'), Decimal('0.00075'))
    position.atr = atr
    position.trailing_activation = entry_price + (risk_manager.atr_trail_mult * atr)
    position.current_stop = entry_price - (risk_manager.atr_sl_mult * atr)
    
    # Test trailing stop update
    new_stop = risk_manager.update_trailing_stop(position, float(current_price))
    
    print(f"Current price: {current_price}")
    print(f"Trailing activation: {position.trailing_activation}")
    print(f"New stop: {new_stop}")
    print(f"Expected new stop: {current_price - position.atr}")

if __name__ == "__main__":
    test_position()
    test_risk_manager() 