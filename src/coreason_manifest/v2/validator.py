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

from typing import List, Set

from coreason_manifest.v2.spec.definitions import (
    AgentStep,
    CouncilStep,
    LogicStep,
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


def validate_strict(manifest: ManifestV2) -> List[str]:
    """Validate manifest for executable integrity.

    Checks:
    - Runs validate_loose.
    - Ensures every 'next' pointer and switch target exists.
    - Ensures workflow.start exists.
    - Ensures definitions references exist.

    Args:
        manifest: The V2 manifest to validate.

    Returns:
        List of error messages (empty if valid).
    """
    errors: List[str] = validate_loose(manifest)

    step_ids: Set[str] = set(manifest.workflow.steps.keys())

    # 1. Entry Point
    if manifest.workflow.start not in step_ids:
        errors.append(f"Workflow start step '{manifest.workflow.start}' not found in steps.")

    # 2. Step Integrity
    for step_id, step in manifest.workflow.steps.items():
        # Check 'next' pointers
        if isinstance(step, (AgentStep, LogicStep, CouncilStep)):
            if step.next and step.next not in step_ids:
                errors.append(f"Step '{step_id}' points to non-existent next step '{step.next}'.")

        # Check SwitchStep targets
        elif isinstance(step, SwitchStep):
            for condition, target_id in step.cases.items():
                if target_id not in step_ids:
                    errors.append(
                        f"SwitchStep '{step_id}' case '{condition}' points to non-existent step '{target_id}'."
                    )
            if step.default and step.default not in step_ids:
                errors.append(f"SwitchStep '{step_id}' default points to non-existent step '{step.default}'.")

        # 3. Definitions References
        if isinstance(step, AgentStep):
            if step.agent not in manifest.definitions:
                errors.append(f"Agent '{step.agent}' referenced in step '{step_id}' not found in definitions.")

    return errors
