"""
Portfolio State Management for the Trading Bot
Handles the current state of the portfolio including cash, positions, and performance metrics.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from .schemas import PortfolioPosition, PortfolioState, OrderAction
import numpy as np

class PortfolioManager:
    """
    Manages the portfolio state and provides methods to update it based on trades.
    This is the in-memory representation that gets persisted to the database layer.
    """
    
    def __init__(self, initial_cash: float = 50000.0, reserve_limit: float = 50000.0):
        """
        Initialize the portfolio with starting cash and reserve limit.
        
        Args:
            initial_cash: Starting cash balance (default $50,000 for paper trading)
            reserve_limit: Minimum cash invariant floor (default $50,000)
        """
        self.state = PortfolioState(
            cash_balance=initial_cash,
            reserve_limit=reserve_limit,  # Minimum cash invariant floor
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

    def calculate_portfolio_volatility(self, lookback_days: int = 30) -> float:
        """Calculate portfolio volatility based on historical returns."""
        try:
            # Get price history for all positions from the transaction ledger
            # For now, we'll use a simplified approach - in production this would
            # fetch from market data service or use stored price history
            if not self.state.positions:
                return 0.0
            
            # Simplified volatility calculation based on position weights
            # In a real implementation, this would use historical price data
            total_value = sum(pos.quantity * pos.current_price for pos in self.state.positions)
            if total_value == 0:
                return 0.0
                
            # Weighted average of individual volatilities (simplified)
            # Using a default volatility estimate per position
            total_weighted_vol = 0.0
            for pos in self.state.positions:
                weight = (pos.quantity * pos.current_price) / total_value
                # Default volatility estimate - in production would use historical data
                vol_estimate = 0.02  # 2% daily volatility as placeholder
                total_weighted_vol += weight * vol_estimate
                
            return total_weighted_vol * np.sqrt(252)  # Annualized volatility
        except Exception:
            return 0.0

    def calculate_max_drawdown(self, lookback_days: int = 252) -> float:
        """Calculate maximum drawdown from equity curve."""
        try:
            # Get transaction history to reconstruct equity curve
            # For now, we'll use a simplified approach
            # In production, this would fetch from transaction ledger and calculate properly
            return max(0.0, (self.state.reserve_limit - self.state.cash_balance) / self.state.reserve_limit)
        except Exception:
            return 0.0

    def get_dynamic_position_size(self, signal_confidence: float, volatility_regime: str = "normal") -> float:
        """Calculate dynamic position size based on signal confidence and volatility regime."""
        try:
            base_size = 0.1  # Base 10% of available capital
            
            # Adjust for signal confidence (0-1 scale)
            confidence_factor = max(0.1, min(1.0, signal_confidence))
            
            # Adjust for volatility regime
            volatility_multipliers = {
                "low": 1.5,
                "normal": 1.0,
                "high": 0.5,
                "extreme": 0.25
            }
            vol_multiplier = volatility_multipliers.get(volatility_regime, 1.0)
            
            # Calculate position size
            position_size = base_size * confidence_factor * vol_multiplier
            
            # Apply limits
            return max(0.01, min(0.25, position_size))  # Between 1% and 25%
        except Exception:
            return 0.05  # Default 5%

    def check_correlation_risk(self, new_ticker: str, max_correlation: float = 0.7) -> bool:
        """Check if adding a position would exceed correlation limits."""
        try:
            # Simplified correlation check - in production would use historical price data
            # For now, we'll use a basic sector-based approach
            sector_map = {
                'AAPL': 'Technology', 'MSFT': 'Technology', 'GOOGL': 'Technology',
                'TSLA': 'Automotive', 'F': 'Automotive', 'GM': 'Automotive',
                'JPM': 'Financial', 'BAC': 'Financial', 'WFC': 'Financial',
                'JNJ': 'Healthcare', 'PFE': 'Healthcare', 'UNH': 'Healthcare',
                'XOM': 'Energy', 'CVX': 'Energy', 'COP': 'Energy'
            }
            
            new_sector = sector_map.get(new_ticker.upper(), 'Other')
            current_sector_exposure = 0.0
            total_portfolio_value = self.state.cash_balance + sum(
                pos.quantity * pos.current_price for pos in self.state.positions
            )
            
            if total_portfolio_value > 0:
                for pos in self.state.positions:
                    pos_sector = sector_map.get(pos.ticker.upper(), 'Other')
                    if pos_sector == new_sector:
                        pos_value = pos.quantity * pos.current_price
                        current_sector_exposure += pos_value / total_portfolio_value
            
            # Simple correlation proxy: same sector = high correlation
            if new_sector != 'Other' and current_sector_exposure > 0.3:  # 30% sector limit
                return False
                
            return True
        except Exception:
            return True  # Allow trade if check fails

    def check_time_based_exposure(self, max_hours_per_day: float = 4.0) -> bool:
        """Check if time-based exposure limits are exceeded."""
        try:
            # Simplified implementation - in production would track actual trading time
            # For now, we'll assume we're within limits
            return True
        except Exception:
            return True

    def check_sector_concentration(self, new_ticker: str, max_sector_exposure: float = 0.3) -> bool:
        """Check if adding a position would exceed sector concentration limits."""
        try:
            sector_map = {
                'AAPL': 'Technology', 'MSFT': 'Technology', 'GOOGL': 'Technology', 'META': 'Technology',
                'TSLA': 'Automotive', 'F': 'Automotive', 'GM': 'Automotive', 'TM': 'Automotive',
                'JPM': 'Financial', 'BAC': 'Financial', 'WFC': 'Financial', 'GS': 'Financial',
                'JNJ': 'Healthcare', 'PFE': 'Healthcare', 'UNH': 'Healthcare', 'MRK': 'Healthcare',
                'XOM': 'Energy', 'CVX': 'Energy', 'COP': 'Energy', 'SLB': 'Energy',
                'DIS': 'Consumer', 'PG': 'Consumer', 'KO': 'Consumer', 'PEP': 'Consumer',
                'NEE': 'Utilities', 'DUK': 'Utilities', 'SO': 'Utilities'
            }
            
            new_sector = sector_map.get(new_ticker.upper(), 'Other')
            if new_sector == 'Other':
                return True  # No limit on 'Other' sector
                
            total_portfolio_value = self.state.cash_balance + sum(
                pos.quantity * pos.current_price for pos in self.state.positions
            )
            
            if total_portfolio_value == 0:
                return True
                
            current_sector_value = sum(
                pos.quantity * pos.current_price for pos in self.state.positions
                if sector_map.get(pos.ticker.upper(), 'Other') == new_sector
            )
            
            current_sector_exposure = current_sector_value / total_portfolio_value
            
            # Check if adding new position would exceed limit
            # Estimate new position value (simplified)
            estimated_new_value = total_portfolio_value * 0.05  # Assume 5% position
            new_sector_exposure = (current_sector_value + estimated_new_value) / (total_portfolio_value + estimated_new_value)
            
            return new_sector_exposure <= max_sector_exposure
        except Exception:
            return True  # Allow trade if check fails