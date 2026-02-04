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
    AgentDefinition,
    AgentStep,
    CouncilStep,
    ManifestV2,
    SwitchStep,
    ToolDefinition,
)


def validate_integrity(manifest: ManifestV2) -> ManifestV2:
    """Validate referential integrity of the manifest.

    Checks:
    1. workflow.start exists in steps.
    2. step.next pointers exist in steps.
    3. SwitchStep.cases targets exist.
    4. agent references in AgentStep exist in definitions.
    5. CouncilStep voters exist in definitions.
    6. AgentDefinition tools exist in definitions.

    Args:
        manifest: The V2 manifest to validate.

    Returns:
        The valid manifest (for chaining).

    Raises:
        ValueError: If referential integrity is violated.
    """
    steps = manifest.workflow.steps

    # 1. Validate Start Step
    if manifest.workflow.start not in steps:
        raise ValueError(f"Start step '{manifest.workflow.start}' not found in steps.")

    for step in steps.values():
        # 2. Validate 'next' pointers (AgentStep, LogicStep, CouncilStep)
        if hasattr(step, "next") and step.next:
            if step.next not in steps:
                raise ValueError(f"Step '{step.id}' references missing next step '{step.next}'.")

        # 3. Validate SwitchStep targets
        if isinstance(step, SwitchStep):
            for target in step.cases.values():
                if target not in steps:
                    raise ValueError(f"SwitchStep '{step.id}' references missing step '{target}' in cases.")
            if step.default and step.default not in steps:
                raise ValueError(f"SwitchStep '{step.id}' references missing step '{step.default}' in default.")

        # 4. Validate Definition References
        if isinstance(step, AgentStep):
            if step.agent not in manifest.definitions:
                raise ValueError(f"AgentStep '{step.id}' references missing agent '{step.agent}'.")

            # Check type
            agent_def = manifest.definitions[step.agent]
            if not isinstance(agent_def, AgentDefinition):
                raise ValueError(
                    f"AgentStep '{step.id}' references '{step.agent}' which is not an AgentDefinition "
                    f"(got {type(agent_def).__name__})."
                )

        if isinstance(step, CouncilStep):
            for voter in step.voters:
                if voter not in manifest.definitions:
                    raise ValueError(f"CouncilStep '{step.id}' references missing voter '{voter}'.")

                # Check type
                agent_def = manifest.definitions[voter]
                if not isinstance(agent_def, AgentDefinition):
                    raise ValueError(
                        f"CouncilStep '{step.id}' references voter '{voter}' which is not an AgentDefinition "
                        f"(got {type(agent_def).__name__})."
                    )

    # 5. Validate Agent Tools
    for _, definition in manifest.definitions.items():
        if isinstance(definition, AgentDefinition):
            for tool_id in definition.tools:
                if tool_id not in manifest.definitions:
                    raise ValueError(f"Agent '{definition.id}' references missing tool '{tool_id}'.")

                tool_def = manifest.definitions[tool_id]
                if not isinstance(tool_def, ToolDefinition):
                    raise ValueError(
                        f"Agent '{definition.id}' references '{tool_id}' which is not a ToolDefinition "
                        f"(got {type(tool_def).__name__})."
                    )

    return manifest


def validate_loose(manifest: ManifestV2) -> List[str]:
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
    warnings: List[str] = []

    # 1. Check unique Step IDs
    for step_id, step in manifest.workflow.steps.items():
        if step.id != step_id:
            warnings.append(f"Step key '{step_id}' does not match step.id '{step.id}'.")

    # 2. Check SwitchStep cases syntax
    for step_id, step in manifest.workflow.steps.items():
        if isinstance(step, SwitchStep):
            for condition in step.cases.keys():
                if not isinstance(condition, str) or not condition.strip():
                    warnings.append(f"SwitchStep '{step_id}' has invalid condition: {condition}")

    # 3. Check Referential Integrity (Warnings)
    steps = manifest.workflow.steps

    # Start Step
    if manifest.workflow.start not in steps:
        warnings.append(f"Start step '{manifest.workflow.start}' not found in steps.")

    for step in steps.values():
        # 'next' pointers
        if hasattr(step, "next") and step.next:
            if step.next not in steps:
                warnings.append(f"Step '{step.id}' references missing next step '{step.next}'.")

        # SwitchStep targets
        if isinstance(step, SwitchStep):
            for target in step.cases.values():
                if target not in steps:
                    warnings.append(f"SwitchStep '{step.id}' references missing step '{target}' in cases.")
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
    for _, definition in manifest.definitions.items():
        if isinstance(definition, AgentDefinition):
            for tool_id in definition.tools:
                if tool_id not in manifest.definitions:
                    warnings.append(f"Agent '{definition.id}' references missing tool '{tool_id}'.")
                else:
                    tool_def = manifest.definitions[tool_id]
                    if not isinstance(tool_def, ToolDefinition):
                        warnings.append(
                            f"Agent '{definition.id}' references '{tool_id}' which is not a ToolDefinition "
                            f"(got {type(tool_def).__name__})."
                        )

    return warnings
