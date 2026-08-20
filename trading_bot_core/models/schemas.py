from pydantic import BaseModel, Field, field_validator, ValidationInfo, AliasChoices
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class OrderAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"

class OrderStatus(str, Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"

class Order(BaseModel):
    order_id: str = Field(..., description="Unique identifier for the order")
    ticker: str = Field(..., description="Stock ticker symbol", validation_alias=AliasChoices('ticker', 'symbol', 'TICKER', 'SYMBOL'))
    action: OrderAction = Field(..., description="BUY or SELL")
    quantity: int = Field(..., gt=0, description="Number of shares")
    order_type: OrderType = Field(default=OrderType.MARKET, description="Type of order")
    price: Optional[float] = Field(None, gt=0, description="Limit price (for LIMIT/STOP_LIMIT)")
    stop_price: Optional[float] = Field(None, gt=0, description="Stop price (for STOP/STOP_LIMIT)")
    execution_price: Optional[float] = Field(None, gt=0, description="Actual execution price")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Order timestamp")
    status: OrderStatus = Field(default=OrderStatus.PENDING, description="Order status")
    fees: float = Field(default=0.0, ge=0, description="Trading fees")
    slippage: float = Field(default=0.0, ge=0, description="Slippage cost")
    trigger_signal: Optional[str] = Field(None, description="Reference to the signal that triggered this order")
    critic_verdict_ref: Optional[str] = Field(None, description="Reference to critic's verdict")

    @field_validator('ticker', mode='before')
    @classmethod
    def ticker_uppercase(cls, v):
        if isinstance(v, str):
            return v.upper()
        return v

    @field_validator('action', mode='before')
    @classmethod
    def action_convert(cls, v):
        if isinstance(v, str):
            return OrderAction(v.upper())
        return v

    @field_validator('price')
    @classmethod
    def price_required_for_limit_stop_limit(cls, v, info):
        if info.data.get('order_type') in [OrderType.LIMIT, OrderType.STOP_LIMIT] and v is None:
            raise ValueError('Price is required for LIMIT and STOP_LIMIT orders')
        return v

    @field_validator('stop_price')
    @classmethod
    def stop_price_required_for_stop_stop_limit(cls, v, info):
        if info.data.get('order_type') in [OrderType.STOP, OrderType.STOP_LIMIT] and v is None:
            raise ValueError('Stop price is required for STOP and STOP_LIMIT orders')
        return v

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() + 'Z' if v.tzinfo is None else v.isoformat()
        }

class PortfolioPosition(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol", validation_alias=AliasChoices('ticker', 'symbol'))
    quantity: int = Field(..., description="Number of shares (can be negative for short)")
    avg_cost: float = Field(..., ge=0, description="Average cost per share")
    current_price: float = Field(..., gt=0, description="Current market price")
    market_value: float = Field(..., ge=0, description="Current market value of position")
    unrealized_pnl: float = Field(..., description="Unrealized profit/loss")
    realized_pnl: float = Field(default=0.0, description="Realized profit/loss from this position")

    @field_validator('ticker', mode='before')
    @classmethod
    def ticker_uppercase(cls, v):
        if isinstance(v, str):
            return v.upper()
        return v

class PortfolioState(BaseModel):
    cash_balance: float = Field(..., ge=0, description="Available cash balance")
    reserve_limit: float = Field(default=50000.0, ge=0, description="Minimum cash reserve invariant")
    total_equity: float = Field(..., ge=0, description="Total portfolio equity (cash + positions value)")
    realized_pnl: float = Field(..., description="Total realized profit/loss")
    unrealized_pnl: float = Field(..., description="Total unrealized profit/loss")
    positions: List[PortfolioPosition] = Field(default_factory=list, description="Current portfolio positions")
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

    @field_validator('total_equity')
    @classmethod
    def equity_matches_cash_plus_positions(cls, v, info):
        cash = info.data.get('cash_balance', 0)
        positions_value = sum(pos.market_value for pos in info.data.get('positions', []))
        # Allow 1% tolerance for timing differences
        if abs(v - (cash + positions_value)) > (cash + positions_value) * 0.01:
            raise ValueError('Total equity does not match cash plus positions value')
        return v

class TradeSignal(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol", validation_alias=AliasChoices('ticker', 'symbol'))
    action: OrderAction = Field(..., description="BUY or SELL")
    quantity: int = Field(..., gt=0, description="Number of shares")
    target_price: Optional[float] = Field(None, gt=0, description="Target price for the trade")
    stop_loss: Optional[float] = Field(None, gt=0, description="Stop loss price")
    take_profit: Optional[float] = Field(None, gt=0, description="Take profit price")
    confidence: float = Field(..., ge=0, le=1, description="Confidence level in the signal (0-1)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Signal timestamp")
    source: str = Field(..., description="Source of the signal (e.g., 'researcher', 'technical')")
    rationale: str = Field(..., description="Explanation for the signal")

    @field_validator('ticker', mode='before')
    @classmethod
    def ticker_uppercase(cls, v):
        if isinstance(v, str):
            return v.upper()
        return v

    @field_validator('action', mode='before')
    @classmethod
    def action_convert(cls, v):
        if isinstance(v, str):
            return OrderAction(v.upper())
        return v

class RiskCheckResult(BaseModel):
    approved: bool = Field(..., description="Whether the trade is approved")
    violations: List[str] = Field(default_factory=list, description="List of violated risk invariants")
    adjusted_quantity: Optional[int] = Field(None, gt=0, description="Suggested adjusted quantity if approved with changes")
    reason: str = Field(..., description="Explanation of the risk check result")
    risk_metrics: Dict[str, Any] = Field(default_factory=dict, description="Additional risk metrics")

class MarketDataPoint(BaseModel):
    timestamp: datetime = Field(..., description="Timestamp of the data point")
    open: float = Field(..., gt=0, description="Open price")
    high: float = Field(..., gt=0, description="High price")
    low: float = Field(..., gt=0, description="Low price")
    close: float = Field(..., gt=0, description="Close price")
    volume: int = Field(..., ge=0, description="Trading volume")

class MarketDataResponse(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol")
    timeframe: str = Field(..., description="Data timeframe")
    data: List[MarketDataPoint] = Field(..., description="Market data points")
    count: int = Field(..., ge=0, description="Number of data points")
    status: str = Field(..., description="Status of the request")
    error: Optional[str] = Field(None, description="Error message if status is error")

class TechnicalIndicatorValue(BaseModel):
    timestamp: datetime = Field(..., description="Timestamp of the indicator value")
    value: float = Field(..., description="Indicator value")

class TechnicalIndicatorResponse(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol")
    indicator: str = Field(..., description="Indicator name")
    timeframe: str = Field(..., description="Data timeframe")
    period: int = Field(..., gt=0, description="Indicator period")
    values: List[TechnicalIndicatorValue] = Field(..., description="Indicator values over time")
    status: str = Field(..., description="Status of the request")
    error: Optional[str] = Field(None, description="Error message if status is error")