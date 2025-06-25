"""
Federal Reserve Economic Data (FRED) API client
"""

import logging
import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import time

class FREDClient:
    """Client for accessing Federal Reserve Economic Data"""
    
    def __init__(self, api_key: str):
        """
        Initialize FRED client
        
        Args:
            api_key: FRED API key
        """
        self.api_key = api_key
        self.base_url = "https://api.stlouisfed.org/fred"
        self.logger = logging.getLogger(__name__)
        
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Make request to FRED API"""
        params['api_key'] = self.api_key
        params['file_type'] = 'json'
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f"FRED API request failed: {str(e)}")
            raise
    
    def get_series(self, series_id: str, 
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None,
                   limit: int = 1000) -> pd.DataFrame:
        """
        Get time series data from FRED
        
        Args:
            series_id: FRED series ID (e.g., 'DFF' for Fed Funds Rate)
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            limit: Maximum number of observations
            
        Returns:
            DataFrame with date and value columns
        """
        params = {
            'series_id': series_id,
            'limit': limit,
            'sort_order': 'desc'  # Most recent first
        }
        
        if start_date:
            params['observation_start'] = start_date
        if end_date:
            params['observation_end'] = end_date
            
        data = self._make_request('series/observations', params)
        
        observations = data.get('observations', [])
        
        if not observations:
            self.logger.warning(f"No data found for series {series_id}")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(observations)
        df['date'] = pd.to_datetime(df['date'])
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        
        # Remove rows with missing values
        df = df.dropna(subset=['value'])
        
        # Sort by date ascending
        df = df.sort_values('date').reset_index(drop=True)
        
        return df[['date', 'value']]
    
    def get_fed_funds_rate(self, days_back: int = 90) -> pd.DataFrame:
        """
        Get Federal Funds Rate data
        
        Args:
            days_back: Number of days of historical data
            
        Returns:
            DataFrame with Fed Funds Rate data
        """
        start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        return self.get_series('DFF', start_date=start_date)
    
    def get_m2_money_supply(self, months_back: int = 24) -> pd.DataFrame:
        """
        Get M2 Money Supply data
        
        Args:
            months_back: Number of months of historical data
            
        Returns:
            DataFrame with M2 data
        """
        start_date = (datetime.now() - timedelta(days=months_back*30)).strftime('%Y-%m-%d')
        return self.get_series('M2SL', start_date=start_date)
    
    def get_current_fed_rate(self) -> Optional[float]:
        """
        Get the most recent Federal Funds Rate
        
        Returns:
            Current Fed Funds Rate or None if unavailable
        """
        try:
            df = self.get_fed_funds_rate(days_back=30)
            if not df.empty:
                return float(df.iloc[-1]['value'])
        except Exception as e:
            self.logger.error(f"Failed to get current Fed rate: {str(e)}")
        
        return None
    
    def get_m2_growth_rate(self) -> Optional[float]:
        """
        Get year-over-year M2 growth rate
        
        Returns:
            M2 YoY growth rate as decimal (e.g., 0.10 for 10%) or None
        """
        try:
            df = self.get_m2_money_supply(months_back=15)
            if len(df) < 12:
                return None
                
            # Calculate YoY growth
            current_value = df.iloc[-1]['value']
            year_ago_value = df.iloc[-13]['value']  # Approximately 12 months ago
            
            growth_rate = (current_value - year_ago_value) / year_ago_value
            return float(growth_rate)
            
        except Exception as e:
            self.logger.error(f"Failed to calculate M2 growth rate: {str(e)}")
        
        return None
    
    def detect_fed_pivot(self, lookback_days: int = 180) -> Dict[str, Any]:
        """
        Detect if Fed has pivoted policy direction
        
        Args:
            lookback_days: Days to look back for trend analysis
            
        Returns:
            Dictionary with pivot information
        """
        try:
            df = self.get_fed_funds_rate(days_back=lookback_days)
            if len(df) < 10:
                return {'pivot_detected': False, 'reason': 'Insufficient data'}
            
            # Get recent rates
            recent_rates = df.tail(30)['value'].tolist()
            older_rates = df.head(30)['value'].tolist()
            
            recent_avg = sum(recent_rates) / len(recent_rates)
            older_avg = sum(older_rates) / len(older_rates)
            
            # Detect significant change in direction
            rate_change = recent_avg - older_avg
            
            pivot_info = {
                'pivot_detected': abs(rate_change) > 0.5,  # 50bps threshold
                'direction': 'cutting' if rate_change < -0.25 else 'hiking' if rate_change > 0.25 else 'neutral',
                'magnitude': abs(rate_change),
                'current_rate': recent_rates[-1],
                'trend_change': rate_change
            }
            
            return pivot_info
            
        except Exception as e:
            self.logger.error(f"Failed to detect Fed pivot: {str(e)}")
            return {'pivot_detected': False, 'error': str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if FRED API is accessible
        
        Returns:
            Health status dictionary
        """
        try:
            # Try to get recent Fed rate
            rate = self.get_current_fed_rate()
            
            return {
                'status': 'healthy' if rate is not None else 'degraded',
                'current_fed_rate': rate,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }