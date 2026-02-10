# Governance

## Overview
The Governance module defines policies and compliance structures for the agent ecosystem. `GovernanceConfig` sets the rules for static analysis, while `ComplianceReport` captures the results of validation.

This module enforces policies on [Agents](agents.md) and their tool usage, ensuring adherence to security and compliance standards.

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
# Governance Model

## Policy and Compliance

This diagram visualizes the `GovernanceConfig` for static validation and `ComplianceConfig` for runtime auditing.

```mermaid
classDiagram
    %% SOTA Styling Init
    %%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#ffecb3', 'edgeLabelBackground':'#ffffff', 'tertiaryColor': '#e1f5fe'}}}%%

    class GovernanceConfig {
        +list~str~ allowed_domains
        +ToolRiskLevel max_risk_level
        +bool require_auth_for_critical_tools
        +bool allow_inline_tools
        +bool allow_custom_logic
        +bool strict_url_validation
    }
    class ComplianceConfig {
        +AuditLevel audit_level
        +RetentionPolicy retention
        +bool generate_aibom
        +bool generate_pdf_report
        +bool require_signature
        +bool mask_pii
        +IntegrityConfig integrity
    }
    class ToolRiskLevel {
        <<Enum>>
        SAFE
        STANDARD
        CRITICAL
    }
    class AuditLevel {
        <<Enum>>
        NONE
        BASIC
        FULL
        GXP_COMPLIANT
    }
    class IntegrityConfig {
        +AuditContentMode input_mode
        +AuditContentMode output_mode
        +IntegrityLevel integrity_level
        +str hash_algorithm
    }

    %% Relationships (Conceptual Dependencies)
    GovernanceConfig ..> ToolRiskLevel : uses
    ComplianceConfig ..> AuditLevel : uses
    ComplianceConfig *-- IntegrityConfig : contains

    %% Note: GovernanceConfig validates the Manifest, while ComplianceConfig governs runtime auditing.

    %% Styling Classes
    classDef root fill:#ffecb3,stroke:#ffb74d,stroke-width:2px;
    classDef config fill:#e1f5fe,stroke:#4fc3f7,stroke-width:1px;
    classDef enum fill:#fbe9e7,stroke:#ffab91,stroke-width:1px,stroke-dasharray: 2 2;

    %% Apply Styles
    class GovernanceConfig,ComplianceConfig root;
    class IntegrityConfig config;
    class ToolRiskLevel,AuditLevel enum;
```
