"""
Generator Worker (Worker Agent - System 1)
Responsible for procedural execution, fast tool calling, and JSON parsing.
Optimized for speed and deterministic outputs (temperature 0.0).
"""

import time
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

from ..models.schemas import TradeSignal, PortfolioState
from ..models.order_contracts import OrderContract, OrderAction, OrderType
from ..broker_gateway.sandbox_broker import SandboxBroker
from ..database.position_tracker import PositionTracker
from ..database.vector_store import VectorStore
from ..self_healing.traceback_sanitizer import safe_execute

logger = logging.getLogger(__name__)

class GeneratorWorker:
    """
    Worker Agent (System 1) - Optimized for procedural execution and fast tool calling.
    Handles market data fetching, technical indicator calculation, and order execution preparation.
    Operates with low temperature (0.0) for deterministic outputs.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Generator Worker.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.broker = SandboxBroker(config.get('broker', {}))
        self.position_tracker = PositionTracker()
        self.vector_store = VectorStore()
        
        # Worker-specific parameters
        self.tickers = config.get('tickers', ['AAPL', 'GOOGL', 'MSFT', 'TSLA'])
        self.timeframe = config.get('timeframe', '1D')
        self.lookback_period = config.get('lookback_period', 20)
        
        logger.info("Generator Worker initialized")
    
    def fetch_market_data(self, ticker: str, timeframe: str = None, limit: int = 100) -> Dict[str, Any]:
        """
        Fetch market data for a given ticker.
        Tool: fetch_market_data
        
        Args:
            ticker: Stock ticker symbol
            timeframe: Data timeframe (optional)
            limit: Number of data points to retrieve
            
        Returns:
            Dictionary containing market data or error
        """
        timeframe = timeframe or self.timeframe
        try:
            data = safe_execute(self.broker.get_market_data, ticker, timeframe, limit)
            if data is None:
                return {"error": "Failed to fetch market data", "status": "error"}
            
            return {
                "ticker": ticker,
                "timeframe": timeframe,
                "data": data,
                "count": len(data),
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Error fetching market data for {ticker}: {e}")
            return {"error": str(e), "status": "error"}
    
    def calculate_technical_indicator(self, ticker: str, indicator: str, 
                                   timeframe: str = None, period: int = None,
                                   apply_to: str = "close") -> Dict[str, Any]:
        """
        Calculate a technical indicator for a given ticker.
        Tool: calculate_technical_indicator
        
        Args:
            ticker: Stock ticker symbol
            indicator: Indicator name (RSI, MACD, BBANDS, ATR, OBV)
            timeframe: Data timeframe (optional)
            period: Indicator period (optional)
            apply_to: Price field to apply indicator to
            
        Returns:
            Dictionary containing indicator values or error
        """
        timeframe = timeframe or self.timeframe
        # Set default periods for common indicators
        if period is None:
            period_map = {"RSI": 14, "MACD": 26, "BBANDS": 20, "ATR": 14, "OBV": None}
            period = period_map.get(indicator, 14)
        
        try:
            # In a real implementation, this would calculate the indicator
            # For now, we'll return simulated data
            market_data = self.fetch_market_data(ticker, timeframe, limit=period+10)
            if market_data.get("status") != "success":
                return market_data
            
            # Simulate indicator calculation
            import random
            base_value = 50.0  # Neutral value for most indicators
            if indicator == "RSI":
                # RSI oscillates between 0 and 100
                value = base_value + random.uniform(-20, 20)
                value = max(0, min(100, value))
            elif indicator == "MACD":
                # MACD can be positive or negative
                value = random.uniform(-2, 2)
            elif indicator == "BBANDS":
                # Bollinger Bands - we'll return the middle band (SMA)
                value = base_value + random.uniform(-5, 5)
            elif indicator == "ATR":
                # ATR is always positive
                value = abs(random.uniform(0.5, 3.0))
            elif indicator == "OBV":
                # OBV is cumulative volume - can be large positive or negative
                value = random.uniform(-1000000, 1000000)
            else:
                value = random.uniform(0, 100)
            
            # Generate historical values
            values = []
            market_data_list = market_data["data"]
            for i, data_point in enumerate(market_data_list[-period:]):  # Last 'period' points
                # Add some variation to each historical value
                hist_value = value + random.uniform(-2, 2)
                values.append({
                    "timestamp": data_point["timestamp"],
                    "value": max(0, hist_value) if indicator in ["RSI", "ATR"] else hist_value
                })
            
            return {
                "ticker": ticker,
                "indicator": indicator,
                "timeframe": timeframe,
                "period": period,
                "values": values,
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Error calculating {indicator} for {ticker}: {e}")
            return {"error": str(e), "status": "error"}
    
    def execute_order(self, ticker: str, action: str, quantity: int,
                     order_type: str = "MARKET", price: float = None,
                     stop_price: float = None) -> Dict[str, Any]:
        """
        Execute a buy or sell order in the paper trading sandbox.
        Tool: execute_order
        
        Args:
            ticker: Stock ticker symbol
            action: "BUY" or "SELL"
            quantity: Number of shares
            order_type: Order type ("MARKET", "LIMIT", "STOP", "STOP_LIMIT")
            price: Limit price (required for LIMIT and STOP_LIMIT)
            stop_price: Stop price (required for STOP and STOP_LIMIT)
            
        Returns:
            Dictionary containing order execution details or error
        """
        try:
            # Validate inputs
            if action not in ["BUY", "SELL"]:
                return {"error": "Action must be BUY or SELL", "status": "error"}
            
            if quantity <= 0:
                return {"error": "Quantity must be positive", "status": "error"}
            
            # Create order contract
            from ..models.order_contracts import OrderAction, OrderType, OrderContract
            
            order_action = OrderAction.BUY if action == "BUY" else OrderAction.SELL
            order_type_enum = OrderType.MARKET  # Default
            
            if order_type == "LIMIT":
                order_type_enum = OrderType.LIMIT
            elif order_type == "STOP":
                order_type_enum = OrderType.STOP
            elif order_type == "STOP_LIMIT":
                order_type_enum = OrderType.STOP_LIMIT
            
            order = OrderContract(
                ticker=ticker,
                action=order_action,
                quantity=quantity,
                order_type=order_type_enum,
                price=price,
                stop_price=stop_price,
                source_component="generator_worker"
            )
            
            # Execute order via broker
            executed_order = safe_execute(self.broker.place_order, order)
            if executed_order is None:
                return {"error": "Order execution failed", "status": "error"}
            
            # Return execution details
            return {
                "order_id": executed_order.order_id,
                "ticker": executed_order.ticker,
                "action": executed_order.action.value,
                "quantity": executed_order.executed_quantity,
                "order_type": executed_order.order_type.value,
                "execution_price": executed_order.execution_price,
                "timestamp": executed_order.execution_timestamp.isoformat() + "Z" if executed_order.execution_timestamp else None,
                "status": executed_order.status.value,
                "fees": executed_order.fees,
                "slippage": executed_order.slippage
            }
        except Exception as e:
            logger.error(f"Error executing order: {e}")
            return {"error": str(e), "status": "error"}
    
    def get_portfolio(self) -> Dict[str, Any]:
        """
        Retrieve current portfolio state including cash, positions, and P&L.
        Tool: get_portfolio
        
        Returns:
            Dictionary containing portfolio state or error
        """
        try:
            state = self.position_tracker.get_state()
            return {
                "cash_balance": state.cash_balance,
                "total_equity": state.total_equity,
                "realized_pnl": state.realized_pnl,
                "unrealized_pnl": state.unrealized_pnl,
                "positions": [
                    {
                        "ticker": pos.ticker,
                        "quantity": pos.quantity,
                        "avg_cost": pos.avg_cost,
                        "current_price": pos.current_price,
                        "market_value": pos.market_value,
                        "unrealized_pnl": pos.unrealized_pnl
                    }
                    for pos in state.positions
                ],
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Error getting portfolio: {e}")
            return {"error": str(e), "status": "error"}
    
    def check_trade_risk(self, ticker: str, action: str, quantity: int, price: float) -> Dict[str, Any]:
        """
        Validate a proposed trade against risk invariants.
        Tool: check_trade_risk
        
        Args:
            ticker: Stock ticker symbol
            action: "BUY" or "SELL"
            quantity: Number of shares
            price: Expected execution price
            
        Returns:
            Dictionary containing risk check results
        """
        try:
            # Validate inputs
            if action not in ["BUY", "SELL"]:
                return {"error": "Action must be BUY or SELL", "status": "error"}
            
            if quantity <= 0:
                return {"error": "Quantity must be positive", "status": "error"}
            
            if price <= 0:
                return {"error": "Price must be positive", "status": "error"}
            
            # Get current portfolio state
            state = self.position_tracker.get_state()
            
            # Calculate trade cost/revenue
            trade_value = quantity * price
            
            violations = []
            adjusted_quantity = quantity
            
            # Check cash reserve for BUY orders
            if action == "BUY":
                trade_cost = trade_value  # Simplified - doesn't include fees
                available_cash = state.cash_balance - state.reserve_limit
                
                if trade_cost > available_cash:
                    violations.append("cash_reserve")
                    # Calculate maximum affordable quantity
                    if price > 0:
                        adjusted_quantity = int(available_cash / price)
                    else:
                        adjusted_quantity = 0
                
                # Check position size limit
                position_value = trade_value
                total_equity_after = state.total_equity  # Simplified
                position_pct = position_value / total_equity_after if total_equity_after > 0 else 0
                
                max_position_pct = 0.1  # 10% max per position
                if position_pct > max_position_pct:
                    violations.append("position_size")
                    # Calculate maximum quantity based on position limit
                    max_position_value = total_equity_after * max_position_pct
                    if price > 0:
                        adjusted_quantity = min(adjusted_quantity, int(max_position_value / price))
            
            # Check if we have sufficient position for SELL orders
            elif action == "SELL":
                current_position = 0
                for pos in state.positions:
                    if pos.ticker == ticker:
                        current_position = pos.quantity
                        break
                
                if current_position < quantity:
                    violations.append("insufficient_position")
                    adjusted_quantity = current_position
            
            approved = len(violations) == 0
            
            return {
                "approved": approved,
                "violations": violations,
                "adjusted_quantity": max(0, adjusted_quantity),
                "reason": "Trade complies with all risk invariants" if approved else f"Violations: {', '.join(violations)}",
                "status": "success"
            }
        except Exception as e:
            logger.error(f"Error checking trade risk: {e}")
            return {"error": str(e), "status": "error"}
    
    def generate_signal(self, ticker: str) -> Optional[TradeSignal]:
        """
        Generate a trade signal based on technical analysis.
        This is the core signal generation logic for the Worker Agent.
        
        Args:
            ticker: Stock ticker symbol to analyze
            
        Returns:
            TradeSignal if a signal is generated, None otherwise
        """
        try:
            # Fetch market data
            market_data_result = self.fetch_market_data(ticker, limit=50)
            if market_data_result.get("status") != "success":
                logger.warning(f"Could not fetch market data for {ticker}")
                return None
            
            market_data = market_data_result["data"]
            if len(market_data) < 20:  # Need enough data for indicators
                logger.warning(f"Insufficient market data for {ticker}")
                return None
            
            # Calculate some technical indicators
            rsi_result = self.calculate_technical_indicator(ticker, "RSI", period=14)
            macd_result = self.calculate_technical_indicator(ticker, "MACD")
            
            # Simple signal generation logic (placeholder for more sophisticated logic)
            current_price = market_data[-1]["close"]
            
            # Get RSI value (if available)
            rsi_value = 50.0  # Default neutral
            if rsi_result.get("status") == "success" and rsi_result.get("values"):
                rsi_value = rsi_result["values"][-1]["value"]
            
            # Generate signal based on RSI (simplified)
            signal = None
            if rsi_value < 30:  # Oversold - potential buy signal
                signal = TradeSignal(
                    ticker=ticker,
                    action=OrderAction.BUY,
                    quantity=100,  # Will be adjusted by risk checks
                    target_price=current_price * 1.02,
                    stop_loss=current_price * 0.95,
                    take_profit=current_price * 1.1,
                    confidence=0.7,
                    timestamp=datetime.utcnow(),
                    source="worker_technical",
                    rationale=f"RSI oversold ({rsi_value:.1f}) - potential buy signal"
                )
            elif rsi_value > 70:  # Overbought - potential sell signal
                signal = TradeSignal(
                    ticker=ticker,
                    action=OrderAction.SELL,
                    quantity=100,  # Will be adjusted by risk checks
                    target_price=current_price * 0.98,
                    stop_loss=current_price * 1.05,
                    take_profit=current_price * 0.9,
                    confidence=0.7,
                    timestamp=datetime.utcnow(),
                    source="worker_technical",
                    rationale=f"RSI overbought ({rsi_value:.1f}) - potential sell signal"
                )
            
            return signal
        except Exception as e:
            logger.error(f"Error generating signal for {ticker}: {e}")
            return None

# Example usage (for testing)
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Configuration
    config = {
        'tickers': ['AAPL', 'GOOGL', 'MSFT'],
        'timeframe': '1D',
        'lookback_period': 20,
        'broker': {
            'initial_balance': 50000.0,
            'commission_per_trade': 0.001,
            'slippage_model': 'fixed'
        }
    }
    
    # Create worker
    worker = GeneratorWorker(config)
    
    # Connect broker
    if worker.broker.connect():
        print("Connected to broker")
        
        # Test market data fetch
        market_data = worker.fetch_market_data("AAPL")
        print(f"Market data fetch: {market_data.get('status')}")
        
        # Test technical indicator calculation
        rsi_data = worker.calculate_technical_indicator("AAPL", "RSI")
        print(f"RSI calculation: {rsi_data.get('status')}")
        
        # Test signal generation
        signal = worker.generate_signal("AAPL")
        if signal:
            print(f"Generated signal: {signal.action} {signal.quantity} {signal.ticker}")
        else:
            print("No signal generated")
        
        # Test portfolio
        portfolio = worker.get_portfolio()
        print(f"Portfolio status: {portfolio.get('status')}")
        
        # Test risk check
        risk_check = worker.check_trade_risk("AAPL", "BUY", 100, 150.0)
        print(f"Risk check: {risk_check.get('approved')}")
        
        # Disconnect
        worker.broker.disconnect()
    else:
        print("Failed to connect to broker")