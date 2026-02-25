# Presentation Schemas: The Visual Contract

Coreason V2 defines a strict **Visual Contract** between the Backend (Runtime) and the Frontend (Builder/Chat). This ensures that while the Runtime executes logic, the Builder can persistently store layout information without polluting the execution model.

## 1. Graph Layout (`NodePresentation`)

When defining a `Recipe`, the Runtime only cares about the topology (nodes and edges). However, the Visual Builder needs to know where to place these nodes on the canvas.

The `presentation` field in `RecipeNode` is the dedicated container for this metadata.

### The Contract
*   **Runtime ignores it:** The engine will not fail if `x/y` are missing (though they are required by schema).
*   **Builder owns it:** The UI is the source of truth for these coordinates.

### Schema

```python
class NodePresentation(CoReasonBaseModel):
    x: float          # Canvas X coordinate
    y: float          # Canvas Y coordinate
    label: str | None # Optional override for display name
    color: str | None # Hex code (e.g. #FF0000)
    icon: str | None  # Icon identifier (e.g. lucide:brain)
    z_index: int      # Rendering layer order
```

### Example: Recipe Node with Layout

```python
from coreason_manifest.spec.v2.recipe import AgentNode
from coreason_manifest.spec.common.presentation import NodePresentation

node = AgentNode(
    id="research-step",
    agent_ref="researcher-v1",
    presentation=NodePresentation(
        x=100.5,
        y=200.0,
        label="Deep Research Phase",
        color="#33FF57",
        icon="lucide:microscope"
    )
)
```

## 2. Runtime Events (`PresentationEvent`)

During execution, Agents emit "Presentation Events" to render rich UI elements like citations, artifacts, and progress bars. These are strictly typed to ensure the Frontend can render them deterministically.

### Core Container

```python
class PresentationEvent(CoReasonBaseModel):
    id: UUID
    timestamp: datetime
    type: PresentationEventType
    data: Union[CitationBlock, ProgressUpdate, MediaCarousel, MarkdownBlock]
```

### Supported Event Types

*   **`citation_block`**: List of source references with snippets.
*   **`progress_indicator`**: Loading bars with status and percentage.
*   **`media_carousel`**: Gallery of images or files.
*   **`markdown_block`**: Standard rich text.

### Example: Emitting a Citation

```json
{
  "type": "citation_block",
  "data": {
    "items": [
      {
        "source_id": "doc-1",
        "uri": "https://example.com/report.pdf",
        "title": "Annual Report 2024",
        "snippet": "Revenue grew by 20%..."
      }
    ]
  }
}
```

## 3. User Experience (`PresentationHints`)

While `NodePresentation` controls the *static layout* of the graph, `PresentationHints` controls the *dynamic user experience* when the agent is active. This field lives in `node.visualization` and is defined in `coreason_manifest.spec.common.presentation`.

It dictates:
*   **ViewportMode:** Whether to show a Chat, Split View, or Planner Console.
*   **Components:** Which Generative UI widgets (Data Grid, Kanban) to render.
*   **Mutability:** Whether the user can edit the agent's workspace.

See [Magentic UI & Visualization Protocol](visualization.md) for details.
