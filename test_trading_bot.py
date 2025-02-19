import unittest
from decimal import Decimal
from crypto_trading_bot import Position, RiskManager, TradingBot

class TestPosition(unittest.TestCase):
    def setUp(self):
        """Set up test cases with common values"""
        self.fee_rate = Decimal('0.00075')  # 0.075% with BNB
        self.entry_price = Decimal('100')
        self.usdt_size = Decimal('1000')
        self.position = Position('BTC/USDT', self.entry_price, self.usdt_size, self.fee_rate)

    def test_position_initialization(self):
        """Test position initialization with proper fee handling"""
        # Calculate expected values
        expected_entry_fee = self.usdt_size * self.fee_rate
        expected_net_usdt = self.usdt_size - expected_entry_fee
        expected_quantity = expected_net_usdt / self.entry_price

        self.assertEqual(self.position.entry_price, self.entry_price)
        self.assertEqual(self.position.usdt_size, self.usdt_size)
        self.assertEqual(self.position.fee_rate, self.fee_rate)
        self.assertEqual(self.position.entry_fee, expected_entry_fee)
        self.assertEqual(self.position.quantity, expected_quantity)

    def test_current_value_calculation(self):
        """Test unrealized PnL calculation with fees"""
        current_price = Decimal('110')  # 10% price increase
        result = self.position.update_current_value(current_price)

        # Calculate expected values
        gross_value = self.position.quantity * current_price
        exit_fee = gross_value * self.fee_rate
        expected_net_value = gross_value - exit_fee
        expected_unrealized_pnl = expected_net_value - self.position.entry_cost

        self.assertEqual(Decimal(str(result['gross_value'])), gross_value)
        self.assertEqual(Decimal(str(result['net_value'])), expected_net_value)
        self.assertEqual(Decimal(str(result['unrealized_pnl'])), expected_unrealized_pnl)

    def test_close_position(self):
        """Test realized PnL calculation with fees at both entry and exit"""
        exit_price = Decimal('120')  # 20% price increase
        result = self.position.close_position(exit_price)

        # Calculate expected values
        gross_value = self.position.quantity * exit_price
        exit_fee = gross_value * self.fee_rate
        expected_net_value = gross_value - exit_fee
        expected_realized_pnl = expected_net_value - self.position.entry_cost
        expected_total_fees = self.position.entry_fee + exit_fee

        self.assertEqual(Decimal(str(result['gross_value'])), gross_value)
        self.assertEqual(Decimal(str(result['net_value'])), expected_net_value)
        self.assertEqual(Decimal(str(result['realized_pnl'])), expected_realized_pnl)
        self.assertEqual(Decimal(str(result['total_fees'])), expected_total_fees)

    def test_minimum_order_size(self):
        """Test position creation with minimum order size validation"""
        min_order = Decimal('10.0')  # $10 minimum order
        small_position = Position('BTC/USDT', self.entry_price, min_order/2, self.fee_rate)
        self.assertFalse(small_position.is_valid())
        
        valid_position = Position('BTC/USDT', self.entry_price, min_order*2, self.fee_rate)
        self.assertTrue(valid_position.is_valid())

    def test_decimal_precision(self):
        """Test decimal precision handling in calculations"""
        # Test with more complex decimal values
        entry_price = Decimal('1234.56789')
        usdt_size = Decimal('123.45678')
        fee_rate = Decimal('0.00075')
        
        position = Position('BTC/USDT', entry_price, usdt_size, fee_rate)
        
        # Verify precision in calculations
        expected_fee = usdt_size * fee_rate
        expected_quantity = (usdt_size - expected_fee) / entry_price
        
        self.assertEqual(position.entry_fee.as_tuple().exponent, -8)  # 8 decimal places
        self.assertEqual(position.quantity.as_tuple().exponent, -8)
        self.assertEqual(position.entry_fee, expected_fee)
        self.assertEqual(position.quantity, expected_quantity)

