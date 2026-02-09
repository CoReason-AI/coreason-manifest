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
    errors = manifest.verify()
    assert len(errors) > 0
    assert "Start step 'missing-step' missing from workflow" in errors[0]


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
    errors = manifest.verify()
    assert len(errors) > 0
    assert "references missing next step 'missing-next'" in errors[0]


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
    errors = manifest.verify()
    assert len(errors) > 0
    assert any("references missing step" in e for e in errors)


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
    errors = manifest.verify()
    assert len(errors) > 0
    assert "AgentStep 'step-1' references missing agent 'missing-agent'" in errors[0]


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
    errors = manifest.verify()
    assert len(errors) > 0
    assert "CouncilStep 'step-1' references missing voter 'missing-voter'" in errors[0]


def test_agent_step_referencing_tool() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Test"},
        "definitions": {
                "my-tool": {"type": "tool", "id": "my-tool", "name": "Tool", "uri": "mcp://tool", "risk_level": "safe"}
        },
        "workflow": {
            "start": "step-1",
            "steps": {"step-1": {"type": "agent", "id": "step-1", "agent": "my-tool"}},
        },
    }
    manifest = ManifestV2.model_validate(data)
    errors = manifest.verify()
    assert len(errors) > 0
    assert "AgentStep 'step-1' references 'my-tool' which is not an AgentDefinition" in errors[0]


def test_council_step_referencing_tool() -> None:
    data = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Test"},
        "definitions": {
                "my-tool": {"type": "tool", "id": "my-tool", "name": "Tool", "uri": "mcp://tool", "risk_level": "safe"}
        },
        "workflow": {
            "start": "step-1",
            "steps": {"step-1": {"type": "council", "id": "step-1", "voters": ["my-tool"], "strategy": "consensus"}},
        },
    }
    manifest = ManifestV2.model_validate(data)
    errors = manifest.verify()
    assert len(errors) > 0
    assert "CouncilStep 'step-1' references voter 'my-tool' which is not an AgentDefinition" in errors[0]


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
    errors = manifest.verify()
    assert len(errors) > 0
    assert "references missing step 'missing-default' in default" in errors[0]
