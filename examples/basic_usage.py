"""
Basic usage example for Bitcoin Strategic Investment Model
"""

import os
import asyncio
import logging
from dotenv import load_dotenv

from bitcoin_model import BitcoinMacroModel
from bitcoin_model.exchange_integration import AutomatedTrader, TradingConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Basic usage example"""
    # Load environment variables
    load_dotenv()
    
    # Setup API keys
    api_keys = {
        'fred': os.getenv('FRED_API_KEY'),
        'glassnode': os.getenv('GLASSNODE_API_KEY'),
        'cryptoquant': os.getenv('CRYPTOQUANT_API_KEY'),
        'coingecko': os.getenv('COINGECKO_API_KEY')
    }
    
    print("🚀 Bitcoin Strategic Investment Model - Basic Usage Example")
    print("=" * 60)
    
    # Initialize model
    print("Initializing model...")
    model = BitcoinMacroModel(api_keys)
    
    # Run health check
    print("\n📊 Running health check...")
    health = model.health_check()
    print(f"Overall status: {health['overall_status']}")
    
    # Check individual scenarios
    portfolio_value = 100000  # $100k portfolio
    
    print(f"\n💰 Analyzing signals for ${portfolio_value:,} portfolio...")
    
    # Scenario 1: Fed Pivot + Exchange Reserves
    print("\n📈 Scenario 1: Fed Pivot + Low Exchange Reserves")
    result1 = model.run_analysis(scenario=1, portfolio_value=portfolio_value)
    
    signals1 = result1['signals']
    print(f"  Fed Score: {signals1['fed_score']:.3f}")
    print(f"  Reserve Score: {signals1['reserve_score']:.3f}")
    print(f"  Combined Score: {signals1['combined_score']:.3f}")
    print(f"  Buy Signal: {'✅ YES' if signals1['buy_signal'] else '❌ NO'}")
    
    if signals1['buy_signal']:
        trade_plan = result1['trade_plan']
        print(f"  📋 Position Size: {trade_plan['position_size']*100:.1f}%")
        print(f"  💵 Position Value: ${trade_plan['position_value']:,.2f}")
        print(f"  ⏰ Entry Strategy: {trade_plan['entry_strategy']}")
    
    # Scenario 2: M2 + Miner Capitulation
    print("\n📈 Scenario 2: M2 Expansion + Miner Capitulation")
    result2 = model.run_analysis(scenario=2, portfolio_value=portfolio_value)
    
    signals2 = result2['signals']
    print(f"  M2 Score: {signals2['m2_score']:.3f}")
    print(f"  Miner Score: {signals2['miner_score']:.3f}")
    print(f"  Combined Score: {signals2['combined_score']:.3f}")
    print(f"  Buy Signal: {'✅ YES' if signals2['buy_signal'] else '❌ NO'}")
    
    if signals2['buy_signal']:
        trade_plan = result2['trade_plan']
        print(f"  📋 Position Size: {trade_plan['position_size']*100:.1f}%")
        print(f"  💵 Position Value: ${trade_plan['position_value']:,.2f}")
        print(f"  ⏰ Entry Strategy: {trade_plan['entry_strategy']}")
    
    # Get strongest signal
    print("\n🎯 Strongest Signal Analysis")
    strongest = model.get_strongest_signal(portfolio_value)
    
    if strongest.get('signals', {}).get('buy_signal', False):
        print(f"✅ STRONG BUY SIGNAL DETECTED!")
        print(f"Scenario: {strongest.get('scenario_name', 'Unknown')}")
        print(f"Signal Strength: {strongest['signals']['combined_score']:.3f}")
        
        trade_plan = strongest.get('trade_plan', {})
        print(f"\n📋 Recommended Action:")
        print(f"  Position Size: {trade_plan.get('position_size', 0)*100:.1f}%")
        print(f"  Position Value: ${trade_plan.get('position_value', 0):,.2f}")
        print(f"  Entry Strategy: {trade_plan.get('entry_strategy', 'N/A')}")
        print(f"  Hold Period: {trade_plan.get('hold_period', 'N/A')}")
        
        print(f"\n💡 Rationale: {trade_plan.get('rationale', 'N/A')}")
    else:
        print("❌ No strong buy signals detected at this time")
    
    print("\n" + "=" * 60)
    print("✅ Analysis complete!")
    
    # Optional: Show how to use automated trading (DRY RUN)
    show_trading_example = input("\nWould you like to see automated trading example? (y/n): ")
    
    if show_trading_example.lower() == 'y':
        print("\n🤖 Automated Trading Example (DRY RUN)")
        print("=" * 60)
        
        # This would require API keys to be set up
        if not os.getenv('BINANCE_API_KEY'):
            print("⚠️  No exchange API keys configured - showing configuration example only")
            
            config_example = TradingConfig(
                exchange='binance',
                api_key='your_api_key_here',
                api_secret='your_secret_here',
                testnet=True,
                dry_run=True,
                max_position_size=0.05  # 5% max position
            )
            
            print("Example trading configuration:")
            print(f"  Exchange: {config_example.exchange}")
            print(f"  Testnet: {config_example.testnet}")
            print(f"  Dry Run: {config_example.dry_run}")
            print(f"  Max Position: {config_example.max_position_size*100}%")
            
            print("\nTo enable automated trading:")
            print("1. Set up exchange API keys in .env file")
            print("2. Start with testnet=True and dry_run=True")
            print("3. Test thoroughly before using real money")
            
        else:
            print("🔄 This would start the automated trader in DRY RUN mode")
            print("(Implementation would go here)")

if __name__ == "__main__":
    main()