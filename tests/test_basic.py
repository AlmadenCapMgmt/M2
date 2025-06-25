"""
Basic tests for Bitcoin Strategic Investment Model
"""

import pytest
import os
from unittest.mock import Mock, patch
from datetime import datetime

from bitcoin_model import BitcoinMacroModel
from bitcoin_model.models.fed_pivot import FedPivotModel
from bitcoin_model.models.m2_miner import M2MinerModel
from bitcoin_model.config.settings import Settings

class TestSettings:
    """Test configuration settings"""
    
    def test_settings_initialization(self):
        """Test that settings initialize correctly"""
        settings = Settings()
        
        assert settings.POSITION_LIMITS is not None
        assert 'conservative' in settings.POSITION_LIMITS
        assert 'moderate' in settings.POSITION_LIMITS
        assert 'aggressive' in settings.POSITION_LIMITS
        
    def test_position_limits(self):
        """Test position limit retrieval"""
        settings = Settings()
        
        conservative = settings.get_position_limits('conservative')
        assert conservative['base'] == 0.03
        assert conservative['max'] == 0.10
        
        moderate = settings.get_position_limits('moderate')
        assert moderate['base'] == 0.05
        assert moderate['max'] == 0.15
    
    def test_signal_thresholds(self):
        """Test signal threshold retrieval"""
        settings = Settings()
        
        threshold1 = settings.get_signal_threshold(1)
        threshold2 = settings.get_signal_threshold(2)
        
        assert threshold1 == 0.70
        assert threshold2 == 0.75
    
    def test_config_validation(self):
        """Test configuration validation"""
        settings = Settings()
        
        validation = settings.validate_config()
        assert validation['valid'] is True
        assert len(validation['issues']) == 0

class TestBitcoinMacroModel:
    """Test main BitcoinMacroModel class"""
    
    @pytest.fixture
    def mock_api_keys(self):
        """Mock API keys for testing"""
        return {
            'fred': 'test_fred_key',
            'glassnode': 'test_glassnode_key',
            'cryptoquant': 'test_cryptoquant_key',
            'coingecko': 'test_coingecko_key'
        }
    
    def test_model_initialization(self, mock_api_keys):
        """Test model initialization"""
        model = BitcoinMacroModel(mock_api_keys)
        
        assert model.api_keys == mock_api_keys
        assert len(model.scenarios) == 2
        assert 1 in model.scenarios
        assert 2 in model.scenarios
        assert isinstance(model.scenarios[1], FedPivotModel)
        assert isinstance(model.scenarios[2], M2MinerModel)
    
    def test_model_initialization_without_keys(self):
        """Test model initialization without API keys"""
        with patch.dict(os.environ, {
            'FRED_API_KEY': 'env_fred_key',
            'GLASSNODE_API_KEY': 'env_glassnode_key'
        }):
            model = BitcoinMacroModel()
            
            assert model.api_keys['fred'] == 'env_fred_key'
            assert model.api_keys['glassnode'] == 'env_glassnode_key'
    
    @patch('bitcoin_model.models.fed_pivot.FedPivotModel.analyze')
    def test_run_analysis_scenario_1(self, mock_analyze, mock_api_keys):
        """Test running analysis for scenario 1"""
        mock_result = {
            'scenario': 1,
            'signals': {'buy_signal': True, 'combined_score': 0.8},
            'trade_plan': {'action': 'buy'}
        }
        mock_analyze.return_value = mock_result
        
        model = BitcoinMacroModel(mock_api_keys)
        result = model.run_analysis(scenario=1, portfolio_value=100000)
        
        mock_analyze.assert_called_once_with(100000, None)
        assert result['scenario'] == 1
        assert 'timestamp' in result
        assert 'portfolio_value' in result
    
    def test_run_analysis_invalid_scenario(self, mock_api_keys):
        """Test running analysis with invalid scenario"""
        model = BitcoinMacroModel(mock_api_keys)
        
        with pytest.raises(ValueError, match="Unknown scenario"):
            model.run_analysis(scenario=99)
    
    @patch('bitcoin_model.models.fed_pivot.FedPivotModel.analyze')
    @patch('bitcoin_model.models.m2_miner.M2MinerModel.analyze')
    def test_get_all_signals(self, mock_m2_analyze, mock_fed_analyze, mock_api_keys):
        """Test getting all signals"""
        mock_fed_result = {
            'scenario': 1,
            'signals': {'buy_signal': False, 'combined_score': 0.5}
        }
        mock_m2_result = {
            'scenario': 2,
            'signals': {'buy_signal': True, 'combined_score': 0.8}
        }
        
        mock_fed_analyze.return_value = mock_fed_result
        mock_m2_analyze.return_value = mock_m2_result
        
        model = BitcoinMacroModel(mock_api_keys)
        results = model.get_all_signals(portfolio_value=100000)
        
        assert 'scenario_1' in results
        assert 'scenario_2' in results
        assert results['scenario_1']['scenario'] == 1
        assert results['scenario_2']['scenario'] == 2
    
    @patch('bitcoin_model.models.fed_pivot.FedPivotModel.analyze')
    @patch('bitcoin_model.models.m2_miner.M2MinerModel.analyze')
    def test_get_strongest_signal(self, mock_m2_analyze, mock_fed_analyze, mock_api_keys):
        """Test getting strongest signal"""
        mock_fed_result = {
            'scenario': 1,
            'signals': {'buy_signal': False, 'combined_score': 0.5}
        }
        mock_m2_result = {
            'scenario': 2,
            'signals': {'buy_signal': True, 'combined_score': 0.8}
        }
        
        mock_fed_analyze.return_value = mock_fed_result
        mock_m2_analyze.return_value = mock_m2_result
        
        model = BitcoinMacroModel(mock_api_keys)
        strongest = model.get_strongest_signal(portfolio_value=100000)
        
        assert strongest['scenario'] == 2
        assert strongest['signals']['combined_score'] == 0.8

