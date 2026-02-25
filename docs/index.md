# Coreason Manifest

**The Immutable Shared Kernel of the CoReason Ecosystem**

## Introduction

`coreason-manifest` serves as the authoritative, passive Shared Kernel for the CoReason ecosystem. It provides the strict vocabulary, schema, and structural rules for defining cognitive agent workflows, reasoning graphs, and governance policies.

As a Shared Kernel, this package is intentionally designed to be a pure definition layer. It dictates the *structure* of a cognitive system—the nodes, the data flow, the tools, and the guardrails—without prescribing *how* that system is executed. This separation of concerns ensures that the blueprint of an agent remains portable, verifiable, and distinct from the runtime environment that powers it.

## The `CoreasonModel` Foundation

Every schema definition within `coreason-manifest` inherits from the foundational `CoreasonModel`, a specialized Pydantic model designed to enforce rigor and consistency across the ecosystem. This base class guarantees three critical properties for all manifest objects:

1.  **Strict Validation (`extra="forbid"`):** The schema allows no ambiguity. Any field not explicitly defined in the model is rejected, preventing silent errors and configuration drift.
2.  **Immutability (`frozen=True`):** Once instantiated, a manifest object cannot be altered. This immutability is essential for distributed state consistency, safe concurrency, and reliable auditing.
3.  **Deterministic Serialization:** The model overrides standard JSON dumping to ensure that keys are always sorted and output is consistent. This determinism allows for reliable cryptographic hashing, meaning that the same configuration will always yield the exact same hash, enabling precise versioning and integrity checks.

## Package Structure

The package is organized into two distinct namespaces to strictly separate data definitions from helper logic.

### `src/coreason_manifest/spec/`

This directory contains the pure, declarative data models. It is the heart of the Shared Kernel.
*   **Purpose:** Defines the canonical schema for Nodes, Flows, Tools, Governance, and Cognitive Engines.
*   **Constraint:** Code in this directory has **zero** external execution dependencies. It imports only standard libraries and Pydantic. It does not know about network requests, databases, or LLM providers.

### `src/coreason_manifest/utils/`

This directory provides the tooling necessary to work with the manifest, without executing it.
*   **Purpose:** Contains helper logic such as:
    *   **Visualizers:** Tools to render the DAG structure of a manifest.
    *   **Diffing:** Logic to semantically compare two versions of a manifest.
    *   **Validation:** Advanced integrity checks beyond basic schema validation.
    *   **I/O Loaders:** Utilities for safely reading and parsing manifest files.
*   **Constraint:** While this directory contains logic, it does **not** contain execution engines. It helps you *manage* the blueprint, but it does not *build* the building.
