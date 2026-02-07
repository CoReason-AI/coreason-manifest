# ADR 001: Strict Separation of Shared Kernel and Utilities

## Context
The `coreason_manifest` library serves as the "Shared Kernel" for the Coreason ecosystem. A concern was raised that bundling logic (Governance, Visualization, Audit) with the kernel creates a "Distributed Monolith", forcing services (like the Engine) to redeploy for unrelated changes (like Visualization bug fixes).

## Decision
We will maintain the physical co-location of `spec` (DTOs) and `utils` (Logic) in the same Python package for developer ergonomics and semantic consistency, **BUT** we strictly enforce an architectural boundary:

**The Core Specification (`spec`) MUST NOT depend on the Utilities (`utils`).**

## Rationale
1.  **Pure Data Kernel**: The `spec` package defines the language. It is pure data (Pydantic models). It has minimal dependencies.
2.  **Optional Batteries**: The `utils` package provides "Reference Implementations" and "Standard Tools". Consumers (like the Engine) that only need the *language* can import `coreason_manifest.spec` without being logically coupled to the implementation of the visualization or governance logic.
3.  **One-Way Dependency**: By enforcing `utils -> spec` (and forbidding `spec -> utils`), we ensure that changes in `utils` do not pollute the ABI or stability of `spec`.
4.  **Version Stability**: While the package version bumps for any change, the *stability* of the `spec` module is guaranteed by the one-way dependency. A change in `viz.py` does not alter the `AgentDefinition` class.

## Enforcement
A regression test (`tests/test_architecture.py`) has been added to the CI pipeline. It scans all modules in `coreason_manifest.spec` and asserts that none of them import `coreason_manifest.utils`.

## Consequences
*   **Positive**: Consumers can trust that importing `ManifestV2` does not drag in heavy logic or side effects.
*   **Positive**: The project remains easy to install (`pip install coreason-manifest`).
*   **Negative**: A new release of the package is still required for utility fixes, which technically triggers a dependency update for consumers, even if they don't use the affected utility. This is accepted as a trade-off for simplicity over managing multi-package release trains (`coreason-spec`, `coreason-viz`, etc.) at this stage.
