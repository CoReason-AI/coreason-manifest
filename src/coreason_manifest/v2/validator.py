# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

"""Validation logic for V2 Manifests."""

from typing import List

from coreason_manifest.v2.spec.definitions import (
    ManifestV2,
    SwitchStep,
)


def validate_loose(manifest: ManifestV2) -> List[str]:
    """Validate "Draft" manifests for structural sanity only.

    Checks:
    - Unique Step IDs.
    - SwitchStep case syntax (basic).

    Args:
        manifest: The V2 manifest to validate.

    Returns:
        List of warning messages (empty if clean).
    """
    warnings: List[str] = []

    # 1. Check unique Step IDs
    for step_id, step in manifest.workflow.steps.items():
        if step.id != step_id:
            warnings.append(f"Step key '{step_id}' does not match step.id '{step.id}'.")

    # 2. Check SwitchStep cases
    for step_id, step in manifest.workflow.steps.items():
        if isinstance(step, SwitchStep):
            for condition in step.cases.keys():
                if not isinstance(condition, str) or not condition.strip():
                    warnings.append(f"SwitchStep '{step_id}' has invalid condition: {condition}")

    return warnings
