# Coreason Manifest: The Blueprint

## System Instruction: Architecting coreason-manifest

**Role:** Lead Compliance Architect for the CoReason platform.
**Objective:** Architect and implement the `coreason-manifest` Python package.
**Philosophy:** "The Blueprint." This package is the definitive source of truth. If it isn't in the manifest, it doesn't exist. If it violates the manifest, it doesn't run.

## Overview

**Package Name:** `coreason-manifest` (The Blueprint)
**Mission:** The definitive source of truth for Asset definitions.

**Responsibilities:**
*   Defines strict Pydantic schemas for Open Agent Specifications (OAS).
*   Provides canonical hashing and versioning logic.
*   Acts as the shared kernel for all downstream services.

**Technology Stack (Standardization):**
*   **Schema:** JSON Schema (standard interchange format).
*   **Data Modeling:** Pydantic V2 (for Python-native interface).

## Agent Instructions

### 1. The "Borrow Over Build" Directive (Strict Constraints)
You are strictly forbidden from writing custom validation logic where a standard schema language exists.

*   **Schema Standard:** JSON Schema Draft 2020-12 (for structural validation).
*   **Data Modeling:** Pydantic V2 (for Python-native interface).

**Forbidden:**
*   Do NOT write custom if/else chains to validate agent configurations.
*   Do NOT invent a proprietary schema format; align with industry standards where possible.

### 2. Business Logic Specifications (The Source of Truth)
The package acts as the contract for the "Agent Development Lifecycle" (ADLC). It ensures that every "Agent" produced by the factory meets strict GxP and security standards.

#### 2.1 The Open Agent Specification (OAS)
You must define the strict schema for a CoReason Agent. A valid Agent Manifest (`agent.yaml`) contains:
*   **Metadata:** `id` (UUID), `version` (SemVer), `name`, `author`, `created_at`.
*   **Interface:**
    *   `inputs`: Typed arguments the agent accepts (JSON Schema).
    *   `outputs`: Typed structure of the result.
*   **Topology:**
    *   `steps`: A directed acyclic graph (DAG) of execution steps.
    *   `model_config`: Specific LLM parameters (model, temperature) — Must be locked per version.
*   **Dependencies:**
    *   `tools`: List of specific external tools (MCP capability URIs) required.
    *   `libraries`: List of Python packages required (if code execution is allowed).

#### 2.2 The Compliance Guardrails
The system must enforce "Clean Room" rules.
*   **Rule 1 (Dependency Pinning):** All library dependencies must have explicit version pins (e.g., `pandas==2.0.1`, not `pandas>=2.0`).
*   **Rule 2 (Allowlist Enforcement):** Libraries must be cross-referenced against a "Trusted Bill of Materials" (TBOM). If an agent requests `requests` but only `httpx` is approved, validation fails.
*   **Rule 3 (Integrity):** The manifest itself must include a SHA256 hash of the agent's source code to prevent tampering.

### 3. Package Architecture & Components
The package exposes pure Pydantic definitions.

#### Component: Shared Definitions
*   **Input:** JSON/YAML data.
*   **Responsibility:**
    *   Define strict Pydantic models.
    *   Provide `canonical_hash()` methods.
*   **Output:** Validated Python objects.

### 4. Definition of Done (The Output)
The agent must generate a Python package structure that allows the consuming middleware (`coreason-api`) and the CLI (`adk`) to write code like this:

```python
from coreason_manifest.definitions import AgentManifest

# Load & Validate
try:
    agent_def = AgentManifest.model_validate(data)
    print(f"Agent {agent_def.metadata.name} is compliant.")

except ValidationError as e:
    print(f"Validation Failure: {e}")
```
