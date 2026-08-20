# ADR 0008: Hermes Cloud Hybrid Harness

## Status
Accepted

## Context
The trading bot leverages both local and cloud-based language models to balance performance, cost, and capability. Local models provide low-latency, private inference for routine tasks, while cloud models offer higher capabilities for complex reasoning when needed. The system needs a robust mechanism to seamlessly switch between local and cloud models based on availability, performance requirements, and task complexity.

## Decision
Implement a hybrid harness that integrates with the Hermes Agent framework to provide cloud-augmented tooling and local hybrid execution. The harness consists of:
1. **Local Primary Models**: 
   - Worker Agent: `qwen2.5-coder:7b` (optimized for code generation and tool calling)
   - Critic Agent: `deepseek-r1:14b` (optimized for reasoning and analysis)
2. **Cloud Fallback Models**:
   - Worker Agent: `hermes-3-llama-3.1-8b` (via Hermes Agent cloud API)
   - Critic Agent: `deepseek-r1:32b` (via Hermes Agent cloud API)
3. **Automatic Fallback Mechanism**: If a local model fails to respond within a timeout or returns an error, the system automatically routes the request to the corresponding cloud fallback model.
4. **Configuration-Driven Routing**: Model routing is defined in `config/settings.yaml` under `model_routing`, allowing easy adjustment without code changes.
5. **Temperature Settings**: 
   - Worker Agent: temperature 0.0 for deterministic, procedural execution
   - Critic Agent: temperature 0.1 for nuanced, analytical reasoning

The harness is implemented through the agent initialization in each component (Worker, Critic, etc.), which loads the appropriate model based on the routing configuration and attempts local inference first before falling back to cloud.

## Consequences
### Advantages
- **Performance Optimization**: Routine tasks use fast local models, while complex reasoning leverages more capable cloud models when needed.
- **Cost Efficiency**: Reduces cloud API usage by prioritizing local models for tasks they can handle adequately.
- **Reliability**: Automatic fallback ensures system availability even if local models encounter issues.
- **Privacy**: Sensitive data can be processed locally when possible, with cloud fallbacks only used when necessary.
- **Scalability**: The harness can accommodate additional models or providers as needed.

### Disadvantages
- **Latency Variability**: Response times may vary depending on whether local or cloud models are used.
- **Complexity**: Requires managing multiple model endpoints and fallback logic.
- **Inconsistency Risk**: Different models may produce slightly different outputs for the same input, requiring careful validation.
- **Dependency on Cloud Connectivity**: Cloud fallbacks require internet access and valid API credentials.

### Memory Allocation
- Local Models: 
  - Worker Agent (qwen2.5-coder:7b): ~4.0 GB VRAM
  - Critic Agent (deepseek-r1:14b): ~6.0 GB VRAM
- Cloud Fallbacks: No persistent memory allocation; used on-demand via API calls.
- The system is designed to fit within a 13.0 GB VRAM budget when running both local models concurrently.