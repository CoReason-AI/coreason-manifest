# Mock Data Factory

The **Mock Data Factory** is a lightweight, pure-Python utility designed to generate deterministic, schema-compliant synthetic data for Agents. It enables offline development and testing for frontend applications and orchestrators without requiring live LLM execution.

## Usage

The primary entry point is `generate_mock_output`. It accepts an `AgentDefinition` and an optional `seed` for determinism.

```python
from coreason_manifest import generate_mock_output
from coreason_manifest import AgentDefinition, InterfaceDefinition

# Define an agent with an output schema
agent = AgentDefinition(
    id="weather-agent",
    name="WeatherBot",
    interface=InterfaceDefinition(
        outputs={
            "type": "object",
            "properties": {
                "temperature": {"type": "integer"},
                "condition": {"type": "string", "enum": ["Sunny", "Rainy"]},
                "location": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string"},
                        "zip": {"type": "string"}
                    }
                }
            }
        }
    )
)

# Generate mock data
mock_data = generate_mock_output(agent, seed=42)
print(mock_data)
# Output might look like:
# {
#   "temperature": 73,
#   "condition": "Sunny",
#   "location": {
#     "city": "XyZ123",
#     "zip": "AbCd"
#   }
# }
```

## Features

### Supported Schema Keywords

The generator supports a subset of JSON Schema relevant for synthetic data generation:

*   **Types:** `string`, `integer`, `number`, `boolean`, `array`, `object`, `null`.
*   **Nullable Types:** Supports `type: ["string", "null"]` (prefers the non-null type).
*   **Enums:** `enum: [...]` selects a random value from the list.
*   **Const:** `const: "value"` returns the exact value.
*   **Refs:** `$ref` resolution for local definitions (e.g., `#/$defs/MyModel`).
*   **Formats:**
    *   `date-time`: Generates an ISO 8601 timestamp (deterministic if seed provided).
    *   `uuid`: Generates a UUID string.

### Determinism

If a `seed` is provided, the output is guaranteed to be identical across runs. This is critical for:

*   **Snapshot Testing:** Ensuring UI components render consistently.
*   **Regression Testing:** Verifying logic against known "random" inputs.

### Safety

*   **Zero Dependencies:** Uses only Python standard library (`random`, `string`, `uuid`, `datetime`).
*   **Recursion Limit:** Includes a maximum recursion depth (default: 10) to prevent infinite loops from circular references in schemas.

## Limitations

*   Does not support complex validation keywords like `pattern`, `minimum`/`maximum` (generates generic random values).
*   `oneOf`, `anyOf`, `allOf` are not currently supported (fallbacks to default behavior or `None`).
*   Remote `$ref` resolution is not supported (only local `$defs` or `definitions`).
