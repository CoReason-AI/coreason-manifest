# Visualization Tools

As Agents grow from simple prompt wrappers into complex multi-step graphs (DAGs), understanding the execution flow becomes critical. The `coreason-manifest` package provides a utility to generate **Mermaid.js Flowcharts** directly from your `AgentDefinition` (Manifest).

## Generating a Graph

The `generate_mermaid_graph` function parses the manifest's workflow, inputs, and steps to produce a Mermaid syntax string.

### Usage Example

```python
from coreason_manifest import generate_mermaid_graph, Manifest

# Load your manifest
manifest = Manifest.model_validate({
    "apiVersion": "coreason.ai/v2",
    "kind": "Agent",
    "metadata": {"name": "Research Agent"},
    "interface": {
        "inputs": {
            "topic": {"type": "string"}
        }
    },
    "workflow": {
        "start": "research",
        "steps": {
            "research": {
                "type": "agent",
                "id": "research",
                "agent": "web-search",
                "next": "summarize"
            },
            "summarize": {
                "type": "logic",
                "id": "summarize",
                "code": "summarizer_func",
                "next": None
            }
        }
    }
})

# Generate the Mermaid string
mermaid_code = generate_mermaid_graph(manifest)
print(mermaid_code)
```

### Output

The output is a string compatible with any Mermaid.js renderer (GitHub, Notion, Obsidian, etc.):

```mermaid
graph TD
classDef input fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
classDef tool fill:#fff3e0,stroke:#e65100,stroke-width:2px;
classDef step fill:#f3e5f5,stroke:#4a148c,stroke-width:2px;
classDef term fill:#e8f5e9,stroke:#1b5e20,stroke-width:2px,rx:10,ry:10;
START((Start)):::term
INPUTS["Inputs<br/>- topic"]:::input
STEP_research["research<br/>(Call: web-search)"]:::step
STEP_summarize["summarize<br/>(Call: Logic)"]:::step
END((End)):::term
START --> INPUTS
INPUTS --> STEP_research
STEP_research --> STEP_summarize
STEP_summarize --> END
```

## Styling

The graph uses specific classes to distinguish node types:
*   **Green (Rounded)**: Start / End terminals.
*   **Blue**: Inputs.
*   **Purple**: Workflow Steps (Agents, Logic, Switch, Council).

## Handling Complex Flows

The visualizer supports:
*   **Switch Steps**: Branches are labeled with their conditions.
*   **Loops**: Cyclic dependencies are rendered naturally by Mermaid.
*   **Disconnected Nodes**: Steps defined in the workflow but not linked are still rendered, helping identify orphaned logic.
