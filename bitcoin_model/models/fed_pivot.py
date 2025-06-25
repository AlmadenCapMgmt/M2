"""
Federal Reserve Policy Pivot + Low Exchange Reserves Model (Scenario 1)

This model identifies high-probability Bitcoin entry points when:
1. Federal Reserve shifts monetary policy (rate cuts, QE expansion)
2. Bitcoin exchange reserves are at multi-year lows
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import pandas as pd

from ..data_providers.fred_client import FREDClient
from ..data_providers.crypto_data import DataProviderFactory
from ..config.settings import Settings

class FedPivotModel:
    """
    Scenario 1: Fed Pivot + Low Exchange Reserves
    
    Combines Federal Reserve policy analysis with Bitcoin supply dynamics
    to identify strategic entry opportunities.
    """
    
    def __init__(self, api_keys: Dict[str, str]):
        """
        Initialize Fed Pivot model
        
        Args:
            api_keys: Dictionary containing API keys for data providers
        """
        self.logger = logging.getLogger(__name__)
        self.settings = Settings()
        
        # Initialize data providers
        self.fred_client = FREDClient(api_keys.get('fred'))
        self.crypto_provider = DataProviderFactory.create_crypto_provider(api_keys)
        self.onchain_provider = DataProviderFactory.create_onchain_provider(api_keys)
        
        self.logger.info("FedPivotModel initialized")
    
    def get_fed_data(self) -> Dict[str, Any]:
        """
        Get Federal Reserve policy data
        
        Returns:
            Dictionary with Fed policy metrics
        """
        try:
            # Get current Fed funds rate
            current_rate = self.fred_client.get_current_fed_rate()
            
            # Detect policy pivot
            pivot_info = self.fred_client.detect_fed_pivot()
            
            # Get M2 for QE context
            m2_growth = self.fred_client.get_m2_growth_rate()
            
            return {
                'fed_funds_rate': current_rate,
                'pivot_detected': pivot_info.get('pivot_detected', False),
                'pivot_direction': pivot_info.get('direction', 'neutral'),
                'pivot_magnitude': pivot_info.get('magnitude', 0),
                'trend_change': pivot_info.get('trend_change', 0),
                'm2_growth_rate': m2_growth,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Failed to get Fed data: {str(e)}")
            return {
                'fed_funds_rate': None,
                'pivot_detected': False,
                'error': str(e)
            }
    
    def get_exchange_reserves(self) -> Dict[str, Any]:
        """
        Get Bitcoin exchange reserve data
        
        Returns:
            Dictionary with exchange reserve metrics
        """
        try:
            reserves = self.onchain_provider.get_exchange_reserves()
            
            if reserves is None:
                return {'exchange_reserves': None, 'error': 'No reserve data available'}
            
            # Classify reserve level
            thresholds = self.settings.EXCHANGE_RESERVE_THRESHOLDS
            
            if reserves < thresholds['critical_low']:
                level = 'critical_low'
                score = 1.0
            elif reserves < thresholds['low']:
                level = 'low'
                score = 0.7
            elif reserves > thresholds['critical_high']:
                level = 'critical_high'
                score = 0.0
            elif reserves > thresholds['high']:
                level = 'high'
                score = 0.2
            else:
                level = 'normal'
                score = 0.4
            
            return {
                'exchange_reserves': reserves,
                'reserve_level': level,
                'reserve_score': score,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Failed to get exchange reserves: {str(e)}")
            return {
                'exchange_reserves': None,
                'error': str(e)
            }
    
    def calculate_fed_score(self, fed_data: Dict[str, Any]) -> float:
        """
        Calculate Fed policy signal score (0-1)
        
        Args:
            fed_data: Fed policy data dictionary
            
        Returns:
            Fed signal score (0-1)
        """
        if fed_data.get('fed_funds_rate') is None:
            return 0.0
        
        current_rate = fed_data['fed_funds_rate']
        pivot_detected = fed_data.get('pivot_detected', False)
        pivot_direction = fed_data.get('pivot_direction', 'neutral')
        pivot_magnitude = fed_data.get('pivot_magnitude', 0)
        
        # Base score from rate level
        thresholds = self.settings.FED_RATE_THRESHOLDS
        if current_rate < thresholds['ultra_low']:
            base_score = 0.8
        elif current_rate < thresholds['low']:
            base_score = 0.5
        elif current_rate < thresholds['neutral']:
            base_score = 0.3
        else:
            base_score = 0.1
        
        # Pivot adjustments
        direction_multiplier = 1.0
        
        if pivot_detected:
            if pivot_direction == 'cutting':
                # Rate cuts are bullish
                direction_multiplier = 1.5 + min(0.5, pivot_magnitude / 2.0)
            elif pivot_direction == 'hiking':
                # Rate hikes are bearish
                direction_multiplier = 0.3
        elif pivot_direction == 'cutting':
            # Ongoing cuts without pivot detection
            direction_multiplier = 1.2
        
        # Calculate final score
        score = min(1.0, base_score * direction_multiplier)
        
        self.logger.debug(f"Fed score calculation: rate={current_rate}, "
                         f"pivot={pivot_detected}, direction={pivot_direction}, "
                         f"score={score:.3f}")
        
        return score
    
    def calculate_signal_strength(self, fed_data: Dict[str, Any], 
                                 reserve_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate combined signal strength
        
        Args:
            fed_data: Federal Reserve data
            reserve_data: Exchange reserve data
            
        Returns:
            Dictionary with signal analysis
        """
        # Individual scores
        fed_score = self.calculate_fed_score(fed_data)
        reserve_score = reserve_data.get('reserve_score', 0.0)
        
        # Weighted combination (Fed policy weighted higher)
        combined_score = (fed_score * 0.6) + (reserve_score * 0.4)
        
        # Signal threshold
        threshold = self.settings.get_signal_threshold(1)  # Scenario 1
        buy_signal = combined_score >= threshold
        
        # Signal strength classification
        if combined_score >= 0.8:
            strength = 'very_strong'
        elif combined_score >= 0.6:
            strength = 'strong'
        elif combined_score >= 0.4:
            strength = 'moderate'
        else:
            strength = 'weak'
        
        return {
            'fed_score': fed_score,
            'reserve_score': reserve_score,
            'combined_score': combined_score,
            'buy_signal': buy_signal,
            'signal_strength': strength,
            'threshold': threshold
        }
    
    def generate_trade_plan(self, signal_data: Dict[str, Any], 
                           portfolio_value: float) -> Dict[str, Any]:
        """
        Generate specific trade execution plan
        
        Args:
            signal_data: Signal strength data
            portfolio_value: Total portfolio value
            
        Returns:
            Dictionary with trade plan details
        """
        if not signal_data.get('buy_signal', False):
            return {
                'action': 'no_action',
                'reason': 'Signal threshold not met',
                'position_size': 0.0
            }
        
        # Calculate position size based on signal strength
        combined_score = signal_data['combined_score']
        position_limits = self.settings.get_position_limits()
        
        # Scale position size with signal strength
        base_size = position_limits['base']
        max_size = position_limits['max']
        
        # Linear scaling based on signal strength above threshold
        threshold = signal_data['threshold']
        excess_signal = max(0, combined_score - threshold)
        max_excess = 1.0 - threshold
        
        if max_excess > 0:
            size_multiplier = 1.0 + (excess_signal / max_excess) * 2.0
        else:
            size_multiplier = 1.0
        
        position_size = min(max_size, base_size * size_multiplier)
        position_value = portfolio_value * position_size
        
        # Entry strategy (scaled over 72 hours)
        entry_plan = [
            {'timing': 'immediate', 'percentage': 0.40, 'value': position_value * 0.40},
            {'timing': '24_hours', 'percentage': 0.30, 'value': position_value * 0.30},
            {'timing': '48_hours', 'percentage': 0.20, 'value': position_value * 0.20},
            {'timing': '72_hours', 'percentage': 0.10, 'value': position_value * 0.10}
        ]
        
        return {
            'action': 'buy',
            'position_size': position_size,
            'position_value': position_value,
            'entry_strategy': 'scaled_72h',
            'entry_plan': entry_plan,
            'rationale': f"Fed pivot signal ({signal_data['signal_strength']}) "
                        f"with low exchange reserves. Combined score: {combined_score:.2f}",
            'hold_period': 'minimum_90_days',
            'exit_conditions': [
                'NUPL > 0.70 (euphoria)',
                'Exchange reserves > 2.8M BTC',
                'Fed policy reversal (rate hikes)'
            ]
        }
    
    def analyze(self, portfolio_value: float = 100000, 
               historical_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Run complete analysis for Scenario 1
        
        Args:
            portfolio_value: Total portfolio value for position sizing
            historical_date: Optional date for historical analysis
            
        Returns:
            Complete analysis results
        """
        self.logger.info("Running Fed Pivot + Exchange Reserves analysis")
        
        # Get data
        fed_data = self.get_fed_data()
        reserve_data = self.get_exchange_reserves()
        
        # Calculate signals
        signals = self.calculate_signal_strength(fed_data, reserve_data)
        
        # Generate trade plan
        trade_plan = self.generate_trade_plan(signals, portfolio_value)
        
        # Compile results
        result = {
            'scenario': 1,
            'scenario_name': 'Fed Pivot + Low Exchange Reserves',
            'data': {
                'fed_policy': fed_data,
                'exchange_reserves': reserve_data
            },
            'signals': signals,
            'trade_plan': trade_plan,
            'timestamp': datetime.now().isoformat()
        }
        
        self.logger.info(f"Analysis complete. Buy signal: {signals['buy_signal']}, "
                        f"Score: {signals['combined_score']:.3f}")
        
        return result
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check health of all data providers
        
        Returns:
            Health status dictionary
        """
        health = {
            'scenario': 1,
            'timestamp': datetime.now().isoformat(),
            'providers': {}
        }
        
        # Check FRED client
        health['providers']['fred'] = self.fred_client.health_check()
        
        # Check crypto providers
        health['providers']['crypto'] = self.crypto_provider.health_check()
        health['providers']['onchain'] = self.onchain_provider.health_check()
        
        # Overall status
        statuses = [provider.get('status') for provider in health['providers'].values()]
        if all(status == 'healthy' for status in statuses):
            health['status'] = 'healthy'
        elif any(status == 'error' for status in statuses):
            health['status'] = 'error'
        else:
            health['status'] = 'degraded'
        
        return health