"""
Cryptocurrency and Bitcoin on-chain data providers
"""

import logging
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import time

class CryptoDataProvider:
    """Base class for crypto data providers"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.logger = logging.getLogger(__name__)
    
    def health_check(self) -> Dict[str, Any]:
        """Check provider health"""
        return {'status': 'unknown', 'provider': self.__class__.__name__}

class CoinGeckoClient(CryptoDataProvider):
    """CoinGecko API client for basic crypto data"""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self.base_url = "https://api.coingecko.com/api/v3"
        self.rate_limit_delay = 1.2  # seconds between requests for free tier
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make request to CoinGecko API"""
        if params is None:
            params = {}
        
        if self.api_key:
            params['x_cg_demo_api_key'] = self.api_key
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            # Rate limiting for free tier
            if not self.api_key:
                time.sleep(self.rate_limit_delay)
            
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"CoinGecko API request failed: {str(e)}")
            raise
    
    def get_bitcoin_price(self) -> Optional[float]:
        """Get current Bitcoin price in USD"""
        try:
            data = self._make_request('simple/price', {
                'ids': 'bitcoin',
                'vs_currencies': 'usd'
            })
            return data.get('bitcoin', {}).get('usd')
        except Exception as e:
            self.logger.error(f"Failed to get Bitcoin price: {str(e)}")
            return None
    
    def get_bitcoin_market_data(self) -> Dict[str, Any]:
        """Get comprehensive Bitcoin market data"""
        try:
            data = self._make_request('coins/bitcoin')
            market_data = data.get('market_data', {})
            
            return {
                'price_usd': market_data.get('current_price', {}).get('usd'),
                'market_cap': market_data.get('market_cap', {}).get('usd'),
                'volume_24h': market_data.get('total_volume', {}).get('usd'),
                'price_change_24h': market_data.get('price_change_percentage_24h'),
                'price_change_7d': market_data.get('price_change_percentage_7d'),
                'price_change_30d': market_data.get('price_change_percentage_30d'),
                'market_cap_rank': data.get('market_cap_rank'),
                'circulating_supply': market_data.get('circulating_supply'),
                'total_supply': market_data.get('total_supply'),
                'max_supply': market_data.get('max_supply')
            }
        except Exception as e:
            self.logger.error(f"Failed to get Bitcoin market data: {str(e)}")
            return {}
    
    def health_check(self) -> Dict[str, Any]:
        """Check CoinGecko API health"""
        try:
            price = self.get_bitcoin_price()
            return {
                'status': 'healthy' if price is not None else 'degraded',
                'provider': 'CoinGecko',
                'btc_price': price,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'error',
                'provider': 'CoinGecko',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

class MockOnChainDataProvider(CryptoDataProvider):
    """
    Mock provider for on-chain data (Glassnode/CryptoQuant replacement)
    
    In production, this would be replaced with actual API integrations
    to Glassnode, CryptoQuant, or similar on-chain data providers.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self.logger.info("Using mock on-chain data provider. Replace with actual API integration.")
    
    def get_exchange_reserves(self) -> Optional[float]:
        """
        Get total Bitcoin reserves on exchanges
        
        Returns:
            Exchange reserves in BTC (mock data)
        """
        # Mock data - in production, fetch from Glassnode/CryptoQuant
        # Current approximate levels are around 2.35M BTC
        return 2.35e6  # 2.35 million BTC
    
    def get_long_term_holder_supply(self) -> Optional[float]:
        """
        Get percentage of supply held by long-term holders (155+ days)
        
        Returns:
            LTH supply percentage (0-1)
        """
        # Mock data - typically 75-80% of supply
        return 0.78  # 78% of supply
    
    def get_nupl(self) -> Optional[float]:
        """
        Get Net Unrealized Profit/Loss (NUPL)
        
        Returns:
            NUPL value (-1 to 1)
        """
        # Mock data - varies significantly with market conditions
        return 0.15  # Mild accumulation phase
    
    def get_hash_ribbon_signal(self) -> Dict[str, Any]:
        """
        Get hash ribbon indicator signal
        
        Returns:
            Dictionary with hash ribbon analysis
        """
        # Mock data - would calculate from actual hash rate data
        return {
            'signal': 'neutral',  # 'buy', 'sell', 'neutral'
            'ma_30': 450e18,  # 30-day hash rate MA
            'ma_60': 440e18,  # 60-day hash rate MA
            'trend': 'recovering',
            'miner_capitulation': False
        }
    
    def get_bitcoin_metrics(self) -> Dict[str, Any]:
        """
        Get comprehensive Bitcoin on-chain metrics
        
        Returns:
            Dictionary with various on-chain metrics
        """
        return {
            'exchange_reserves': self.get_exchange_reserves(),
            'lth_supply_percentage': self.get_long_term_holder_supply(),
            'nupl': self.get_nupl(),
            'hash_ribbon': self.get_hash_ribbon_signal(),
            'timestamp': datetime.now().isoformat(),
            'data_source': 'mock'  # Indicates this is mock data
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Check mock provider health"""
        try:
            metrics = self.get_bitcoin_metrics()
            return {
                'status': 'healthy',
                'provider': 'MockOnChainData',
                'exchange_reserves': metrics['exchange_reserves'],
                'timestamp': datetime.now().isoformat(),
                'warning': 'Using mock data - replace with actual API integration'
            }
        except Exception as e:
            return {
                'status': 'error',
                'provider': 'MockOnChainData',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

class DataProviderFactory:
    """Factory for creating data provider instances"""
    
    @staticmethod
    def create_crypto_provider(api_keys: Dict[str, str]) -> CoinGeckoClient:
        """Create CoinGecko provider"""
        return CoinGeckoClient(api_keys.get('coingecko'))
    
    @staticmethod
    def create_onchain_provider(api_keys: Dict[str, str]) -> MockOnChainDataProvider:
        """
        Create on-chain data provider
        
        TODO: Replace with actual Glassnode/CryptoQuant integration
        """
        return MockOnChainDataProvider(api_keys.get('glassnode') or api_keys.get('cryptoquant'))