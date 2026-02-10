# Governance

## Overview
The Governance module defines policies and compliance structures for the agent ecosystem. `GovernanceConfig` sets the rules for static analysis, while `ComplianceReport` captures the results of validation.

## Application Pattern
This example demonstrates how to configure governance rules to restrict tool usage and enforce strict compliance.

```python
# Example: Configuring Governance Rules
from coreason_manifest import GovernanceConfig, ToolRiskLevel

# Define a strict governance policy
policy = GovernanceConfig(
    allowed_domains=["api.github.com", "slack.com"],
    max_risk_level=ToolRiskLevel.STANDARD,
    require_auth_for_critical_tools=True,
    allow_inline_tools=False,
    strict_url_validation=True
)

# This configuration ensures that:
# 1. Tools can only call github.com or slack.com
# 2. No CRITICAL risk tools are allowed
# 3. Authentication is strictly enforced
```

## API Reference

### GovernanceConfig

::: coreason_manifest.spec.governance.GovernanceConfig

### ComplianceReport

::: coreason_manifest.spec.governance.ComplianceReport
