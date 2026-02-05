# Governance & Policy Enforcement

The **Governance / Policy Enforcer** module (`src/coreason_manifest/spec/governance.py`) provides a mechanism for Organizations to define rules for Agent validation.

## Overview

The module provides configuration models to define organizational standards (e.g., security, allowed domains, risk levels).

### Key Features
*   **Domain Restriction**: Whitelist specific domains for external tools (e.g., only allow tools from `*.internal.corp`).
*   **Risk Level Enforcement**: Set a maximum allowed risk level for tools (e.g., `SAFE` only).
*   **Authentication Mandates**: Ensure that agents using `CRITICAL` tools enforce user authentication. If `require_auth_for_critical_tools` is enabled (default), any manifest defining a `CRITICAL` tool must explicitly set `requires_auth: true` in its metadata.
*   **Logic Execution Control**: Restrict the usage of arbitrary Python code in `LogicStep`s and `SwitchStep`s.
*   **Strict URL Validation**: Enforce strict normalization (lower-case, no trailing dots) on tool URIs to prevent bypasses.

## Configuration: `GovernanceConfig`

The `GovernanceConfig` model defines the ruleset.

```python
from coreason_manifest.spec.governance import GovernanceConfig
from coreason_manifest.spec.common_base import ToolRiskLevel

config = GovernanceConfig(
    # Only allow tools from these domains
    allowed_domains=["trusted-api.com", "corp.internal"],

    # Block any tool with risk level > STANDARD
    max_risk_level=ToolRiskLevel.STANDARD,

    # If an agent uses CRITICAL tools, it MUST have requires_auth=True
    require_auth_for_critical_tools=True,

    # Prevent agents from running arbitrary Python code (Security)
    # Controls usage of LogicStep and custom logic in SwitchStep
    # Default: False (Secure by Default)
    allow_custom_logic=False,

    # Enforce strict URL normalization (strip trailing dots, case-insensitive match)
    # Default: True (Secure by Default)
    strict_url_validation=True
)
```

## Compliance Models

The module also defines models for reporting compliance violations.

```python
from coreason_manifest.spec.governance import ComplianceViolation, ComplianceReport

# Example structure of a violation
violation = ComplianceViolation(
    rule="domain_restriction",
    message="Tool URI 'http://evil.com/api' is not in allowed domains.",
    component_id="google-search"
)

# Example structure of a report
report = ComplianceReport(
    passed=False,
    violations=[violation]
)
```

## Validation Logic Details

### Authentication Mandate Lookup
When `require_auth_for_critical_tools` is enabled, the validator checks the manifest's metadata for the `requires_auth` flag. It performs a robust lookup:
1.  **Standard Field**: Checks `manifest.metadata.requires_auth`.
2.  **Dynamic Fields**: If not found (or False), it checks the `model_extra` dictionary (e.g., `manifest.metadata.model_extra['requires_auth']`). This supports manifests where the metadata model is extensible.

### Strict vs. Loose URL Validation
The `strict_url_validation` setting controls how Tool URIs are normalized before comparison with `allowed_domains`:

*   **Strict Mode (`True`)**:
    *   Hostnames are lower-cased.
    *   Trailing dots (DNS root) are removed (e.g., `example.com.` becomes `example.com`).
    *   This ensures that `https://Example.COM.` matches an allowed domain of `example.com`.

*   **Loose Mode (`False`)**:
    *   Hostnames are lower-cased (standard `urlparse` behavior).
    *   Trailing dots are **preserved**.
    *   Comparison is exact against the `allowed_domains` list. If your allowed list contains `example.com` but the tool uses `example.com.`, validation will fail in Loose mode but pass in Strict mode.
