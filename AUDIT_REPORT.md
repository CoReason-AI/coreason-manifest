# Coreason Manifest Audit Report

**Date:** 2025-05-20
**Auditor:** Jules (Principal Data Architect)
**Scope:** `coreason-manifest` (v0.22.0)

## Executive Summary
This audit identifies three critical areas of "Logic Fragmentation" where business rules and structural patterns are duplicated across the codebase. Consolidating these into the Pydantic models and base classes will improve maintainability, reduce bugs, and enforce the "Single Source of Truth" principle.

## 1. The "Validator vs. Model" Violation

**Severity:** Critical
**Location:** `src/coreason_manifest/utils/v2/validator.py` vs `src/coreason_manifest/spec/v2/definitions.py`

### Evidence
The function `validate_integrity(manifest: ManifestV2)` in `validator.py` manually iterates over steps to verify:
1. `workflow.start` exists in steps.
2. `step.next` pointers exist in steps.
3. `SwitchStep.cases` targets exist.
4. `AgentStep.agent` references exist in definitions.

This logic is external to the `ManifestV2` model, meaning a `ManifestV2` instance can be instantiated in an invalid state (broken references) unless the validator is explicitly called.

### Proposed Fix
Move the validation logic directly into `ManifestV2` using a Pydantic `@model_validator(mode='after')`. This ensures that any `ManifestV2` object is guaranteed to be referentially intact upon creation.

```python
# src/coreason_manifest/spec/v2/definitions.py

@model_validator(mode="after")
def validate_integrity(self) -> Self:
    # 1. Validate Start Step
    if self.workflow.start not in self.workflow.steps:
        raise ValueError(f"Start step '{self.workflow.start}' not found in steps.")

    # ... (rest of logic)
    return self
```

## 2. The "Adapter Boilerplate" Violation

**Severity:** Major
**Location:** `src/coreason_manifest/utils/openai_adapter.py` vs `src/coreason_manifest/utils/langchain_adapter.py`

### Evidence
Both adapter modules share near-identical logic for:
1. constructing the system prompt from `role`, `goal`, and `backstory`.
2. Iterating over `agent.tools` to separate `InlineToolDefinition` (local) from `ToolRequirement` (remote).
3. Handling defaults (e.g., model name).

This duplication increases the risk of drift if the prompt construction strategy changes (e.g., adding a new field like `skills`).

### Proposed Fix
Introduce a `BaseManifestAdapter` class in `src/coreason_manifest/utils/base_adapter.py` that encapsulates the common traversal and prompt generation logic.

```python
# src/coreason_manifest/utils/base_adapter.py

class BaseManifestAdapter:
    def _build_system_prompt(self, agent: AgentDefinition) -> str:
        parts = [f"Role: {agent.role}", f"Goal: {agent.goal}"]
        if agent.backstory:
            parts.append(f"Backstory: {agent.backstory}")
        return "\n\n".join(parts)
```

## 3. The "Test Data Sprawl" Violation

**Severity:** Moderate
**Location:** `tests/test_v2_*.py` (e.g., `test_v2_agent_def.py`, `test_v2_complex_scenarios.py`)

### Evidence
Multiple test files define their own raw dictionary literals or verbose constructor calls to create `ManifestV2` and `AgentDefinition` objects. This makes tests brittle to schema changes (e.g., adding a required field) and violates DRY.

### Proposed Fix
Implement a centralized `tests/factories.py` module containing helper functions (factories) to generate valid default objects.

```python
# tests/factories.py

def create_agent_definition(id="agent-1", name="Test Agent", **kwargs) -> AgentDefinition:
    defaults = {
        "type": "agent",
        "role": "Tester",
        "goal": "Test things",
        # ...
    }
    defaults.update(kwargs)
    return AgentDefinition(**defaults)
```
