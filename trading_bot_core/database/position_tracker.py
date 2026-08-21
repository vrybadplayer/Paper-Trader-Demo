# Position Tracker - Atomic Key-Value State Document
# Provides instant O(1) state lookups for active share counts and cash without re-aggregating the transaction history.

import json
import os
from typing import Dict, List, Optional
from threading import Lock
from trading_bot_core.models.schemas import PortfolioPosition

class PositionTracker:
    """
    Atomic key-value state document for the portfolio.
    Stores cash balance, positions, and other portfolio metrics.
    Updated after each trade to reflect the current state.
    """
    
    def __init__(self, file_path: str = "database/data/logs/positions.json"):
        """
        Initialize the position tracker.
        
        Args:
            file_path: Path to the JSON file for storing position state
        """
        self.file_path = file_path
        self.lock = Lock()  # To ensure atomic updates
        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        # Initialize the file if it doesn't exist
        if not os.path.exists(self.file_path):
            self._initialize_file()
    
    def _initialize_file(self):
        """Create the initial state file with default values."""
        initial_state = {
            "cash_balance": 50000.0,  # Starting cash
            "reserve_limit": 50000.0,  # Minimum cash reserve invariant
            "total_equity": 50000.0,
            "realized_pnl": 0.0,
            "unrealized_pnl": 0.0,
            "positions": {}  # ticker -> {quantity, avg_cost}
        }
        self._write_state(initial_state)
    
    def _read_state(self) -> Dict:
        """Read the current state from the JSON file."""
        try:
            with open(self.file_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # If file doesn't exist or is corrupted, reinitialize
            self._initialize_file()
            return self._read_state()
    
    def _write_state(self, state: Dict):
        """Write the state to the JSON file atomically."""
        # Write to a temporary file first, then rename for atomicity
        temp_file = self.file_path + ".tmp"
        with open(temp_file, 'w') as f:
            json.dump(state, f, indent=2)
        os.replace(temp_file, self.file_path)
    
    def update_position(self, ticker: str, quantity: float, price: float, action: str) -> bool:
        """
        Update a position after a trade.
        
        Args:
            ticker: Stock ticker symbol
            quantity: Number of shares (positive for buy, negative for sell)
            price: Execution price per share
            action: Either 'buy' or 'sell'
        
        Returns:
            bool: True if updated successfully, False otherwise
        """
        with self.lock:
            try:
                state = self._read_state()
                
                # Calculate trade value and fees (simplified, assuming no fees for now)
                trade_value = quantity * price
                
                if action.lower() == 'buy':
                    # Buying: decrease cash, increase position
                    state["cash_balance"] -= trade_value
                    
                    if ticker in state["positions"]:
                        # Update existing position: weighted average cost
                        old_qty = state["positions"][ticker]["quantity"]
                        old_cost = state["positions"][ticker]["avg_cost"]
                        new_qty = old_qty + quantity
                        if new_qty != 0:
                            new_avg_cost = (old_qty * old_cost + quantity * price) / new_qty
                        else:
                            new_avg_cost = 0
                        state["positions"][ticker] = {
                            "quantity": new_qty,
                            "avg_cost": new_avg_cost
                        }
                        # Remove if quantity becomes zero
                        if new_qty == 0:
                            del state["positions"][ticker]
                    else:
                        # New position
                        state["positions"][ticker] = {
                            "quantity": quantity,
                            "avg_cost": price
                        }
                elif action.lower() == 'sell':
                    # Selling: increase cash, decrease position
                    state["cash_balance"] += trade_value
                    
                    if ticker in state["positions"]:
                        old_qty = state["positions"][ticker]["quantity"]
                        old_cost = state["positions"][ticker]["avg_cost"]
                        new_qty = old_qty - quantity  # quantity is positive for sell, so subtract
                        if new_qty == 0:
                            del state["positions"][ticker]
                        else:
                            state["positions"][ticker] = {
                                "quantity": new_qty,
                                "avg_cost": old_cost  # Average cost remains the same for remaining shares
                            }
                    else:
                        # Should not happen: selling without a position
                        # In a real system, this would be an error (short selling not allowed or handled differently)
                        # For now, we'll allow it and create a short position (negative quantity)
                        state["positions"][ticker] = {
                            "quantity": -quantity,
                            "avg_cost": price
                        }
                else:
                    print(f"Invalid action: {action}")
                    return False
                
                # Update total equity and P&L (simplified)
                # In a real system, we would recalculate based on current prices
                # For now, we'll keep it simple and just update cash and assume positions are at cost
                state["total_equity"] = state["cash_balance"]  # Plus market value of positions (to be implemented)
                # For simplicity, we'll set unrealized P&L to 0 and realized P&L to 0 in this basic version
                # A more complete version would update realized P&L on sell and track unrealized P&L
                
                self._write_state(state)
                return True
            except Exception as e:
                print(f"Error updating position: {e}")
                return False
    
    def get_state(self) -> Dict:
        """
        Get the current portfolio state.
        
        Returns:
            Dict containing cash_balance, reserve_limit, total_equity, realized_pnl, unrealized_pnl, positions
        """
        with self.lock:
            return self._read_state()
    
    def get_cash_balance(self) -> float:
        """Get the current cash balance."""
        with self.lock:
            return self._read_state().get("cash_balance", 0.0)
    
    def get_position(self, ticker: str) -> Optional[Dict]:
        """Get the position for a specific ticker."""
        with self.lock:
            state = self._read_state()
            return state.get("positions", {}).get(ticker)
    
    def get_all_positions(self) -> Dict[str, Dict]:
        """Get all positions."""
        with self.lock:
            state = self._read_state()
            return state.get("positions", {}).copy()

# Example usage (for testing)
if __name__ == "__main__":
    tracker = PositionTracker("test_positions.json")
    
    # Buy 100 shares of AAPL at $150
    tracker.update_position("AAPL", 100, 150.0, "buy")
    
    # Buy another 50 shares at $155
    tracker.update_position("AAPL", 50, 155.0, "buy")
    
    # Sell 30 shares at $160
    tracker.update_position("AAPL", 30, 160.0, "sell")
    
    state = tracker.get_state()
    print(f"Current state: {json.dumps(state, indent=2)}")
    
    # Clean up
    os.remove("test_positions.json")