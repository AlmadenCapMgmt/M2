"""
Configuration settings for the Bitcoin Strategic Investment Model
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class Settings:
    """Configuration settings loaded from environment variables"""
    
    def __init__(self):
        # Risk profiles with position sizing parameters
        self.POSITION_LIMITS = {
            'conservative': {
                'base': 0.03,  # 3%
                'max': 0.10    # 10%
            },
            'moderate': {
                'base': 0.05,  # 5%
                'max': 0.15    # 15%
            },
            'aggressive': {
                'base': 0.10,  # 10%
                'max': 0.25    # 25%
            }
        }
        
        # API rate limits (requests per minute unless noted)
        self.RATE_LIMITS = {
            'fred': None,  # No limits
            'coingecko_free': 50,  # per minute
            'glassnode_advanced': 20,  # per minute
            'cryptoquant_professional': 3000  # per day
        }
        
        # Signal thresholds for each scenario
        self.SIGNAL_THRESHOLDS = {
            'scenario_1': 0.70,  # Fed Pivot + Exchange Reserves
            'scenario_2': 0.75   # M2 + Miner Capitulation
        }
        
        # Exchange reserve thresholds (in BTC)
        self.EXCHANGE_RESERVE_THRESHOLDS = {
            'critical_low': 2.35e6,
            'low': 2.5e6,
            'high': 2.8e6,
            'critical_high': 3.0e6
        }
        
        # M2 growth thresholds
        self.M2_THRESHOLDS = {
            'extreme_expansion': 0.15,  # 15%+
            'strong_expansion': 0.10,   # 10%+
            'normal_expansion': 0.05,   # 5%+
            'contraction': 0.0          # Below 0%
        }
        
        # Fed funds rate thresholds
        self.FED_RATE_THRESHOLDS = {
            'ultra_low': 1.0,   # Below 1%
            'low': 3.0,         # Below 3%
            'neutral': 5.0,     # Below 5%
            'high': 5.0         # Above 5%
        }
        
        # NUPL (Net Unrealized Profit/Loss) levels
        self.NUPL_LEVELS = {
            'capitulation': 0.0,
            'accumulation': 0.25,
            'optimism': 0.5,
            'belief': 0.75,
            'euphoria': 1.0
        }
        
        # Default configuration from environment
        self.DEFAULT_PORTFOLIO_VALUE = float(os.getenv('DEFAULT_PORTFOLIO_VALUE', 100000))
        self.RISK_PROFILE = os.getenv('RISK_PROFILE', 'moderate')
        self.TESTNET_MODE = os.getenv('TESTNET_MODE', 'true').lower() == 'true'
        self.DRY_RUN = os.getenv('DRY_RUN', 'true').lower() == 'true'
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        self.LOG_FILE = os.getenv('LOG_FILE', 'bitcoin_model.log')
        
    def get_position_limits(self, risk_profile: str = None) -> Dict[str, float]:
        """Get position limits for given risk profile"""
        profile = risk_profile or self.RISK_PROFILE
        return self.POSITION_LIMITS.get(profile, self.POSITION_LIMITS['moderate'])
    
    def get_signal_threshold(self, scenario: int) -> float:
        """Get signal threshold for scenario"""
        key = f'scenario_{scenario}'
        return self.SIGNAL_THRESHOLDS.get(key, 0.7)
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate configuration and return status"""
        issues = []
        
        if self.RISK_PROFILE not in self.POSITION_LIMITS:
            issues.append(f"Invalid risk profile: {self.RISK_PROFILE}")
        
        if self.DEFAULT_PORTFOLIO_VALUE <= 0:
            issues.append(f"Invalid portfolio value: {self.DEFAULT_PORTFOLIO_VALUE}")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues
        }