from pathlib import Path

from coreason_manifest.workflow.envelope import WorkflowEnvelope


def test_legacy_workflow_envelope_migration() -> None:
    fixture_path = Path("tests/fixtures/v0.24_workflow_legacy.json")
    with fixture_path.open("r", encoding="utf-8") as f:
        data = f.read()

    # Should not raise validation error
    env = WorkflowEnvelope.model_validate_json(data)
    assert env.manifest_version == "0.24.0"
    assert env.topology.type == "dag"
    assert env.topology.allow_cycles is False
