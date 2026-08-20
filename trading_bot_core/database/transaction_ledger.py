"""
Transaction Ledger - Append-Only JSONL
Immutable historical audit trail of all filled buy/sell actions.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from ..models.schemas import Order

class TransactionLedger:
    """
    Append-only ledger for recording all executed trades.
    Each transaction is a JSON object written as a line in a JSONL file.
    """
    
    def __init__(self, file_path: str = "database/data/logs/transactions.jsonl"):
        """
        Initialize the transaction ledger.
        
        Args:
            file_path: Path to the JSONL file for storing transactions
        """
        self.file_path = file_path
        # Ensure the directory exists
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        
        # If the file doesn't exist, create it (optional, as we'll create on first write)
        if not os.path.exists(self.file_path):
            # Create an empty file
            open(self.file_path, 'a').close()
    
    def record_transaction(self, order: Dict) -> bool:
        """
        Record a executed transaction to the ledger.
        
        Args:
            order: Dictionary containing order execution details (should match Order schema)
            
        Returns:
            bool: True if recorded successfully, False otherwise
        """
        try:
            # Prepare the transaction record
            transaction = {
                "trade_id": order.get("order_id"),
                "timestamp_utc": order.get("timestamp", datetime.utcnow()).isoformat() + "Z",
                "ticker": order.get("ticker"),
                "action": order.get("action"),
                "quantity": order.get("executed_quantity", order.get("quantity")),
                "execution_price": order.get("execution_price"),
                "fees": order.get("fees", 0.0),
                "slippage": order.get("slippage", 0.0),
                "trigger_signal": order.get("trigger_signal"),
                "critic_verdict_ref": order.get("critic_verdict_ref")
            }
            
            # Remove any None values to keep the JSON clean
            transaction = {k: v for k, v in transaction.items() if v is not None}
            
            # Write as a JSON line
            with open(self.file_path, 'a') as f:
                f.write(json.dumps(transaction) + '\n')
            
            return True
        except Exception as e:
            print(f"Error recording transaction: {e}")
            return False
    
    def get_transactions(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Retrieve transactions from the ledger.
        
        Args:
            limit: Maximum number of transactions to return (most recent first)
            
        Returns:
            List of transaction dictionaries
        """
        transactions = []
        try:
            with open(self.file_path, 'r') as f:
                lines = f.readlines()
            
            # Process lines in reverse to get most recent first if limit is specified
            if limit is not None:
                lines = lines[-limit:]
                lines.reverse()  # Now most recent first
            
            for line in lines:
                line = line.strip()
                if line:
                    try:
                        transaction = json.loads(line)
                        transactions.append(transaction)
                    except json.JSONDecodeError:
                        # Skip invalid lines
                        continue
            
            # If we reversed for limit, we need to reverse back to chronological order
            if limit is not None:
                transactions.reverse()
                
        except FileNotFoundError:
            # If file doesn't exist, return empty list
            pass
        except Exception as e:
            print(f"Error reading transactions: {e}")
        
        return transactions
    
    def get_transaction_by_id(self, trade_id: str) -> Optional[Dict]:
        """
        Retrieve a specific transaction by its trade_id.
        
        Args:
            trade_id: The trade ID to search for
            
        Returns:
            Transaction dictionary if found, None otherwise
        """
        try:
            with open(self.file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            transaction = json.loads(line)
                            if transaction.get("trade_id") == trade_id:
                                return transaction
                        except json.JSONDecodeError:
                            continue
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Error reading transaction by ID: {e}")
        
        return None
    
    def clear_ledger(self) -> bool:
        """
        Clear the transaction ledger (use with caution).
        
        Returns:
            bool: True if cleared successfully, False otherwise
        """
        try:
            open(self.file_path, 'w').close()
            return True
        except Exception as e:
            print(f"Error clearing ledger: {e}")
            return False

# Example usage (for testing)
if __name__ == "__main__":
    ledger = TransactionLedger("test_transactions.jsonl")
    
    # Sample order
    sample_order = {
        "order_id": "ord_12345",
        "timestamp": datetime.utcnow(),
        "ticker": "AAPL",
        "action": "BUY",
        "quantity": 100,
        "executed_quantity": 100,
        "execution_price": 150.0,
        "fees": 1.0,
        "slippage": 0.05,
        "trigger_signal": "signal_001",
        "critic_verdict_ref": "critic_001"
    }
    
    ledger.record_transaction(sample_order)
    
    transactions = ledger.get_transactions()
    print(f"Recorded {len(transactions)} transactions")
    
    # Clean up test file
    os.remove("test_transactions.jsonl")