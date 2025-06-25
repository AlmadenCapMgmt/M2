"""
Core BitcoinMacroModel class that orchestrates the different scenario models
"""

import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

from .models.fed_pivot import FedPivotModel
from .models.m2_miner import M2MinerModel
from .config.settings import Settings

load_dotenv()

class BitcoinMacroModel:
    """
    Main class for Bitcoin Strategic Investment Model
    
    Orchestrates multiple scenario models to generate investment signals
    based on macroeconomic indicators, Federal Reserve policy, and on-chain metrics.
    """
    
    def __init__(self, api_keys: Optional[Dict[str, str]] = None):
        """
        Initialize the Bitcoin Macro Model
        
        Args:
            api_keys: Dictionary of API keys for data providers
                     If None, will attempt to load from environment variables
        """
        self.logger = logging.getLogger(__name__)
        
        # Load API keys from environment if not provided
        if api_keys is None:
            api_keys = {
                'fred': os.getenv('FRED_API_KEY'),
                'glassnode': os.getenv('GLASSNODE_API_KEY'),
                'cryptoquant': os.getenv('CRYPTOQUANT_API_KEY'),
                'coingecko': os.getenv('COINGECKO_API_KEY')
            }
        
        self.api_keys = api_keys
        self.settings = Settings()
        
        # Initialize scenario models
        self.fed_pivot_model = FedPivotModel(api_keys)
        self.m2_miner_model = M2MinerModel(api_keys)
        
        # Available scenarios
        self.scenarios = {
            1: self.fed_pivot_model,
            2: self.m2_miner_model
        }
        
        self.logger.info("BitcoinMacroModel initialized with scenarios: %s", 
                        list(self.scenarios.keys()))
    
    def run_analysis(self, 
                    scenario: int, 
                    portfolio_value: float = 100000,
                    historical_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Run analysis for a specific scenario
        
        Args:
            scenario: Scenario number (1 or 2)
            portfolio_value: Total portfolio value for position sizing
            historical_date: Optional date for historical analysis
            
        Returns:
            Dictionary containing analysis results including signals and trade plan
        """
        if scenario not in self.scenarios:
            raise ValueError(f"Unknown scenario: {scenario}. Available: {list(self.scenarios.keys())}")
        
        self.logger.info(f"Running analysis for scenario {scenario}")
        
        model = self.scenarios[scenario]
        
        try:
            # Get scenario-specific analysis
            result = model.analyze(portfolio_value, historical_date)
            
            # Add metadata
            result['scenario'] = scenario
            result['timestamp'] = datetime.now().isoformat()
            result['portfolio_value'] = portfolio_value
            
            self.logger.info(f"Analysis complete for scenario {scenario}. "
                           f"Buy signal: {result['signals']['buy_signal']}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in scenario {scenario} analysis: {str(e)}")
            raise
    
    def get_all_signals(self, portfolio_value: float = 100000) -> Dict[str, Any]:
        """
        Get signals from all scenarios
        
        Args:
            portfolio_value: Total portfolio value for position sizing
            
        Returns:
            Dictionary with results from all scenarios
        """
        results = {}
        
        for scenario_id in self.scenarios:
            try:
                result = self.run_analysis(scenario_id, portfolio_value)
                results[f'scenario_{scenario_id}'] = result
            except Exception as e:
                self.logger.error(f"Failed to get signals for scenario {scenario_id}: {str(e)}")
                results[f'scenario_{scenario_id}'] = {
                    'error': str(e),
                    'signals': {'buy_signal': False, 'combined_score': 0.0}
                }
        
        return results
    
    def get_strongest_signal(self, portfolio_value: float = 100000) -> Dict[str, Any]:
        """
        Get the strongest signal across all scenarios
        
        Args:
            portfolio_value: Total portfolio value for position sizing
            
        Returns:
            Dictionary with the strongest signal result
        """
        all_signals = self.get_all_signals(portfolio_value)
        
        strongest = None
        max_score = 0.0
        
        for scenario_name, result in all_signals.items():
            if 'error' not in result:
                score = result['signals']['combined_score']
                if score > max_score:
                    max_score = score
                    strongest = result
        
        if strongest is None:
            self.logger.warning("No valid signals found")
            return {
                'signals': {'buy_signal': False, 'combined_score': 0.0},
                'error': 'No valid signals available'
            }
        
        return strongest
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check the health of all data providers and models
        
        Returns:
            Dictionary with health status of each component
        """
        health = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'components': {}
        }
        
        # Check each scenario model
        for scenario_id, model in self.scenarios.items():
            try:
                model_health = model.health_check()
                health['components'][f'scenario_{scenario_id}'] = model_health
                
                if model_health.get('status') != 'healthy':
                    health['overall_status'] = 'degraded'
                    
            except Exception as e:
                health['components'][f'scenario_{scenario_id}'] = {
                    'status': 'error',
                    'error': str(e)
                }
                health['overall_status'] = 'error'
        
        return health