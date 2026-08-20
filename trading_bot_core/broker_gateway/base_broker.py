"""
Base Broker Interface
Abstract base class defining the interface for all broker implementations.
"""

import abc
from typing import Dict, List, Optional, Any
from datetime import datetime
from ..models.order_contracts import OrderContract, OrderAction, OrderType, OrderStatus
from ..models.schemas import PortfolioState

class BaseBroker(abc.ABC):
    """
    Abstract base class for broker implementations.
    Defines the interface that all brokers (sandbox, live, etc.) must implement.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the broker with configuration.
        
        Args:
            config: Configuration dictionary for the broker
        """
        self.config = config
        self.is_connected = False
        self.last_error = None
    
    @abc.abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the broker.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        pass
    
    @abc.abstractmethod
    def disconnect(self) -> bool:
        """
        Disconnect from the broker.
        
        Returns:
            bool: True if disconnection successful, False otherwise
        """
        pass
    
    @abc.abstractmethod
    def get_account_info(self) -> Dict[str, Any]:
        """
        Get account information (cash balance, buying power, etc.).
        
        Returns:
            Dictionary containing account information
        """
        pass
    
    @abc.abstractmethod
    def get_positions(self) -> List[Dict[str, Any]]:
        """
        Get current positions.
        
        Returns:
            List of position dictionaries
        """
        pass
    
    @abc.abstractmethod
    def place_order(self, order: OrderContract) -> OrderContract:
        """
        Place an order with the broker.
        
        Args:
            order: OrderContract object representing the order to place
            
        Returns:
            OrderContract: Updated order object with execution details
        """
        pass
    
    @abc.abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an existing order.
        
        Args:
            order_id: ID of the order to cancel
            
        Returns:
            bool: True if cancellation successful, False otherwise
        """
        pass
    
    @abc.abstractmethod
    def get_order_status(self, order_id: str) -> OrderContract:
        """
        Get the status of an existing order.
        
        Args:
            order_id: ID of the order to check
            
        Returns:
            OrderContract: Order object with current status
        """
        pass
    
    @abc.abstractmethod
    def get_market_data(self, ticker: str, timeframe: str = "1D", limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get market data for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            timeframe: Data timeframe (1m, 5m, 1H, 1D, etc.)
            limit: Number of data points to retrieve
            
        Returns:
            List of market data dictionaries
        """
        pass
    
    def is_market_open(self) -> bool:
        """
        Check if the market is currently open.
        Default implementation returns True (for simplicity in sandbox).
        
        Returns:
            bool: True if market is open, False otherwise
        """
        return True
    
    def get_last_error(self) -> Optional[str]:
        """
        Get the last error message from the broker.
        
        Returns:
            Last error message or None if no error
        """
        return self.last_error
    
    def _set_error(self, error_message: str):
        """Set the last error message."""
        self.last_error = error_message
    
    def _update_order_with_execution(self, order: OrderContract, 
                                   execution_price: float, 
                                   executed_quantity: int,
                                   fees: float = 0.0,
                                   slippage: float = 0.0) -> OrderContract:
        """
        Helper method to update an order with execution details.
        
        Args:
            order: OrderContract to update
            execution_price: Price at which the order was executed
            executed_quantity: Quantity that was executed
            fees: Trading fees
            slippage: Slippage cost
            
        Returns:
            Updated OrderContract
        """
        order.execution_price = execution_price
        order.executed_quantity = executed_quantity
        order.fees = fees
        order.slippage = slippage
        order.status = OrderStatus.FILLED
        order.execution_timestamp = datetime.utcnow()
        return order

