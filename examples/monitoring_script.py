"""
Continuous monitoring script for Bitcoin Strategic Investment Model
"""

import os
import time
import schedule
import logging
from datetime import datetime
from dotenv import load_dotenv

from bitcoin_model import BitcoinMacroModel

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bsi_monitor.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class BSIMonitor:
    """Continuous monitoring for BSI signals"""
    
    def __init__(self):
        load_dotenv()
        
        # Setup API keys
        self.api_keys = {
            'fred': os.getenv('FRED_API_KEY'),
            'glassnode': os.getenv('GLASSNODE_API_KEY'),
            'cryptoquant': os.getenv('CRYPTOQUANT_API_KEY'),
            'coingecko': os.getenv('COINGECKO_API_KEY')
        }
        
        self.model = BitcoinMacroModel(self.api_keys)
        self.portfolio_value = float(os.getenv('DEFAULT_PORTFOLIO_VALUE', 100000))
        
        logger.info(f"BSI Monitor initialized with ${self.portfolio_value:,} portfolio")
    
    def check_signals(self):
        """Check for buy signals and log results"""
        try:
            logger.info("🔄 Checking BSI signals...")
            
            # Get all signals
            all_results = self.model.get_all_signals(self.portfolio_value)
            
            # Check each scenario
            for scenario_name, result in all_results.items():
                if 'error' in result:
                    logger.error(f"❌ {scenario_name}: {result['error']}")
                    continue
                
                signals = result.get('signals', {})
                buy_signal = signals.get('buy_signal', False)
                score = signals.get('combined_score', 0.0)
                
                status = "🚨 BUY SIGNAL" if buy_signal else "⏳ Monitor"
                logger.info(f"{status} - {scenario_name}: Score {score:.3f}")
                
                if buy_signal:
                    trade_plan = result.get('trade_plan', {})
                    position_size = trade_plan.get('position_size', 0) * 100
                    position_value = trade_plan.get('position_value', 0)
                    
                    logger.info(f"  📊 Recommended Position: {position_size:.1f}% (${position_value:,.2f})")
                    logger.info(f"  💡 Rationale: {trade_plan.get('rationale', 'N/A')}")
                    
                    # Send alert (implement your notification system here)
                    self.send_alert(result)
            
            # Get strongest signal
            strongest = self.model.get_strongest_signal(self.portfolio_value)
            if strongest.get('signals', {}).get('buy_signal', False):
                logger.info("🎯 STRONGEST SIGNAL ACTIVE!")
                logger.info(f"   Scenario: {strongest.get('scenario_name')}")
                logger.info(f"   Score: {strongest['signals']['combined_score']:.3f}")
        
        except Exception as e:
            logger.error(f"Error checking signals: {str(e)}")
    
    def health_check(self):
        """Perform health check on the system"""
        try:
            logger.info("🏥 Performing health check...")
            
            health = self.model.health_check()
            overall_status = health.get('overall_status', 'unknown')
            
            if overall_status == 'healthy':
                logger.info("✅ All systems healthy")
            elif overall_status == 'degraded':
                logger.warning("⚠️  System degraded - some data providers may be offline")
            else:
                logger.error("❌ System unhealthy - critical errors detected")
            
            # Log component status
            components = health.get('components', {})
            for component, status in components.items():
                component_status = status.get('status', 'unknown')
                emoji = "✅" if component_status == 'healthy' else "❌"
                logger.info(f"  {emoji} {component}: {component_status}")
        
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
    
    def send_alert(self, signal_result):
        """
        Send alert for buy signal
        
        Implement your preferred notification method:
        - Email
        - Slack
        - Discord
        - SMS
        - Push notification
        """
        scenario_name = signal_result.get('scenario_name', 'Unknown')
        score = signal_result['signals']['combined_score']
        trade_plan = signal_result.get('trade_plan', {})
        
        message = f"""
🚨 BSI BUY SIGNAL ALERT 🚨

Scenario: {scenario_name}
Signal Strength: {score:.3f}
Position Size: {trade_plan.get('position_size', 0)*100:.1f}%
Position Value: ${trade_plan.get('position_value', 0):,.2f}

Rationale: {trade_plan.get('rationale', 'N/A')}

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        # TODO: Implement your notification system
        logger.info(f"ALERT: {message}")
        
        # Example integrations:
        # self.send_email(message)
        # self.send_slack(message)
        # self.send_discord(message)
    
    def run_scheduler(self):
        """Run the monitoring scheduler"""
        logger.info("📅 Starting BSI monitoring scheduler...")
        
        # Schedule signal checks every 30 minutes
        schedule.every(30).minutes.do(self.check_signals)
        
        # Schedule health checks every 6 hours
        schedule.every(6).hours.do(self.health_check)
        
        # Run initial checks
        self.health_check()
        self.check_signals()
        
        # Main loop
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("👋 Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Scheduler error: {str(e)}")

def main():
    """Main entry point"""
    print("🚀 BSI Monitoring System Starting...")
    print("Press Ctrl+C to stop")
    
    monitor = BSIMonitor()
    monitor.run_scheduler()

if __name__ == "__main__":
    main()