# ADR 0003: Asymmetric Dual-Model Orchestration

## Status
Accepted

## Context
The trading bot requires two distinct modes of reasoning: fast, procedural execution for routine tasks and deep, analytical reasoning for risk assessment and market psychology analysis. Using a single model for both tasks would compromise either speed or depth. The system leverages two different language models with varying capabilities and temperature settings to achieve asymmetric reasoning.

## Decision
Implement an asymmetric dual-model orchestration where:
- **Worker Agent (System 1)**: Uses `qwen2.5-coder:7b` (primary) with `hermes-3-llama-3.1-8b` (cloud fallback) at temperature 0.0 for fast, deterministic, procedural execution (tool calling, JSON parsing, order execution).
- **Critic Agent (System 2)**: Uses `deepseek-r1:14b` (primary) with `deepseek-r1:32b` (cloud fallback) at temperature 0.1 for deep chain-of-thought reasoning, risk auditing, and market psychology analysis.

The system routes tasks to the appropriate agent based on the nature of the task:
- Worker Agent handles: market data fetching, technical indicator calculation, order execution, portfolio updates, and basic risk checks.
- Critic Agent handles: market psychology analysis, regime detection, risk scenario analysis, signal validation, and knowledge base queries.

Communication between agents occurs through shared state (database layer) and message passing (via the orchestrator).

## Consequences
### Advantages
- **Speed**: Routine operations are handled quickly by the Worker Agent without the overhead of deep reasoning.
- **Depth**: Complex analysis benefits from the Critic Agent's larger model size and slightly higher temperature for nuanced analysis.
- **Specialization**: Each model is used for its strengths, leading to better overall system performance.
- **Fallback Mechanism**: Cloud fallbacks ensure system availability if local models fail or are unavailable.

### Disadvantages
- **Increased Complexity**: Managing two different models and routing logic adds to system complexity.
- **Resource Usage**: Running two large language models concurrently requires significant VRAM/RAM (approximately 13.0 GB as allocated).
- **Potential Inconsistencies**: Differences in model outputs may require additional reconciliation logic.

### Memory Allocation
- Worker Agent (qwen2.5-coder:7b): ~4.0 GB VRAM
- Critic Agent (deepseek-r1:14b): ~6.0 GB VRAM
- Cloud fallbacks are used only when local models are unavailable, not concurrently.