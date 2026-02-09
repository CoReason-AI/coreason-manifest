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
from pydantic import ValidationError

from coreason_manifest.spec.v2.definitions import ManifestV2


def test_integrity_start_step_missing() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Invalid Start"},
        "status": "published",
        "workflow": {
            "start": "missing-step",
            "steps": {"step-1": {"type": "logic", "id": "step-1", "code": "pass"}},
        },
    }
    with pytest.raises(ValidationError) as excinfo:
        ManifestV2.model_validate(data)
    assert "Start step 'missing-step' not found" in str(excinfo.value)


def test_integrity_next_step_missing() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Invalid Next"},
        "status": "published",
        "workflow": {
            "start": "step-1",
            "steps": {
                "step-1": {
                    "type": "logic",
                    "id": "step-1",
                    "code": "pass",
                    "next": "missing-next",
                }
            },
        },
    }
    with pytest.raises(ValidationError) as excinfo:
        ManifestV2.model_validate(data)
    assert "references missing next step 'missing-next'" in str(excinfo.value)


def test_integrity_switch_case_missing() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Invalid Switch"},
        "status": "published",
        "workflow": {
            "start": "step-1",
            "steps": {
                "step-1": {
                    "type": "switch",
                    "id": "step-1",
                    "cases": {"cond": "missing-case"},
                    "default": "missing-default",
                }
            },
        },
    }
    with pytest.raises(ValidationError) as excinfo:
        ManifestV2.model_validate(data)
    # The error could be about case or default, depends on order.
    assert "references missing step" in str(excinfo.value)


def test_integrity_agent_definition_missing() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Invalid Agent Ref"},
        "status": "published",
        "workflow": {
            "start": "step-1",
            "steps": {
                "step-1": {
                    "type": "agent",
                    "id": "step-1",
                    "agent": "missing-agent",
                }
            },
        },
        "definitions": {},
    }
    with pytest.raises(ValidationError) as excinfo:
        ManifestV2.model_validate(data)
    assert "references missing agent 'missing-agent'" in str(excinfo.value)


def test_integrity_agent_tool_reference_missing() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Invalid Tool Ref"},
        "status": "published",
        "workflow": {
            "start": "step-1",
            "steps": {"step-1": {"type": "logic", "id": "step-1", "code": "pass"}},
        },
        "definitions": {
            "my-agent": {
                "type": "agent",
                "id": "my-agent",
                "name": "Agent",
                "role": "Worker",
                "goal": "Work",
                "tools": [{"type": "remote", "uri": "missing-tool-id"}],
            }
        },
    }
    with pytest.raises(ValidationError) as excinfo:
        ManifestV2.model_validate(data)
    assert "references missing tool 'missing-tool-id'" in str(excinfo.value)


def test_integrity_success_published() -> None:
    """Ensure validation passes for a correct published manifest."""
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Valid Published"},
        "status": "published",
        "workflow": {
            "start": "step-1",
            "steps": {"step-1": {"type": "logic", "id": "step-1", "code": "pass"}},
        },
    }
    manifest = ManifestV2.model_validate(data)
    assert manifest.status == "published"
