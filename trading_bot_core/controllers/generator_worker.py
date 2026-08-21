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

from trading_bot_core.models.schemas import TradeSignal, PortfolioState
from trading_bot_core.models.order_contracts import OrderContract, OrderAction, OrderType
from trading_bot_core.broker_gateway.sandbox_broker import SandboxBroker
from trading_bot_core.broker_gateway.alpaca_broker import AlpacaBroker
from trading_bot_core.broker_gateway.bursa_malaysia_broker import BursaMalaysiaBroker
from trading_bot_core.models.portfolio_state import PortfolioManager
from trading_bot_core.database.vector_store import VectorStore
from trading_bot_core.self_healing.traceback_sanitizer import safe_execute
from trading_bot_core.controllers.llm_client import OllamaClient

logger = logging.getLogger(__name__)

class GeneratorWorker:
    """
    Worker Agent (System 1) - Optimized for procedural execution and fast tool calling.
    Handles market data fetching, technical indicator calculation, and order execution preparation.
    Powered by qwen2.5-coder:7b via local Ollama endpoint with fallback heuristics.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Generator Worker.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        broker_cfg = config.get('broker', {})
        init_cash = broker_cfg.get('sandbox_initial_balance') or broker_cfg.get('initial_balance') or config.get('initial_cash', 100000.0)
        b_type = str(broker_cfg.get('type', 'bursa')).lower()
        if b_type in ['bursa', 'moomoo', 'klse', 'myx', 'malaysia'] or config.get('tickers', ['1155.KL'])[0].endswith('.KL'):
            self.broker = BursaMalaysiaBroker(broker_cfg)
        elif b_type == 'alpaca' or broker_cfg.get('live_enabled') or bool(config.get('alpaca_api_key')):
            self.broker = AlpacaBroker(broker_cfg)
        else:
            self.broker = SandboxBroker(broker_cfg)
        self.min_cash_reserve = config.get('system', {}).get('cash_reserve', config.get('min_cash_reserve', 50000.0))
        self.position_tracker = PortfolioManager(initial_cash=init_cash, reserve_limit=self.min_cash_reserve)
        self.vector_store = VectorStore()
        
        # LLM integration
        ollama_url = config.get('model_routing', {}).get('ollama_base_url', 'http://localhost:11434') if isinstance(config.get('model_routing'), dict) else 'http://localhost:11434'
        self.llm_client = OllamaClient(base_url=ollama_url)
        self.worker_model = "qwen2.5-coder:7b"
        if isinstance(config.get('model_routing'), dict) and 'worker_engine' in config['model_routing']:
            self.worker_model = config['model_routing']['worker_engine'].get('primary', 'qwen2.5-coder:7b')
        
        # Worker-specific parameters
        self.tickers = config.get('tickers', ['AAPL', 'GOOGL', 'MSFT', 'TSLA'])
        self.timeframe = config.get('timeframe', '1D')
        self.lookback_period = config.get('lookback_period', 20)
        
        logger.info(f"Generator Worker initialized (Model: {self.worker_model}, Ollama: {ollama_url})")
    
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
        Generate a trade signal using the Researcher Persona (Quinn) powered by Ollama (qwen2.5-coder:7b),
        with deterministic quantitative fallback.
        
        Args:
            ticker: Stock ticker symbol to analyze
            
        Returns:
            TradeSignal if a signal is generated, None otherwise
        """
        try:
            # 1. Fetch market data
            market_data_result = self.fetch_market_data(ticker, limit=50)
            if market_data_result.get("status") != "success":
                logger.warning(f"Could not fetch market data for {ticker}")
                return None
            
            market_data = market_data_result["data"]
            if len(market_data) < 20:
                logger.warning(f"Insufficient market data for {ticker}")
                return None
            
            # 2. Calculate indicators
            rsi_result = self.calculate_technical_indicator(ticker, "RSI", period=14)
            macd_result = self.calculate_technical_indicator(ticker, "MACD")
            bbands_result = self.calculate_technical_indicator(ticker, "BBANDS")
            
            current_price = float(market_data[-1]["close"])
            high_price = float(market_data[-1].get("high", current_price))
            low_price = float(market_data[-1].get("low", current_price))
            volume = float(market_data[-1].get("volume", 0))
            
            rsi_value = 50.0
            if rsi_result.get("status") == "success" and rsi_result.get("values"):
                rsi_value = float(rsi_result["values"][-1]["value"])
            
            macd_value = 0.0
            macd_signal = 0.0
            if macd_result.get("status") == "success" and macd_result.get("values"):
                macd_value = float(macd_result["values"][-1].get("macd", 0.0))
                macd_signal = float(macd_result["values"][-1].get("signal", 0.0))

            portfolio_state = self.position_tracker.get_state()
            current_qty = self.position_tracker.get_position_quantity(ticker)
            available_cash = portfolio_state.cash_balance - portfolio_state.reserve_limit
            
            # 3. LLM Strategy: Load Persona and Tool Manifest
            persona_prompt = self.llm_client.load_persona("finance-investment-researcher.md")
            tools_manifest = self.llm_client.load_manifest("worker_tools_manifest.md")
            
            system_message = (
                f"{persona_prompt}\n\n"
                f"### AVAILABLE SYSTEM TOOLS:\n{tools_manifest}\n\n"
                "You must respond ONLY with a valid JSON object matching this schema:\n"
                "{\n"
                '  "action": "BUY" | "SELL" | "HOLD",\n'
                '  "confidence": 0.0 to 1.0,\n'
                '  "target_price": number,\n'
                '  "stop_loss": number,\n'
                '  "take_profit": number,\n'
                '  "suggested_quantity": integer,\n'
                '  "thesis": "detailed investment thesis and indicator analysis"\n'
                "}"
            )
            
            user_message = (
                f"Analyze trading opportunity for ticker {ticker}:\n"
                f"- Current Price: ${current_price:.2f} (High: ${high_price:.2f}, Low: ${low_price:.2f}, Volume: {volume:,.0f})\n"
                f"- RSI(14): {rsi_value:.2f}\n"
                f"- MACD: {macd_value:.4f}, Signal: {macd_signal:.4f}\n"
                f"- Portfolio Cash Available: ${max(0, available_cash):.2f}\n"
                f"- Current Owned Position: {current_qty} shares\n"
                f"- Equity Reserve Floor: ${portfolio_state.reserve_limit:,.2f}\n\n"
                "Evaluate whether a BUY, SELL, or HOLD signal should be issued based on market conditions, risk-reward (>= 1:2), and technical setups."
            )
            
            # Try Ollama LLM call
            llm_response = self.llm_client.chat(
                model=self.worker_model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.0,
                format_json=True
            )
            
            if llm_response.get("status") == "success" and llm_response.get("json_data"):
                data = llm_response["json_data"]
                action_str = str(data.get("action", "HOLD")).upper().strip()
                
                if action_str in ["BUY", "SELL"]:
                    action = OrderAction.BUY if action_str == "BUY" else OrderAction.SELL
                    raw_qty = int(data.get("suggested_quantity", 100))
                    qty = max(1, min(raw_qty, 500))
                    
                    target_p = float(data.get("target_price", current_price))
                    stop_l = float(data.get("stop_loss", current_price * 0.95 if action == OrderAction.BUY else current_price * 1.05))
                    take_p = float(data.get("take_profit", current_price * 1.10 if action == OrderAction.BUY else current_price * 0.90))
                    conf = float(data.get("confidence", 0.75))
                    thesis = data.get("thesis", f"Researcher {action_str} thesis on {ticker}")
                    
                    logger.info(f"[Researcher LLM - {self.worker_model}] Signal: {action_str} {qty} {ticker} @ ${current_price:.2f} (Conf: {conf:.2f})")
                    
                    return TradeSignal(
                        ticker=ticker,
                        action=action,
                        quantity=qty,
                        target_price=target_p,
                        stop_loss=stop_l,
                        take_profit=take_p,
                        confidence=conf,
                        timestamp=datetime.utcnow(),
                        source=f"worker_llm_{self.worker_model}",
                        rationale=thesis
                    )
                elif action_str == "HOLD":
                    logger.debug(f"[Researcher LLM] HOLD recommendation for {ticker}: {data.get('thesis', 'No high-probability setup')}")
                    return None
            
            # 4. Fallback Heuristic Rule (when LLM is offline or no JSON response)
            logger.debug(f"Using quantitative fallback signal generator for {ticker}")
            signal = None
            if rsi_value < 30 and available_cash > (current_price * 10):
                signal = TradeSignal(
                    ticker=ticker,
                    action=OrderAction.BUY,
                    quantity=100,
                    target_price=current_price * 1.02,
                    stop_loss=current_price * 0.95,
                    take_profit=current_price * 1.10,
                    confidence=0.7,
                    timestamp=datetime.utcnow(),
                    source="worker_technical_fallback",
                    rationale=f"RSI oversold ({rsi_value:.1f}) with MACD ({macd_value:.3f}) - potential mean reversion"
                )
            elif rsi_value > 70 and current_qty > 0:
                signal = TradeSignal(
                    ticker=ticker,
                    action=OrderAction.SELL,
                    quantity=min(100, current_qty),
                    target_price=current_price * 0.98,
                    stop_loss=current_price * 1.05,
                    take_profit=current_price * 0.90,
                    confidence=0.7,
                    timestamp=datetime.utcnow(),
                    source="worker_technical_fallback",
                    rationale=f"RSI overbought ({rsi_value:.1f}) - profit taking"
                )
            
            return signal
        except Exception as e:
            logger.error(f"Error generating signal for {ticker}: {e}", exc_info=True)
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