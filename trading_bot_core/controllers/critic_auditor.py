"""
Critic Auditor (Critic Agent - System 2)
Responsible for deep chain-of-thought reasoning, risk auditing, and market psychology analysis.
Optimized for analytical depth and nuanced analysis (temperature 0.1).
"""

import time
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from ..models.schemas import TradeSignal, PortfolioState, RiskCheckResult
from ..models.order_contracts import OrderContract
from ..broker_gateway.sandbox_broker import SandboxBroker
from ..database.position_tracker import PositionTracker
from ..database.transaction_ledger import TransactionLedger
from ..database.vector_store import VectorStore
from ..self_healing.traceback_sanitizer import safe_execute

logger = logging.getLogger(__name__)

class CriticAuditor:
    """
    Critic Agent (System 2) - Optimized for deep reasoning and analysis.
    Handles market psychology analysis, regime detection, risk scenario analysis,
    and signal validation. Operates with slightly higher temperature (0.1) 
    for nuanced analysis.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Critic Auditor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.broker = SandboxBroker(config.get('broker', {}))
        self.position_tracker = PositionTracker()
        self.transaction_ledger = TransactionLedger()
        self.vector_store = VectorStore()
        
        # Critic-specific parameters
        self.tickers = config.get('tickers', ['AAPL', 'GOOGL', 'MSFT', 'TSLA'])
        self.lookback_days = config.get('lookback_days', 30)
        
        logger.info("Critic Auditor initialized")
    
    def analyze_market_psychology(self, ticker: str = None, 
                                 lookback_days: int = None,
                                 data_sources: List[str] = None) -> Dict[str, Any]:
        """
        Analyze market sentiment, fear/greed indices, and behavioral patterns.
        Tool: analyze_market_psychology
        
        Args:
            ticker: Stock ticker symbol (optional, analyzes overall market if not provided)
            lookback_days: Number of days to look back for sentiment data
            data_sources: List of sources to consider (e.g., ["social_media", "news", "options_flow"])
            
        Returns:
            Dictionary containing market psychology analysis or error
        """
        lookback_days = lookback_days or self.lookback_days
        data_sources = data_sources or ["social_media", "news", "options_flow"]
        
        try:
            # In a real implementation, this would connect to sentiment data providers
            # For now, we'll return simulated analysis based on the vector store
            
            # Query the vector store for relevant market psychology knowledge
            query_text = f"market psychology sentiment FOMO fear greed"
            if ticker:
                query_text += f" for {ticker}"
            
            psychology_results = self.vector_store.query_market_psychology(
                query_text, n_results=3
            )
            
            # Simulate sentiment analysis
            import random
            sentiment_score = random.uniform(-0.8, 0.8)  # -1 to 1 scale
            
            # Determine dominant emotion based on score
            if sentiment_score > 0.5:
                dominant_emotion = "euphoria"
            elif sentiment_score > 0.2:
                dominant_emotion = "optimism"
            elif sentiment_score > -0.2:
                dominant_emotion = "neutral"
            elif sentiment_score > -0.5:
                dominant_emotion = "pessimism"
            else:
                dominant_emotion = "fear"
            
            # Detect patterns based on knowledge base
            detected_patterns = []
            for result in psychology_results:
                content = result.get('content', '').lower()
                if 'fomo' in content or 'fear of missing out' in content:
                    detected_patterns.append("FOMO")
                if 'distribution' in content or 'whale' in content:
                    detected_patterns.append("whale_distribution")
                if 'liquidity' in content or 'sweep' in content:
                    detected_patterns.append("liquidity_sweep")
                if 'panic' in content or 'capitulation' in content:
                    detected_patterns.append("panic_selling")
            
            # Remove duplicates
            detected_patterns = list(set(detected_patterns))
            
            return {
                "ticker": ticker or "MARKET",
                "sentiment_score": round(sentiment_score, 3),
                "dominant_emotion": dominant_emotion,
                "detected_patterns": detected_patterns,
                "confidence": round(random.uniform(0.7, 0.95), 3),
                "explanation": f"Market sentiment shows {dominant_emotion} with detected patterns: {', '.join(detected_patterns) if detected_patterns else 'none significant'}",
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Error analyzing market psychology: {e}")
            return {"error": str(e), "status": "error"}
    
    def detect_market_regime(self, indicators: List[str] = None,
                            lookback_days: int = None) -> Dict[str, Any]:
        """
        Identify the current macro market regime based on key indicators.
        Tool: detect_market_regime
        
        Args:
            indicators: Specific indicators to consider (e.g., ["VIX", "10Y_Yield", "DXY"])
            lookback_days: Number of days to look back for regime classification
            
        Returns:
            Dictionary containing market regime analysis or error
        """
        lookback_days = lookback_days or self.lookback_days
        indicators = indicators or ["VIX", "10Y_Yield", "DXY", "SPY_VOL"]
        
        try:
            # In a real implementation, this would fetch macroeconomic data
            # For now, we'll simulate regime detection
            
            import random
            
            # Simulate indicator values
            simulated_indicators = {
                "VIX": random.uniform(12, 35),  # Volatility index
                "10Y_Yield": random.uniform(3.0, 5.0),  # 10-year Treasury yield
                "DXY": random.uniform(95, 105),  # US Dollar index
                "SPY_VOL": random.uniform(0.15, 0.45)  # S&P 500 volatility
            }
            
            # Determine regime based on indicators
            vix = simulated_indicators.get("VIX", 20)
            yield_10y = simulated_indicators.get("10Y_Yield", 4.0)
            dxy = simulated_indicators.get("DXY", 100)
            
            regime = "neutral"
            confidence = 0.7
            
            # Regime logic
            if vix < 20 and yield_10y > 4.0 and dxy > 100:
                regime = "risk-on"
                confidence = 0.85
                explanation = "Low VIX, rising yields, and strong dollar indicate a risk-on environment."
            elif vix > 25 or (yield_10y < 3.5 and dxy < 98):
                regime = "risk-off"
                confidence = 0.8
                explanation = "Elevated VIX or falling yields with weak dollar indicate risk-off sentiment."
            elif yield_10y > 4.5 and simulated_indicators.get("SPY_VOL", 0.2) > 0.3:
                regime = "inflationary"
                confidence = 0.75
                explanation = "Rising yields and high volatility suggest inflationary pressures."
            elif yield_10y < 3.0 and dxy > 102:
                regime = "deflationary"
                confidence = 0.7
                explanation = "Falling yields and strong dollar suggest deflationary concerns."
            else:
                regime = "neutral"
                confidence = 0.6
                explanation = "Mixed signals suggest a neutral or transitioning market regime."
            
            return {
                "regime": regime,
                "confidence": round(confidence, 3),
                "supporting_indicators": {k: round(v, 2) for k, v in simulated_indicators.items()},
                "explanation": explanation,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Error detecting market regime: {e}")
            return {"error": str(e), "status": "error"}
    
    def analyze_risk_scenarios(self, portfolio: Dict[str, Any] = None,
                              trade_proposal: Dict[str, Any] = None,
                              scenarios: List[str] = None) -> Dict[str, Any]:
        """
        Performs stress testing and scenario analysis on a proposed trade or portfolio.
        Tool: analyze_risk_scenarios
        
        Args:
            portfolio: Current portfolio state (from get_portfolio tool)
            trade_proposal: Proposed trade details (ticker, action, quantity, price)
            scenarios: List of scenarios to test (e.g., ["market_crash", "liquidity_dry_up", "volatility_spike"])
            
        Returns:
            Dictionary containing risk scenario analysis or error
        """
        scenarios = scenarios or ["market_crash", "liquidity_dry_up", "volatility_spike", "interest_rate_shock"]
        
        try:
            # Use provided data or fetch current state
            if portfolio is None:
                portfolio_result = safe_execute(self.position_tracker.get_state)
                if portfolio_result is None:
                    return {"error": "Unable to get portfolio state", "status": "error"}
                portfolio = {
                    "cash_balance": portfolio_result.cash_balance,
                    "total_equity": portfolio_result.total_equity,
                    "realized_pnl": portfolio_result.realized_pnl,
                    "unrealized_pnl": portfolio_result.unrealized_pnl,
                    "positions": [
                        {
                            "ticker": pos.ticker,
                            "quantity": pos.quantity,
                            "avg_cost": pos.avg_cost,
                            "current_price": pos.current_price,
                            "market_value": pos.market_value,
                            "unrealized_pnl": pos.unrealized_pnl
                        }
                        for pos in portfolio_result.positions
                    ]
                }
            
            if trade_proposal is None:
                # Default trade proposal for analysis
                trade_proposal = {
                    "ticker": "AAPL",
                    "action": "BUY",
                    "quantity": 100,
                    "price": 150.0
                }
            
            # Calculate base portfolio metrics
            total_equity = portfolio.get('total_equity', 50000.0)
            cash_balance = portfolio.get('cash_balance', 50000.0)
            
            # Estimate portfolio Value at Risk (VaR) - simplified
            # In reality, this would use historical returns or Monte Carlo simulation
            portfolio_var_95 = total_equity * 0.02  # 2% VaR at 95% confidence
            expected_shortfall = portfolio_var_95 * 1.5  # Expected shortfall
            
            # Analyze each scenario
            scenario_impacts = {}
            
            for scenario in scenarios:
                if scenario == "market_crash":
                    # 20% market drop
                    portfolio_change_pct = -20.0
                    new_cash_reserve = cash_balance  # Cash unchanged in crash (initially)
                    passes_invariant = new_cash_reserve >= 50000.0  # Check cash reserve
                    
                elif scenario == "liquidity_dry_up":
                    # 5% portfolio impact due to widened spreads
                    portfolio_change_pct = -5.0
                    new_cash_reserve = cash_balance
                    passes_invariant = new_cash_reserve >= 50000.0
                    
                elif scenario == "volatility_spike":
                    # 10% impact from increased volatility
                    portfolio_change_pct = -10.0
                    new_cash_reserve = cash_balance
                    passes_invariant = new_cash_reserve >= 50000.0
                    
                elif scenario == "interest_rate_shock":
                    # 15% impact from rising rates
                    portfolio_change_pct = -15.0
                    new_cash_reserve = cash_balance
                    passes_invariant = new_cash_reserve >= 50000.0
                    
                else:
                    # Generic scenario
                    portfolio_change_pct = -10.0
                    new_cash_reserve = cash_balance
                    passes_invariant = new_cash_reserve >= 50000.0
                
                scenario_impacts[scenario] = {
                    "portfolio_change_pct": portfolio_change_pct,
                    "new_cash_reserve": new_cash_reserve,
                    "passes_invariant": passes_invariant
                }
            
            # Generate recommendation based on scenario analysis
            failing_scenarios = [s for s, impact in scenario_impacts.items() if not impact['passes_invariant']]
            
            if failing_scenarios:
                recommendation = f"Reduce position size to pass scenarios: {', '.join(failing_scenarios)}"
            else:
                recommendation = "Trade passes all scenario tests"
            
            return {
                "portfolio_var_95": round(portfolio_var_95, 2),
                "expected_shortfall": round(expected_shortfall, 2),
                "scenario_impacts": scenario_impacts,
                "recommendation": recommendation,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Error analyzing risk scenarios: {e}")
            return {"error": str(e), "status": "error"}
    
    def validate_trade_signal(self, signal: Dict[str, Any] = None,
                             execution: Dict[str, Any] = None,
                             market_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Validates an executed trade against the original signal and checks for slippage, fees, and adherence.
        Tool: validate_trade_signal
        
        Args:
            signal: Original trade signal (ticker, action, quantity, target price)
            execution: Executed trade details (from order execution)
            market_data: Market data around the time of execution (for slippage calculation)
            
        Returns:
            Dictionary containing signal validation results or error
        """
        try:
            # Use provided data or simulate
            if signal is None:
                signal = {
                    "ticker": "AAPL",
                    "action": "BUY",
                    "quantity": 100,
                    "target_price": 150.0
                }
            
            if execution is None:
                execution = {
                    "ticker": "AAPL",
                    "action": "BUY",
                    "quantity": 100,
                    "execution_price": 150.5,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "fees": 1.0,
                    "slippage": 0.05
                }
            
            # Calculate adherence score (how closely execution followed signal)
            adherence_score = 1.0  # Start with perfect score
            
            # Check ticker match
            if signal.get('ticker') != execution.get('ticker'):
                adherence_score -= 0.3
            
            # Check action match
            if signal.get('action') != execution.get('action'):
                adherence_score -= 0.4  # Major deviation
            
            # Check quantity (allow 10% tolerance)
            signal_qty = signal.get('quantity', 0)
            exec_qty = execution.get('quantity', 0)
            if signal_qty > 0:
                qty_diff = abs(signal_qty - exec_qty) / signal_qty
                if qty_diff > 0.1:  # More than 10% difference
                    adherence_score -= min(0.3, qty_diff)  # Penalize up to 0.3
            
            # Check price vs target (if target price provided)
            target_price = signal.get('target_price')
            exec_price = execution.get('execution_price')
            if target_price is not None and exec_price is not None:
                price_diff = abs(target_price - exec_price) / target_price
                if price_diff > 0.02:  # More than 2% difference from target
                    adherence_score -= min(0.2, price_diff * 10)  # Penalize for slippage from target
            
            # Ensure adherence score is between 0 and 1
            adherence_score = max(0.0, min(1.0, adherence_score))
            
            # Extract slippage and fees from execution
            slippage = execution.get('slippage', 0.0)
            fees = execution.get('fees', 0.0)
            
            # Generate notes
            notes = []
            if adherence_score < 0.9:
                notes.append("Execution deviated from signal")
            if slippage > 0.01:
                notes.append(f"High slippage detected: {slippage:.4f}")
            if fees > 5.0:
                notes.append(f"High fees: ${fees:.2f}")
            if not notes:
                notes.append("Execution adhered closely to signal")
            
            return {
                "adherence_score": round(adherence_score, 3),
                "slippage": round(slippage, 4),
                "fees": round(fees, 2),
                "notes": "; ".join(notes),
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Error validating trade signal: {e}")
            return {"error": str(e), "status": "error"}
    
    def query_knowledge_base(self, query: str, n_results: int = 5,
                            filter_dict: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Queries the embedded ChromaDB vector store for relevant market psychology, 
        regime indicators, or historical cases.
        Tool: query_knowledge_base
        
        Args:
            query: Natural language query to search the knowledge base
            n_results: Number of results to return
            filter_dict: Optional metadata filter (e.g., {"category": "liquidity_sweeps"})
            
        Returns:
            Dictionary containing query results or error
        """
        try:
            results = self.vector_store.query_knowledge(query, n_results, filter_dict)
            
            # Format results for return
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "content": result.get('content', ''),
                    "metadata": result.get('metadata', {}),
                    "similarity": round(result.get('similarity', 0.0), 3)
                })
            
            return {
                "results": formatted_results,
                "count": len(formatted_results),
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Error querying knowledge base: {e}")
            return {"error": str(e), "status": "error"}

# Example usage (for testing)
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Configuration
    config = {
        'tickers': ['AAPL', 'GOOGL', 'MSFT'],
        'lookback_days': 30,
        'broker': {
            'initial_balance': 50000.0,
            'commission_per_trade': 0.001,
            'slippage_model': 'fixed'
        }
    }
    
    # Create critic
    critic = CriticAuditor(config)
    
    # Connect broker
    if critic.broker.connect():
        print("Connected to broker")
        
        # Test market psychology analysis
        psychology = critic.analyze_market_psychology("AAPL")
        print(f"Market psychology: {psychology.get('status')}")
        if psychology.get('status') == 'success':
            print(f"  Sentiment: {psychology.get('sentiment_score')}")
            print(f"  Emotion: {psychology.get('dominant_emotion')}")
        
        # Test regime detection
        regime = critic.detect_market_regime()
        print(f"Market regime: {regime.get('status')}")
        if regime.get('status') == 'success':
            print(f"  Regime: {regime.get('regime')}")
            print(f"  Confidence: {regime.get('confidence')}")
        
        # Test risk scenario analysis
        portfolio_state = {
            'total_equity': 100000.0,
            'cash_balance': 60000.0,
            'realized_pnl': 5000.0,
            'unrealized_pnl': 2000.0,
            'positions': []
        }
        trade_proposal = {
            'ticker': 'AAPL',
            'action': 'BUY',
            'quantity': 100,
            'price': 150.0
        }
        risk_analysis = critic.analyze_risk_scenarios(portfolio_state, trade_proposal)
        print(f"Risk analysis: {risk_analysis.get('status')}")
        if risk_analysis.get('status') == 'success':
            print(f"  VaR 95: ${risk_analysis.get('portfolio_var_95'):.2f}")
            print(f"  Recommendation: {risk_analysis.get('recommendation')}")
        
        # Test knowledge base query
        kb_results = critic.query_knowledge_base("What is FOMO in trading?", n_results=2)
        print(f"Knowledge query: {kb_results.get('status')}")
        if kb_results.get('status') == 'success':
            print(f"  Found {kb_results.get('count')} results")
        
        # Disconnect
        critic.broker.disconnect()
    else:
        print("Failed to connect to broker")