"""
Trading configuration and safety settings for automated trading
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum
import logging

class ExchangeType(Enum):
    """Supported exchange types"""
    BINANCE = "binance"
    COINBASE = "coinbase"
    KRAKEN = "kraken"
    BYBIT = "bybit"
    OKX = "okx"
    KUCOIN = "kucoin"
    GEMINI = "gemini"

class OrderType(Enum):
    """Order types for trade execution"""
    MARKET = "market"
    LIMIT = "limit"
    LIMIT_MAKER = "limit_maker"

@dataclass
class TradingConfig:
    """Configuration for automated trading"""
    
    # Exchange settings
    exchange: str
    api_key: str
    api_secret: str
    api_passphrase: Optional[str] = None  # Required for some exchanges
    testnet: bool = True  # Always start with testnet
    dry_run: bool = True  # Paper trading mode
    
    # Safety limits
    max_position_size: float = 0.10  # Maximum 10% of portfolio
    min_order_size_btc: float = 0.001  # Minimum order size
    max_daily_trades: int = 10  # Maximum trades per day
    max_daily_loss: float = 0.02  # Maximum 2% daily loss
    
    # Order execution settings
    default_order_type: OrderType = OrderType.LIMIT
    slippage_tolerance: float = 0.02  # 2% slippage tolerance
    order_timeout: int = 300  # Order timeout in seconds
    
    # Rate limiting
    requests_per_minute: int = 20
    burst_limit: int = 5
    
    # Risk management
    stop_loss_percentage: Optional[float] = None  # Optional stop loss
    take_profit_percentage: Optional[float] = None  # Optional take profit
    
    # Monitoring
    health_check_interval: int = 300  # Health check every 5 minutes
    
    def validate(self) -> List[str]:
        """
        Validate trading configuration
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Check required fields
        if not self.api_key:
            errors.append("API key is required")
        if not self.api_secret:
            errors.append("API secret is required")
        
        # Check exchange support
        try:
            ExchangeType(self.exchange)
        except ValueError:
            errors.append(f"Unsupported exchange: {self.exchange}")
        
        # Check safety limits
        if self.max_position_size <= 0 or self.max_position_size > 1.0:
            errors.append("max_position_size must be between 0 and 1.0")
        
        if self.min_order_size_btc <= 0:
            errors.append("min_order_size_btc must be positive")
        
        if self.max_daily_loss <= 0 or self.max_daily_loss > 1.0:
            errors.append("max_daily_loss must be between 0 and 1.0")
        
        if self.slippage_tolerance < 0 or self.slippage_tolerance > 0.5:
            errors.append("slippage_tolerance must be between 0 and 0.5")
        
        # Warn about safety settings
        if not self.testnet:
            errors.append("WARNING: testnet=False means real money trading!")
        
        if not self.dry_run:
            errors.append("WARNING: dry_run=False means real order execution!")
        
        return errors
    
    def get_exchange_specific_config(self) -> Dict[str, Any]:
        """
        Get exchange-specific configuration
        
        Returns:
            Dictionary with exchange-specific settings
        """
        base_config = {
            'apiKey': self.api_key,
            'secret': self.api_secret,
            'sandbox': self.testnet,
            'enableRateLimit': True,
            'rateLimit': 60000 / self.requests_per_minute  # ms between requests
        }
        
        # Exchange-specific settings
        if self.exchange == 'coinbase':
            base_config['passphrase'] = self.api_passphrase
            base_config['pro'] = True
        elif self.exchange == 'binance':
            base_config['options'] = {'defaultType': 'spot'}
        elif self.exchange == 'kraken':
            base_config['apiKey'] = self.api_key
        
        return base_config

@dataclass
class SafetyManager:
    """Safety checks and circuit breakers for automated trading"""
    
    daily_loss_limit: float = 0.02  # 2% daily loss limit
    consecutive_loss_limit: int = 3  # Stop after 3 consecutive losses
    unusual_price_movement_threshold: float = 0.10  # 10% price movement
    
    # State tracking
    daily_pnl: float = field(default=0.0, init=False)
    consecutive_losses: int = field(default=0, init=False)
    last_price_check: float = field(default=0.0, init=False)
    trades_today: int = field(default=0, init=False)
    
    def __post_init__(self):
        self.logger = logging.getLogger(__name__)
    
    def check_safety_conditions(self, current_portfolio_value: float,
                               btc_price: float) -> Dict[str, Any]:
        """
        Check all safety conditions before allowing trades
        
        Args:
            current_portfolio_value: Current portfolio value
            btc_price: Current Bitcoin price
            
        Returns:
            Safety check results
        """
        checks = {
            'safe_to_trade': True,
            'reasons': [],
            'warnings': []
        }
        
        # Check daily loss limit
        daily_loss_pct = abs(self.daily_pnl) / current_portfolio_value
        if daily_loss_pct >= self.daily_loss_limit:
            checks['safe_to_trade'] = False
            checks['reasons'].append(f"Daily loss limit exceeded: {daily_loss_pct:.2%}")
        
        # Check consecutive losses
        if self.consecutive_losses >= self.consecutive_loss_limit:
            checks['safe_to_trade'] = False
            checks['reasons'].append(f"Consecutive loss limit exceeded: {self.consecutive_losses}")
        
        # Check for unusual price movements
        if self.last_price_check > 0:
            price_change = abs(btc_price - self.last_price_check) / self.last_price_check
            if price_change >= self.unusual_price_movement_threshold:
                checks['warnings'].append(f"Unusual price movement detected: {price_change:.2%}")
        
        self.last_price_check = btc_price
        
        return checks
    
    def record_trade_result(self, pnl: float, is_profitable: bool):
        """
        Record trade result for safety tracking
        
        Args:
            pnl: Profit/loss from trade
            is_profitable: Whether trade was profitable
        """
        self.daily_pnl += pnl
        self.trades_today += 1
        
        if is_profitable:
            self.consecutive_losses = 0
        else:
            self.consecutive_losses += 1
        
        self.logger.info(f"Trade recorded: PnL={pnl:.2f}, "
                        f"Daily PnL={self.daily_pnl:.2f}, "
                        f"Consecutive losses={self.consecutive_losses}")
    
    def reset_daily_counters(self):
        """Reset daily tracking counters (call at start of each day)"""
        self.daily_pnl = 0.0
        self.trades_today = 0
        self.logger.info("Daily safety counters reset")