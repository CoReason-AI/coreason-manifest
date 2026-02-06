# Semantic Diffing Utility

The **Semantic Diffing Utility** (`src/coreason_manifest/utils/diff.py`) provides a robust mechanism to programmatically determine the impact of changes between two `AgentDefinition` or `ManifestV2` objects.

Unlike standard text-based diffs, this utility understands the *structure* of the manifest and categorizes changes by their operational and governance risk.

## Overview

CI/CD pipelines and Governance systems use this utility to answer critical questions:
*   **Is this update safe?** (No BREAKING changes to the interface)
*   **Does it increase cost?** (RESOURCE changes)
*   **Does it weaken security?** (GOVERNANCE changes like removing a policy)

## Usage

```python
from coreason_manifest import compare_agents, ManifestV2

# Load your manifests
old_manifest = ManifestV2(...)
new_manifest = ManifestV2(...)

# Compare
report = compare_agents(old_manifest, new_manifest)

# Analyze the report
if report.has_breaking:
    print("Warning: This update breaks the API contract!")

if report.has_governance_impact:
    print("Alert: Governance policies have been modified.")

for change in report.changes:
    print(f"[{change.category}] {change.path}: {change.old_value} -> {change.new_value}")
```

## Change Categories

The utility classifies every detected change into one of the following categories:

| Category | Description | Examples |
| :--- | :--- | :--- |
| **BREAKING** | Changes that violate the API contract or reliability. | Removing an input field, adding a required input, removing a tool. |
| **GOVERNANCE** | Changes to policies or safety configurations. | Removing the `policy` block, changing `human_in_the_loop`, altering `governance` settings. |
| **RESOURCE** | Changes that impact cost or operational limits. | Increasing `input_cost`, changing `model_id`, adding a `resources` block. |
| **FEATURE** | Additive changes that extend functionality safely. | Adding an optional input field, adding a new tool. |
| **PATCH** | Metadata or documentation updates. | Changing `description`, `version`, or internal metadata. |

## DiffReport Structure

The `DiffReport` object contains:

*   `changes`: A list of `DiffChange` objects.
*   `has_breaking`: Boolean flag, true if any change is BREAKING.
*   `has_governance_impact`: Boolean flag, true if any change is GOVERNANCE.

### DiffChange

Each `DiffChange` provides detailed granularity:

*   `path`: Dot-notation path to the changed field (e.g., `interface.inputs.properties.limit`).
*   `old_value`: The value in the original object.
*   `new_value`: The value in the new object.
*   `category`: The assigned `ChangeCategory`.

## Comparison Logic Details

### Robustness
The comparator is designed to be robust against:
*   **Missing Blocks**: Handles cases where optional blocks (like `resources` or `policy`) are added or removed entirely.
*   **Type Mismatches**: Detects when a field changes type (e.g., from `int` to `str`).

### Recursion
The utility performs a deep, recursive walk of the dictionary representation of the models. It identifies specific leaf-node changes rather than just flagging the parent container.

### Categorization Rules
1.  **Resources**: Any change within `resources.*` is flagged as **RESOURCE**.
2.  **Policies**: Any change within `policy.*` or `governance.*` is flagged as **GOVERNANCE**.
3.  **Interface Inputs**:
    *   Removing a property -> **BREAKING**.
    *   Adding a required property -> **BREAKING**.
    *   Adding an optional property -> **FEATURE**.
    *   Replacing the entire schema -> **BREAKING** (default safety).
4.  **Tools**:
    *   Removing a tool -> **BREAKING**.
    *   Adding a tool -> **FEATURE**.
5.  **Metadata**: Changes to `description`, `version`, etc., are **PATCH**.
