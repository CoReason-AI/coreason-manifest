# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import pytest

from coreason_manifest.spec.v2.definitions import ManifestV2
from coreason_manifest.utils.v2.validator import validate_integrity


def test_missing_start_step() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Test"},
        "workflow": {
            "start": "missing-step",
            "steps": {"step-1": {"type": "logic", "id": "step-1", "code": "pass"}},
        },
    }
    manifest = ManifestV2.model_validate(data)
    with pytest.raises(ValueError, match="Start step 'missing-step' not found"):
        validate_integrity(manifest)


def test_missing_next_step() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Test"},
        "workflow": {
            "start": "step-1",
            "steps": {"step-1": {"type": "logic", "id": "step-1", "code": "pass", "next": "missing-next"}},
        },
    }
    manifest = ManifestV2.model_validate(data)
    with pytest.raises(ValueError, match="Step 'step-1' references missing next step 'missing-next'"):
        validate_integrity(manifest)


def test_switch_step_missing_targets() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Test"},
        "workflow": {
            "start": "step-1",
            "steps": {
                "step-1": {
                    "type": "switch",
                    "id": "step-1",
                    "cases": {"cond1": "missing-case"},
                    "default": "missing-default",
                }
            },
        },
    }
    manifest = ManifestV2.model_validate(data)
    # Match generic error message since both are missing, either could be hit first
    with pytest.raises(ValueError, match="references missing step"):
        validate_integrity(manifest)


def test_agent_step_missing_definition() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Test"},
        "definitions": {},
        "workflow": {
            "start": "step-1",
            "steps": {"step-1": {"type": "agent", "id": "step-1", "agent": "missing-agent"}},
        },
    }
    manifest = ManifestV2.model_validate(data)
    with pytest.raises(ValueError, match="AgentStep 'step-1' references missing agent 'missing-agent'"):
        validate_integrity(manifest)


def test_council_step_missing_voters() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Test"},
        "definitions": {},
        "workflow": {
            "start": "step-1",
            "steps": {
                "step-1": {"type": "council", "id": "step-1", "voters": ["missing-voter"], "strategy": "consensus"}
            },
        },
    }
    manifest = ManifestV2.model_validate(data)
    with pytest.raises(ValueError, match="CouncilStep 'step-1' references missing voter 'missing-voter'"):
        validate_integrity(manifest)


def test_agent_step_referencing_tool() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Test"},
        "definitions": {
            "my-tool": {"type": "tool", "id": "tool-1", "name": "Tool", "uri": "mcp://tool", "risk_level": "safe"}
        },
        "workflow": {
            "start": "step-1",
            "steps": {"step-1": {"type": "agent", "id": "step-1", "agent": "my-tool"}},
        },
    }
    manifest = ManifestV2.model_validate(data)
    with pytest.raises(ValueError, match="AgentStep 'step-1' references 'my-tool' which is not an AgentDefinition"):
        validate_integrity(manifest)


def test_council_step_referencing_tool() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Test"},
        "definitions": {
            "my-tool": {"type": "tool", "id": "tool-1", "name": "Tool", "uri": "mcp://tool", "risk_level": "safe"}
        },
        "workflow": {
            "start": "step-1",
            "steps": {"step-1": {"type": "council", "id": "step-1", "voters": ["my-tool"], "strategy": "consensus"}},
        },
    }
    manifest = ManifestV2.model_validate(data)
    with pytest.raises(
        ValueError, match="CouncilStep 'step-1' references voter 'my-tool' which is not an AgentDefinition"
    ):
        validate_integrity(manifest)


def test_switch_step_missing_default() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Test"},
        "workflow": {
            "start": "step-1",
            "steps": {"step-1": {"type": "switch", "id": "step-1", "cases": {}, "default": "missing-default"}},
        },
    }
    manifest = ManifestV2.model_validate(data)
    with pytest.raises(ValueError, match="references missing step 'missing-default' in default"):
        validate_integrity(manifest)
