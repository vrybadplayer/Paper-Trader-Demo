# Macro Regime Indicators

## Definition
Macro regime indicators are broad economic and market metrics that help identify the prevailing economic environment (e.g., expansion, contraction, inflationary, deflationary) and investor risk sentiment (risk-on vs risk-off). These indicators influence asset allocation, sector rotation, and overall market direction.

## Key Indicators

### 1. **Volatility Index (VIX)**
- **What it measures**: Market expectation of near-term volatility conveyed by S&P 500 index options.
- **Regime signals**:
  - VIX < 20: Low volatility, complacent or risk-on environment.
  - VIX 20-30: Moderate volatility, uncertain or transitioning regime.
  - VIX > 30: High volatility, fear, risk-off, or market stress.

### 2. **10-Year Treasury Yield**
- **What it measures**: Interest rate on U.S. government debt maturing in 10 years.
- **Regime signals**:
  - Rising yields: Expectations of stronger growth and/or higher inflation (can be risk-on if moderate, risk-off if too rapid).
  - Falling yields: Expectations of slower growth, deflationary pressures, or flight to safety (risk-off).
  - Yield curve inversion (short-term yields > long-term yields): Strong recession signal.

### 3. **U.S. Dollar Index (DXY)**
- **What it measures**: Value of the U.S. dollar relative to a basket of foreign currencies.
- **Regime signals**:
  - Rising dollar: Often indicates risk-off sentiment or expectations of U.S. monetary tightening.
  - Falling dollar: Can signal risk-on, expectations of easier monetary policy, or improving global growth.

### 4. **Credit Spreads (e.g., BAA-AAA, High Yield)**
- **What it measures**: Yield difference between corporate bonds and Treasuries, reflecting perceived credit risk.
- **Regime signals**:
  - Widening spreads: Increasing credit risk, risk-off, potential economic slowdown.
  - Narrowing spreads: Improving credit conditions, risk-on, economic expansion.

### 5. **Commodity Prices (e.g., Oil, Copper, Gold)**
- **What it measures**: Prices of key commodities reflecting global demand and inflation expectations.
- **Regime signals**:
  - Rising oil & copper: Strong global demand, inflationary pressures, risk-on for growth assets.
  - Rising gold: Flight to safety, inflation hedge, or currency debasement fears (can be risk-off or inflation hedge).
  - Falling commodities: Weak global demand, deflationary concerns, risk-off.

### 6. **Purchasing Managers' Index (PMI)**
- **What it measures**: Surveys of private sector companies indicating expansion (>50) or contraction (<50) in manufacturing/services.
- **Regime signals**:
  - PMI > 50: Economic expansion, generally risk-on.
  - PMI < 50: Economic contraction, risk-off.
  - Sharp changes: Turning points in the economic cycle.

### 7. **Unemployment Rate & Non-Farm Payrolls**
- **What it measures**: Labor market health.
- **Regime signals**:
  - Falling unemployment + strong payrolls: Tight labor market, potential wage inflation, late-cycle concerns.
  - Rising unemployment: Weakening economy, risk-off.

### 8. **Consumer Price Index (CPI) & Personal Consumption Expenditures (PCE)**
- **What it measures**: Inflation at the consumer level.
- **Regime signals**:
  - Rising inflation: Potential for tighter monetary policy, can be negative for duration assets.
  - Falling inflation/deflation: Risk of economic stagnation, may prompt monetary easing.

## Regime Classification Framework

### Risk-On Regime Characteristics
- Low volatility (VIX < 20)
- Rising or moderate 10Y yields (2.5%-4.0%)
- Stabilizing or slightly falling dollar
- Narrowing credit spreads
- Rising commodity prices (oil, copper)
- PMI > 50 and rising
- Strong labor market
- Moderate inflation (2%-3%)

### Risk-Off Regime Characteristics
- High volatility (VIX > 25)
- Falling 10Y yields (<2.5%) or inverted yield curve
- Rising dollar (safe haven)
- Widening credit spreads
- Falling commodity prices (except gold)
- PMI < 50 or falling
- Weak labor market
- Very low or negative inflation/deflation fears

### Inflationary Regime
- Rising 10Y yields (>4.0%)
- Rising commodity prices (especially energy)
- Rising CPI/PCE (>3%)
- Potential for Fed tightening
- Often accompanied by rising inflation expectations (breakeven inflation)

### Deflationary Regime
- Falling 10Y yields (<2.0%)
- Falling commodity prices
- Falling CPI/PCE (<1%) or deflation fears
- Rising demand for Treasuries
- Often accompanied by economic contraction signals

## Trading Implications

### Asset Allocation
- **Risk-On**: Favor equities (especially cyclicals, emerging markets), high-yield bonds, commodities.
- **Risk-Off**: Favor Treasuries, investment-grade bonds, gold, cash, defensive equities (utilities, consumer staples).
- **Inflationary**: Favor TIPS, commodities, real estate, equities with pricing power.
- **Deflationary**: Favor long-duration Treasuries, high-quality bonds, cash.

### Sector Rotation
- Early expansion: Industrials, materials, technology.
- Late expansion: Energy, utilities.
- Contraction: Consumer staples, healthcare, utilities.
- Recovery: Financials, consumer discretionary.

### Risk Management
- Regime shifts often precede significant market moves; positioning ahead of shifts can enhance returns.
- Use regime indicators to adjust portfolio beta, leverage, and hedging strategies.
- Monitor multiple indicators for confirmation; no single indicator is foolproof.

## Limitations
- Indicators can give false signals during transitional periods.
- Some indicators are lagging (e.g., unemployment) while others are leading (e.g., yield curve).
- Global interdependence means domestic indicators may be influenced by foreign factors.
- Central bank interventions can distort traditional indicator relationships.

## Integration with Trading Bot
The Critic Agent monitors these regime indicators via the knowledge base and market data feeds to:
- Adjust risk parameters (e.g., reduce position sizing in risk-off regimes).
- Filter trade signals (e.g., only take long positions in risk-on regimes for growth assets).
- Provide context for market psychology analysis (e.g., high VIX may amplify fear-driven behavior).
- Trigger regime-based strategy shifts in the orchestration layer.
