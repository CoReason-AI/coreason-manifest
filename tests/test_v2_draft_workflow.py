# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest.spec.v2.definitions import (
    ManifestV2,
    PlaceholderStep,
    PlaceholderDefinition,
    Workflow,
    ManifestMetadata,
    AgentStep,
    AgentDefinition,
    SwitchStep,
    CouncilStep
)

def test_draft_workflow_placeholders() -> None:
    manifest = ManifestV2(
        kind="Recipe",
        metadata=ManifestMetadata(name="Draft Workflow"),
        workflow=Workflow(
            start="step1",
            steps={
                "step1": PlaceholderStep(id="step1", notes="This step is TBD")
            }
        )
    )

    # It should be structurally valid (loadable)
    assert isinstance(manifest, ManifestV2)

    # It should not be executable
    assert not manifest.is_executable

    # Verify errors
    errors = manifest.verify()
    assert len(errors) == 1
    assert "Step 'step1' is a placeholder" in errors[0]

def test_draft_workflow_missing_start() -> None:
    manifest = ManifestV2(
        kind="Recipe",
        metadata=ManifestMetadata(name="Broken Start"),
        workflow=Workflow(
            start="step1",
            steps={}
        )
    )

    assert not manifest.is_executable
    errors = manifest.verify()
    assert len(errors) == 1
    assert "Start step 'step1' missing from workflow" in errors[0]

def test_draft_workflow_broken_references() -> None:
    manifest = ManifestV2(
        kind="Recipe",
        metadata=ManifestMetadata(name="Broken Refs"),
        definitions={
            "agent1": AgentDefinition(
                id="agent1",
                name="Agent 1",
                role="tester",
                goal="test"
            )
        },
        workflow=Workflow(
            start="step1",
            steps={
                "step1": AgentStep(
                    id="step1",
                    agent="agent1",
                    next="step2"
                )
            }
        )
    )

    assert not manifest.is_executable
    errors = manifest.verify()
    assert len(errors) == 1
    assert "Step 'step1' references missing next step 'step2'" in errors[0]

def test_draft_workflow_placeholder_definition() -> None:
    manifest = ManifestV2(
        kind="Recipe",
        metadata=ManifestMetadata(name="Placeholder Definition"),
        definitions={
            "agent1": PlaceholderDefinition(id="agent1", notes="TBD Agent")
        },
        workflow=Workflow(
            start="step1",
            steps={
                "step1": AgentStep(
                    id="step1",
                    agent="agent1"
                )
            }
        )
    )

    assert not manifest.is_executable
    errors = manifest.verify()
    assert len(errors) == 1
    assert "AgentStep 'step1' references placeholder agent 'agent1'" in errors[0]

def test_draft_workflow_council_placeholder() -> None:
    manifest = ManifestV2(
        kind="Recipe",
        metadata=ManifestMetadata(name="Placeholder Council"),
        definitions={
            "agent1": PlaceholderDefinition(id="agent1", notes="TBD Agent")
        },
        workflow=Workflow(
            start="step1",
            steps={
                "step1": CouncilStep(
                    id="step1",
                    voters=["agent1"]
                )
            }
        )
    )

    assert not manifest.is_executable
    errors = manifest.verify()
    assert len(errors) == 1
    assert "CouncilStep 'step1' references placeholder voter 'agent1'" in errors[0]

def test_switch_step_validation() -> None:
    manifest = ManifestV2(
        kind="Recipe",
        metadata=ManifestMetadata(name="Switch Validation"),
        workflow=Workflow(
            start="switch1",
            steps={
                "switch1": SwitchStep(
                    id="switch1",
                    cases={"cond1": "missing_step"},
                    default="also_missing"
                )
            }
        )
    )

    errors = manifest.verify()
    assert len(errors) == 2
    assert any("references missing step 'missing_step'" in e for e in errors)
    assert any("references missing step 'also_missing'" in e for e in errors)

def test_valid_manifest() -> None:
    manifest = ManifestV2(
        kind="Recipe",
        metadata=ManifestMetadata(name="Valid Workflow"),
        definitions={
            "agent1": AgentDefinition(
                id="agent1",
                name="Agent 1",
                role="tester",
                goal="test"
            )
        },
        workflow=Workflow(
            start="step1",
            steps={
                "step1": AgentStep(
                    id="step1",
                    agent="agent1"
                )
            }
        )
    )

    assert manifest.is_executable
    assert len(manifest.verify()) == 0
