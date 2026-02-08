# Cognitive Visualization and Collaboration Protocols

The `coreason-manifest` library supports advanced visualization and collaboration capabilities, enabling "Glass Box" reasoning and "Magentic-UI" experiences. These features are configured directly within `RecipeNode` definitions, allowing the execution engine to render the agent's internal state and facilitate human-in-the-loop interactions.

## 1. Glass Box Visualization (`PresentationHints`)

The `presentation` field (type `PresentationHints`) on any `RecipeNode` controls how the node's execution is visualized.

### Visualization Styles (`VisualizationStyle`)

*   `CHAT`: (Default) Standard linear conversation stream. ideal for simple Q&A agents.
*   `TREE`: Interactive "Tree of Thoughts". Essential for visualizing `GenerativeNode` execution using solvers like Tree Search or MCTS.
*   `KANBAN`: Task board view. Useful for visualizing parallel execution or optimization workflows.
*   `DOCUMENT`: Artifact-centric view. Designed for "Draft & Refine" workflows where the primary output is a structured document.

### Configuration Fields

*   `style`: `VisualizationStyle` (Default: `CHAT`).
*   `display_title`: `str | None`. A human-friendly label override for the node.
*   `icon`: `str | None`. An icon name or emoji (e.g., `lucide:brain`).
*   `hidden_fields`: `list[str]`. A list of internal variable names to hide from the UI to reduce cognitive load.
*   `progress_indicator`: `str | None`. The name of a field in the state to watch for percentage completion updates.

### Example

```python
from coreason_manifest.spec.v2.recipe import AgentNode, PresentationHints, VisualizationStyle

node = AgentNode(
    id="writer",
    agent_ref="writer-agent",
    presentation=PresentationHints(
        style=VisualizationStyle.DOCUMENT,
        display_title="Drafting Article",
        icon="lucide:file-text",
        hidden_fields=["scratchpad", "raw_search_results"]
    )
)
```

## 2. Co-Pilot Collaboration (`CollaborationConfig`)

The `collaboration` field (type `CollaborationConfig`) defines the protocol for human engagement with the node.

### Collaboration Modes (`CollaborationMode`)

*   `COMPLETION`: (Default) The human waits for the node to finish, then reviews the final output.
*   `INTERACTIVE`: The human can chat and inject messages *during* the node's execution loop (Human-on-the-Loop).
*   `CO_EDIT`: The human and the agent edit a shared structured artifact together in real-time.

### Configuration Fields

*   `mode`: `CollaborationMode` (Default: `COMPLETION`).
*   `feedback_schema`: `dict[str, Any] | None`. A JSON Schema defining the structure of feedback the human can provide (e.g., `{ 'rating': int, 'critique': str }`).
*   `supported_commands`: `list[str]`. A list of slash commands the agent understands during interaction (e.g., `['/refine', '/expand', '/switch_tool']`).

### Example

```python
from coreason_manifest.spec.v2.recipe import AgentNode, CollaborationConfig, CollaborationMode

node = AgentNode(
    id="researcher",
    agent_ref="research-agent",
    collaboration=CollaborationConfig(
        mode=CollaborationMode.INTERACTIVE,
        supported_commands=["/search_more", "/summarize"],
        feedback_schema={
            "type": "object",
            "properties": {
                "quality_score": {"type": "integer", "minimum": 1, "maximum": 5},
                "notes": {"type": "string"}
            }
        }
    )
)
```
