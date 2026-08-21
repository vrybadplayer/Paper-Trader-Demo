"""
Sandbox Broker Implementation
Paper-trading sandbox that simulates order execution without real market risk.
"""

import logging
import threading
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from .base_broker import BaseBroker
from ..models.order_contracts import OrderContract, OrderAction, OrderType, OrderStatus
from ..models.schemas import PortfolioState
from ..models.portfolio_state import PortfolioManager
from ..database.transaction_ledger import TransactionLedger
from ..database.vector_store import VectorStore

logger = logging.getLogger(__name__)

class SandboxBroker(BaseBroker):
    """
    Paper-trading sandbox broker that simulates order execution.
    Uses internal position tracker and transaction ledger for state management.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the sandbox broker.
        
        Args:
            config: Configuration dictionary containing:
                - initial_balance: Starting cash balance (default 50000.0)
                - commission_per_trade: Commission per trade (default 0.001)
                - slippage_model: Slippage model to use (default "fixed")
                - enable_latency_simulation: Whether to simulate network latency (default False)
                - latency_range_ms: Range of latency to simulate in ms (default [10, 100])
        """
        super().__init__(config)
        
        # Configuration
        self.initial_balance = config.get('initial_balance', 50000.0)
        self.commission_per_trade = config.get('commission_per_trade', 0.001)
        self.slippage_model = config.get('slippage_model', 'fixed')
        self.enable_latency_simulation = config.get('enable_latency_simulation', False)
        self.latency_range_ms = config.get('latency_range_ms', [10, 100])
        
        # Internal state management
        self.position_tracker = PortfolioManager(initial_cash=self.initial_balance)
        self.transaction_ledger = TransactionLedger()
        self.vector_store = VectorStore()
        
        # Order tracking
        self.orders: Dict[str, OrderContract] = {}
        self.next_order_id = 1
        self.order_lock = threading.Lock()
        
        # Market data simulation (in real implementation, this would come from a data feed)
        self.market_data_cache: Dict[str, Dict] = {}
        self._initialize_market_data()
        
        logger.info("Sandbox broker initialized")
    
    def _initialize_market_data(self):
        """Initialize simulated market data for common tickers."""
        # In a real implementation, this would be fetched from a market data provider
        self.market_data_cache = {
            "AAPL": {"price": 150.0, "volume": 50000000, "volatility": 0.02},
            "GOOGL": {"price": 2800.0, "volume": 1500000, "volatility": 0.015},
            "MSFT": {"price": 300.0, "volume": 25000000, "volatility": 0.018},
            "TSLA": {"price": 800.0, "volume": 30000000, "volatility": 0.035},
            "AMZN": {"price": 3200.0, "volume": 20000000, "volatility": 0.02},
            "NVDA": {"price": 400.0, "volume": 40000000, "volatility": 0.04},
            "META": {"price": 350.0, "volume": 20000000, "volatility": 0.025},
            "NFLX": {"price": 450.0, "volume": 10000000, "volatility": 0.03},
        }
    
    def connect(self) -> bool:
        """
        Connect to the sandbox broker.
        For sandbox, this is always successful.
        
        Returns:
            bool: True (always connected)
        """
        self.is_connected = True
        self.last_error = None
        logger.info("Connected to sandbox broker")
        return True
    
    def disconnect(self) -> bool:
        """
        Disconnect from the sandbox broker.
        
        Returns:
            bool: True (always successful)
        """
        self.is_connected = False
        logger.info("Disconnected from sandbox broker")
        return True
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information from the position tracker.
        
        Returns:
            Dictionary containing account information
        """
        state = self.position_tracker.get_state()
        
        return {
            "cash_balance": state.cash_balance,
            "buying_power": state.cash_balance * 2,  # 2x margin in sandbox
            "total_equity": state.total_equity,
            "day_trade_count": 0,  # Would be calculated from transaction history
            "is_pattern_day_trader": False,
            "reserve_limit": state.reserve_limit,
            "available_for_trading": max(0, state.cash_balance - state.reserve_limit)
        }
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get current positions from the position tracker.
        
        Returns:
            List of position dictionaries
        """
        state = self.position_tracker.get_state()
        positions_list = []
        
        for pos in state.positions:
            # Get current price from market data cache
            current_price = self.market_data_cache.get(pos.ticker, {}).get('price', pos.current_price)
            
            market_value = pos.quantity * current_price
            unrealized_pnl = market_value - (pos.quantity * pos.avg_cost)
            
            positions_list.append({
                "ticker": pos.ticker,
                "quantity": pos.quantity,
                "avg_cost": pos.avg_cost,
                "current_price": current_price,
                "market_value": market_value,
                "unrealized_pnl": unrealized_pnl,
                "unrealized_pnl_percent": (unrealized_pnl / (pos.quantity * pos.avg_cost)) * 100 if pos.avg_cost > 0 else 0
            })
        
        return positions_list
    
    def place_order(self, order: OrderContract) -> OrderContract:
        """
        Place an order in the sandbox broker.
        
        Args:
            order: OrderContract object representing the order to place
            
        Returns:
            OrderContract: Updated order object with execution details
        """
        if not self.is_connected:
            order.status = OrderStatus.REJECTED
            self._set_error("Not connected to broker")
            return order
        
        # Validate order
        validation_error = self._validate_order(order)
        if validation_error:
            order.status = OrderStatus.REJECTED
            self._set_error(validation_error)
            return order
        
        # Simulate latency if enabled
        if self.enable_latency_simulation:
            import random
            latency_ms = random.randint(self.latency_range_ms[0], self.latency_range_ms[1])
            time.sleep(latency_ms / 1000.0)
        
        # Generate order ID
        with self.order_lock:
            order.order_id = f"sandbox_{self.next_order_id:08d}"
            self.next_order_id += 1
        
        # Execute the order
        try:
            executed_order = self._execute_order(order)
            
            # Store the order
            with self.order_lock:
                self.orders[order.order_id] = executed_order
            
            # Record transaction in ledger
            self.transaction_ledger.record_transaction(executed_order.dict())
            
            # Add to vector store as memory
            self.vector_store.add_trade_memory(executed_order.dict())
            
            logger.info(f"Order executed: {order.order_id} {order.action} {order.quantity} {order.ticker} @ {order.execution_price}")
            
            return executed_order
        except Exception as e:
            order.status = OrderStatus.REJECTED
            self._set_error(f"Order execution failed: {str(e)}")
            logger.error(f"Order execution failed: {e}")
            return order
    
    def _validate_order(self, order: OrderContract) -> Optional[str]:
        """
        Validate an order before execution.
        
        Args:
            order: OrderContract to validate
            
        Returns:
            Error message if validation fails, None otherwise
        """
        # Check required fields
        if not order.ticker:
            return "Ticker symbol is required"
        
        if order.quantity <= 0:
            return "Quantity must be positive"
        
        if order.action not in [OrderAction.BUY, OrderAction.SELL]:
            return "Action must be BUY or SELL"
        
        # Check order type specific requirements
        if order.order_type in [OrderType.LIMIT, OrderType.STOP_LIMIT]:
            if order.price is None or order.price <= 0:
                return "Price is required and must be positive for LIMIT orders"
        
        if order.order_type in [OrderType.STOP, OrderType.STOP_LIMIT]:
            if order.stop_price is None or order.stop_price <= 0:
                return "Stop price is required and must be positive for STOP orders"
        
        # Check if we have sufficient funds for BUY orders
        if order.action == OrderAction.BUY:
            # Get current price for cost estimation
            current_price = self._get_current_price(order.ticker)
            if current_price is None:
                return f"Unable to get current price for {order.ticker}"
            
            estimated_cost = order.quantity * current_price
            account_info = self.get_account_info()
            available_cash = account_info['available_for_trading']
            
            if estimated_cost > available_cash:
                return f"Insufficient funds: need ${estimated_cost:.2f}, have ${available_cash:.2f} available"
        
        # Check if we have sufficient position for SELL orders
        if order.action == OrderAction.SELL:
            current_position = self.position_tracker.get_position_quantity(order.ticker)
            if current_position < order.quantity:
                return f"Insufficient position: have {current_position}, need {order.quantity}"
        
        return None
    
    def _execute_order(self, order: OrderContract) -> OrderContract:
        """
        Execute an order in the sandbox.
        
        Args:
            order: OrderContract to execute
            
        Returns:
            OrderContract: Updated order with execution details
        """
        ticker = order.ticker
        action = order.action
        quantity = order.quantity
        
        # Get execution price based on order type
        execution_price = self._get_execution_price(order)
        
        # Calculate fees and slippage
        fees = self._calculate_fees(quantity, execution_price)
        slippage = self._calculate_slippage(order, execution_price)
        
        # Update order with execution details
        order.execution_price = execution_price
        order.executed_quantity = quantity
        order.fees = fees
        order.slippage = slippage
        order.status = OrderStatus.FILLED
        order.execution_timestamp = datetime.utcnow()
        
        # Update internal position tracker
        order_dict = order.dict()
        self.position_tracker.update_from_order(order_dict)
        
        return order
    
    def _get_current_price(self, ticker: str) -> Optional[float]:
        """
        Get the current price for a ticker from market data cache.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Current price or None if not available
        """
        data = self.market_data_cache.get(ticker.upper())
        if data:
            return data['price']
        return None
    
    def _get_execution_price(self, order: OrderContract) -> float:
        """
        Get the execution price for an order based on its type.
        
        Args:
            order: OrderContract to get execution price for
            
        Returns:
            Execution price
        """
        ticker = order.ticker.upper()
        base_price = self._get_current_price(ticker)
        
        if base_price is None:
            # If we don't have price data, use a default
            base_price = 100.0
            logger.warning(f"No price data for {ticker}, using default price ${base_price}")
        
        # Add some random variation for realism
        import random
        volatility = self.market_data_cache.get(ticker, {}).get('volatility', 0.02)
        price_variation = random.uniform(-volatility, volatility)
        execution_price = base_price * (1 + price_variation)
        
        # Apply slippage based on order type
        if order.order_type == OrderType.MARKET:
            # Market orders: execute at current price with slippage
            slippage_amount = execution_price * 0.001  # 0.1% slippage
            if order.action == OrderAction.BUY:
                execution_price += slippage_amount
            else:  # SELL
                execution_price -= slippage_amount
        
        elif order.order_type == OrderType.LIMIT:
            # Limit orders: execute at limit price or better
            limit_price = order.price
            if order.action == OrderAction.BUY:
                # Buy limit: execute at limit price or lower
                execution_price = min(execution_price, limit_price)
            else:  # SELL
                # Sell limit: execute at limit price or higher
                execution_price = max(execution_price, limit_price)
        
        elif order.order_type in [OrderType.STOP, OrderType.STOP_LIMIT]:
            # Stop orders: trigger when price reaches stop price
            # For simplicity, we'll assume the stop price has been reached
            # and execute at the current price (with slippage)
            pass  # Already using current price
        
        return max(0.01, execution_price)  # Ensure price is positive
    
    def _calculate_fees(self, quantity: int, price: float) -> float:
        """
        Calculate trading fees.
        
        Args:
            quantity: Number of shares
            price: Execution price
            
        Returns:
            Fee amount
        """
        # Simple fee model: $1 minimum + $0.005 per share
        base_fee = 1.0
        per_share_fee = quantity * 0.005
        return max(base_fee, per_share_fee)
    
    def _calculate_slippage(self, order: OrderContract, execution_price: float) -> float:
        """
        Calculate slippage for an order.
        
        Args:
            order: OrderContract
            execution_price: Execution price
            
        Returns:
            Slippage amount
        """
        if self.slippage_model == "fixed":
            # Fixed percentage slippage
            return execution_price * 0.001  # 0.1%
        elif self.slippage_model == "random":
            # Random slippage between 0.05% and 0.2%
            import random
            slippage_pct = random.uniform(0.0005, 0.002)
            return execution_price * slippage_pct
        elif self.slippage_model == "volume_weighted":
            # Volume-weighted slippage (simplified)
            # In reality, this would use actual volume data
            volume = self.market_data_cache.get(order.ticker.upper(), {}).get('volume', 1000000)
            # Higher volume = lower slippage
            volume_factor = max(0.1, min(1.0, 1000000 / volume))  # Normalize around 1M volume
            base_slippage = 0.001  # 0.1% base
            return execution_price * base_slippage * volume_factor
        else:
            # Default to fixed
            return execution_price * 0.001
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an existing order.
        In sandbox, we can only cancel pending orders (but we execute immediately).
        
        Args:
            order_id: ID of the order to cancel
            
        Returns:
            bool: True if cancellation successful, False otherwise
        """
        with self.order_lock:
            if order_id in self.orders:
                order = self.orders[order_id]
                # In sandbox, orders are filled immediately, so we can't cancel them
                # But we'll mark them as cancelled for consistency
                if order.status == OrderStatus.PENDING:
                    order.status = OrderStatus.CANCELLED
                    return True
                else:
                    logger.warning(f"Cannot cancel order {order_id} with status {order.status}")
                    return False
            else:
                logger.warning(f"Order {order_id} not found")
                return False
    
    def get_order_status(self, order_id: str) -> OrderContract:
        """
        Get the status of an existing order.
        
        Args:
            order_id: ID of the order to check
            
        Returns:
            OrderContract: Order object with current status
        """
        with self.order_lock:
            if order_id in self.orders:
                return self.orders[order_id]
            else:
                # Return a rejected order if not found
                order = OrderContract(
                    ticker="UNKNOWN",
                    action=OrderAction.BUY,
                    quantity=0,
                    order_id=order_id,
                    status=OrderStatus.REJECTED
                )
                return order
    
    def get_market_data(self, ticker: str, timeframe: str = "1D", limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get simulated market data for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            timeframe: Data timeframe (1m, 5m, 1H, 1D, etc.)
            limit: Number of data points to retrieve
            
        Returns:
            List of market data dictionaries
        """
        ticker = ticker.upper()
        if ticker not in self.market_data_cache:
            logger.warning(f"No market data available for {ticker}")
            return []
        
        # Generate simulated historical data
        import random
        from datetime import datetime, timedelta
        
        base_data = self.market_data_cache[ticker]
        base_price = base_data['price']
        volatility = base_data['volatility']
        
        data = []
        current_time = datetime.utcnow()
        
        # Adjust time delta based on timeframe
        if timeframe == "1m":
            delta = timedelta(minutes=1)
        elif timeframe == "5m":
            delta = timedelta(minutes=5)
        elif timeframe == "1H":
            delta = timedelta(hours=1)
        elif timeframe == "1D":
            delta = timedelta(days=1)
        elif timeframe == "1W":
            delta = timedelta(weeks=1)
        else:
            delta = timedelta(days=1)  # Default to daily
        
        for i in range(limit):
            # Go backwards in time
            time_offset = delta * i
            timestamp = current_time - time_offset
            
            # Generate OHLCV with some randomness
            price_change = random.uniform(-volatility, volatility)
            close_price = base_price * (1 + price_change)
            
            # Open price is close from previous period (with some gap)
            if i == 0:
                open_price = close_price
            else:
                prev_close = data[-1]['close']
                gap = random.uniform(-0.005, 0.005)  # Small gap between periods
                open_price = prev_close * (1 + gap)
            
            # High and low prices
            intra_period_vol = volatility * 0.5  # Half volatility for intra-period
            high_price = max(open_price, close_price) * (1 + random.uniform(0, intra_period_vol))
            low_price = min(open_price, close_price) * (1 - random.uniform(0, intra_period_vol))
            
            # Volume with some randomness
            base_volume = base_data['volume']
            volume = int(base_volume * random.uniform(0.5, 2.0))
            
            data.append({
                "timestamp": timestamp.isoformat() + "Z",
                "open": round(open_price, 2),
                "high": round(high_price, 2),
                "low": round(low_price, 2),
                "close": round(close_price, 2),
                "volume": volume
            })
        
        return data

# Example usage (for testing)
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # Create a sandbox broker
    config = {
        "initial_balance": 50000.0,
        "commission_per_trade": 0.001,
        "slippage_model": "fixed",
        "enable_latency_simulation": True,
        "latency_range_ms": [10, 50]
    }
    broker = SandboxBroker(config)
    
    # Connect
    if broker.connect():
        print("Connected to sandbox broker")
        
        # Get account info
        account_info = broker.get_account_info()
        print(f"Account info: {account_info}")
        
        # Create a test order
        from ..models.order_contracts import OrderContract, OrderAction, OrderType
        order = OrderContract(
            ticker="AAPL",
            action=OrderAction.BUY,
            quantity=100,
            order_type=OrderType.MARKET
        )
        
        # Place the order
        executed_order = broker.place_order(order)
        print(f"Executed order: {executed_order}")
        
        # Get positions
        positions = broker.get_positions()
        print(f"Positions: {positions}")
        
        # Get updated account info
        account_info = broker.get_account_info()
        print(f"Updated account info: {account_info}")
        
        # Disconnect
        broker.disconnect()
    else:
        print("Failed to connect to broker")