class TestRiskManager(unittest.TestCase):
    def setUp(self):
        """Set up test cases with common values"""
        self.risk_manager = RiskManager()

    def test_position_size_calculation(self):
        """Test ATR-based position sizing with proper constraints"""
        balance = Decimal('1000')
        current_price = Decimal('100')
        atr = Decimal('5')  # 5% ATR

        position_size = self.risk_manager.compute_position_size(
            float(balance), float(current_price), float(atr)
        )

        # Verify position size is within limits
        self.assertLessEqual(Decimal(str(position_size)), balance * self.risk_manager.max_position_size)
        self.assertGreaterEqual(Decimal(str(position_size)), self.risk_manager.min_trade_amount)

    def test_stop_levels_calculation(self):
        """Test ATR-based stop loss and take profit calculations"""
        entry_price = Decimal('100')
        atr = Decimal('5')

        levels = self.risk_manager.calculate_stop_levels(float(entry_price), float(atr))

        # Verify stop levels are properly calculated
        expected_sl = entry_price - (self.risk_manager.atr_sl_mult * atr)
        expected_tp = entry_price + (self.risk_manager.atr_tp_mult * atr)
        expected_trail = entry_price + (self.risk_manager.atr_trail_mult * atr)

        self.assertEqual(Decimal(str(levels['stop_loss'])), expected_sl)
        self.assertEqual(Decimal(str(levels['take_profit'])), expected_tp)
        self.assertEqual(Decimal(str(levels['trailing_activation'])), expected_trail)

    def test_trailing_stop_update(self):
        """Test trailing stop updates based on price movement"""
        entry_price = Decimal('100')
        atr = Decimal('5')
        current_price = Decimal('110')

        # Create a position for testing
        position = Position('BTC/USDT', entry_price, Decimal('1000'), Decimal('0.00075'))
        position.atr = atr
        position.trailing_activation = entry_price + (self.risk_manager.atr_trail_mult * atr)
        position.current_stop = entry_price - (self.risk_manager.atr_sl_mult * atr)

        # Test trailing stop update
        new_stop = self.risk_manager.update_trailing_stop(position, float(current_price))
        
        # Verify trailing stop is updated correctly when price moves above activation
        if current_price >= position.trailing_activation:
            expected_new_stop = current_price - position.atr
            self.assertEqual(Decimal(str(new_stop)), expected_new_stop)
        else:
            self.assertEqual(new_stop, position.current_stop)

    def test_daily_loss_limit(self):
        """Test daily loss limit enforcement"""
        initial_balance = Decimal('1000')
        daily_loss_limit = Decimal('0.02')  # 2% daily loss limit
        
        # Simulate trades reaching daily loss limit
        balance = initial_balance
        daily_pnl = Decimal('0')
        
        # First trade - small loss
        trade_loss = initial_balance * Decimal('0.01')  # 1% loss
        daily_pnl -= trade_loss
        balance -= trade_loss
        
        # Should allow trading
        self.assertTrue(self.risk_manager.can_trade(daily_pnl, initial_balance))
        
        # Second trade - reaches limit
        trade_loss = initial_balance * Decimal('0.01')  # Another 1% loss
        daily_pnl -= trade_loss
        balance -= trade_loss
        
        # Should prevent trading
        self.assertFalse(self.risk_manager.can_trade(daily_pnl, initial_balance))

    def test_dynamic_position_sizing(self):
        """Test dynamic position sizing based on volatility"""
        balance = Decimal('1000')
        price = Decimal('100')
        
        # Test with different volatility scenarios
        low_atr = Decimal('1')  # 1% volatility
        high_atr = Decimal('10')  # 10% volatility
        
        low_vol_size = self.risk_manager.compute_position_size(
            float(balance), float(price), float(low_atr)
        )
        high_vol_size = self.risk_manager.compute_position_size(
            float(balance), float(price), float(high_atr)
        )
        
        # Higher volatility should result in smaller position size
        self.assertGreater(Decimal(str(low_vol_size)), Decimal(str(high_vol_size)))

class TestTradingBot(unittest.TestCase):
    """Integration tests for the TradingBot class"""
    
    def setUp(self):
        """Set up test cases with common values"""
        self.trading_pairs = ['ETH/USDT', 'BNB/USDT']
        self.initial_balance = Decimal('1000')
        self.bot = TradingBot(self.trading_pairs, float(self.initial_balance))
    
    def test_portfolio_risk_management(self):
        """Test portfolio-level risk management"""
        # Simulate multiple positions
        eth_entry = Decimal('2000')
        bnb_entry = Decimal('200')
        
        # Open positions
        self.bot.positions['ETH/USDT'] = Position(
            'ETH/USDT', eth_entry, 
            self.initial_balance * Decimal('0.2'),  # 20% allocation
            Decimal('0.00075')
        )
        self.bot.positions['BNB/USDT'] = Position(
            'BNB/USDT', bnb_entry,
            self.initial_balance * Decimal('0.2'),  # 20% allocation
            Decimal('0.00075')
        )
        
        # Verify total exposure
        total_exposure = sum(pos.usdt_size for pos in self.bot.positions.values())
        self.assertLessEqual(
            total_exposure,
            self.initial_balance * self.bot.risk_manager.max_portfolio_allocation
        )
    
    def test_complete_trade_lifecycle(self):
        """Test complete trade lifecycle with multiple positions"""
        # Initial state
        self.assertEqual(self.bot.balance, self.initial_balance)
        self.assertEqual(len(self.bot.positions), 0)
        
        # Open first position
        eth_entry = Decimal('2000')
        eth_size = Decimal('200')  # $200 position
        self.bot.positions['ETH/USDT'] = Position(
            'ETH/USDT', eth_entry, eth_size, Decimal('0.00075')
        )
        self.bot.balance -= eth_size
        
        # Verify position opened correctly
        self.assertEqual(len(self.bot.positions), 1)
        self.assertLess(self.bot.balance, self.initial_balance)
        
        # Update position value
        new_eth_price = Decimal('2100')  # 5% increase
        result = self.bot.positions['ETH/USDT'].update_current_value(new_eth_price)
        
        # Verify unrealized PnL
        self.assertGreater(Decimal(str(result['unrealized_pnl'])), 0)
        
        # Close position
        close_result = self.bot.positions['ETH/USDT'].close_position(new_eth_price)
        self.bot.balance += Decimal(str(close_result['net_value']))
        del self.bot.positions['ETH/USDT']
        
        # Verify final state
        self.assertEqual(len(self.bot.positions), 0)
        self.assertGreater(self.bot.balance, self.initial_balance)  # Profitable trade

if __name__ == '__main__':
    unittest.main() 