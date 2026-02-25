# Governance

## Overview
This module defines the policies and constraints for agents, flows, and tools.

## Example

```python
from coreason_manifest.spec.core.governance import Governance, Safety, Audit

safety_policy = Safety(
    input_filtering=True,
    pii_redaction=True,
    content_safety="high"
)

audit_policy = Audit(
    trace_retention_days=90,
    log_payloads=False
)

gov = Governance(
    rate_limit_rpm=60,
    timeout_seconds=300,
    cost_limit_usd=1.0,
    safety=safety_policy,
    audit=audit_policy
)
```

## API Reference

::: coreason_manifest.spec.core.governance.Governance

::: coreason_manifest.spec.core.governance.Safety

::: coreason_manifest.spec.core.governance.Audit
