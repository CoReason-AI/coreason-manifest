# Interoperability & Adapter Hints

The **Interoperability Layer** (also known as the "Rosetta Stone" layer) allows the Coreason Manifest to carry metadata for external transpilers and runtimes without introducing runtime dependencies into the shared kernel.

This enables a single Manifest definition to be transpiled into code for various agent frameworks, such as LangGraph, AutoGen, or CrewAI, by providing framework-specific "hints" and configurations.

## Core Concepts

### Adapter Hints

`AdapterHints` provide instructions to a transpiler on how to map a generic Coreason Agent or Step to a specific construct in a target framework.

*   **Framework:** The target runtime (e.g., `'langgraph'`, `'autogen'`).
*   **Adapter Type:** The specific class or construct to generate (e.g., `'ReActNode'`, `'AssistantAgent'`).
*   **Settings:** An arbitrary dictionary of configuration parameters specific to that framework.

### Agent Runtime Config

The `AgentRuntimeConfig` container holds a list of `AdapterHints` for a given agent. This allows a single agent definition to support multiple targets simultaneously.

## Schema

### AdapterHints

```python
class AdapterHints(CoReasonBaseModel):
    framework: str        # e.g., 'langgraph'
    adapter_type: str     # e.g., 'ReActNode'
    settings: Dict[str, Any] # Framework-specific config
```

### AgentRuntimeConfig

```python
class AgentRuntimeConfig(CoReasonBaseModel):
    adapters: List[AdapterHints]
```

### Integration in AgentDefinition

The `AgentDefinition` now includes an optional `runtime` field:

```python
class AgentDefinition(CoReasonBaseModel):
    # ... standard fields ...
    runtime: Optional[AgentRuntimeConfig] = None
```

## Usage Examples

### Defining Hints in Python

```python
from coreason_manifest import (
    AgentDefinition,
    AgentRuntimeConfig,
    AdapterHints
)

# Define hints for LangGraph
langgraph_hint = AdapterHints(
    framework="langgraph",
    adapter_type="ReActNode",
    settings={
        "recursion_limit": 50,
        "checkpoint_memory": True
    }
)

# Define hints for AutoGen
autogen_hint = AdapterHints(
    framework="autogen",
    adapter_type="AssistantAgent",
    settings={
        "llm_config": {
            "seed": 42,
            "temperature": 0.1
        },
        "human_input_mode": "NEVER"
    }
)

# Create the Agent Definition
agent = AgentDefinition(
    id="researcher-1",
    name="Deep Researcher",
    role="Researcher",
    goal="Analyze complex topics",
    runtime=AgentRuntimeConfig(
        adapters=[langgraph_hint, autogen_hint]
    )
)
```

### Transpiler Implementation Pattern

A transpiler reading this manifest would look for hints matching its target framework:

```python
def transpile_agent(agent_def: AgentDefinition, target_framework: str):
    if not agent_def.runtime:
        return default_transpilation(agent_def)

    # Find relevant hint
    hint = next(
        (a for a in agent_def.runtime.adapters if a.framework == target_framework),
        None
    )

    if hint:
        return generate_code(
            type=hint.adapter_type,
            config=hint.settings,
            core_def=agent_def
        )
    else:
        return default_transpilation(agent_def)
```
