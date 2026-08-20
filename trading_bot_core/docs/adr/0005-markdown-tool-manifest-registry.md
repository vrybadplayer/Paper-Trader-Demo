# ADR 0005: Markdown Tool Manifest Registry

## Status
Accepted

## Context
The trading bot requires a standardized way to document the capabilities, parameters, and expected outputs of the tools available to the Worker and Critic Agents. This documentation is essential for the agents to understand how to invoke tools correctly and interpret their results. The manifests should be easily accessible, version-controlled, and human-readable.

## Decision
Adopt a Markdown-based tool manifest registry stored in the `tools_registry/` directory. Each tool manifest is a Markdown file that exhaustively documents:
- Tool name and description
- Parameters (name, type, required, constraints)
- Input types and formats
- Expected response payloads (structure, data types, example responses)
- Error conditions and handling
- Usage examples

Two manifests are maintained:
- `worker_tools_manifest.md` for tools used by the Worker Agent (System 1)
- `critic_tools_manifest.md` for tools used by the Critic Agent (System 2)

The manifests are written in Markdown for readability and are kept alongside the code they document. They serve as the single source of truth for tool interfaces and are referenced by the agents during operation.

## Consequences
### Advantages
- **Clarity**: Provides clear, detailed documentation of each tool's interface.
- **Accessibility**: Easy to read and update without requiring special tools.
- **Consistency**: Ensures all agents use the same understanding of tool capabilities.
- **Integration**: Facilitates automatic documentation generation and validation.

### Disadvantages
- **Maintenance**: Requires effort to keep the manifests in sync with the actual tool implementations.
- **Redundancy**: Information may be duplicated from docstrings or interface definitions.

### Memory Allocation
- Negligible: The manifest files are small text files stored on disk, loaded into memory only when referenced.