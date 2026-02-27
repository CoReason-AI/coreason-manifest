# tests/contracts/test_schema_contracts.py

import json
import pytest
from pathlib import Path
from deepdiff import DeepDiff

from coreason_manifest.spec.core.flow import GraphFlow, LinearFlow, AgentRequest

# Define where snapshots are stored
SNAPSHOT_DIR = Path(__file__).parent / "fixtures"

@pytest.fixture(scope="session", autouse=True)
def ensure_snapshot_dir():
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

def check_schema_contract(model_class, schema_name):
    """
    Validates that the current JSON schema of the model matches the stored snapshot.
    If snapshot does not exist, it creates it (first run).
    """
    current_schema = model_class.model_json_schema()
    snapshot_path = SNAPSHOT_DIR / f"{schema_name}.json"

    if not snapshot_path.exists():
        # First run: Baseline generation
        snapshot_path.write_text(json.dumps(current_schema, indent=2, sort_keys=True))
        pytest.fail(f"Snapshot created for {schema_name}. Please rerun tests to verify contract.")

    # Contract Check
    stored_schema = json.loads(snapshot_path.read_text())

    # Ignore order in lists if it doesn't matter? Schema lists usually matter (enums, etc).
    # DeepDiff is strict.
    diff = DeepDiff(stored_schema, current_schema, ignore_order=False)

    if diff:
        pytest.fail(f"Schema Contract Broken for {schema_name}!\nDiff: {diff.to_json(indent=2)}")

def test_contract_graph_flow():
    check_schema_contract(GraphFlow, "v1_graphflow_schema")

def test_contract_linear_flow():
    check_schema_contract(LinearFlow, "v1_linearflow_schema")

def test_contract_agent_request():
    check_schema_contract(AgentRequest, "v1_agent_request_schema")
