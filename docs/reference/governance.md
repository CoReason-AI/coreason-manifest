# Governance

## Overview
This module defines the policies for static validation and runtime auditing, ensuring that [agents](../reference/agents.md) and tools comply with security and safety standards.

## Application Pattern
This example shows how to configure a [GovernanceConfig][coreason_manifest.spec.governance.GovernanceConfig] that enforces strict risk levels and blocks the use of "Critical" tools without authentication.

```python
# Example: Creating a Governance Configuration
from coreason_manifest.spec.governance import GovernanceConfig, ToolRiskLevel

# Define a policy that blocks critical tools and restricts domains
policy = GovernanceConfig(
    allowed_domains=["api.github.com", "slack.com"],
    max_risk_level=ToolRiskLevel.STANDARD,
    require_auth_for_critical_tools=True,
    allow_inline_tools=False,
    strict_url_validation=True
)

# If an agent attempts to use a tool with Risk Level 'CRITICAL',
# this policy will cause a validation error during the manifest check.
```

## API Reference

::: coreason_manifest.spec.governance.GovernanceConfig

::: coreason_manifest.spec.governance.ComplianceReport
