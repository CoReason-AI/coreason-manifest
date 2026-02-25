# Refactor Plan

## Phase 1: Unify Flow Topology Handling (DRY & OCP)
**Goal:** Abstract away the difference between `LinearFlow` and `GraphFlow` topology access.

**Files to Change:**
1.  `src/coreason_manifest/utils/topology.py`:
    -   Implement `get_unified_topology(flow: LinearFlow | GraphFlow) -> tuple[list[AnyNode], list[Edge]]`.
    -   For `LinearFlow`, generate implicit edges between sequential steps.
    -   For `GraphFlow`, return `graph.nodes.values()` and `graph.edges`.
2.  `src/coreason_manifest/utils/visualizer.py`:
    -   Refactor `to_mermaid` to use `get_unified_topology`.
    -   Refactor `to_react_flow` to use `get_unified_topology`.
3.  `src/coreason_manifest/utils/validator.py`:
    -   Refactor `_build_unified_adjacency_map` to use `get_unified_topology` (or verify if it's redundant).
    -   Refactor `validate_flow` to use `get_unified_topology` for node access.
4.  `src/coreason_manifest/utils/gatekeeper.py`:
    -   Refactor `_get_capabilities`, `validate_policy`, `_is_guarded` to use `get_unified_topology`.
5.  `src/coreason_manifest/utils/langchain_adapter.py`:
    -   Refactor `flow_to_langchain_config`.

## Phase 2: Centralize Semantic Validation
**Goal:** Enforce "Shared Kernel" rule: Pydantic models = Structure, Utils = Semantics.

**Files to Change:**
1.  `src/coreason_manifest/spec/core/flow.py`:
    -   Remove `@model_validator` methods from `GraphFlow`:
        -   `validate_topology`
        -   `validate_swarm_variables`
        -   `enforce_global_kill_switch`
        -   `validate_middleware_refs`
    -   Remove `@model_validator` methods from `LinearFlow`:
        -   `validate_resilience_references`
        -   `enforce_global_kill_switch`
        -   `validate_middleware_refs`
    -   Remove helper functions `_scan_for_kill_switch_violations` and `_validate_middleware_references`.
2.  `src/coreason_manifest/utils/validator.py`:
    -   Add logic for resilience reference validation (for both Flow types).
    -   Add logic for entry point validation (GraphFlow).
    -   Add logic for fallback orphans (GraphFlow).
    -   Add logic for swarm variables validation.
    -   Add logic for global kill switch enforcement.
    -   Add logic for middleware reference validation.
    -   Update `validate_flow` to call these new validation steps.

## Phase 3: Fix Sandboxing Concurrency Vulnerability
**Goal:** Remove `sys.modules` modification to prevent race conditions.

**Files to Change:**
1.  `src/coreason_manifest/utils/loader.py`:
    -   Identify functions modifying `sys.modules` (e.g., `load_agent_from_ref`, `_compile_module`).
    -   Refactor to use `exec()` with a dedicated `local_namespace` dict.
    -   Ensure that type checks (e.g. `isinstance(obj, MyClass)`) still work correctly (might need to inject base classes into globals).
    -   Remove `sys.modules` manipulation code.

## Phase 4: Structured Validation Errors
**Goal:** Return structured objects instead of strings for validation errors.

**Files to Change:**
1.  `src/coreason_manifest/utils/validator.py`:
    -   Import `ComplianceReport` or define a new `ValidationFault` model.
    -   Refactor `validate_flow` and all helper functions to return list of these objects.
    -   Replace string formatting with structured data (code, message, context).
2.  `tests/`:
    -   Update tests to assert on error codes/types instead of string matching.

## Phase 5: Builder Pattern Boilerplate (DRY)
**Goal:** Deduplicate `.build()` logic in builders.

**Files to Change:**
1.  `src/coreason_manifest/builder.py`:
    -   Update `BaseFlowBuilder`:
        -   Add abstract method `_create_flow_instance()`.
        -   Implement `build()`:
            -   Call `_create_flow_instance()`.
            -   Call `validate_flow()` (from utils).
            -   Return flow.
    -   Update `NewLinearFlow`:
        -   Implement `_create_flow_instance`.
        -   Remove `build`.
    -   Update `NewGraphFlow`:
        -   Implement `_create_flow_instance`.
        -   Remove `build`.

## Phase 6: Test Suite Boilerplate (DRY)
**Goal:** Centralize test fixtures.

**Files to Change:**
1.  `tests/conftest.py`:
    -   Move common helper functions from test files here as fixtures (e.g., `create_dummy_node`, `create_basic_flow`).
2.  `tests/*.py`:
    -   Refactor tests to use the new fixtures.
