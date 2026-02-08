# Cognitive Visualization & Collaboration

The `coreason-manifest` library implements a "Glass Box" philosophy, making the internal reasoning of AI agents visible and understandable. This is achieved through two distinct configuration schemas on `RecipeNode`:

1.  **`visualization` (`PresentationHints`)**: Controls *how* the node's internal state and reasoning process are rendered to the user (e.g., as a chat, a tree of thoughts, or a kanban board).
2.  **`collaboration` (`CollaborationConfig`)**: Defines the *protocol* for human engagement (e.g., waiting for approval, interactive chat, or co-editing artifacts).

---

## 1. Cognitive Visualization (`PresentationHints`)

This configuration tells the UI which "lens" to use when displaying the node's execution.

### Schema

```python
class VisualizationStyle(StrEnum):
    CHAT = "CHAT"          # Standard linear message stream (Default)
    TREE = "TREE"          # Interactive "Tree of Thoughts"
    KANBAN = "KANBAN"      # Task board view
    DOCUMENT = "DOCUMENT"  # Artifact-centric view

class PresentationHints(CoReasonBaseModel):
    style: VisualizationStyle = Field(VisualizationStyle.CHAT, description="Rendering style.")
    display_title: str | None = Field(None, description="Human-friendly label override.")
    icon: str | None = Field(None, description="Icon name/emoji (e.g., 'lucide:brain').")
    hidden_fields: list[str] = Field(default_factory=list, description="Internal variables to hide.")
    progress_indicator: str | None = Field(None, description="Field name to watch for % completion.")
```

### Usage Example

```python
from coreason_manifest.spec.v2.recipe import AgentNode, PresentationHints, VisualizationStyle

node = AgentNode(
    id="research_step",
    agent_ref="researcher",
    visualization=PresentationHints(
        style=VisualizationStyle.TREE,
        display_title="Deep Research Process",
        icon="lucide:network",
        hidden_fields=["raw_logs", "embedding_cache"]
    )
)
```

---

## 2. Collaboration (`CollaborationConfig`)

This configuration defines the "Rules of Engagement" between the AI and the human.

### Schema

```python
class CollaborationMode(StrEnum):
    COMPLETION = "COMPLETION"   # Human waits for finish, then reviews output (Default)
    INTERACTIVE = "INTERACTIVE" # Human can chat/inject messages *during* execution loops (HOTL)
    CO_EDIT = "CO_EDIT"         # Human and Agent edit a shared structured artifact together (Magentic-UI)

class CollaborationConfig(CoReasonBaseModel):
    mode: CollaborationMode = Field(CollaborationMode.COMPLETION, description="Engagement mode.")
    feedback_schema: dict[str, Any] | None = Field(None, description="JSON Schema for structured feedback.")
    supported_commands: list[str] = Field(default_factory=list, description="Slash commands allowed (e.g., '/refine').")
```

### Usage Example

```python
from coreason_manifest.spec.v2.recipe import AgentNode, CollaborationConfig, CollaborationMode

node = AgentNode(
    id="drafting_step",
    agent_ref="writer",
    collaboration=CollaborationConfig(
        mode=CollaborationMode.CO_EDIT,
        feedback_schema={
            "type": "object",
            "properties": {
                "tone": {"type": "string", "enum": ["formal", "casual"]},
                "comments": {"type": "string"}
            }
        },
        supported_commands=["/rewrite", "/expand", "/shorten"]
    )
)
```

---

## 3. Graph Layout (`NodePresentation`)

**Note:** The `presentation` field on `RecipeNode` is reserved strictly for **static graph layout** data. It does *not* control the cognitive rendering style.

### Schema

```python
class NodePresentation(CoReasonBaseModel):
    x: float = Field(..., description="X coordinate.")
    y: float = Field(..., description="Y coordinate.")
    color: str | None = Field(None, description="Color code (hex/name).")
```

### Usage Example

```python
node = AgentNode(
    id="step_1",
    agent_ref="worker",
    presentation=NodePresentation(x=100.0, y=200.0, color="#FF5733")
)
```

---

## Summary of Fields

| Field | Type | Purpose | Example |
| :--- | :--- | :--- | :--- |
| **`visualization`** | `PresentationHints` | **Cognitive Rendering**: How the *running* state is shown. | Tree of Thoughts, Chat, Kanban |
| **`collaboration`** | `CollaborationConfig` | **Human Protocol**: How the human *interacts* with it. | Co-Edit, Interactive Chat |
| **`presentation`** | `NodePresentation` | **Static Layout**: Where the node sits on the canvas. | X=100, Y=200, Color=Red |
