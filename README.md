# coreason-manifest

> The definitive source of truth for Asset definitions.

[![License: Prosperity 3.0](https://img.shields.io/badge/License-Prosperity%203.0-blue)](https://github.com/CoReason-AI/coreason_manifest/blob/main/LICENSE)
[![Build Status](https://github.com/CoReason-AI/coreason_manifest/actions/workflows/ci.yml/badge.svg)](https://github.com/CoReason-AI/coreason_manifest/actions)
[![Code Style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**coreason-manifest** ("The Blueprint") is the core compliance and validation engine for the CoReason platform. It enforces strict architectural and security standards for Agent specifications, ensuring that every asset produced meets GxP and security protocols before execution.

## Features

*   **Open Agent Specification (OAS):** Defines a strict, schema-driven contract for Agents (Metadata, Interface, Topology, Dependencies).
*   **Compliance Guardrails:**
    *   **Dependency Pinning:** Enforces explicit versioning for all libraries.
    *   **Allowlist Enforcement:** Validates libraries against a "Trusted Bill of Materials" (TBOM).
    *   **Integrity Checks:** Verifies source code SHA256 hashes against the manifest signature.
*   **Policy as Code:** Leverages Open Policy Agent (OPA) and Rego for complex, logic-based compliance rules.
*   **Standardized Validation:** Uses JSON Schema Draft 2020-12 and Pydantic V2 for robust data modeling.

## Installation

```bash
pip install coreason-manifest
```

## Usage

```python
from coreason_manifest import ManifestEngine, ManifestConfig, PolicyViolationError

# 1. Initialize the engine with compliance policies
config = ManifestConfig(
    policy_path="./policies/gx_compliant.rego",
    opa_path="opa"  # Ensure OPA is installed and in PATH
)
engine = ManifestEngine(config)

# 2. Load, Validate, and Verify an Agent
try:
    agent_def = engine.load_and_validate(
        manifest_path="./agents/payer_war_game/agent.yaml",
        source_dir="./agents/payer_war_game/src"
    )
    print(f"Agent {agent_def.metadata.name} (v{agent_def.metadata.version}) is compliant.")

except PolicyViolationError as e:
    print(f"Compliance Failure: {e.violations}")

except Exception as e:
    print(f"Validation Error: {e}")
```

## License

This project is licensed under the **Prosperity Public License 3.0**. See the [LICENSE](LICENSE) file for details.
