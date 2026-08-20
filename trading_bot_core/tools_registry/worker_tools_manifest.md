# Worker Tools Manifest

## Overview
The Worker Engine (System 1) is responsible for fast, procedural execution and tool calling. 
These tools are optimized for low-latency operations, JSON parsing, and interaction with the trading system's core components.

## Tool List

### 1. `fetch_market_data`
**Description**: Retrieves real-time or historical market data for a given ticker.
**Parameters**:
- `ticker` (string, required): Stock ticker symbol (e.g., "AAPL").
- `timeframe` (string, optional, default="1D"): Data granularity ("1m", "5m", "15m", "1H", "1D", "1W").
- `limit` (integer, optional, default=100): Number of data points to retrieve.
**Returns**: 
```json
{
  "ticker": "string",
  "timeframe": "string",
  "data": [
    {
      "timestamp": "string (ISO 8601)",
      "open": "number",
      "high": "number",
      "low": "number",
      "close": "number",
      "volume": "integer"
    }
  ],
  "count": "integer"
}
```

### 2. `execute_trade`
**Description**: Submits a trade order to the broker (paper or live).
**Parameters**:
- `ticker` (string, required): Stock ticker symbol.
- `action` (string, required): Either "buy" or "sell".
- `quantity` (number, required): Number of shares to trade.
- `order_type` (string, optional, default="market"): Order type ("market", "limit", "stop").
- `price` (number, optional): Limit or stop price (required for limit/stop orders).
**Returns**:
```json
{
  "trade_id": "string (UUID)",
  "ticker": "string",
  "action": "string",
  "quantity": "number",
  "execution_price": "number",
  "timestamp": "string (ISO 8601)",
  "fees": "number",
  "slippage": "number",
  "status": "string (e.g., 'filled', 'pending', 'rejected')"
}
```

### 3. `calculate_technical_indicator`
**Description**: Calculates a technical indicator for a given ticker and timeframe.
**Parameters**:
- `ticker` (string, required): Stock ticker symbol.
- `indicator` (string, required): Indicator name (e.g., "SMA", "EMA", "RSI", "MACD").
- `timeframe` (string, optional, default="1D"): Data granularity.
- `period` (integer, optional): Lookback period (indicator-specific).
**Returns**:
```json
{
  "ticker": "string",
  "indicator": "string",
  "timeframe": "string",
  "value": "number",
  "timestamp": "string (ISO 8601)"
}
```

### 4. `update_ledger`
**Description**: Appends a trade record to the transaction ledger and updates the position ledger.
**Parameters**:
- `trade_record` (object, required): Trade details to log.
  - Must include: `trade_id`, `timestamp_utc`, `ticker`, `action`, `quantity`, `execution_price`, `fees`, `slippage`, `trigger_signal`, `critic_verdict_ref`.
**Returns**:
```json
{
  "success": "boolean",
  "message": "string",
  "ledger_updated": "string (timestamp)"
}
```

### 5. `query_vector_store`
**Description**: Queries the ChromaDB vector store for similar past trades or market conditions.
**Parameters**:
- `query_text` (string, required): Natural language query or embedding text.
- `n_results` (integer, optional, default=5): Number of similar results to return.
**Returns**:
```json
{
  "query": "string",
  "results": [
    {
      "id": "string",
      "document": "string",
      "metadata": "object",
      "distance": "number"
    }
  ]
}
```

### 6. `get_portfolio_state`
**Description**: Retrieves the current state of the portfolio (cash, positions, equity).
**Parameters**: None
**Returns**:
```json
{
  "cash_balance": "number",
  "reserve_limit": "number",
  "total_equity": "number",
  "realized_pnl": "number",
  "unrealized_pnl": "number",
  "positions": [
    {
      "ticker": "string",
      "quantity": "number",
      "avg_cost": "number",
      "current_price": "number",
      "unrealized_pnl": "number"
    }
  ]
}
```

### 7. `calculate_position_size`
**Description**: Calculates the recommended position size based on risk parameters.
**Parameters**:
- `ticker` (string, required): Stock ticker symbol.
- `risk_per_trade` (number, optional, default=0.02): Fraction of equity to risk (e.g., 0.02 for 2%).
- `stop_loss_price` (number, required): Stop-loss price for the trade.
- `entry_price` (number, required): Intended entry price.
**Returns**:
```json
{
  "ticker": "string",
  "recommended_quantity": "number",
  "risk_amount": "number",
  "risk_percentage": "number"
}
```

## Notes
- All tools are designed to be stateless and idempotent where applicable.
- Error handling: Each tool returns an error object with a `success: false` field and a `message` describing the issue.
- The Worker Engine prefers tools that return structured data (JSON) for easy parsing and chaining.
