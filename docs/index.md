# CoReason Manifest

**A schema-first, typed manifest for AI agent orchestration and governance.**

`coreason_manifest` is an immutable "Shared Kernel" built on strict Pydantic V2 models. It defines the universal contracts for AI agent workflows, Directed Acyclic Graph (DAG) execution, state management, governance, and oversight. Designed for enterprise integration engineers and AI architects, it ensures resilient, secure, and predictable multi-agent autonomous systems.

## Core Tenets

*   **Immutability:** All workflows and configurations are immutable, ensuring deterministic execution and full auditability.
*   **Pydantic V2 Validation:** Schema-first design guarantees that all states, messages, and configurations conform to strict types before execution begins.
*   **Sandbox Isolation:** Agent nodes operate within strict, bounded environments. Tools and memory are strictly access-controlled.
*   **Bounded Autonomy:** Robust governance policies—including rate limits, budget constraints, and tool access controls—ensure agents operate safely within defined boundaries.

## Quick Start

### Installation

Install `coreason_manifest` via pip:

```bash
pip install coreason_manifest
```

### Basic `GraphFlow` Example

Define a simple multi-agent DAG with strict governance and error handling:

```python
from coreason_manifest.core.workflow.flow import GraphFlow
from coreason_manifest.core.workflow.nodes import AgentNode
from coreason_manifest.core.oversight.governance import Governance, ToolAccessPolicy

# 1. Define Governance
governance = Governance(
    tool_access=ToolAccessPolicy(allowed_tools=["fetch_data", "analyze_data"]),
    max_steps=5
)

# 2. Define an Agent Node
data_agent = AgentNode(
    id="data_retriever",
    system_prompt="You retrieve data safely.",
    governance=governance
)

# 3. Create a GraphFlow
flow = GraphFlow(
    id="data_pipeline",
    nodes=[data_agent],
    edges=[],  # Add edges here to define the DAG structure
    entry_point="data_retriever"
)

# The flow is now strictly typed, validated, and ready for execution.
```

## Repository Map

| Domain | Description | Path |
| :--- | :--- | :--- |
| **Workflow** | DAG execution, nodes (`Agent`, `Human`, `Routing`), and edges. | `core/workflow/` |
| **Oversight** | Governance, policies, resilience strategies, and interventions. | `core/oversight/` |
| **State** | Memory subsystems, event ledgers, and ephemeral storage. | `core/state/` |
| **Adapters** | Interfaces to external systems and LLM providers. | `adapters/` |

---

## Documentation

For deep-dive architectural explanations, API references, and comprehensive how-to guides, please visit the [official documentation](https://coreason-manifest.docs.example.com) or build it locally using MkDocs:

```bash
pip install mkdocs-material mkdocstrings[python]
mkdocs serve
```