# Critic Tools Manifest

## Overview
The Critic Engine (System 2) is responsible for deep chain-of-thought reasoning, risk auditing, and market psychology analysis.
These tools are designed for complex analysis, leveraging the knowledge base and performing sophisticated checks.

## Tool List

### 1. `analyze_market_psychology`
**Description**: Analyzes current market conditions for behavioral patterns (FOMO, whale traps, liquidity sweeps, etc.).
**Parameters**:
- `ticker` (string, required): Stock ticker symbol.
- `timeframe` (string, optional, default="1D"): Analysis timeframe.
- `lookback_period` (integer, optional, default=20): Number of periods to analyze for patterns.
**Returns**:
```json
{
  "ticker": "string",
  "timeframe": "string",
  "analysis": {
    "fomo_detected": "boolean",
    "whale_trap_risk": "string (low, medium, high)",
    "liquidity_sweep_risk": "string (low, medium, high)",
    "market_regime": "string (e.g., 'bullish', 'bearish', 'choppy')",
    "sentiment_score": "number (-1 to 1)",
    "confidence": "number (0 to 1)"
  },
  "timestamp": "string (ISO 8601)"
}
```

### 2. `validate_risk_parameters`
**Description**: Validates a proposed trade against the portfolio's risk limits and invariants.
**Parameters**:
- `trade_proposal` (object, required): The trade details to validate.
  - Must include: `ticker`, `action`, `quantity`, `entry_price`, `stop_loss_price`, `target_price`.
- `portfolio_state` (object, required): Current portfolio state (from `get_portfolio_state`).
**Returns**:
```json
{
  "approved": "boolean",
  "violations": [
    {
      "rule": "string (e.g., 'cash_reserve', 'position_size', 'risk_reward')",
      "message": "string",
      "current_value": "number",
      "limit": "number"
    }
  ],
  "suggested_adjustments": {
    "quantity": "number (optional)",
    "stop_loss_price": "number (optional)",
    "target_price": "number (optional)"
  }
}
```

### 3. `assess_trade_quality`
**Description**: Provides a qualitative assessment of a trade idea based on fundamental, technical, and sentiment factors.
**Parameters**:
- `ticker` (string, required): Stock ticker symbol.
- `trade_direction` (string, required): Either "buy" or "sell".
- `time_horizon` (string, optional, default="swing"): Expected holding period.
**Returns**:
```json
{
  "ticker": "string",
  "trade_direction": "string",
  "time_horizon": "string",
  "assessment": {
    "fundamental_score": "number (0 to 10)",
    "technical_score": "number (0 to 10)",
    "sentiment_score": "number (0 to 10)",
    "composite_score": "number (0 to 10)",
    "recommendation": "string (e.g., 'strong_buy', 'buy', 'neutral', 'sell', 'strong_sell')"
  },
  "timestamp": "string (ISO 8601)"
}
```

### 4. `query_historical_similarity`
**Description**: Queries the vector store for historical trades or market conditions similar to the current setup.
**Parameters**:
- `query_context` (string, required): Description of the current trade setup or market condition.
- `n_results` (integer, optional, default=5): Number of similar historical cases to return.
**Returns**:
```json
{
  "query": "string",
  "results": [
    {
      "id": "string",
      "document": "string",
      "metadata": {
        "ticker": "string",
        "date": "string",
        "action": "string",
        "outcome": "string (e.g., 'profit', 'loss')",
        "pnl": "number"
      },
      "similarity_score": "number (0 to 1, higher is more similar)"
    }
  ]
}
```

### 5. `calculate_portfolio_risk_metrics`
**Description**: Calculates advanced risk metrics for the current portfolio.
**Parameters**:
- `portfolio_state` (object, required): Current portfolio state.
- `lookback_days` (integer, optional, default=30): Number of days for historical calculations.
**Returns**:
```json
{
  "portfolio_id": "string",
  "timestamp": "string (ISO 8601)",
  "metrics": {
    "var_95": "number (Value at Risk at 95% confidence)",
    "cvar_95": "number (Conditional VaR at 95% confidence)",
    "max_drawdown": "number (maximum drawdown over lookback period)",
    "sharpe_ratio": "number (annualized Sharpe ratio)",
    "sortino_ratio": "number (annualized Sortino ratio)",
    "volatility": "number (annualized volatility)",
    "beta": "number (portfolio beta to benchmark, if applicable)"
  }
}
```

### 6. `generate_risk_report`
**Description**: Generates a comprehensive risk report for the portfolio or a specific trade.
**Parameters**:
- `report_type` (string, required): Either "portfolio" or "trade".
- `target` (string, required): For "trade", the trade_id; for "portfolio", can be omitted or set to "current".
**Returns**:
```json
{
  "report_type": "string",
  "target": "string",
  "timestamp": "string (ISO 8601)",
  "report": {
    "summary": "string (text summary)",
    "details": "object (detailed findings)",
    "recommendations": "array of strings"
  }
}
```

## Notes
- The Critic Engine tools are designed to be used in a reasoning loop, where the output of one tool can inform the input to another.
- Error handling follows the same pattern as the Worker Engine: each tool returns an object with a `success` field (boolean) and a `message` string on failure.
- The Critic Engine may chain multiple tools together to form a comprehensive analysis before providing a final verdict on a trade.
