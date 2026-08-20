# ADR 0007: Pre-Flight Cash Reserve Invariants

## Status
Accepted

## Context
The trading bot must ensure that it never risks more capital than it has available, maintaining a strict cash reserve to prevent margin calls, forced liquidations, or insolvency. The system needs a mechanism to guarantee that a minimum cash balance is always preserved, regardless of trading activity or market conditions.

## Decision
Implement a pre-flight cash reserve invariant that must be satisfied before any trade is executed. The invariant requires that the projected cash balance after a trade must remain at or above a minimum threshold ($50,000 in this system). This check is performed by the Critic Agent during the risk validation phase and enforced by the Worker Agent before order submission.

The invariant is checked as part of the risk validation process:
1. Calculate the projected cash balance after executing the proposed trade (including fees and slippage).
2. Ensure that projected cash balance >= cash reserve limit ($50,000).
3. If the invariant would be violated, the trade is rejected or the position size is reduced to comply.

This invariant is stored in the configuration (`config/settings.yaml`) and loaded by both agents at startup.

## Consequences
### Advantages
- **Capital Protection**: Guarantees that a minimum cash reserve is always maintained, protecting against catastrophic losses.
- **Risk Management**: Provides a clear, quantifiable risk limit that is easy to understand and enforce.
- **Automated Enforcement**: The invariant is checked automatically for every proposed trade, reducing reliance on manual oversight.
- **Configurable**: The reserve limit can be adjusted in configuration without code changes.

### Disadvantages
- **Opportunity Cost**: During periods of attractive trading opportunities, the reserve may limit position sizing or prevent trades entirely.
- **False Sense of Security**: While it protects against cash depletion, it does not protect against losses within the available capital.
- **Complexity in Calculation**: Accurately projecting post-trade cash requires accounting for fees, slippage, and potential market impact.

### Memory Allocation
- Negligible: The cash reserve limit is a single floating-point number stored in configuration and loaded into memory at startup.