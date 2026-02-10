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
