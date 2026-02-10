# Documentation Audit Report

## 1. Executive Summary

This report outlines the discrepancies found between the `coreason-manifest` codebase (`src/`) and its documentation (`docs/`). The primary finding is a significant number of "orphaned" documentation files that describe critical V2 features but are not reachable via the `mkdocs.yml` navigation structure. Additionally, while the core `graph_recipes.md` documentation is generally accurate, it requires updates to strictly align with the latest Pydantic model definitions in `src/coreason_manifest/spec/v2/recipe.py`.

## 2. Orphaned Documentation Files

The following files exist in `docs/` but are missing from `mkdocs.yml`. These contain critical information about new V2 features:

1.  `docs/compliance_schema.md`
2.  `docs/council_features.md`
3.  `docs/episteme_reasoning.md`
4.  `docs/evaluator_optimizer.md`
5.  `docs/flow_governance.md`
6.  `docs/gateway_qos.md`
7.  `docs/generative_solvers.md`
8.  `docs/identity_access_management.md`
9.  `docs/knowledge_retrieval.md`
10. `docs/mcp_runtime.md`
11. `docs/model_routing.md`
12. `docs/provenance_metadata.md`
13. `docs/ux_collaboration.md`
14. `docs/v2_harvesting_features.md`
15. `docs/veritas_integrity.md`

## 3. Discrepancies in `graph_recipes.md` vs `src/coreason_manifest/spec/v2/recipe.py`

*   **`RecipeDefinition`**:
    *   The documentation correctly identifies high-level fields but needs to ensure `environment`, `compliance`, `identity`, and `guardrails` are prominently featured as first-class citizens, matching their definition in the Pydantic model.
    *   The `default_model_policy` field is present in code but might need more detailed explanation in the context of the `model_routing.md` link.

*   **`PolicyConfig`**:
    *   The code includes fields like `priority` (ExecutionPriority enum), `rate_limit_rpm`, `budget_cap_usd`, `sensitive_tools`, `allowed_mcp_servers`, `safety_preamble`, and `legal_disclaimer`. The documentation should be verified to include all these governance levers.

*   **`RecoveryConfig`**:
    *   The code defines `behavior` as `FailureBehavior` enum (`fail_workflow`, `continue_with_default`, `route_to_fallback`, `ignore`). The documentation should explicitly list these options to avoid ambiguity.

## 4. `mkdocs.yml` Structure

The current `mkdocs.yml` structure is disorganized, mixing V1 and V2 concepts and lacking a clear "Core Specifications" section for V2. It needs a complete overhaul to reflect the "Code is Source of Truth" doctrine and provide a logical developer journey.

## 5. Code Snippets

Several code snippets in `docs/` may still be using outdated import paths (e.g., `from coreason_manifest.spec import ...` instead of `from coreason_manifest.spec.v2 import ...`). A grep search is required to identify and fix these.
