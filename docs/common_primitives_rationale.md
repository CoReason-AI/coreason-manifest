# Common Primitives & Decoupling Strategy

## Introduction

As `coreason-manifest` evolves from its legacy V1 architecture to the new V2 **Coreason Orchestration Protocol (COP)**, we face the challenge of managing dependencies between these two distinct generations of code.

This document explains the architectural decision to introduce a neutral `common.py` module, which serves as a shared foundation for both V1 and V2, enabling the eventual deprecation of legacy code.

## The Problem: Circular & Legacy Dependencies

Initially, foundational primitives like `CoReasonBaseModel` (the base Pydantic class) and `ToolRiskLevel` (an Enum) were defined inside V1 modules:
*   `src/coreason_manifest/definitions/base.py`
*   `src/coreason_manifest/definitions/agent.py`

When we began building V2 (`src/coreason_manifest/v2/`), it needed these primitives to ensure type consistency and serialization behavior. Importing them directly from V1 created a hard dependency: **V2 depended on V1**.

This prevented us from:
1.  Isolating V2 for testing.
2.  Deprecating or deleting V1 code in the future without breaking V2.
3.  Maintaining a clean dependency graph (it created potential circular imports if V1 needed V2 features).

## The Solution: `src/coreason_manifest/common.py`

We extracted these shared primitives into a new, neutral module: `src/coreason_manifest/common.py`.

This module acts as a **Leaf Node** in the dependency tree. It has zero internal dependencies on other `coreason_manifest` modules.

### Shared Primitives

The following core components reside in `common.py`:

1.  **`CoReasonBaseModel`**: The base Pydantic model providing standardized JSON serialization (`dump()`, `to_json()`) for handling UUIDs and datetimes.
2.  **`StrictUri`**: A Pydantic type alias for strict URI validation and string serialization.
3.  **`ToolRiskLevel`**: An Enum defining the risk levels (`SAFE`, `STANDARD`, `CRITICAL`) for governance.

## Architecture

The dependency flow is now strictly unidirectional:

```
[V1 Legacy Code] ----> [common.py] <---- [V2 New Architecture]
```

*   **V1 (`definitions/`)**: Imports from `common.py` but **re-exports** the symbols to maintain backward compatibility for existing external consumers.
*   **V2 (`v2/`)**: Imports directly from `common.py`, bypassing V1 entirely.

## Backward Compatibility

To ensure this refactor was non-breaking for existing users, we maintained the original import paths in V1:

*   `coreason_manifest.definitions.base.CoReasonBaseModel` is now an import from `common.py`.
*   `coreason_manifest.definitions.agent.ToolRiskLevel` is now an import from `common.py`.

These modules include explicit `__all__` definitions to ensure static analysis tools (like `mypy`) treat these re-exports as public attributes.

## Future Roadmap

This structure allows us to eventually remove the `definitions/` directory (V1) entirely when the migration to V2 is complete, without requiring any changes to the V2 codebase.
