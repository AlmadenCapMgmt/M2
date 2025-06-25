"""
M2 Money Supply Expansion + Miner Capitulation Model (Scenario 2)

This model identifies strategic Bitcoin accumulation opportunities when:
1. M2 money supply is expanding rapidly (>10% YoY)
2. Bitcoin miners show capitulation signals through hash rate metrics
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import pandas as pd

from ..data_providers.fred_client import FREDClient
from ..data_providers.crypto_data import DataProviderFactory
from ..config.settings import Settings

class M2MinerModel:
    """
    Scenario 2: M2 Expansion + Miner Capitulation
    
    Combines macroeconomic monetary expansion analysis with Bitcoin network
    dynamics to identify strategic accumulation periods.
    """
    
    def __init__(self, api_keys: Dict[str, str]):
        """
        Initialize M2 Miner model
        
        Args:
            api_keys: Dictionary containing API keys for data providers
        """
        self.logger = logging.getLogger(__name__)
        self.settings = Settings()
        
        # Initialize data providers
        self.fred_client = FREDClient(api_keys.get('fred'))
        self.crypto_provider = DataProviderFactory.create_crypto_provider(api_keys)
        self.onchain_provider = DataProviderFactory.create_onchain_provider(api_keys)
        
        self.logger.info("M2MinerModel initialized")
    
    def get_m2_data(self) -> Dict[str, Any]:
        """
        Get M2 money supply data and analysis
        
        Returns:
            Dictionary with M2 metrics
        """
        try:
            # Get M2 growth rate
            m2_growth = self.fred_client.get_m2_growth_rate()
            
            if m2_growth is None:
                return {'m2_growth_rate': None, 'error': 'M2 data unavailable'}
            
            # Get detailed M2 data for acceleration calculation
            m2_df = self.fred_client.get_m2_money_supply(months_back=18)
            
            m2_acceleration = None
            m2_velocity = None
            
            if len(m2_df) >= 24:  # Need at least 2 years of data
                # Calculate acceleration (change in growth rate)
                recent_growth = []
                for i in range(3):  # Last 3 months
                    if len(m2_df) > (13 + i):
                        current = m2_df.iloc[-(1+i)]['value']
                        year_ago = m2_df.iloc[-(13+i)]['value']
                        growth = (current - year_ago) / year_ago
                        recent_growth.append(growth)
                
                if len(recent_growth) >= 2:
                    current_growth = recent_growth[0]
                    prev_growth = recent_growth[-1]
                    m2_acceleration = current_growth - prev_growth
            
            # Classify M2 growth level
            thresholds = self.settings.M2_THRESHOLDS
            
            if m2_growth >= thresholds['extreme_expansion']:
                growth_level = 'extreme_expansion'
                growth_score = 1.0
            elif m2_growth >= thresholds['strong_expansion']:
                growth_level = 'strong_expansion'
                growth_score = 0.8
            elif m2_growth >= thresholds['normal_expansion']:
                growth_level = 'normal_expansion'
                growth_score = 0.5
            elif m2_growth >= thresholds['contraction']:
                growth_level = 'slow_growth'
                growth_score = 0.2
            else:
                growth_level = 'contraction'
                growth_score = 0.0
            
            return {
                'm2_growth_rate': m2_growth,
                'm2_acceleration': m2_acceleration,
                'm2_velocity': m2_velocity,  # TODO: Calculate from GDP data
                'growth_level': growth_level,
                'growth_score': growth_score,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Failed to get M2 data: {str(e)}")
            return {
                'm2_growth_rate': None,
                'error': str(e)
            }
    
    def get_hash_ribbon_data(self) -> Dict[str, Any]:
        """
        Get Bitcoin hash ribbon and miner capitulation data
        
        Returns:
            Dictionary with miner metrics
        """
        try:
            # Get hash ribbon signal from on-chain provider
            hash_data = self.onchain_provider.get_hash_ribbon_signal()
            
            if not hash_data:
                return {'hash_ribbon_signal': None, 'error': 'Hash data unavailable'}
            
            signal = hash_data.get('signal', 'neutral')
            miner_capitulation = hash_data.get('miner_capitulation', False)
            
            # Score based on hash ribbon signal
            if signal == 'buy':
                ribbon_score = 1.0
                signal_strength = 'strong_buy'
            elif signal == 'sell':
                ribbon_score = 0.0
                signal_strength = 'strong_sell'
            else:  # neutral
                ribbon_score = 0.4
                signal_strength = 'neutral'
            
            # Bonus for post-capitulation recovery
            capitulation_bonus = 0.3 if miner_capitulation else 0.0
            
            total_score = min(1.0, ribbon_score + capitulation_bonus)
            
            return {
                'hash_ribbon_signal': signal,
                'miner_capitulation': miner_capitulation,
                'ribbon_score': total_score,
                'signal_strength': signal_strength,
                'ma_30': hash_data.get('ma_30'),
                'ma_60': hash_data.get('ma_60'),
                'trend': hash_data.get('trend', 'unknown'),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Failed to get hash ribbon data: {str(e)}")
            return {
                'hash_ribbon_signal': None,
                'error': str(e)
            }
    
    def calculate_m2_score(self, m2_data: Dict[str, Any]) -> float:
        """
        Calculate M2 signal score (0-1)
        
        Args:
            m2_data: M2 money supply data
            
        Returns:
            M2 signal score (0-1)
        """
        if m2_data.get('m2_growth_rate') is None:
            return 0.0
        
        growth_rate = m2_data['m2_growth_rate']
        acceleration = m2_data.get('m2_acceleration', 0)
        base_score = m2_data.get('growth_score', 0)
        
        # Acceleration adjustment
        accel_bonus = 0.0
        if acceleration is not None:
            # Positive acceleration (increasing growth) is bullish
            accel_bonus = min(0.2, max(-0.2, acceleration * 5))
        
        # TODO: Add velocity adjustment when GDP data is available
        # Lower velocity (money sitting idle) is bullish for Bitcoin
        velocity_adjustment = 0.0
        
        final_score = min(1.0, max(0.0, base_score + accel_bonus + velocity_adjustment))
        
        self.logger.debug(f"M2 score calculation: growth={growth_rate:.3f}, "
                         f"accel={acceleration}, score={final_score:.3f}")
        
        return final_score
    
    def calculate_signal_strength(self, m2_data: Dict[str, Any], 
                                 miner_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate combined signal strength
        
        Args:
            m2_data: M2 money supply data
            miner_data: Miner/hash ribbon data
            
        Returns:
            Dictionary with signal analysis
        """
        # Individual scores
        m2_score = self.calculate_m2_score(m2_data)
        miner_score = miner_data.get('ribbon_score', 0.0)
        
        # Equal weighted combination for this scenario
        combined_score = (m2_score * 0.5) + (miner_score * 0.5)
        
        # Signal threshold (higher than Scenario 1 - requires more conviction)
        threshold = self.settings.get_signal_threshold(2)  # Scenario 2
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
        
        # Special case: Extreme M2 expansion can override miner signals
        if m2_data.get('growth_level') == 'extreme_expansion':
            if combined_score >= 0.6:  # Lower threshold for extreme M2
                buy_signal = True
                strength = 'strong_m2_override'
        
        return {
            'm2_score': m2_score,
            'miner_score': miner_score,
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
        
        # More aggressive sizing for M2 scenario due to longer timeframes
        threshold = signal_data['threshold']
        excess_signal = max(0, combined_score - threshold)
        max_excess = 1.0 - threshold
        
        if max_excess > 0:
            size_multiplier = 1.2 + (excess_signal / max_excess) * 2.5
        else:
            size_multiplier = 1.2
        
        position_size = min(max_size, base_size * size_multiplier)
        position_value = portfolio_value * position_size
        
        # Entry strategy (accumulated over 30 days for M2 scenario)
        entry_plan = [
            {'timing': 'week_1', 'percentage': 0.30, 'value': position_value * 0.30},
            {'timing': 'week_2', 'percentage': 0.25, 'value': position_value * 0.25},
            {'timing': 'week_3', 'percentage': 0.25, 'value': position_value * 0.25},
            {'timing': 'week_4', 'percentage': 0.20, 'value': position_value * 0.20}
        ]
        
        return {
            'action': 'accumulate',
            'position_size': position_size,
            'position_value': position_value,
            'entry_strategy': 'accumulate_30_days',
            'entry_plan': entry_plan,
            'rationale': f"M2 expansion signal ({signal_data['signal_strength']}) "
                        f"with miner capitulation. Combined score: {combined_score:.2f}",
            'hold_period': 'minimum_180_days',
            'exit_conditions': [
                'M2 growth deceleration below 5% YoY',
                'Hash ribbon sell signal',
                'NUPL > 0.75 (euphoria)',
                'Fed aggressive tightening cycle'
            ]
        }
    
    def analyze(self, portfolio_value: float = 100000, 
               historical_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Run complete analysis for Scenario 2
        
        Args:
            portfolio_value: Total portfolio value for position sizing
            historical_date: Optional date for historical analysis
            
        Returns:
            Complete analysis results
        """
        self.logger.info("Running M2 Expansion + Miner Capitulation analysis")
        
        # Get data
        m2_data = self.get_m2_data()
        miner_data = self.get_hash_ribbon_data()
        
        # Calculate signals
        signals = self.calculate_signal_strength(m2_data, miner_data)
        
        # Generate trade plan
        trade_plan = self.generate_trade_plan(signals, portfolio_value)
        
        # Compile results
        result = {
            'scenario': 2,
            'scenario_name': 'M2 Expansion + Miner Capitulation',
            'data': {
                'm2_money_supply': m2_data,
                'miner_metrics': miner_data
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
            'scenario': 2,
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