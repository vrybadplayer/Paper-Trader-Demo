"""
Portfolio State Management for the Trading Bot
Handles the current state of the portfolio including cash, positions, and performance metrics.
"""

from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from .schemas import PortfolioPosition, PortfolioState, OrderAction

class PortfolioManager:
    """
    Manages the portfolio state and provides methods to update it based on trades.
    This is the in-memory representation that gets persisted to the database layer.
    """
    
    def __init__(self, initial_cash: float = 50000.0):
        """
        Initialize the portfolio with starting cash.
        
        Args:
            initial_cash: Starting cash balance (default $50,000 for paper trading)
        """
        self.state = PortfolioState(
            cash_balance=initial_cash,
            reserve_limit=50000.0,  # Minimum cash invariant
            total_equity=initial_cash,
            realized_pnl=0.0,
            unrealized_pnl=0.0,
            positions=[]
        )
        self.last_updated = datetime.utcnow()
    
    def get_state(self) -> PortfolioState:
        """Get the current portfolio state."""
        # Update total equity before returning
        self._update_equity()
        return self.state
    
    def update_from_order(self, order: Dict) -> None:
        """
        Update portfolio state based on an executed order.
        
        Args:
            order: Dictionary containing order execution details
        """
        ticker = order.get('ticker')
        action = order.get('action')
        quantity = order.get('executed_quantity', order.get('quantity', 0))
        execution_price = order.get('execution_price', 0.0)
        fees = order.get('fees', 0.0)
        
        if action == OrderAction.BUY:
            self._execute_buy(ticker, quantity, execution_price, fees)
        elif action == OrderAction.SELL:
            self._execute_sell(ticker, quantity, execution_price, fees)
        
        self._update_equity()
        self.last_updated = datetime.utcnow()
    
    def _execute_buy(self, ticker: str, quantity: int, price: float, fees: float) -> None:
        """Execute a buy order and update positions."""
        cost = quantity * price + fees
        
        # Check if we already have a position
        existing_pos = None
        for pos in self.state.positions:
            if pos.ticker == ticker:
                existing_pos = pos
                break
        
        if existing_pos:
            # Update average cost
            total_quantity = existing_pos.quantity + quantity
            total_cost = (existing_pos.quantity * existing_pos.avg_cost) + (quantity * price)
            new_avg_cost = total_cost / total_quantity if total_quantity > 0 else 0
            
            existing_pos.quantity = total_quantity
            existing_pos.avg_cost = new_avg_cost
        else:
            # Create new position
            new_position = PortfolioPosition(
                ticker=ticker,
                quantity=quantity,
                avg_cost=price,
                current_price=price,  # Assume execution price is current
                market_value=quantity * price,
                unrealized_pnl=0.0
            )
            self.state.positions.append(new_position)
        
        # Deduct cash
        self.state.cash_balance -= cost
    
    def _execute_sell(self, ticker: str, quantity: int, price: float, fees: float) -> None:
        """Execute a sell order and update positions."""
        revenue = quantity * price - fees
        
        # Find the position
        for pos in self.state.positions:
            if pos.ticker == ticker:
                if pos.quantity < quantity:
                    raise ValueError(f"Insufficient position to sell: {pos.quantity} < {quantity}")
                
                # Calculate realized P&L
                cost_basis = quantity * pos.avg_cost
                realized_pnl = revenue - cost_basis
                
                # Update position
                pos.quantity -= quantity
                if pos.quantity == 0:
                    self.state.positions.remove(pos)
                else:
                    # Market value and unrealized P&L will be updated in _update_equity
                    pass
                
                # Update cash and realized P&L
                self.state.cash_balance += revenue
                self.state.realized_pnl += realized_pnl
                break
        else:
            raise ValueError(f"No position found for ticker: {ticker}")
    
    def _update_equity(self) -> None:
        """Update total equity and unrealized P&L based on current prices."""
        # This method should be called with current market prices
        # For now, we'll assume current prices are stored in positions
        # In a real system, you'd fetch latest prices before calling this
        
        total_positions_value = 0.0
        total_unrealized_pnl = 0.0
        
        for pos in self.state.positions:
            # In a real implementation, you'd update pos.current_price from market data
            # For now, we'll keep it as is (last execution price)
            market_value = pos.quantity * pos.current_price
            pos.market_value = market_value
            pos.unrealized_pnl = market_value - (pos.quantity * pos.avg_cost)
            
            total_positions_value += market_value
            total_unrealized_pnl += pos.unrealized_pnl
        
        self.state.total_equity = self.state.cash_balance + total_positions_value
        self.state.unrealized_pnl = total_unrealized_pnl
    
    def update_position_price(self, ticker: str, current_price: float) -> None:
        """
        Update the current price for a position (called when new market data arrives).
        
        Args:
            ticker: Stock ticker symbol
            current_price: Current market price
        """
        for pos in self.state.positions:
            if pos.ticker == ticker:
                pos.current_price = current_price
                break
        self._update_equity()
    
    def get_cash_available(self) -> float:
        """Get cash available for trading (respecting reserve limit)."""
        return max(0, self.state.cash_balance - self.state.reserve_limit)
    
    def get_position_quantity(self, ticker: str) -> int:
        """Get current quantity for a ticker (0 if not held)."""
        for pos in self.state.positions:
            if pos.ticker == ticker:
                return pos.quantity
        return 0
    
    def get_position_market_value(self, ticker: str) -> float:
        """Get current market value for a ticker position."""
        quantity = self.get_position_quantity(ticker)
        # Need current price - in practice, we'd get from market data
        # For now, we'll search positions for current_price
        for pos in self.state.positions:
            if pos.ticker == ticker:
                return pos.quantity * pos.current_price
        return 0.0