from coreason_manifest.workflow.envelope import WorkflowEnvelope
from pathlib import Path

def test_migration() -> None:
    fixture_path = Path("tests/fixtures/v0.24_workflow_legacy.json")
    with fixture_path.open("r", encoding="utf-8") as f:
        data = f.read()

    envelope = WorkflowEnvelope.model_validate_json(data)
    assert envelope.manifest_version == "0.24.0"
