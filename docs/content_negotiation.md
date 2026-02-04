# Smart Content Negotiation (Client Capabilities)

The Coreason Agent Protocol (CAP) supports "Smart Content Negotiation" to allow agents to adapt their output based on the specific rendering capabilities of the client (Web, Mobile, CLI, Voice, etc.).

Instead of assuming every client can render every type of event (e.g., complex charts, markdown, images), the client declares its support via the `ClientCapabilities` object in the request.

## The `ClientCapabilities` Model

The `ClientCapabilities` model is an optional field within the `AgentRequest` envelope.

```python
from typing import List, Optional
from pydantic import ConfigDict, Field
from coreason_manifest.common import CoReasonBaseModel

class ClientCapabilities(CoReasonBaseModel):
    """Defines the rendering capabilities of the client for content negotiation."""

    model_config = ConfigDict(extra="ignore", frozen=True)

    supported_events: List[str] = Field(
        default_factory=list,
        description="List of event types the client can render (e.g., 'CITATION_BLOCK', 'MEDIA_CAROUSEL')."
    )
    prefers_markdown: bool = Field(
        default=True,
        description="Whether the client prefers markdown text."
    )
    image_resolution: Optional[str] = Field(
        default=None,
        description="Preferred image resolution (e.g., 'low', 'high', 'auto')."
    )
```

### Fields

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `supported_events` | `List[str]` | `[]` | A list of [Presentation Schemas](presentation_schemas.md) the client can render. Examples: `CITATION_BLOCK`, `MEDIA_CAROUSEL`, `PROGRESS_INDICATOR`. |
| `prefers_markdown` | `bool` | `True` | If `True`, the agent should emit `MARKDOWN_BLOCK` or markdown-formatted text. If `False`, it should emit plain text. |
| `image_resolution` | `str` | `None` | Hint for image generation/selection. Values: `low`, `high`, `auto`. |

## Usage Pattern

### 1. Client Declaration
When constructing the `AgentRequest`, the client populates the `capabilities` field.

**Example: Rich Web Client**
```python
req = AgentRequest(
    session_id=...,
    payload={"input": "Show me the sales chart"},
    capabilities=ClientCapabilities(
        supported_events=["CITATION_BLOCK", "MEDIA_CAROUSEL", "PROGRESS_INDICATOR"],
        prefers_markdown=True,
        image_resolution="high"
    )
)
```

**Example: CLI Client**
```python
req = AgentRequest(
    session_id=...,
    payload={"input": "Summarize the report"},
    capabilities=ClientCapabilities(
        supported_events=["PROGRESS_INDICATOR"], # Can render progress bars but not images
        prefers_markdown=True, # Can render terminal markdown
        image_resolution="low"
    )
)
```

**Example: Voice Interface**
```python
req = AgentRequest(
    session_id=...,
    payload={"input": "What is the weather?"},
    capabilities=ClientCapabilities(
        supported_events=[], # Cannot render visual blocks
        prefers_markdown=False, # Needs plain text for TTS
        image_resolution=None
    )
)
```

### 2. Agent Adaptation
The agent (or the Engine) reads these capabilities and adjusts its response strategy.

*   **Filtering:** If a client doesn't support `MEDIA_CAROUSEL`, the agent might skip generating charts or provide a text description instead ("I found a chart showing sales growth...").
*   **Formatting:** If `prefers_markdown` is `False`, the agent strips markdown syntax (bold, links) to ensure clean Text-to-Speech (TTS) output.
*   **Optimization:** If `image_resolution` is `low`, the agent requests smaller thumbnails to save bandwidth.

## Defaults & Backward Compatibility

The `capabilities` field is **optional**.
*   If missing (`None`), the agent assumes a "Standard Client" (typically equivalent to a Rich Web Client) or falls back to safe defaults depending on the implementation.
*   New fields added to `ClientCapabilities` in the future will be ignored by older agents (`extra="ignore"`), ensuring forward compatibility.