# Example concrete implementation for testing
class MockBroker(BaseBroker):
    """
    Mock broker implementation for testing purposes.
    Simulates order execution without connecting to a real broker.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.orders = {}  # Store orders by ID
        self.positions = {}  # Store positions by ticker
        self.cash_balance = config.get('initial_balance', 50000.0)
        self.next_order_id = 1
        
        # Simulate some market data
        self.market_data = {
            "AAPL": {"price": 150.0, "change": 0.5},
            "GOOGL": {"price": 2800.0, "change": -1.2},
            "MSFT": {"price": 300.0, "change": 0.8},
            "TSLA": {"price": 800.0, "change": 2.5},
            "AMZN": {"price": 3200.0, "change": -0.5}
        }
    
    def connect(self) -> bool:
        """Simulate connecting to the broker."""
        self.is_connected = True
        self.last_error = None
        return True
    
    def disconnect(self) -> bool:
        """Simulate disconnecting from the broker."""
        self.is_connected = False
        return True
    
    def get_account_info(self) -> Dict[str, Any]:
        """Get simulated account information."""
        total_positions_value = sum(
            pos['quantity'] * self.market_data.get(ticker, {}).get('price', 0) 
            for ticker, pos in self.positions.items()
        )
        
        return {
            "cash_balance": self.cash_balance,
            "buying_power": self.cash_balance * 2,  # 2x margin
            "total_equity": self.cash_balance + total_positions_value,
            "day_trade_count": 0,
            "is_pattern_day_trader": False
        }
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """Get simulated positions."""
        positions_list = []
        for ticker, pos in self.positions.items():
            current_price = self.market_data.get(ticker, {}).get('price', pos['avg_cost'])
            market_value = pos['quantity'] * current_price
            unrealized_pnl = market_value - (pos['quantity'] * pos['avg_cost'])
            
            positions_list.append({
                "ticker": ticker,
                "quantity": pos['quantity'],
                "avg_cost": pos['avg_cost'],
                "current_price": current_price,
                "market_value": market_value,
                "unrealized_pnl": unrealized_pnl,
                "unrealized_pnl_percent": (unrealized_pnl / (pos['quantity'] * pos['avg_cost'])) * 100 if pos['avg_cost'] > 0 else 0
            })
        
        return positions_list
    
    def place_order(self, order: OrderContract) -> OrderContract:
        """Simulate placing an order."""
        if not self.is_connected:
            order.status = OrderStatus.REJECTED
            self._set_error("Not connected to broker")
            return order
        
        # Generate order ID
        order.order_id = f"mock_{self.next_order_id:08d}"
        self.next_order_id += 1
        
        # Simulate order execution
        ticker = order.ticker
        quantity = order.quantity
        action = order.action
        
        # Get current price (with small random variation for realism)
        import random
        base_price = self.market_data.get(ticker, {}).get('price', 100.0)
        price_variation = random.uniform(-0.005, 0.005)  # +/- 0.5%
        execution_price = base_price * (1 + price_variation)
        
        # Apply slippage based on order type
        slippage = 0.0
        if order.order_type == OrderType.MARKET:
            # Market orders have small slippage
            slippage = execution_price * 0.001  # 0.1% slippage
            if action == OrderAction.BUY:
                execution_price += slippage
            else:
                execution_price -= slippage
        
        # Calculate fees (simplified)
        fees = max(1.0, quantity * 0.005)  # $1 minimum or $0.005 per share
        
        # Update cash balance
        if action == OrderAction.BUY:
            cost = quantity * execution_price + fees
            if cost > self.cash_balance:
                order.status = OrderStatus.REJECTED
                self._set_error("Insufficient funds")
                return order
            self.cash_balance -= cost
            
            # Update position
            if ticker in self.positions:
                pos = self.positions[ticker]
                total_quantity = pos['quantity'] + quantity
                total_cost = (pos['quantity'] * pos['avg_cost']) + (quantity * execution_price)
                pos['avg_cost'] = total_cost / total_quantity
                pos['quantity'] = total_quantity
            else:
                self.positions[ticker] = {
                    'quantity': quantity,
                    'avg_cost': execution_price
                }
        else:  # SELL
            if ticker not in self.positions or self.positions[ticker]['quantity'] < quantity:
                order.status = OrderStatus.REJECTED
                self._set_error("Insufficient position")
                return order
            
            revenue = quantity * execution_price - fees
            self.cash_balance += revenue
            
            # Update position
            pos = self.positions[ticker]
            pos['quantity'] -= quantity
            if pos['quantity'] == 0:
                del self.positions[ticker]
        
        # Update order with execution details
        order.execution_price = execution_price
        order.executed_quantity = quantity
        order.fees = fees
        order.slippage = slippage
        order.status = OrderStatus.FILLED
        order.execution_timestamp = datetime.utcnow()
        
        # Store order
        self.orders[order.order_id] = order
        
        return order
    
    def cancel_order(self, order_id: str) -> bool:
        """Simulate cancelling an order."""
        if order_id in self.orders:
            order = self.orders[order_id]
            if order.status in [OrderStatus.PENDING, OrderStatus.FILLED]:
                # Can only cancel pending orders in reality, but we'll allow for simplicity
                order.status = OrderStatus.CANCELLED
                return True
        return False
    
    def get_order_status(self, order_id: str) -> OrderContract:
        """Get the status of an order."""
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
        """Get simulated market data."""
        # Return some simulated historical data
        import random
        from datetime import datetime, timedelta
        
        base_price = self.market_data.get(ticker, {}).get('price', 100.0)
        if base_price == 100.0:  # Unknown ticker
            return []
        
        data = []
        current_time = datetime.utcnow()
        
        for i in range(limit):
            # Go backwards in time
            time_offset = timedelta(days=i)
            timestamp = current_time - time_offset
            
            # Generate OHLCV with some randomness
            volatility = base_price * 0.02  # 2% volatility
            close = base_price + random.uniform(-volatility, volatility)
            open_price = close + random.uniform(-volatility/2, volatility/2)
            high = max(open_price, close) + random.uniform(0, volatility)
            low = min(open_price, close) - random.uniform(0, volatility)
            volume = random.randint(1000000, 10000000)
            
            data.append({
                "timestamp": timestamp.isoformat() + "Z",
                "open": round(open_price, 2),
                "high": round(high, 2),
                "low": round(low, 2),
                "close": round(close, 2),
                "volume": volume
            })
        
        return data

# Example usage (for testing)
if __name__ == "__main__":
    # Create a mock broker
    config = {"initial_balance": 50000.0}
    broker = MockBroker(config)
    
    # Connect
    if broker.connect():
        print("Connected to mock broker")
        
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
        
        # Disconnect
        broker.disconnect()
    else:
        print("Failed to connect to broker")