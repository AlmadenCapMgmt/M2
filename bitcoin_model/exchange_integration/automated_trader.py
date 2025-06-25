"""
Automated trading system for executing BSI model signals
"""

import asyncio
import logging
import ccxt
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import json

from .trading_config import TradingConfig, SafetyManager, OrderType
from ..core import BitcoinMacroModel

class AutomatedTrader:
    """
    Automated trading system that executes trades based on BSI model signals
    """
    
    def __init__(self, model: BitcoinMacroModel, config: TradingConfig):
        """
        Initialize automated trader
        
        Args:
            model: BitcoinMacroModel instance
            config: Trading configuration
        """
        self.model = model
        self.config = config
        self.safety_manager = SafetyManager()
        self.logger = logging.getLogger(__name__)
        
        # Validate configuration
        errors = config.validate()
        if errors:
            error_msg = "Trading configuration errors: " + "; ".join(errors)
            self.logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Initialize exchange
        self.exchange = self._initialize_exchange()
        
        # Trading state
        self.is_running = False
        self.current_position = 0.0  # Current BTC position size
        self.last_signal_check = None
        self.pending_orders = []
        
        self.logger.info(f"AutomatedTrader initialized for {config.exchange}")
        if config.dry_run:
            self.logger.warning("DRY RUN MODE - No real trades will be executed")
    
    def _initialize_exchange(self) -> ccxt.Exchange:
        """Initialize CCXT exchange instance"""
        try:
            exchange_class = getattr(ccxt, self.config.exchange)
            exchange_config = self.config.get_exchange_specific_config()
            
            exchange = exchange_class(exchange_config)
            
            # Test connection
            if not self.config.dry_run:
                exchange.load_markets()
                self.logger.info(f"Successfully connected to {self.config.exchange}")
            
            return exchange
        except Exception as e:
            self.logger.error(f"Failed to initialize exchange: {str(e)}")
            raise
    
    async def start(self):
        """Start the automated trading loop"""
        if self.is_running:
            self.logger.warning("Trader is already running")
            return
        
        self.is_running = True
        self.logger.info("Starting automated trading...")
        
        try:
            while self.is_running:
                await self._trading_cycle()
                await asyncio.sleep(60)  # Check every minute
        except Exception as e:
            self.logger.error(f"Trading loop error: {str(e)}")
            self.is_running = False
            raise
    
    def stop(self):
        """Stop the automated trading loop"""
        self.logger.info("Stopping automated trading...")
        self.is_running = False
    
    async def _trading_cycle(self):
        """Execute one cycle of the trading loop"""
        try:
            # Health check
            if not await self._health_check():
                self.logger.warning("Health check failed, skipping cycle")
                return
            
            # Get current market data
            btc_price = await self._get_btc_price()
            portfolio_value = await self._get_portfolio_value()
            
            # Safety check
            safety_check = self.safety_manager.check_safety_conditions(
                portfolio_value, btc_price
            )
            
            if not safety_check['safe_to_trade']:
                self.logger.warning(f"Safety check failed: {safety_check['reasons']}")
                return
            
            # Check for signals (only check every 15 minutes to avoid overload)
            now = datetime.now()
            if (self.last_signal_check is None or 
                now - self.last_signal_check >= timedelta(minutes=15)):
                
                await self._check_and_execute_signals(portfolio_value)
                self.last_signal_check = now
            
            # Monitor existing positions
            await self._monitor_positions()
            
        except Exception as e:
            self.logger.error(f"Error in trading cycle: {str(e)}")
    
    async def _check_and_execute_signals(self, portfolio_value: float):
        """Check for new signals and execute trades"""
        try:
            # Get strongest signal across all scenarios
            result = self.model.get_strongest_signal(portfolio_value)
            
            if result.get('signals', {}).get('buy_signal', False):
                trade_plan = result.get('trade_plan', {})
                
                self.logger.info(f"Buy signal detected: {result['scenario_name']}")
                self.logger.info(f"Signal strength: {result['signals']['combined_score']:.3f}")
                
                await self._execute_trade_plan(trade_plan, portfolio_value)
            else:
                self.logger.debug("No buy signals detected")
                
        except Exception as e:
            self.logger.error(f"Error checking signals: {str(e)}")
    
    async def _execute_trade_plan(self, trade_plan: Dict[str, Any], 
                                  portfolio_value: float):
        """Execute a trade plan"""
        if trade_plan.get('action') != 'buy' and trade_plan.get('action') != 'accumulate':
            self.logger.info(f"No action required: {trade_plan.get('action', 'none')}")
            return
        
        position_size = trade_plan.get('position_size', 0)
        target_btc_amount = portfolio_value * position_size / await self._get_btc_price()
        
        # Check if we already have sufficient position
        if self.current_position >= target_btc_amount * 0.9:  # 90% tolerance
            self.logger.info(f"Already have sufficient position: {self.current_position:.4f} BTC")
            return
        
        # Calculate how much more BTC to buy
        btc_to_buy = target_btc_amount - self.current_position
        
        if btc_to_buy < self.config.min_order_size_btc:
            self.logger.info(f"Order size too small: {btc_to_buy:.4f} BTC")
            return
        
        # Execute based on entry strategy
        entry_strategy = trade_plan.get('entry_strategy', 'immediate')
        
        if entry_strategy == 'scaled_72h':
            await self._execute_scaled_entry(btc_to_buy, '72h')
        elif entry_strategy == 'accumulate_30_days':
            await self._execute_scaled_entry(btc_to_buy, '30d')
        else:
            await self._execute_immediate_buy(btc_to_buy)
    
    async def _execute_immediate_buy(self, btc_amount: float):
        """Execute immediate market buy"""
        try:
            if self.config.dry_run:
                self.logger.info(f"DRY RUN: Would buy {btc_amount:.4f} BTC immediately")
                self.current_position += btc_amount
                return
            
            # Place market buy order
            order = await self._place_order('buy', btc_amount, order_type='market')
            
            if order:
                self.logger.info(f"Executed immediate buy: {btc_amount:.4f} BTC")
                self.current_position += btc_amount
            
        except Exception as e:
            self.logger.error(f"Failed to execute immediate buy: {str(e)}")
    
    async def _execute_scaled_entry(self, total_btc_amount: float, timeframe: str):
        """Execute scaled entry over time"""
        # For now, implement as immediate buy
        # TODO: Implement actual time-based scaling
        self.logger.info(f"Scaled entry ({timeframe}) not yet implemented, "
                        f"executing immediate buy of {total_btc_amount:.4f} BTC")
        await self._execute_immediate_buy(total_btc_amount)
    
    async def _place_order(self, side: str, amount: float, 
                          order_type: str = 'market', 
                          price: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """Place an order on the exchange"""
        try:
            if self.config.dry_run:
                current_price = await self._get_btc_price()
                order = {
                    'id': f'dry_run_{datetime.now().timestamp()}',
                    'side': side,
                    'amount': amount,
                    'price': price or current_price,
                    'type': order_type,
                    'status': 'filled',
                    'filled': amount,
                    'cost': amount * (price or current_price)
                }
                self.logger.info(f"DRY RUN ORDER: {order}")
                return order
            
            # Real order execution
            symbol = 'BTC/USDT'  # or 'BTC/USD' depending on exchange
            
            if order_type == 'market':
                order = self.exchange.create_market_buy_order(symbol, amount)
            else:
                order = self.exchange.create_limit_buy_order(symbol, amount, price)
            
            self.logger.info(f"Order placed: {order}")
            return order
            
        except Exception as e:
            self.logger.error(f"Failed to place order: {str(e)}")
            return None
    
    async def _get_btc_price(self) -> float:
        """Get current BTC price"""
        try:
            if self.config.dry_run:
                # Use CoinGecko for dry run
                return self.model.crypto_provider.get_bitcoin_price() or 50000.0
            
            ticker = self.exchange.fetch_ticker('BTC/USDT')
            return float(ticker['last'])
            
        except Exception as e:
            self.logger.error(f"Failed to get BTC price: {str(e)}")
            return 50000.0  # Fallback price
    
    async def _get_portfolio_value(self) -> float:
        """Get current portfolio value"""
        try:
            if self.config.dry_run:
                return 100000.0  # Default dry run portfolio value
            
            balance = self.exchange.fetch_balance()
            # Calculate portfolio value from balance
            # This is simplified - real implementation would be more complex
            return float(balance.get('total', {}).get('USDT', 100000.0))
            
        except Exception as e:
            self.logger.error(f"Failed to get portfolio value: {str(e)}")
            return 100000.0  # Fallback value
    
    async def _monitor_positions(self):
        """Monitor existing positions for exit conditions"""
        # TODO: Implement position monitoring for:
        # - Stop losses
        # - Take profits  
        # - Signal-based exits
        # - Time-based exits
        pass
    
    async def _health_check(self) -> bool:
        """Perform health check on exchange and model"""
        try:
            # Check model health
            model_health = self.model.health_check()
            if model_health.get('overall_status') == 'error':
                self.logger.error("Model health check failed")
                return False
            
            # Check exchange connection (only for live trading)
            if not self.config.dry_run:
                try:
                    self.exchange.fetch_ticker('BTC/USDT')
                except Exception as e:
                    self.logger.error(f"Exchange connection failed: {str(e)}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current trading status"""
        return {
            'is_running': self.is_running,
            'exchange': self.config.exchange,
            'dry_run': self.config.dry_run,
            'current_position': self.current_position,
            'last_signal_check': self.last_signal_check.isoformat() if self.last_signal_check else None,
            'pending_orders': len(self.pending_orders),
            'safety_status': {
                'daily_pnl': self.safety_manager.daily_pnl,
                'consecutive_losses': self.safety_manager.consecutive_losses,
                'trades_today': self.safety_manager.trades_today
            }
        }