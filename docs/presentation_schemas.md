# Presentation Schemas: UI-First Artifacts

## Overview

The `coreason_manifest.definitions.presentation` module defines a set of standardized "Presentation Blocks." These blocks serve as interim artifacts that allow agents to emit UI-specific events—such as thinking processes, structured data visualizations, rich text, or user-facing errors—independently of the final response.

These schemas are designed to be "UI-First," meaning they provide hints and structures that frontend applications can directly render without complex parsing logic.

## Core Concepts

All presentation blocks inherit from `PresentationBlock`, which provides the following common fields:

*   **`block_type`**: A discriminator field (`THOUGHT`, `DATA`, `MARKDOWN`, `ERROR`).
*   **`id`**: A unique identifier for the block (UUID).
*   **`title`**: An optional title for the block (e.g., "Analyzing Data").

### 1. ThinkingBlock

Represents the agent's internal monologue or planning process. This is useful for showing "work in progress" to the user, increasing transparency and trust.

*   **`block_type`**: `THOUGHT`
*   **`content`**: The chain-of-thought text.
*   **`status`**: The current status of the thought process (`IN_PROGRESS` or `COMPLETE`).

**Example:**
```python
from coreason_manifest.definitions.presentation import ThinkingBlock

block = ThinkingBlock(
    content="Querying the database for recent orders...",
    status="IN_PROGRESS"
)
```

### 2. DataBlock

Represents structured data that should be rendered in a specific way (e.g., a table, a list, or a JSON view).

*   **`block_type`**: `DATA`
*   **`data`**: A dictionary containing the structured data.
*   **`view_hint`**: A hint to the UI on how to render the data (`TABLE`, `JSON`, `LIST`, `KEY_VALUE`).
    *   **`TABLE`**: Expects a list of objects with similar keys.
    *   **`JSON`**: Renders a code block with syntax highlighting.
    *   **`LIST`**: Renders a bulleted or numbered list.
    *   **`KEY_VALUE`**: Renders a property list or definition list.

**Example:**
```python
from coreason_manifest.definitions.presentation import DataBlock

data = {
    "columns": ["ID", "Name", "Role"],
    "rows": [
        {"ID": 1, "Name": "Alice", "Role": "Admin"},
        {"ID": 2, "Name": "Bob", "Role": "User"}
    ]
}

block = DataBlock(
    title="User Directory",
    data=data,
    view_hint="TABLE"
)
```

### 3. MarkdownBlock

Represents rich text content formatted using Markdown. This is the standard block for general text responses.

*   **`block_type`**: `MARKDOWN`
*   **`content`**: The Markdown string.

**Example:**
```python
from coreason_manifest.definitions.presentation import MarkdownBlock

content = """
# Summary

Based on the analysis, we found **3 critical issues**.
"""

block = MarkdownBlock(content=content)
```

### 4. UserErrorBlock

Represents a user-facing error message. Unlike internal exceptions, these are designed to be shown to the end-user with helpful context.

*   **`block_type`**: `ERROR`
*   **`user_message`**: A friendly, human-readable error message.
*   **`technical_details`**: Optional dictionary containing error codes or stack traces for debugging (hidden by default in most UIs).
*   **`recoverable`**: Boolean indicating if the user can retry the action.

**Example:**
```python
from coreason_manifest.definitions.presentation import UserErrorBlock

block = UserErrorBlock(
    user_message="Unable to connect to the weather service. Please try again later.",
    technical_details={"status_code": 503, "service": "weather-api"},
    recoverable=True
)
```
