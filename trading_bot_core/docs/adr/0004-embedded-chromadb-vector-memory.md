# ADR 0004: Embedded ChromaDB Vector Memory

## Status
Accepted

## Context
The trading bot requires a persistent memory mechanism to store and retrieve trade memories, market psychology patterns, and regime indicators for enhanced decision-making. The system needs to leverage vector similarity search to find similar historical cases and improve the Critic Agent's analysis. An external database would introduce latency and operational complexity, while an in-memory solution would not persist across sessions.

## Decision
Use an embedded ChromaDB vector store with persistent storage to provide dynamic Retrieval-Augmented Generation (RAG) capabilities. The vector store is initialized with a persistent directory (`./database/data/chroma_db`) and uses the HNSW index with cosine similarity for efficient similarity search. The store is updated continuously after each trade to include new trade memories and market knowledge.

The vector store is accessed by both the Worker and Critic Agents:
- Worker Agent: Uses it for fetching similar trade setups and market data patterns.
- Critic Agent: Uses it for market psychology analysis, regime detection, and risk scenario analysis.

## Consequences
### Advantages
- **Persistence**: Memories and knowledge are stored on disk and available across system restarts.
- **Performance**: Embedded ChromaDB provides low-latency vector similarity search without network overhead.
- **Dynamic Updates**: The store can be updated in real-time as new trades occur and new market knowledge is added.
- **Scalability**: The HNSW index scales efficiently with the number of documents.

### Disadvantages
- **Disk Usage**: The vector store will grow over time and require periodic maintenance or pruning.
- **Memory Mapping**: ChromaDB uses memory-mapped files, which can consume virtual memory.
- **Single-Writer Limitation**: While ChromaDB supports multiple readers, writes are serialized; however, in our system, updates are infrequent (per trade) and handled by a single agent at a time.

### Memory Allocation
- Vector Store: Allocated ~2.0 GB of memory for caching and the HNSW index (configured via ChromaDB settings).
- The actual disk usage depends on the number of stored documents but is designed to fit within the allocated memory budget for caching.