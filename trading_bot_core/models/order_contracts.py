from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from .schemas import OrderAction, OrderType, OrderStatus

class OrderContract(BaseModel):
    """
    Contract defining the exact format for orders exchanged between system components.
    This ensures all parts of the system speak the same language when creating, modifying, or executing orders.
    """
    # Core order identification
    order_id: str = Field(..., description="Unique order identifier (UUID or similar)")
    client_order_id: Optional[str] = Field(None, description="Optional client-assigned order ID")
    
    # Instrument and direction
    ticker: str = Field(..., description="Stock ticker symbol (e.g., AAPL)")
    action: OrderAction = Field(..., description="BUY or SELL")
    
    # Order specifications
    quantity: int = Field(..., gt=0, description="Number of shares (positive integer)")
    order_type: OrderType = Field(default=OrderType.MARKET, description="Order type")
    price: Optional[float] = Field(None, gt=0, description="Limit price (required for LIMIT orders)")
    stop_price: Optional[float] = Field(None, gt=0, description="Stop price (required for STOP orders)")
    
    # Execution details (filled by broker/execution engine)
    execution_price: Optional[float] = Field(None, gt=0, description="Actual execution price")
    executed_quantity: Optional[int] = Field(None, ge=0, description="Actual quantity executed")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Order creation timestamp")
    execution_timestamp: Optional[datetime] = Field(None, description="Order execution timestamp")
    
    # Status and lifecycle
    status: OrderStatus = Field(default=OrderStatus.PENDING, description="Current order status")
    time_in_force: str = Field(default="DAY", description="Time in force (DAY, GTC, IOC, FOK)")
    
    # Risk and compliance
    trigger_signal_id: Optional[str] = Field(None, description="Reference to originating signal")
    critic_approval_id: Optional[str] = Field(None, description="Reference to critic's approval record")
    pre_trade_risk_check_id: Optional[str] = Field(None, description="Reference to pre-trade risk check")
    
    # Costs
    commission: float = Field(default=0.0, ge=0, description="Commission charged")
    fees: float = Field(default=0.0, ge=0, description="Other fees (exchange, regulatory)")
    slippage: float = Field(default=0.0, ge=0, description="Slippage cost (execution vs expected price)")
    
    # Metadata
    notes: Optional[str] = Field(None, description="Optional notes or tags")
    source_component: str = Field(..., description="Component that created this order (worker, critic, manual)")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z' if v.tzinfo is None else v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "order_id": "ord_1234567890abcdef",
                "client_order_id": "cli_9876543210fedcba",
                "ticker": "AAPL",
                "action": "BUY",
                "quantity": 100,
                "order_type": "MARKET",
                "price": None,
                "stop_price": None,
                "execution_price": 150.25,
                "executed_quantity": 100,
                "timestamp": "2026-08-21T10:30:00Z",
                "execution_timestamp": "2026-08-21T10:30:01Z",
                "status": "FILLED",
                "time_in_force": "DAY",
                "trigger_signal_id": "sig_1111111111",
                "critic_approval_id": "crit_2222222222",
                "pre_trade_risk_check_id": "risk_3333333333",
                "commission": 1.0,
                "fees": 0.5,
                "slippage": 0.05,
                "notes": "Momentum breakout signal",
                "source_component": "worker"
            }
        }