# OpenAI Assistant Adapter

The **OpenAI Assistant** Adapter enables any `Coreason` agent definition to be converted into an OpenAI Assistant configuration, allowing seamless integration with the OpenAI Assistants API.

This implementation provides a pure data transformation layer, projecting `AgentDefinition` interfaces directly into the OpenAI Assistant `create` payload format.

## Overview

The adapter maps the following Coreason concepts to OpenAI Assistant concepts:

| Coreason Concept | OpenAI Assistant Concept | Notes |
| :--- | :--- | :--- |
| `AgentDefinition.name` | `name` | Passed directly. |
| `AgentDefinition.role`, `goal`, `backstory` | `instructions` | Concatenated into a single prompt. |
| `AgentDefinition.model` | `model` | Defaults to `gpt-4o` if unspecified. |
| `InlineToolDefinition` | `tools` (type: function) | Mapped directly via JSON Schema. |
| `ToolRequirement` | (Skipped) | Remote tools are currently skipped as their schema is not locally available. |

## Installation

This functionality is part of the core `coreason-manifest` package and requires no additional dependencies beyond the standard installation.

```bash
pip install coreason-manifest
```

## Usage

### Converting an Agent to an OpenAI Assistant

You can convert a Coreason Agent Definition into a dictionary compatible with the OpenAI API `client.beta.assistants.create(**config)` method.

```python
from coreason_manifest import AgentDefinition, InlineToolDefinition
from coreason_manifest.interop.openai import convert_to_openai_assistant

# 1. Define your agent with tools
calculator_tool = InlineToolDefinition(
    name="calculator",
    description="Perform basic arithmetic",
    parameters={
        "type": "object",
        "properties": {
            "expression": {"type": "string", "description": "Mathematical expression"}
        },
        "required": ["expression"]
    }
)

agent = AgentDefinition(
    id="math-tutor",
    name="Math Tutor",
    role="Tutor",
    goal="Help students learn math",
    backstory="You are a patient and encouraging math teacher.",
    tools=[calculator_tool],
    model="gpt-4-turbo"
)

# 2. Convert to OpenAI format
openai_config = convert_to_openai_assistant(agent)

print(openai_config)
# Output:
# {
#   "name": "Math Tutor",
#   "instructions": "Role: Tutor\n\nGoal: Help students learn math\n\nBackstory: ...",
#   "model": "gpt-4-turbo",
#   "tools": [
#     {
#       "type": "function",
#       "function": {
#         "name": "calculator",
#         "description": "Perform basic arithmetic",
#         "parameters": { ... }
#       }
#     }
#   ],
#   "metadata": { ... }
# }
```

### Integrating with OpenAI Python Client

The output dictionary can be passed directly to the OpenAI client using kwargs unpacking.

```python
from openai import OpenAI

client = OpenAI()

# Create the assistant
assistant = client.beta.assistants.create(**openai_config)

print(f"Created Assistant ID: {assistant.id}")
```

## Limitations

*   **Remote Tools:** Currently, `ToolRequirement` (remote tools referenced by URI) are skipped because their JSON Schema definition is not available in the manifest itself. To use remote tools, you must manually resolve and attach their definitions.
*   **Knowledge/Files:** The `knowledge` field (file paths) is currently ignored. File uploading requires stateful API calls (uploading files, getting file IDs), which is outside the scope of this stateless manifest library.
