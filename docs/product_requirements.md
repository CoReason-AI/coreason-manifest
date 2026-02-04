# Coreason Manifest: The Blueprint

## System Instruction: Architecting coreason-manifest

**Role:** Lead Compliance Architect for the CoReason platform.
**Objective:** Architect and implement the `coreason-manifest` Python package (Shared Kernel).
**Philosophy:** "The Blueprint." This package is the definitive source of truth. If it isn't in the manifest, it doesn't exist. If it violates the manifest, it doesn't run.

## Overview

**Package Name:** `coreason-manifest` (The Blueprint)
**Mission:** The definitive source of truth for Asset definitions and Schemas.

**Responsibilities (Shared Kernel):**
*   **Defines** the Coreason Agent Manifest (CAM) and strict Pydantic models.
*   **Provides** the data structures required for compliance enforcement and integrity verification.
*   **Ensures** strict typing and consistent serialization across the ecosystem.

### Standards Clarification
*Note: The "Coreason Agent Manifest" (CAM) is a proprietary, strict governance schema designed for the CoReason Platform. It is distinct from the Oracle/Linux Foundation "Open Agent Specification," though we aim for future interoperability via adapters.*

**Note:** Active policy enforcement (e.g., OPA Rego checks) and artifact integrity verification (hashing source files) are performed by consumer services (e.g., Builder, Engine) *using* the schemas defined in this package.

**Technology Stack (Standardization):**
*   **Schema:** JSON Schema (standard interchange format).
*   **Data Modeling:** Pydantic V2 (for Python-native interface).
*   **Policy Compatibility:** Structures designed to be validated by Open Policy Agent (OPA).

## Agent Instructions

### 1. The "Shared Kernel" Directive
You are strictly forbidden from embedding execution logic or side effects within this library. It must remain a pure data library.

*   **Schema Standard:** JSON Schema Draft 2020-12 (for structural validation).
*   **Data Modeling:** Pydantic V2 (for Python-native interface).

**Forbidden:**
*   Do NOT include execution engines (HTTP servers, runners).
*   Do NOT hardcode specific compliance rules in Python; define the *structure* to hold them.

### 2. Business Logic Specifications (The Source of Truth)
The package acts as the validator for the "Agent Development Lifecycle" (ADLC). It ensures that every "Agent" produced by the factory meets strict GxP and security standards.

#### 2.1 The Coreason Agent Manifest (CAM)
You must define the strict schema for a CoReason Agent. A valid Agent Definition (`AgentDefinition`) contains:
*   **Identity:** `id`, `name`.
*   **Persona:** `role`, `goal`, `backstory`.
*   **Capabilities:**
    *   `tools`: List of specific external tool IDs (referencing definitions).
    *   `knowledge`: List of knowledge base references.
*   **Model:** `model` (LLM identifier).

A valid Recipe/Manifest (`ManifestV2`) contains:
*   **Metadata:** `metadata` (name, design info).
*   **Interface:** `inputs` and `outputs` schemas.
*   **Workflow:**
    *   `start`: Entry point step ID.
    *   `steps`: A collection of execution units (`AgentStep`, `LogicStep`, `SwitchStep`, `CouncilStep`).
*   **Definitions:** Dictionary of reusable components (`AgentDefinition`, `ToolDefinition`).
*   **Policy:** Governance rules (`PolicyDefinition`).
*   **State:** Shared memory schema (`StateDefinition`).

#### 2.2 The Compliance Guardrails (Schema Support)
The system must support "Clean Room" rules via data structures.
*   **Rule 1 (Referential Integrity):** The Manifest must validate that all step transitions and definition references are valid.
*   **Rule 2 (Allowlist Enforcement):** The schema must expose dependencies clearly for external validation.
*   **Rule 3 (Type Safety):** All fields must be strictly typed using Pydantic.

### 3. Package Architecture & Components
The package exposes Pydantic models that validate data structure and format synchronously.

#### Component A: Definitions (The Models)
*   **Input:** Dictionary or JSON.
*   **Responsibility:**
    *   Validate structure against Pydantic models (`AgentDefinition`, `ManifestV2`).
    *   **Normalization:** Ensure IDs and references are valid.
*   **Output:** Validated object or `ValidationError`.

### 4. Definition of Done (The Output)
The agent must generate a Python package structure that allows the consuming middleware (`coreason-api`) and the CLI (`adk`) to write code exactly like this:

```python
from coreason_manifest import AgentDefinition
import yaml

# 1. Load Raw Data
# (Assuming raw_data is loaded from a YAML file)
raw_data = {
    "type": "agent",
    "id": "researcher",
    "name": "Researcher",
    "role": "Senior Researcher",
    "goal": "Find accurate information",
    "model": "gpt-4"
}

# 2. Validate Structure
try:
    agent = AgentDefinition(**raw_data)
    print(f"Agent {agent.name} is structurally valid.")

    # Further compliance checks (OPA, Integrity) would be performed
    # by the consuming application using this 'agent' object.

except Exception as e:
    print(f"Validation Failure: {e}")
```
