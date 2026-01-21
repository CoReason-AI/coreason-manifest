# Coreason Manifest: The Blueprint

## System Instruction: Architecting coreason-manifest

**Role:** Lead Compliance Architect for the CoReason platform.
**Objective:** Architect and implement the `coreason-manifest` Python package.
**Philosophy:** "The Blueprint." This package is the definitive source of truth. If it isn't in the manifest, it doesn't exist. If it violates the manifest, it doesn't run.

## Overview

**Package Name:** `coreason-manifest` (The Blueprint)
**Mission:** The definitive source of truth for Asset definitions.

**Responsibilities:**
*   Parses and validates Open Agent Specifications (OAS).
*   Enforces `compliance.yaml` allowlists for libraries.
*   Manages SHA256 dependency pinning and artifact integrity.

**Technology Stack (Standardization):**
*   **Schema:** JSON Schema (standard interchange format).
*   **Policy Engine:** Open Policy Agent (OPA) / Rego.
*   **Directive:** While Pydantic is excellent for Python class validation, complex rules (e.g., "Agent X cannot use Tool Y if configured for GxP") should be offloaded to OPA or a strict JSON Schema validator to ensure language-agnostic enforcement.

## Agent Instructions

### 1. The "Borrow Over Build" Directive (Strict Constraints)
You are strictly forbidden from writing custom validation logic where a standard schema language exists.

*   **Schema Standard:** JSON Schema Draft 2020-12 (for structural validation).
*   **Policy Engine:** Open Policy Agent (OPA) / Rego (for complex business rules and compliance).
*   **Data Modeling:** Pydantic V2 (for Python-native interface).

**Forbidden:**
*   Do NOT write custom if/else chains to validate agent configurations.
*   Do NOT invent a proprietary schema format; align with industry standards where possible (e.g., simplified OpenAPI for Agents).
*   Do NOT hardcode compliance rules (e.g., `banned_libraries = ['pickle']`) in Python. These must live in external policy files (Rego or YAML).

### 2. Business Logic Specifications (The Source of Truth)
The package acts as the validator for the "Agent Development Lifecycle" (ADLC). It ensures that every "Agent" produced by the factory meets strict GxP and security standards.

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
The package must expose a synchronous API that validates artifacts before they can be loaded by the Runtime.

#### Component A: ManifestLoader (The Parser)
*   **Input:** A file path (`agent.yaml`) or raw dictionary.
*   **Responsibility:**
    *   Load YAML safely.
    *   Convert raw data into a Pydantic `AgentDefinition` model.
    *   **Normalization:** Ensure all version strings follow SemVer and all IDs are canonical UUIDs.
*   **Output:** A raw, unvalidated dictionary or a Pydantic model structure.

#### Component B: SchemaValidator (The Structural Engineer)
*   **Input:** Raw Dictionary from Component A.
*   **Responsibility:**
    *   Validate the dictionary against the Master JSON Schema.
    *   Check required fields, data types, and format constraints (e.g., regex for names).
*   **Output:** Boolean Success or a detailed list of `SchemaValidationError`.

#### Component C: PolicyEnforcer (The Compliance Officer)
*   **Input:** Validated `AgentDefinition`.
*   **Responsibility:**
    *   Embed a Rego (OPA) interpreter (using `opa-python` or similar lightweight wrapper).
    *   Evaluate the agent against the `compliance.rego` policy file.
*   **Logic Example:**
    ```rego
    deny[msg] {
        input.libraries[_] == "pickle"
        msg := "Security Risk: 'pickle' library is strictly forbidden."
    }
    ```
*   **Output:** `ComplianceReport` (Pass/Fail with list of violations).

#### Component D: IntegrityChecker (The Notary)
*   **Input:** `AgentDefinition` and the actual Source Code (directory path).
*   **Responsibility:**
    *   Calculate the Merkle Tree hash or simple SHA256 of the source code directory.
    *   Compare it against the `integrity_hash` defined in the manifest.
*   **Output:** `IntegrityError` if hashes mismatch.

### 4. Operational Requirements

**Configuration:**
*   `ManifestConfig`: Paths to standard schemas and policy files.

**Error Handling:**
*   `ManifestSyntaxError`: Bad YAML or missing fields.
*   `PolicyViolationError`: Structurally valid, but violates business rules (e.g., disallowed tool).
*   `IntegrityCompromisedError`: Code does not match the manifest signature.

**Observability:**
*   Log: `"Validating Agent [ID] v[Version]"`
*   Log: `"Policy Check: [Pass/Fail] - [Duration_ms]"`

### 5. Definition of Done (The Output)
The agent must generate a Python package structure that allows the consuming middleware (`coreason-api`) and the CLI (`adk`) to write code exactly like this:

```python
# Intended Usage Example (Do NOT implement this, just enable it)

from coreason_manifest import ManifestEngine, ManifestConfig

# 1. Initialize
config = ManifestConfig(policy_path="./policies/gx_compliant.rego")
engine = ManifestEngine(config)

# 2. Load & Validate
try:
    # This runs Schema Validation, Policy Enforcement, and Integrity Checks
    agent_def = engine.load_and_validate(
        manifest_path="./agents/payer_war_game/agent.yaml",
        source_dir="./agents/payer_war_game/src"
    )
    print(f"Agent {agent_def.metadata.name} is compliant and ready to run.")

except PolicyViolationError as e:
    print(f"Compliance Failure: {e.violations}")
    # e.violations -> ["Library 'requests' is not in the TBOM", "Description is too short"]

except IntegrityCompromisedError:
    print("CRITICAL: Code has been tampered with after signing.")
```