class TestFedPivotModel:
    """Test Fed Pivot Model"""
    
    @pytest.fixture
    def mock_api_keys(self):
        return {'fred': 'test_key'}
    
    def test_fed_score_calculation(self, mock_api_keys):
        """Test Fed score calculation"""
        model = FedPivotModel(mock_api_keys)
        
        # Test low rate scenario
        fed_data_low = {
            'fed_funds_rate': 0.5,
            'pivot_detected': True,
            'pivot_direction': 'cutting',
            'pivot_magnitude': 1.0
        }
        
        score_low = model.calculate_fed_score(fed_data_low)
        assert score_low > 0.8  # Should be high for low rates + cuts
        
        # Test high rate scenario
        fed_data_high = {
            'fed_funds_rate': 6.0,
            'pivot_detected': False,
            'pivot_direction': 'neutral',
            'pivot_magnitude': 0.0
        }
        
        score_high = model.calculate_fed_score(fed_data_high)
        assert score_high < 0.3  # Should be low for high rates
    
    def test_signal_strength_calculation(self, mock_api_keys):
        """Test signal strength calculation"""
        model = FedPivotModel(mock_api_keys)
        
        fed_data = {
            'fed_funds_rate': 1.0,
            'pivot_detected': True,
            'pivot_direction': 'cutting'
        }
        
        reserve_data = {
            'exchange_reserves': 2.3e6,  # Very low reserves
            'reserve_score': 1.0
        }
        
        signals = model.calculate_signal_strength(fed_data, reserve_data)
        
        assert 'fed_score' in signals
        assert 'reserve_score' in signals
        assert 'combined_score' in signals
        assert 'buy_signal' in signals
        assert signals['combined_score'] > 0.7  # Should trigger buy signal

class TestDataProviders:
    """Test data provider functionality"""
    
    def test_fred_client_initialization(self):
        """Test FRED client initialization"""
        from bitcoin_model.data_providers.fred_client import FREDClient
        
        client = FREDClient('test_key')
        assert client.api_key == 'test_key'
        assert client.base_url == "https://api.stlouisfed.org/fred"
    
    def test_crypto_data_provider_initialization(self):
        """Test crypto data provider initialization"""
        from bitcoin_model.data_providers.crypto_data import CoinGeckoClient, MockOnChainDataProvider
        
        coingecko = CoinGeckoClient('test_key')
        assert coingecko.api_key == 'test_key'
        
        mock_provider = MockOnChainDataProvider()
        reserves = mock_provider.get_exchange_reserves()
        assert reserves is not None
        assert reserves > 0

def test_import():
    """Test that main imports work"""
    from bitcoin_model import BitcoinMacroModel, FedPivotModel, M2MinerModel
    
    assert BitcoinMacroModel is not None
    assert FedPivotModel is not None
    assert M2MinerModel is not None

if __name__ == "__main__":
    pytest.main([__file__])