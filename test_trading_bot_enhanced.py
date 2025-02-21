import pytest
from decimal import Decimal, getcontext
from crypto_trading_bot import Position, RiskManager, TradingBot

# Set precision for all decimal calculations
getcontext().prec = 8

@pytest.fixture
def risk_manager():
    """Fixture for RiskManager instance"""
    return RiskManager()

@pytest.fixture
def position_params():
    """Fixture for common position parameters"""
    return {
        'pair': 'BTC/USDT',
        'entry_price': Decimal('100'),
        'usdt_size': Decimal('1000'),
        'fee_rate': Decimal('0.00075')
    }

@pytest.fixture
def position(position_params):
    """Fixture for Position instance"""
    return Position(**position_params)

class TestPositionPrecision:
    """Tests for position calculations precision"""
    
    @pytest.mark.parametrize("price,size,fee,expected_precision", [
        ('1234.56789', '123.45678', '0.00075', 7),  # Adjusted precision expectation
        ('100000.00', '10000.00', '0.00075', 7),
        ('0.12345678', '100.00', '0.00075', 7)
    ])
    def test_decimal_precision(self, price, size, fee, expected_precision):
        """Test precision in calculations with different values"""
        pos = Position('BTC/USDT', Decimal(price), Decimal(size), Decimal(fee))
        
        # Verify precision in calculations
        assert pos.entry_fee.as_tuple().exponent <= -expected_precision
        assert pos.quantity.as_tuple().exponent <= -expected_precision

class TestPositionValidation:
    """Tests for position validation rules"""
    
    @pytest.mark.parametrize("size,min_size,expected_valid", [
        (Decimal('9.99'), Decimal('10.0'), False),
        (Decimal('10.0'), Decimal('10.0'), True),
        (Decimal('100.0'), Decimal('10.0'), True)
    ])
    def test_minimum_order_size(self, position_params, size, min_size, expected_valid):
        """Test minimum order size validation"""
        position_params['usdt_size'] = size
        pos = Position(**position_params)
        assert pos.is_valid() == expected_valid

class TestRiskManagement:
    """Tests for risk management calculations"""
    
    @pytest.mark.parametrize("balance,volatility,expected_relation", [
        (Decimal('1000'), (Decimal('0.01'), Decimal('0.10')), 'larger'),
        (Decimal('100'), (Decimal('0.05'), Decimal('0.20')), 'larger'),
        (Decimal('10000'), (Decimal('0.02'), Decimal('0.15')), 'larger')
    ])
    def test_dynamic_position_sizing(self, risk_manager, balance, volatility, expected_relation):
        """Test position sizing adapts to volatility"""
        low_vol, high_vol = volatility
        price = Decimal('100')
        
        # Convert to string first to maintain precision
        low_vol_size = Decimal(str(risk_manager.compute_position_size(
            str(balance), str(price), str(low_vol)
        )))
        high_vol_size = Decimal(str(risk_manager.compute_position_size(
            str(balance), str(price), str(high_vol)
        )))
        
        if expected_relation == 'larger':
            assert low_vol_size > high_vol_size, f"Expected {low_vol_size} > {high_vol_size}"

    @pytest.mark.parametrize("daily_pnl_pct,initial_balance,can_trade", [
        (Decimal('-0.01'), Decimal('1000'), True),   # 1% loss
        (Decimal('-0.02'), Decimal('1000'), False),  # 2% loss (limit)
        (Decimal('-0.03'), Decimal('1000'), False),  # 3% loss
        (Decimal('0.01'), Decimal('1000'), True)     # 1% profit
    ])
    def test_daily_loss_limit(self, risk_manager, daily_pnl_pct, initial_balance, can_trade):
        """Test daily loss limit enforcement"""
        daily_pnl = initial_balance * daily_pnl_pct
        assert risk_manager.can_trade(daily_pnl, initial_balance) == can_trade

    def test_market_gap_handling(self, risk_manager, position_params):
       """Test handling of large price gaps"""
       position = Position(**position_params)
       
       # Set initial stop loss
       stop_levels = risk_manager.calculate_stop_levels(
           float(position.entry_price),
           float(position.entry_price * Decimal('0.02'))  # 2% ATR
       )
       position.current_stop = Decimal(str(stop_levels['stop_loss']))
       
       # Initial position value
       initial_value = position.update_current_value(Decimal('100'))
       assert Decimal(str(initial_value['unrealized_pnl'])) >= -position.entry_fee
       
       # Simulate price gap (30% drop)
       gap_price = Decimal('70')
       gap_result = position.update_current_value(gap_price)
       
       # Verify significant loss beyond stop loss
       assert gap_price < position.current_stop
       assert Decimal(str(gap_result['unrealized_pnl'])) < -position.entry_cost * Decimal('0.25')

    def test_volatility_position_sizing(self, risk_manager):
       """Test position sizing during high volatility"""
       balance = Decimal('1000')
       price = Decimal('100')
       
       # Test with different volatility levels
       normal_vol = Decimal('0.02')  # 2% volatility
       high_vol = Decimal('0.08')    # 8% volatility
       
       normal_size = Decimal(str(risk_manager.compute_position_size(
           float(balance), float(price), float(normal_vol)
       )))
       
       high_size = Decimal(str(risk_manager.compute_position_size(
           float(balance), float(price), float(high_vol)
       )))
       
       # Verify position size reduction in high volatility
       assert high_size < normal_size
       assert high_size <= normal_size * Decimal('0.6')  # At least 40% smaller

