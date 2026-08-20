# ADR 0001: MVC-Agentic Architecture

## Status
Accepted

## Context
The trading bot requires a clean separation of concerns between data management, user interface, and control logic. Additionally, the system leverages dual-agent orchestration (Worker and Critic) for asymmetric reasoning, necessitating an architectural pattern that supports both traditional MVC and agent-based coordination.

## Decision
Adopt an MVC-Agentic architecture that combines the Model-View-Controller pattern with dual-agent orchestration. The system consists of:
- **Model Layer**: Pydantic schemas, data contracts, and memory objects (handled by `models/` and `database/`).
- **View Layer**: Live terminal telemetry, logging, and performance dashboards (handled by `views/`).
- **Controller Layer**: Agent orchestration, FSM state machines, and DAGs (handled by `controllers/`), which includes the Worker Agent (System 1) and Critic Agent (System 2).
- **Dual-Agent Orchestration**: The Worker Agent (fast, procedural, temperature 0.0) handles execution and tool calling, while the Critic Agent (deep, analytical, temperature 0.1) handles risk auditing and market psychology analysis.

## Consequences
### Advantages
- Clear separation of concerns makes the system modular and maintainable.
- The dual-agent approach allows for both rapid execution and thorough risk analysis.
- The architecture is extensible; new tools, models, or strategies can be added without disrupting existing components.
- The MVC structure facilitates testing and independent development of each layer.

### Disadvantages
- Increased complexity due to the agent orchestration layer.
- Potential latency introduced by the Critic Agent's deep reasoning processes.
- Requires careful coordination between the Worker and Critic to avoid conflicts.

### Memory Allocation
The system allocates a total of 13.0 GB of memory across components:
- Worker Agent (qwen2.5-coder:7b): ~4.0 GB
- Critic Agent (deepseek-r1:14b): ~6.0 GB
- ChromaDB vector store and caching: ~2.0 GB
- OS, runtime, and buffers: ~1.0 GB