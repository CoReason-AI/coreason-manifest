# Coreason Manifest

The definitive source of truth for CoReason-AI Asset definitions. "The Blueprint."

[![License: Prosperity 3.0](https://img.shields.io/badge/license-Prosperity%203.0-blue)](https://github.com/CoReason-AI/coreason-manifest)
[![Build Status](https://github.com/CoReason-AI/coreason-manifest/actions/workflows/ci.yml/badge.svg)](https://github.com/CoReason-AI/coreason-manifest/actions)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Documentation](https://img.shields.io/badge/docs-product_requirements-informational)](docs/product_requirements.md)

## Overview

`coreason-manifest` acts as the validator for the "Agent Development Lifecycle" (ADLC). It ensures that every Agent produced meets strict GxP and security standards. If it isn't in the manifest, it doesn't exist. If it violates the manifest, it doesn't run.

## Features

*   **Open Agent Specification (OAS) Validation:** Parses and validates agent definitions against a strict schema.
*   **Compliance Enforcement:** Uses Open Policy Agent (OPA) / Rego to enforce complex business rules and allowlists.
*   **Integrity Verification:** Calculates and verifies SHA256 hashes of the agent's source code to prevent tampering.
*   **Dependency Pinning:** Enforces strict version pinning for all library dependencies.
*   **Trusted Bill of Materials (TBOM):** Validates libraries against an approved list.

## Installation

```bash
pip install coreason-manifest
```

## Usage

Here is how to initialize the engine and validate an agent manifest:

```python
from coreason_manifest import ManifestEngine, ManifestConfig, PolicyViolationError, IntegrityCompromisedError

# 1. Initialize configuration with policy path
config = ManifestConfig(policy_path="./policies/gx_compliant.rego")
engine = ManifestEngine(config)

# 2. Load & Validate Agent Manifest
try:
    # This runs Schema Validation, Policy Enforcement, and Integrity Checks
    agent_def = engine.load_and_validate(
        manifest_path="./agents/payer_war_game/agent.yaml",
        source_dir="./agents/payer_war_game/src"
    )
    print(f"Agent {agent_def.metadata.name} is compliant and ready to run.")

except PolicyViolationError as e:
    print(f"Compliance Failure: {e.violations}")

except IntegrityCompromisedError:
    print("CRITICAL: Code has been tampered with after signing.")
```

For detailed requirements and architecture, please refer to the [Product Requirements](docs/product_requirements.md).
