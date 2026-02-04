# CoReasonBaseModel Rationale

## Introduction

We introduced `CoReasonBaseModel`, a custom base class inheriting from `pydantic.BaseModel`. This document explains the "why" behind this architectural decision, focusing on solving serialization challenges with Pydantic and improving the developer experience.

## The Problem: JSON Serialization with Pydantic

Pydantic's default `model_dump()` behavior returns Python objects for complex types. While this is correct for Python-to-Python data exchange, it poses significant challenges when serializing to standard JSON:

1.  **UUIDs**: `uuid.UUID` objects are not JSON serializable by the standard `json` library.
2.  **Datetimes**: `datetime.datetime` objects are not JSON serializable.
3.  **Inconsistency**: Downstream consumers often had to implement custom encoders or rely on deprecated `json_encoders` to handle these types correctly.

This led to repetitive boilerplate code and potential errors where different parts of the system might serialize these objects differently (e.g., ISO format vs. epoch timestamp).

## The Solution: CoReasonBaseModel

`CoReasonBaseModel` serves as a source of truth for serialization logic for specific parts of the Coreason Manifest ecosystem. It encapsulates the optimal Pydantic configuration to ensure consistent, safe, and easy-to-use JSON serialization.

### Key Features

1.  **`dump()` Method**:
    *   **Purpose**: Returns a Python dictionary that is **guaranteed to be JSON-serializable**.
    *   **Implementation**: It calls `self.model_dump(mode='json', by_alias=True, exclude_none=True)`.
    *   **Benefit**: Consumers can pass the output of `.dump()` directly to `json.dumps()` or any other JSON-compliant API without worrying about `UUID` or `datetime` serialization errors.
    *   **DRY Principle**: The specific flags (`mode='json'`, `by_alias=True`, `exclude_none=True`) are defined once, preventing configuration drift.

2.  **`to_json()` Method**:
    *   **Purpose**: Returns a JSON string representation of the model.
    *   **Implementation**: It calls `self.model_dump_json(by_alias=True, exclude_none=True)`.
    *   **Benefit**: Provides a quick, one-line way to get a valid JSON string for logging, storage, or HTTP responses.

### Usage in the Ecosystem

While core definitions like `AgentDefinition`, `Recipe`, and `Workflow` inherit directly from `pydantic.BaseModel` to maintain standard Pydantic behavior for maximal compatibility with external tools, shared configuration models used for governance and reporting utilize `CoReasonBaseModel` for its enhanced serialization capabilities.

*   **`GovernanceConfig`**
*   **`ComplianceViolation`**
*   **`ComplianceReport`**

## Usage Example

```python
from coreason_manifest.governance import GovernanceConfig, ToolRiskLevel
import json

# Create a governance config
config = GovernanceConfig(
    max_risk_level=ToolRiskLevel.SAFE,
    strict_url_validation=True
)

# Get a JSON-safe dictionary (enums are strings)
safe_dict = config.dump()
print(json.dumps(safe_dict)) # Works perfectly

# Get a JSON string directly
json_str = config.to_json()
print(json_str)
```
