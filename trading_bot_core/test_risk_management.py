#!/usr/bin/env python3
"""
Test script for the enhanced risk management features.
"""

import sys
import os
# Add the parent directory of this script to sys.path so that trading_bot_core becomes a package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_portfolio_manager_methods():
    """Test the new methods in PortfolioManager."""
    print("Testing PortfolioManager risk management methods...")
    
    # Import after setting path
    from trading_bot_core.models.portfolio_state import PortfolioManager
    
    # Create a portfolio manager
    pm = PortfolioManager(initial_cash=100000.0, reserve_limit=50000.0)
    
    # Test 1: Dynamic position sizing
    print("\n1. Testing dynamic position sizing:")
    size_low_vol = pm.get_dynamic_position_size(0.8, "low")
    size_normal_vol = pm.get_dynamic_position_size(0.8, "normal")
    size_high_vol = pm.get_dynamic_position_size(0.8, "high")
    print(f"   Low volatility: {size_low_vol:.3f}")
    print(f"   Normal volatility: {size_normal_vol:.3f}")
    print(f"   High volatility: {size_high_vol:.3f}")
    assert 0.01 <= size_low_vol <= 0.25, "Size should be between 1% and 25%"
    assert size_low_vol > size_normal_vol > size_high_vol, "Size should decrease with volatility"
    
    # Test 2: Portfolio volatility (should be 0.0 for empty portfolio)
    print("\n2. Testing portfolio volatility:")
    vol = pm.calculate_portfolio_volatility()
    print(f"   Portfolio volatility: {vol}")
    assert vol == 0.0, "Volatility should be 0.0 for empty portfolio"
    
    # Test 3: Max drawdown
    print("\n3. Testing max drawdown:")
    dd = pm.calculate_max_drawdown()
    print(f"   Max drawdown: {dd}")
    assert dd == 0.0, "Drawdown should be 0.0 initially"
    
    # Test 4: Correlation risk (should be True for empty portfolio)
    print("\n4. Testing correlation risk:")
    corr_risk = pm.check_correlation_risk("AAPL")
    print(f"   Correlation risk for AAPL: {corr_risk}")
    assert corr_risk == True, "Should allow trade when portfolio is empty"
    
    # Test 5: Time-based exposure
    print("\n5. Testing time-based exposure:")
    time_exp = pm.check_time_based_exposure()
    print(f"   Time-based exposure check: {time_exp}")
    assert time_exp == True, "Should allow trade (placeholder implementation)"
    
    # Test 6: Sector concentration
    print("\n6. Testing sector concentration:")
    sector_conc = pm.check_sector_concentration("AAPL")
    print(f"   Sector concentration for AAPL: {sector_conc}")
    assert sector_conc == True, "Should allow trade when portfolio is empty"
    
    print("\n✅ All PortfolioManager tests passed!")

def test_imports():
    """Test that we can import the key modules."""
    print("\nTesting imports...")
    
    # Test importing orchestrator (this will test our changes)
    try:
        from trading_bot_core.controllers.orchestrator import Orchestrator
        print("✅ Orchestrator imported successfully")
    except Exception as e:
        print(f"❌ Failed to import Orchestrator: {e}")
        raise
    
    # Test importing portfolio manager
    try:
        from trading_bot_core.models.portfolio_state import PortfolioManager
        print("✅ PortfolioManager imported successfully")
    except Exception as e:
        print(f"❌ Failed to import PortfolioManager: {e}")
        raise

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Enhanced Risk Management Features")
    print("=" * 60)
    
    try:
        test_imports()
        test_portfolio_manager_methods()
        
        print("\n" + "=" * 60)
        print("🎉 ALL TESTS PASSED! Risk management enhancements are working.")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)