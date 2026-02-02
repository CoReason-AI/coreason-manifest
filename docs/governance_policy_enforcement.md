# Governance & Policy Enforcement

The **Governance / Policy Enforcer** module (`src/coreason_manifest/governance.py`) provides a mechanism for Organizations to enforce rules *upon* an Agent. While an `AgentDefinition` can define its own internal policy (like budget caps), the Governance module allows an external authority to validate that an agent complies with organizational standards (e.g., security, allowed domains).

## Overview

The module centers around the `check_compliance` function, which validates an `AgentDefinition` against a `GovernanceConfig`. It returns a `ComplianceReport` detailing any violations.

### Key Features
*   **Domain Restriction**: Whitelist specific domains for external tools (e.g., only allow tools from `*.internal.corp`).
*   **Risk Level Enforcement**: Set a maximum allowed risk level for tools (e.g., `SAFE` only).
*   **Authentication Mandates**: Ensure that agents using `CRITICAL` tools enforce user authentication.

## Configuration: `GovernanceConfig`

The `GovernanceConfig` model defines the ruleset.

```python
from coreason_manifest.governance import GovernanceConfig
from coreason_manifest.definitions.agent import ToolRiskLevel

config = GovernanceConfig(
    # Only allow tools from these domains
    allowed_domains=["trusted-api.com", "corp.internal"],

    # Block any tool with risk level > STANDARD
    max_risk_level=ToolRiskLevel.STANDARD,

    # If an agent uses CRITICAL tools, it MUST have requires_auth=True
    require_auth_for_critical_tools=True
)
```

## Compliance Report

The `check_compliance` function returns a `ComplianceReport` containing a pass/fail status and a list of `ComplianceViolation` objects.

```python
class ComplianceViolation(CoReasonBaseModel):
    rule: str          # Name of the rule broken (e.g., 'domain_restriction')
    message: str       # Human-readable details
    component_id: str  # The tool or component causing the violation

class ComplianceReport(CoReasonBaseModel):
    passed: bool
    violations: List[ComplianceViolation]
```

## Usage Example

```python
from coreason_manifest.definitions.agent import AgentDefinition
from coreason_manifest.governance import check_compliance, GovernanceConfig, ToolRiskLevel

# 1. Load your Agent Definition
agent: AgentDefinition = ...

# 2. Define Organizational Rules
rules = GovernanceConfig(
    allowed_domains=["api.weather.gov"],
    max_risk_level=ToolRiskLevel.SAFE
)

# 3. Run Compliance Check
report = check_compliance(agent, rules)

if report.passed:
    print("Agent is compliant!")
else:
    print("Compliance Violations Found:")
    for v in report.violations:
        print(f" - [{v.rule}] {v.message} (Source: {v.component_id})")
```

## Enforcement Logic

### Domain Checks
*   Iterates through `agent.dependencies.tools`.
*   Parses the URI of each `ToolRequirement`.
*   Checks if the hostname exists in `allowed_domains`.
*   *Note: `InlineToolDefinition` items are currently skipped as they do not have URIs.*

### Risk Level Checks
*   Compares the `risk_level` of each tool against `max_risk_level`.
*   Risk hierarchy: `SAFE` < `STANDARD` < `CRITICAL`.

### Authentication Checks
*   If `require_auth_for_critical_tools` is `True`:
    *   Scans for any tool with `risk_level=CRITICAL`.
    *   If found, validates that `agent.metadata.requires_auth` is `True`.
