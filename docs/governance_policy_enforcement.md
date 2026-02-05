# Governance & Policy Enforcement

The **Governance / Policy Enforcer** module (`src/coreason_manifest/governance.py`) provides a mechanism for Organizations to define rules for Agent validation.

## Overview

The module provides configuration models to define organizational standards (e.g., security, allowed domains, risk levels).

### Key Features
*   **Domain Restriction**: Whitelist specific domains for external tools (e.g., only allow tools from `*.internal.corp`).
*   **Risk Level Enforcement**: Set a maximum allowed risk level for tools (e.g., `SAFE` only).
*   **Authentication Mandates**: Ensure that agents using `CRITICAL` tools enforce user authentication. If `require_auth_for_critical_tools` is enabled (default), any manifest defining a `CRITICAL` tool must explicitly set `requires_auth: true` in its metadata.
*   **Logic Execution Control**: Restrict the usage of arbitrary Python code in `LogicStep`s and `SwitchStep`s.
*   **Strict URL Validation**: Enforce strict normalization (lower-case, no trailing dots, punycode encoding) on tool URIs to prevent bypasses.

## Configuration: `GovernanceConfig`

The `GovernanceConfig` model defines the ruleset.

```python
from coreason_manifest.governance import GovernanceConfig
from coreason_manifest.common import ToolRiskLevel

config = GovernanceConfig(
    # Only allow tools from these domains (and their subdomains)
    # e.g., "internal.corp" allows "api.internal.corp"
    allowed_domains=["trusted-api.com", "corp.internal"],

    # Block any tool with risk level > STANDARD
    max_risk_level=ToolRiskLevel.STANDARD,

    # If an agent uses CRITICAL tools, it MUST have requires_auth=True in metadata
    # Default: True (Secure by Default)
    require_auth_for_critical_tools=True,

    # Prevent agents from running arbitrary Python code (Security)
    # Controls usage of LogicStep
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
from coreason_manifest.governance import ComplianceViolation, ComplianceReport

# Example structure of a violation
violation = ComplianceViolation(
    rule="domain_restriction",
    message="Tool URI 'http://evil.com/api' is not in allowed domains.",
    component_id="google-search"
)

# Example structure of a report
report = ComplianceReport(
    compliant=False,
    violations=[violation]
)
```

## Verification

To check an agent against a policy:

```python
from coreason_manifest.governance import check_compliance

report = check_compliance(agent_manifest, config)

if not report.compliant:
    for violation in report.violations:
        print(f"Violation: {violation.message}")
```
