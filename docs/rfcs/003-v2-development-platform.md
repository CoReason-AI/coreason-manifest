# RFC 003: V2 Development Platform - Validation, Governance, and Tooling

## 1. Executive Summary

### The Challenge
Coreason Manifest V2 (RFC 001) introduced a Human-Centric YAML format. However, simply "loading" YAML isn't enough for a robust Development Platform. We identified three critical gaps:
1.  **Draft State:** Users often save "work in progress" (WIP) manifests. The compiler previously crashed on incomplete graphs (e.g., missing steps).
2.  **External Tooling:** V2 lacked a strict schema for defining external tools (MCP), relying on loose dictionaries.
3.  **Governance:** Enterprise policies (e.g., "No Critical Tools allowed") were difficult to enforce on the YAML source before compilation.

### The Solution: Phase 3 "Development Platform"
We introduce a layered validation architecture that treats the Manifest as a living document with lifecycle states: **Draft** and **Compiled**.

---

## 2. Dual-Mode Validation Architecture

The system now supports two distinct validation modes, allowing the Editor (Drafts) and the Runtime (Compiler) to coexist peacefully.

### 2.1 Loose Mode (Drafts)
*   **Purpose:** Used by the Visual Builder / Editor when saving WIP.
*   **Behavior:** Checks for structural sanity (syntax, unique IDs) but **ignores** referential integrity errors (dangling pointers).
*   **Result:** A list of `warnings`. The user can save a broken graph.

```python
warnings = validate_loose(manifest)
# ["Step 'A' points to non-existent step 'B'"] -> Non-blocking
```

### 2.2 Strict Mode (Compilation)
*   **Purpose:** Used when deploying or running the agent.
*   **Behavior:** Enforces full referential integrity. All `next` pointers, `switch` cases, and `agent` references must exist.
*   **Result:** Raises `ValueError` if any error is found.

---

## 3. Strict Tool Definitions

We have formalized the `definitions` block to support strongly-typed Tool definitions alongside Agents.

### Schema: `ToolDefinition`
*   **`id`**: Unique identifier.
*   **`name`**: Human-readable name.
*   **`uri`**: Strict URI (e.g., `mcp://...` or `https://...`).
*   **`risk_level`**: `SAFE`, `STANDARD`, or `CRITICAL`.
*   **`description`**: Optional details.

### Example YAML
```yaml
definitions:
  # Strictly Validated Tool
  calculator:
    id: "tool-calc"
    name: "Calculator"
    uri: "https://api.calc.com/v1"
    risk_level: "safe"

workflow:
  start: "step1"
  steps: ...
```

The Compiler (`compile_dependencies`) now automatically extracts these definitions and converts them into the V1 `AgentDependencies` structure (`ToolRequirement`) for the runtime.

---

## 4. Governance & Policy Enforcement

We introduce **Static Analysis for Governance** (`check_compliance_v2`). This runs on the YAML *before* it is compiled or executed, acting as a "Gatekeeper."

### Capabilities
1.  **Risk Level Caps:** Prevent usage of `CRITICAL` tools if the environment only allows `STANDARD`.
2.  **Domain Whitelisting:** Enforce that all Tool URIs belong to trusted domains (e.g., `*.coreason.ai`).
3.  **Logic Restrictions:** Flag `LogicStep` or complex `SwitchStep` conditions if "Custom Logic" is forbidden by policy (e.g., for non-technical users).

### Usage
```python
config = GovernanceConfig(
    max_risk_level=ToolRiskLevel.STANDARD,
    allowed_domains=["internal.corp"],
    allow_custom_logic=False
)

report = check_compliance_v2(manifest, config)
if not report.passed:
    print(report.violations)
```

---

## 5. Integration

*   **Compiler:** Automatically calls `validate_strict`. Fails fast if the graph is invalid.
*   **Bridge:** The `v2_to_recipe` adapter seamlessly translates V2 Tools into V1 Requirements, ensuring backward compatibility with the existing Engine.
