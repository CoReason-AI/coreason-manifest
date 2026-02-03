# Interoperability & The Rosetta Stone Strategy

The Coreason ecosystem is designed to be the "Shared Kernel" for AI agents—a definitive source of truth that is engine-agnostic. However, we recognize that the AI landscape is diverse, with powerful frameworks like **LangGraph**, **AutoGen**, and **CrewAI** offering specialized capabilities for execution.

To support this diversity without polluting our strict kernel with heavy dependencies, Coreason employs a **"Rosetta Stone"** strategy.

## Adapter Hints

The primary mechanism for interoperability is the `AdapterHints` schema. These hints are embedded directly into the `AgentRuntimeConfig` of your Agent Manifest. They serve as metadata instructions for external translation tools (or "Adapters") to generate high-fidelity code for target platforms.

### The Concept

The Coreason Manifest defines *what* the agent is (inputs, outputs, tools, policy). The `AdapterHints` define *how* it should be instantiated in a specific foreign runtime.

This keeps the Coreason kernel **logic-free** (no `langchain` or `autogen` imports) while enabling seamless transpilation.

### Schema Definition

```python
class AdapterHints(CoReasonBaseModel):
    framework: str        # e.g., "langgraph", "autogen"
    adapter_type: str     # e.g., "ReActNode", "UserProxyAgent"
    settings: Dict[str, Any]  # Framework-specific config
```

### Example Usage

Here is how you might define an agent that is intended to be run primarily by Coreason's engine but can also be exported to **LangGraph** or **AutoGen**.

```python
from coreason_manifest.definitions.agent import (
    AgentDefinition,
    AgentRuntimeConfig,
    AdapterHints
)

agent = AgentDefinition(
    # ... metadata, capabilities ...
    config=AgentRuntimeConfig(
        # Standard Coreason Configuration
        model_config=...,

        # Interoperability Hints
        adapter_hints=[
            # Hint for LangGraph Adapters
            AdapterHints(
                framework="langgraph",
                adapter_type="ReActNode",
                settings={
                    "memory_key": "chat_history",
                    "recursion_limit": 50
                }
            ),
            # Hint for AutoGen Adapters
            AdapterHints(
                framework="autogen",
                adapter_type="AssistantAgent",
                settings={
                    "human_input_mode": "NEVER",
                    "max_consecutive_auto_reply": 10
                }
            )
        ]
    ),
    # ... dependencies ...
)
```

## How It Works

1.  **Define**: You define your agent in the Coreason Manifest, adding `AdapterHints` for your target platforms.
2.  **Export**: You use a Coreason CLI tool or SDK (separate from this kernel) to "export" the agent.
3.  **Translate**: The exporter reads the `framework` hint.
    *   If `framework="langgraph"`, it looks up the `LangGraphAdapter`.
    *   It uses `adapter_type="ReActNode"` to determine which class to instantiate.
    *   It passes `settings` directly to that class constructor.
4.  **Generate**: The tool outputs a valid Python file (e.g., `agent.py`) containing the LangGraph code, pre-configured with the tools, prompts, and models defined in your manifest.

## Benefits

*   **No Vendor Lock-in**: Your agent definition is portable. You can switch execution engines by simply adding a new hint and re-exporting.
*   **Clean Kernel**: The `coreason-manifest` package remains lightweight and secure, with zero dependencies on the rapidly changing AI framework ecosystem.
*   **High Fidelity**: Instead of generic translations, hints allow you to leverage framework-specific features (like AutoGen's `groupchat` settings or LangGraph's `checkpoint` config) explicitly.
