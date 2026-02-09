# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest


from coreason_manifest.spec.v2.definitions import ManifestV2


def test_integrity_start_step_missing() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Invalid Start"},
        "workflow": {
            "start": "missing-step",
            "steps": {"step-1": {"type": "logic", "id": "step-1", "code": "pass"}},
        },
    }
    manifest = ManifestV2.model_validate(data)
    errors = manifest.verify()
    assert len(errors) > 0
    assert "Start step 'missing-step' missing from workflow" in errors[0]


def test_integrity_next_step_missing() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Invalid Next"},
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
    manifest = ManifestV2.model_validate(data)
    errors = manifest.verify()
    assert len(errors) > 0
    assert "references missing next step 'missing-next'" in errors[0]


def test_integrity_switch_case_missing() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Invalid Switch"},
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
    manifest = ManifestV2.model_validate(data)
    errors = manifest.verify()
    assert len(errors) > 0
    # The error could be about case or default, depends on order.
    assert any("references missing step" in e for e in errors)


def test_integrity_agent_definition_missing() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Invalid Agent Ref"},
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
    manifest = ManifestV2.model_validate(data)
    errors = manifest.verify()
    assert len(errors) > 0
    assert "references missing agent 'missing-agent'" in errors[0]


def test_integrity_agent_tool_reference_missing() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Invalid Tool Ref"},
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
    manifest = ManifestV2.model_validate(data)
    errors = manifest.verify()
    assert len(errors) > 0
    assert "references missing tool 'missing-tool-id'" in errors[0]


def test_integrity_success_published() -> None:
    """Ensure validation passes for a correct published manifest."""
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Valid Published"},
        "workflow": {
            "start": "step-1",
            "steps": {"step-1": {"type": "logic", "id": "step-1", "code": "pass"}},
        },
    }
    manifest = ManifestV2.model_validate(data)
    assert manifest.is_executable
