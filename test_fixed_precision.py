#!/usr/bin/env python3
"""
Test Fixed Decimal Precision
============================

This script tests the fixed Position and RiskManager classes to ensure
they correctly maintain 8 decimal places of precision.
"""

import unittest
from decimal import Decimal
from fixed_position import Position, normalize_decimal
from fixed_risk_manager import RiskManager

class TestNormalizeDecimal(unittest.TestCase):
    def test_normalize_maintains_8_decimal_places(self):
        """Test that normalize_decimal maintains exactly 8 decimal places"""
        test_values = [
            123.45678901234,
            "123.45678901234",
            Decimal("123.45678901234"),
            0.00000001,
            12345.0
        ]
        
        for value in test_values:
            normalized = normalize_decimal(value)
            self.assertEqual(normalized.as_tuple().exponent, -8, 
                            f"Value {value} normalized to {normalized} should have exponent -8")
    
    def test_rounding_behavior(self):
        """Test that rounding behavior is consistent with ROUND_HALF_UP"""
        test_cases = [
            ("1.234567895", "1.23456790"),  # Round up (5 and above)
            ("1.234567894", "1.23456789"),  # Round down (4 and below)
        ]
        
        for value, expected in test_cases:
            normalized = normalize_decimal(value)
            self.assertEqual(str(normalized), expected, 
                            f"Value {value} should round to {expected}")


class TestPosition(unittest.TestCase):
    def setUp(self):
        """Set up test position"""
        self.pair = "BTC/USDT"
        self.entry_price = Decimal("40000")
        self.usdt_size = Decimal("1000")
        self.fee_rate = Decimal("0.001")
        self.position = Position(self.pair, self.entry_price, self.usdt_size, self.fee_rate)
    
    def test_position_initialization(self):
        """Test that position initialization maintains 8 decimal places"""
        self.assertEqual(self.position.entry_price.as_tuple().exponent, -8)
        self.assertEqual(self.position.usdt_size.as_tuple().exponent, -8)
        self.assertEqual(self.position.fee_rate.as_tuple().exponent, -8)
        self.assertEqual(self.position.entry_fee.as_tuple().exponent, -8)
        
        # Check that calculations are correct
        expected_fee = normalize_decimal(self.usdt_size * self.fee_rate)
        self.assertEqual(self.position.entry_fee, expected_fee)
    
    def test_close_position(self):
        """Test that close_position maintains 8 decimal places"""
        exit_price = Decimal("44000")  # 10% price increase
        result = self.position.close_position(exit_price)
        
        # Test that all returned values have 8 decimal places
        for key, value in result.items():
            self.assertEqual(value.as_tuple().exponent, -8, 
                            f"{key} should have 8 decimal places, got {value}")
        
        # Calculate expected values
        quantity = normalize_decimal((self.usdt_size - self.position.entry_fee) / self.entry_price)
        gross_value = normalize_decimal(quantity * exit_price)
        exit_fee = normalize_decimal(gross_value * self.fee_rate)
        net_value = normalize_decimal(gross_value - exit_fee)
        
        # Compare with calculated values
        self.assertEqual(result['gross_value'], gross_value)
        self.assertEqual(result['net_value'], net_value)


class TestRiskManager(unittest.TestCase):
    def setUp(self):
        """Set up risk manager"""
        self.account_balance = Decimal("10000")
        self.risk_manager = RiskManager(self.account_balance, 0.01, 0.05)
    
    def test_position_size_calculation(self):
        """Test that position size calculation maintains 8 decimal places"""
        entry_price = Decimal("40000")
        stop_loss = Decimal("38000")
        
        position_size = self.risk_manager.calculate_position_size(
            entry_price, stop_loss, 0.001
        )
        
        # Test that position size has 8 decimal places
        self.assertEqual(position_size.as_tuple().exponent, -8)
        
        # Test that calculations are reasonable
        risk_amount = normalize_decimal(self.account_balance * Decimal("0.01"))
        self.assertLess(position_size, risk_amount)
    
    def test_stop_levels(self):
        """Test that stop level calculations maintain 8 decimal places"""
        entry_price = Decimal("40000")
        atr = Decimal("2000")
        
        levels = self.risk_manager.calculate_stop_levels(entry_price, atr, 'long')
        
        # Test that all returned values have 8 decimal places
        for key, value in levels.items():
            self.assertEqual(value.as_tuple().exponent, -8, 
                            f"{key} should have 8 decimal places, got {value}")


if __name__ == "__main__":
    unittest.main() 