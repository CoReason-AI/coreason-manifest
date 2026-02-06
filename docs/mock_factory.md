# Mock Data Factory

The **Mock Data Factory** (`src/coreason_manifest/utils/mock.py`) provides a utility to programmatically generate deterministic, schema-compliant synthetic data for Agents.

This is essential for testing, simulating agent outputs, and validating downstream systems without running actual LLM inference.

## Overview

The factory parses the `output` schema of an `AgentDefinition` and recursively generates a Python dictionary that satisfies all constraints (types, enums, formats).

Key features:
*   **Deterministic:** Supports seeding for reproducible test cases.
*   **Schema Compliant:** Respects JSON Schema keywords like `enum`, `const`, `allOf`, `anyOf`, `oneOf`.
*   **Safe:** Handles recursive schemas (e.g., self-referencing definitions) with depth limits.
*   **Zero Dependency:** Uses only Python standard library.

## Usage

```python
from coreason_manifest import generate_mock_output, Manifest
from coreason_manifest.spec.v2.definitions import AgentDefinition, InterfaceDefinition

# 1. Define an Agent with an Output Schema
agent = AgentDefinition(
    id="weather-agent",
    description="Gets weather",
    interface=InterfaceDefinition(
        inputs={"location": {"type": "string"}},
        outputs={
            "type": "object",
            "properties": {
                "temperature": {"type": "integer", "minimum": -50, "maximum": 50},
                "condition": {"type": "string", "enum": ["sunny", "cloudy", "rainy"]},
                "timestamp": {"type": "string", "format": "date-time"}
            },
            "required": ["temperature", "condition"]
        }
    )
)

# 2. Generate Mock Data
# Use a seed for reproducibility
mock_data = generate_mock_output(agent, seed=42)

print(mock_data)
# Output might look like:
# {
#   "temperature": 12,
#   "condition": "cloudy",
#   "timestamp": "2023-10-27T10:00:00Z"
# }
```

## MockGenerator Logic

The utility uses the `MockGenerator` class internally to traverse the schema.

### Type Support

| Type | Generator Behavior |
| :--- | :--- |
| `string` | Random alphanumeric string. Supports `format: uuid` and `format: date-time`. |
| `integer` | Random integer within range (default 0-100). |
| `number` | Random float. |
| `boolean` | Random `True` or `False`. |
| `array` | List of items (length 1-3). |
| `object` | Dictionary with properties generated recursively. |
| `null` | Returns `None`. |

### Advanced Keywords

*   **`$ref`**: Resolves local definitions (`$defs` or `definitions`) and recurses.
*   **`enum`**: Randomly selects one of the allowed values.
*   **`const`**: Returns the exact constant value.
*   **`allOf`**: Merges properties from all sub-schemas.
*   **`anyOf` / `oneOf`**: Randomly selects one sub-schema to generate from.

### Safety Mechanisms

To prevent infinite recursion in circular schemas (e.g., a Person object containing a list of Friends, who are also People), the generator enforces a strict recursion depth limit (default: 10). When the limit is reached, it returns `None` or an empty container to terminate the branch safely.
