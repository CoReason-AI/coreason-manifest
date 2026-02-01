# CoReasonBaseModel Rationale

## Introduction

In v0.10.0, we introduced `CoReasonBaseModel`, a custom base class inheriting from `pydantic.BaseModel`. This document explains the "why" behind this architectural decision, focusing on solving serialization challenges with Pydantic v2 and improving the developer experience.

## The Problem: JSON Serialization with Pydantic v2

Pydantic v2's default `model_dump()` behavior returns Python objects for complex types. While this is correct for Python-to-Python data exchange, it poses significant challenges when serializing to standard JSON:

1.  **UUIDs**: `uuid.UUID` objects are not JSON serializable by the standard `json` library.
2.  **Datetimes**: `datetime.datetime` objects are not JSON serializable.
3.  **Inconsistency**: Downstream consumers (like `coreason-validator` or the execution engine) often had to implement custom encoders or rely on Pydantic's `json_encoders` (which are deprecated in v2) to handle these types correctly.

This led to repetitive boilerplate code and potential errors where different parts of the system might serialize these objects differently (e.g., ISO format vs. epoch timestamp).

## The Solution: CoReasonBaseModel

`CoReasonBaseModel` serves as the single source of truth for serialization logic across the entire Coreason Manifest ecosystem. It encapsulates the optimal Pydantic configuration to ensure consistent, safe, and easy-to-use JSON serialization.

### Key Features

1.  **`dump()` Method**:
    *   **Purpose**: Returns a Python dictionary that is **guaranteed to be JSON-serializable**.
    *   **Implementation**: It calls `self.model_dump(mode='json', by_alias=True, exclude_none=True)`.
    *   **Benefit**: Consumers can pass the output of `.dump()` directly to `json.dumps()` or any other JSON-compliant API without worrying about `UUID` or `datetime` serialization errors.
    *   **DRY Principle**: The specific flags (`mode='json'`, `by_alias=True`, `exclude_none=True`) are defined once, preventing configuration drift across the codebase.

2.  **`to_json()` Method**:
    *   **Purpose**: Returns a JSON string representation of the model.
    *   **Implementation**: It calls `self.model_dump_json(by_alias=True, exclude_none=True)`.
    *   **Benefit**: Provides a quick, one-line way to get a valid JSON string for logging, storage, or HTTP responses.

### Consistency Across Artifacts

By having all "root" level artifacts inherit from `CoReasonBaseModel`, we ensure uniform behavior:

*   **`AgentDefinition`** (`src/coreason_manifest/definitions/agent.py`)
*   **`RecipeManifest`** (`src/coreason_manifest/recipes.py`)
*   **`GraphTopology`** (`src/coreason_manifest/definitions/topology.py`)
*   **`AuditLog`** (`src/coreason_manifest/definitions/audit.py`)

This consistency simplifies the mental model for developers working with different parts of the Coreason ecosystem. Whether you are validating an Agent or auditing a Graph execution, the serialization interface remains the same.

## Usage Example

```python
from coreason_manifest.definitions.agent import AgentDefinition

# Load an agent (assuming valid data)
agent = AgentDefinition(...)

# Get a JSON-safe dictionary (UUIDs and datetimes are strings)
safe_dict = agent.dump()
import json
print(json.dumps(safe_dict)) # Works perfectly

# Get a JSON string directly
json_str = agent.to_json()
print(json_str)
```
