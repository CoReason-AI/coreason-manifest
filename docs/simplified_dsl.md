# Simplified YAML DSL

The Simplified YAML DSL allows developers to define Coreason Agents using a concise, human-readable syntax. It serves as an alternative to the verbose Python Builder SDK or raw JSON Schemas.

## Overview

Instead of writing complex JSON Schema dictionaries for inputs and outputs, you can use **Shorthand Types** (e.g., `city: string`, `tags: list[string]`). The DSL loader compiles this YAML into the strict `AgentDefinition` required by the Coreason Kernel.

## Syntax Guide

### Basic Structure

```yaml
name: "MyAgent"
version: "0.1.0"
author: "Team Coreason"
status: "draft"  # or "published"

system_prompt: "You are a helpful assistant."

model:
  name: "gpt-4o"
  temperature: 0.5

capabilities:
  - name: "my_capability"
    description: "Does something useful."
    type: "atomic"  # default
    inputs:
      field_name: type_shorthand
    outputs:
      result: type_shorthand
```

### Type Shorthands

The DSL supports the following shorthand types:

| Shorthand | JSON Schema Equivalent |
| :--- | :--- |
| `string` | `{"type": "string"}` |
| `int`, `integer` | `{"type": "integer"}` |
| `float`, `number` | `{"type": "number"}` |
| `bool`, `boolean` | `{"type": "boolean"}` |
| `any` | `{}` (Any type allowed) |
| `list[T]`, `array[T]` | `{"type": "array", "items": ...}` |

**Examples:**
- `age: int`
- `tags: list[string]`
- `scores: array[float]`
- `matrix: list[list[int]]`

### Implicit Rules

1.  **Required Fields**: All fields defined in `inputs` or `outputs` are treated as **Required**.
2.  **No Additional Properties**: The generated schema sets `additionalProperties: false`.

## Usage in Python

To use the DSL, import `load_from_yaml` from `coreason_manifest`.

```python
from coreason_manifest import load_from_yaml

yaml_content = """
name: "WeatherBot"
capabilities:
  - name: "get_weather"
    inputs:
      city: string
    outputs:
      temp: int
"""

# Compile into a strict AgentDefinition
agent = load_from_yaml(yaml_content)

print(agent.metadata.name)
# Output: WeatherBot
```

## Complete Example

```yaml
name: "WeatherBot"
version: "1.0.0"
status: "draft"
system_prompt: "You are a meteorological expert."

model:
  name: "gpt-4-turbo"
  temperature: 0.0

capabilities:
  - name: "get_forecast"
    description: "Retrieves the weather forecast for a city."
    inputs:
      city: string
      days: int
      include_rain: bool
    outputs:
      description: string
      temps: list[float]
```
