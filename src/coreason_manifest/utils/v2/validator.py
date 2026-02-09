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

from coreason_manifest.spec.v2.definitions import (
    AgentDefinition,
    AgentStep,
    CouncilStep,
    ManifestV2,
    SwitchStep,
    ToolDefinition,
    ToolRequirement,
)


def validate_integrity(manifest: ManifestV2) -> ManifestV2:
    """Validate referential integrity of the manifest.

    DEPRECATED: ManifestV2 now self-validates on instantiation.
    Any ManifestV2 object passed here is already guaranteed to be valid.

    Args:
        manifest: The V2 manifest to validate.

    Returns:
        The valid manifest (for chaining).
    """
    return manifest


def validate_loose(manifest: ManifestV2) -> list[str]:
    """Validate "Draft" manifests for structural sanity only.

    Checks:
    - Unique Step IDs.
    - SwitchStep case syntax (basic).
    - Referential integrity (Start, Next, Switch, Agents, Tools) - warnings only.

    Args:
        manifest: The V2 manifest to validate.

    Returns:
        List of warning messages (empty if clean).
    """
    warnings: list[str] = []

    # 1. Check unique Step IDs
    for step_id, step in manifest.workflow.steps.items():
        if step.id != step_id:
            warnings.append(f"Step key '{step_id}' does not match step.id '{step.id}'.")

    # 2. Check SwitchStep cases syntax
    for step_id, step in manifest.workflow.steps.items():
        if isinstance(step, SwitchStep):
            warnings.extend(
                f"SwitchStep '{step_id}' has invalid condition: {condition}"
                for condition in step.cases
                if not isinstance(condition, str) or not condition.strip()
            )

    # 3. Check Referential Integrity (Warnings)
    steps = manifest.workflow.steps

    # Start Step
    if manifest.workflow.start not in steps:
        warnings.append(f"Start step '{manifest.workflow.start}' not found in steps.")

    for step in steps.values():
        # 'next' pointers
        if hasattr(step, "next") and step.next and step.next not in steps:
            warnings.append(f"Step '{step.id}' references missing next step '{step.next}'.")

        # SwitchStep targets
        if isinstance(step, SwitchStep):
            warnings.extend(
                f"SwitchStep '{step.id}' references missing step '{target}' in cases."
                for target in step.cases.values()
                if target not in steps
            )
            if step.default and step.default not in steps:
                warnings.append(f"SwitchStep '{step.id}' references missing step '{step.default}' in default.")

        # Definition References
        if isinstance(step, AgentStep):
            if step.agent not in manifest.definitions:
                warnings.append(f"AgentStep '{step.id}' references missing agent '{step.agent}'.")
            else:
                agent_def = manifest.definitions[step.agent]
                if not isinstance(agent_def, AgentDefinition):
                    warnings.append(
                        f"AgentStep '{step.id}' references '{step.agent}' which is not an AgentDefinition "
                        f"(got {type(agent_def).__name__})."
                    )

        if isinstance(step, CouncilStep):
            for voter in step.voters:
                if voter not in manifest.definitions:
                    warnings.append(f"CouncilStep '{step.id}' references missing voter '{voter}'.")
                else:
                    agent_def = manifest.definitions[voter]
                    if not isinstance(agent_def, AgentDefinition):
                        warnings.append(
                            f"CouncilStep '{step.id}' references voter '{voter}' which is not an AgentDefinition "
                            f"(got {type(agent_def).__name__})."
                        )

    # Agent Tools
    for definition in manifest.definitions.values():
        if isinstance(definition, AgentDefinition):
            for tool_ref in definition.tools:
                if isinstance(tool_ref, ToolRequirement):
                    if tool_ref.uri in manifest.definitions:
                        tool_def = manifest.definitions[tool_ref.uri]
                        if not isinstance(tool_def, ToolDefinition):
                            warnings.append(
                                f"Agent '{definition.id}' references '{tool_ref.uri}' which is not a ToolDefinition "
                                f"(got {type(tool_def).__name__})."
                            )
                    elif "://" not in tool_ref.uri:
                        warnings.append(f"Agent '{definition.id}' references missing tool '{tool_ref.uri}'.")

    return warnings
