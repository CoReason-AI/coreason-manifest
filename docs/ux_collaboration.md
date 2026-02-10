# UX & Collaboration: Human-on-the-Loop

Coreason V2 introduces dedicated schemas to bridge the gap between autonomous execution and human understanding. This is achieved through two new planes: **Cognitive Visualization** (How the AI thinks) and **Collaboration** (How the Human engages).

## 1. Cognitive Visualization (`PresentationHints`)

The `visualization` field on any `RecipeNode` allows the recipe author to hint at the most effective way to render the agent's internal state. This enables "Magentic-UI" experiences where the interface adapts to the cognitive process (e.g., displaying a research agent as a document editor, or a planning agent as a tree).

### Schema

```python
class PresentationHints(CoReasonBaseModel):
    style: VisualizationStyle = Field(VisualizationStyle.CHAT, ...)
    display_title: str | None = Field(None, ...)
    icon: str | None = Field(None, ...)
    hidden_fields: list[str] = Field(default=[], ...)
    progress_indicator: str | None = Field(None, ...)
```

### Visualization Styles (`VisualizationStyle`)

1.  **`CHAT` (Default)**
    *   **Metaphor**: Standard Linear Message Stream.
    *   **Use Case**: Simple conversational agents, Q&A bots.
    *   **UI Behavior**: Appends messages to a chat history.

2.  **`TREE` (Tree of Thoughts)**
    *   **Metaphor**: Interactive Node-Link Diagram.
    *   **Use Case**: Complex reasoning, Multi-step planning, LATS/MCTS solvers.
    *   **UI Behavior**: Visualizes the search space, allowing users to expand branches and inspect alternative thoughts.

3.  **`KANBAN` (Task Board)**
    *   **Metaphor**: Columns and Cards.
    *   **Use Case**: Parallel sub-agents, Task decomposition, Project management.
    *   **UI Behavior**: Displays sub-tasks as cards moving through status columns (ToDo -> Doing -> Done).

4.  **`DOCUMENT` (Artifact-Centric)**
    *   **Metaphor**: Shared Document Editor (like Google Docs).
    *   **Use Case**: Draft & Refine workflows, Copywriting, Coding assistants.
    *   **UI Behavior**: Focuses on the artifact (text/code) with the chat as a sidebar.

### Example: Tree Search Visualization

```python
node = GenerativeNode(
    id="planner",
    goal="Plan trip to Tokyo",
    output_schema=...,
    visualization=PresentationHints(
        style=VisualizationStyle.TREE,
        display_title="Exploration Tree",
        icon="lucide:network",
        hidden_fields=["raw_search_results"] # Hide verbose data
    )
)
```

## 2. Collaboration (`CollaborationConfig`)

The `collaboration` field defines the rules of engagement for "Human-on-the-Loop" (HOTL) scenarios. It dictates *when* and *how* a human can intervene.

### Schema

```python
class CollaborationConfig(CoReasonBaseModel):
    mode: CollaborationMode = Field(CollaborationMode.COMPLETION, ...)
    feedback_schema: dict[str, Any] | None = Field(None, ...)
    supported_commands: list[SteeringCommand] = Field(default=[], ...)

    # Shared Agency Fields
    render_strategy: RenderStrategy = Field(RenderStrategy.PLAIN_TEXT, ...)
    trace_intervention: bool = Field(False, ...) # If True, intervention is crystallized into memory

    # Harvesting Fields (Human-Layer)
    channels: list[str] = Field(default=[], ...)
    timeout_seconds: int | None = Field(None, ...)
    fallback_behavior: Literal["fail", "proceed_with_default", "escalate"] = Field("fail", ...)
```

### Steering Commands (`SteeringCommand`)

Replaces "magic strings" with standardized primitives for human intervention.

1.  **`APPROVE`**: Accept the current state/plan.
2.  **`REJECT`**: Deny the current state/plan.
3.  **`MODIFY`**: Edit the content or parameters directly.
4.  **`ESCALATE`**: Route to a higher authority or specialized human pool.
5.  **`REWIND`**: Go back to a previous state (Time Travel).
6.  **`REPLY`**: Provide textual feedback or answer a question.

### Render Strategies (`RenderStrategy`)

Protocol for rendering the feedback interface.

1.  **`PLAIN_TEXT`**: Simple text input.
2.  **`JSON_FORMS`**: Native forms generated via JSON Schema.
3.  **`ADAPTIVE_CARD`**: Microsoft Adaptive Cards format.
4.  **`CUSTOM_IFRAME`**: Embedded Web View.

### Collaboration Modes (`CollaborationMode`)

1.  **`COMPLETION` (Default)**
    *   **Protocol**: Fire-and-Forget (until finish).
    *   **Interaction**: User waits for the final output. Can only review *after* completion (unless paused by `InteractionConfig`).

2.  **`INTERACTIVE` (Human-on-the-Loop)**
    *   **Protocol**: Chat/Steering during execution.
    *   **Interaction**: User can inject messages or commands *while* the loop is running.
    *   **Example**: "Stop researching X, focus on Y instead."

3.  **`CO_EDIT` (Magentic-UI)**
    *   **Protocol**: Shared State Mutation.
    *   **Interaction**: User and Agent edit a structured artifact simultaneously.
    *   **Example**: A coding agent writes a function, and the user fixes a typo in real-time.

### Example: Interactive Feedback

```python
from coreason_manifest.spec.v2.recipe import SteeringCommand, RenderStrategy

node = AgentNode(
    id="writer",
    agent_ref="copywriter",
    collaboration=CollaborationConfig(
        mode=CollaborationMode.INTERACTIVE,
        render_strategy=RenderStrategy.JSON_FORMS,
        trace_intervention=True,
        # Structured Feedback Form
        feedback_schema={
            "type": "object",
            "properties": {
                "rating": {"type": "integer", "minimum": 1, "maximum": 5},
                "critique": {"type": "string"}
            }
        },
        # Strictly Typed Commands
        supported_commands=[SteeringCommand.MODIFY, SteeringCommand.REPLY]
    )
)
```

## Integrating with Interaction Config

`CollaborationConfig` (Experience) works hand-in-hand with `InteractionConfig` (Control).

*   **`InteractionConfig`** handles the *mechanics* of pausing execution and allowing state mutation (the "Backend" of HOTL).
*   **`CollaborationConfig`** handles the *protocol* and *expectations* of the user interface (the "Frontend" of HOTL).

For example, a `CO_EDIT` mode implies that the UI should render a shared editor (`visualization.style="DOCUMENT"`), while `InteractionConfig.editable_fields` whitelist which parts of the state the user is actually allowed to touch.