class TestPortfolioIntegration:
    """Integration tests for portfolio management"""
    
    @pytest.fixture
    def trading_bot(self):
        """Fixture for TradingBot instance"""
        pairs = ['ETH/USDT', 'BNB/USDT']
        return TradingBot(pairs, 1000)
    
    def test_portfolio_allocation(self, trading_bot):
        """Test portfolio allocation limits"""
        # Open positions up to limit
        eth_entry = Decimal('2000')
        bnb_entry = Decimal('200')
        allocation = Decimal('0.2')  # 20% each
        
        # Add positions
        trading_bot.positions['ETH/USDT'] = Position(
            'ETH/USDT', eth_entry,
            trading_bot.initial_balance * allocation,
            Decimal('0.00075')
        )
        trading_bot.positions['BNB/USDT'] = Position(
            'BNB/USDT', bnb_entry,
            trading_bot.initial_balance * allocation,
            Decimal('0.00075')
        )
        
        # Verify total exposure
        total_exposure = sum(pos.usdt_size for pos in trading_bot.positions.values())
        assert total_exposure <= trading_bot.initial_balance * trading_bot.risk_manager.max_portfolio_allocation
    
    def test_trade_lifecycle(self, trading_bot):
        """Test complete trade lifecycle"""
        # Initial state
        assert trading_bot.balance == trading_bot.initial_balance
        assert len(trading_bot.positions) == 0
        
        # Open position
        eth_entry = Decimal('2000')
        eth_size = Decimal('200')
        
        trading_bot.positions['ETH/USDT'] = Position(
            'ETH/USDT', eth_entry, eth_size, Decimal('0.00075')
        )
        trading_bot.balance -= eth_size
        
        # Verify position state
        assert len(trading_bot.positions) == 1
        assert trading_bot.balance < trading_bot.initial_balance
        
        # Update and close position
        new_price = eth_entry * Decimal('1.05')  # 5% increase
        position = trading_bot.positions['ETH/USDT']
        
        # Check unrealized PnL
        unrealized = position.update_current_value(new_price)
        assert Decimal(str(unrealized['unrealized_pnl'])) > 0
        
        # Close position
        realized = position.close_position(new_price)
        trading_bot.balance += Decimal(str(realized['net_value']))
        del trading_bot.positions['ETH/USDT']
        
        # Verify final state
        assert len(trading_bot.positions) == 0
        assert trading_bot.balance > trading_bot.initial_balance 