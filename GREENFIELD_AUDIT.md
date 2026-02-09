# Greenfield Protocol Audit: Legacy Artifacts

**Date:** 2025-05-20
**Target:** `coreason-manifest` v1.0.0
**Context:** Strict, breaking-change-heavy refactor for a clean release. No backward compatibility requirements.

## 1. The Migration Module (`src/coreason_manifest/utils/migration.py`)

*   **Artifact:** `src/coreason_manifest/utils/migration.py` (and usage in `__init__.py`).
*   **Why it is Legacy:**
    *   This module implements `migrate_graph_event_to_cloud_event`, which converts an internal `GraphEvent` structure to a `CloudEvent` format.
    *   The prompt states: "If this is a brand new release with no legacy clients... all of that is dead weight."
    *   Since we are assuming a Greenfield scenario, the internal event structure should *already be* the desired output structure (CloudEvent), or the system should emit CloudEvents directly without a translation layer for "old" formats.
*   **Greenfield Recommendation:**
    *   **Delete** the entire module `src/coreason_manifest/utils/migration.py`.
    *   Remove `migrate_graph_event_to_cloud_event` from `src/coreason_manifest/__init__.py`.
    *   Ensure the core runtime emits `CloudEvent` objects natively if that is the required format, rather than converting from an intermediate `GraphEvent`.

## 2. The Shortcuts Module (`src/coreason_manifest/shortcuts.py`)

*   **Artifact:** `src/coreason_manifest/shortcuts.py`.
*   **Why it is Legacy:**
    *   Contains `simple_agent`, a helper function that wraps `AgentBuilder`.
    *   The prompt asks: "Are these functions actual productivity boosters, or are they just 'Legacy Names' for new functions?"
    *   While it acts as a helper, it introduces ambiguity (guessing if inputs are schema or properties) and hides the explicit `AgentBuilder` API. In a strict v1.0.0, we want users to use the canonical Builder pattern directly to ensure clarity and type safety.
*   **Greenfield Recommendation:**
    *   **Delete** `src/coreason_manifest/shortcuts.py`.
    *   Remove `simple_agent` from `src/coreason_manifest/__init__.py`.
    *   Direct users to use `AgentBuilder` for all agent construction needs.

## 3. Deprecated Validator (`src/coreason_manifest/utils/v2/validator.py`)

*   **Artifact:** `src/coreason_manifest/utils/v2/validator.py`.
*   **Why it is Legacy:**
    *   The file contains `validate_integrity` which is explicitly marked as `DEPRECATED: ManifestV2 now self-validates on instantiation.` in its docstring.
    *   It also contains `validate_loose`, which performs checks that should be (and largely are) covered by Pydantic validators on the models themselves.
    *   Keeping a deprecated external validator confuses the API surface.
*   **Greenfield Recommendation:**
    *   **Delete** `src/coreason_manifest/utils/v2/validator.py`.
    *   Remove imports from `src/coreason_manifest/__init__.py`.
    *   Rely entirely on Pydantic's `model_validator` methods within `ManifestV2` and `RecipeDefinition` for integrity checks.

## 4. Legacy Field Aliases

*   **Artifacts:**
    *   `src/coreason_manifest/spec/v2/agent.py`: `memory_read` field aliased as `memory`, with a `@property def memory(self)` shim.
    *   `src/coreason_manifest/spec/v2/contracts.py`: `schema_` field aliased as `schema`.
    *   `src/coreason_manifest/spec/v2/definitions.py` (and others): `design_metadata` aliased as `x-design`.
*   **Why it is Legacy:**
    *   `alias="memory"` and the property shim exist solely to support code accessing `.memory` instead of `.memory_read`.
    *   `alias="schema"` maps a Python attribute to a JSON key that conflicts with Pydantic internal names or legacy formats.
    *   `alias="x-design"` supports the OpenAPI "vendor extension" pattern, which may not be necessary if we control the full spec.
    *   Aliases add complexity to serialization/deserialization and confuse the developer experience (attribute name vs. constructor argument).
*   **Greenfield Recommendation:**
    *   **Remove all aliases.**
    *   Rename `schema_` to `memory_schema` (or similar) in both Python and JSON.
    *   Rename `memory_read` to `knowledge_sources` or keep `memory_read` and enforce it in JSON.
    *   Use `design_metadata` in JSON directly.
    *   Enforce a strict 1:1 mapping between Python attributes and JSON keys (snake_case preferred).

## 5. Input Normalization Logic ("Magic Coercion")

*   **Artifacts:**
    *   `src/coreason_manifest/spec/v2/definitions.py`: `AgentDefinition.normalize_tools` validator.
    *   `src/coreason_manifest/spec/v2/recipe.py`: `coerce_topology` validator.
*   **Why it is Legacy:**
    *   `normalize_tools` accepts strings in a list where objects are expected, converting them to `{"type": "remote", "uri": ...}`. This supports "lazy" or "old" input formats.
    *   `coerce_topology` accepts a list of steps (linear sequence) and converts it to a `GraphTopology` object. While convenient, it violates strict typing and schema validation principles for a "Greenfield" core library.
    *   These "magic" conversions hide the actual structure of the data and make validation more complex.
*   **Greenfield Recommendation:**
    *   **Remove** `normalize_tools` and `coerce_topology`.
    *   Require `tools` to be a list of explicit `ToolRequirement` or `InlineToolDefinition` objects.
    *   Require `topology` to be a strict `GraphTopology` object (or matching dict).
    *   If "sugar" is needed, provide it via a separate factory or builder (like `AgentBuilder`), not implicitly in the data model.
