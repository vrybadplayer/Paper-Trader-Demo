# ADR 0002: Dual-Ledger P&L System

## Status
Accepted

## Context
The trading bot needs to maintain both an immutable audit trail of all transactions and an efficient, real-time view of the portfolio's current state for risk checks, position sizing, and performance reporting. Using only a transaction history would require O(n) aggregation for every state query, which is inefficient for high-frequency trading systems. Conversely, relying solely on a mutable state ledger loses the immutable audit trail required for compliance and post-trade analysis.

## Decision
Implement a dual-ledger system consisting of:
1. **Transaction Ledger**: An append-only JSONL file (`database/data/logs/transactions.jsonl`) that records every executed trade as an immutable JSON object. This serves as the system of record for all trades and enables full auditability.
2. **Position Ledger**: An atomic key-value JSON document (`database/data/logs/positions.json`) that stores the current portfolio state (cash balance, positions, realized/unrealized P&L, total equity) for O(1) lookups. This ledger is updated after each trade to reflect the new state.

The Position Ledger is derived from the Transaction Ledger but is updated incrementally to avoid recomputation. Each trade triggers an update to both ledgers: the transaction is appended to the JSONL file, and the Position Ledger is updated in-place.

## Consequences
### Advantages
- **Auditability**: Every trade is permanently recorded in the Transaction Ledger, enabling full traceability and compliance reporting.
- **Performance**: The Position Ledger provides instant access to current portfolio state, allowing risk checks and position sizing to occur without latency.
- **Consistency**: The dual-ledger design ensures that the mutable state is always derived from the immutable history, preventing divergence.
- **Recovery**: In case of corruption, the Position Ledger can be rebuilt by replaying the Transaction Ledger.

### Disadvantages
- **Complexity**: The system must maintain two ledgers and ensure they stay in sync.
- **Storage**: Slightly increased storage overhead due to maintaining both ledgers.
- **Update Logic**: Requires careful implementation of the update logic to correctly adjust positions, cash, and P&L.

### Memory Allocation
- Transaction Ledger: Stored on disk, memory-mapped for reading; negligible RAM footprint.
- Position Ledger: Loaded entirely into memory; sized proportional to number of active positions (typically <10 KB).