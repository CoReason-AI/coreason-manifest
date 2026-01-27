from pathlib import Path
from typing import Any, Dict, Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from coreason_manifest.server import app

@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c

# Minimal valid manifest
VALID_MANIFEST: Dict[str, Any] = {
    "metadata": {
        "id": "12345678-1234-5678-1234-567812345678",
        "version": "1.0.0",
        "name": "Test Agent",
        "author": "Test Author",
        "created_at": "2023-10-27T10:00:00Z",
    },
    "interface": {
        "inputs": {"type": "object", "properties": {"query": {"type": "string"}}},
        "outputs": {"type": "object", "properties": {"result": {"type": "string"}}},
    },
    "topology": {
        "steps": [
            {"id": "step1", "description": "A valid step description."}
        ],
        "model_config": {
            "model": "gpt-4",
            "temperature": 0.5
        }
    },
    "dependencies": {
        "tools": [],
        "libraries": []
    },
    "integrity_hash": "a" * 64,
}


def test_health_check(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"
    assert "policy_version" in data


def test_validate_valid_manifest(client: TestClient) -> None:
    # We rely on the mock OPA runner provided by conftest.py
    # and the policy files in src/coreason_manifest/policies/
    response = client.post("/validate", json=VALID_MANIFEST)
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["agent_id"] == VALID_MANIFEST["metadata"]["id"]
    assert data["version"] == "1.0.0"
    assert data["policy_violations"] == []


def test_validate_invalid_json(client: TestClient) -> None:
    response = client.post("/validate", content="invalid json")
    assert response.status_code == 400


def test_validate_invalid_schema(client: TestClient) -> None:
    invalid_manifest = VALID_MANIFEST.copy()
    invalid_manifest["metadata"] = "invalid_type"  # Should be dict

    response = client.post("/validate", json=invalid_manifest)
    # The SchemaValidator raises ManifestSyntaxError, which we map to 422
    assert response.status_code == 422
    data = response.json()
    assert data["valid"] is False
    assert len(data["policy_violations"]) > 0
    assert "Syntax Error" in data["policy_violations"][0]


def test_validate_policy_violation(client: TestClient) -> None:
    # Trigger a policy violation
    # Rule: Description too short (< 5 chars)
    invalid_manifest = VALID_MANIFEST.copy()
    invalid_manifest["topology"] = VALID_MANIFEST["topology"].copy()
    invalid_manifest["topology"]["steps"] = [
        {"id": "step1", "description": "Bad"} # < 5 chars
    ]

    response = client.post("/validate", json=invalid_manifest)
    assert response.status_code == 422
    data = response.json()
    assert data["valid"] is False
    assert len(data["policy_violations"]) > 0
    # The actual message depends on the mock OPA runner or real policy
    # MockOPARunner in conftest checks for "Step description is too short."
    assert "Step description is too short." in data["policy_violations"]


def test_validate_integrity_skipped(client: TestClient) -> None:
    # The integrity hash in VALID_MANIFEST is dummy ("a"*64).
    # If IntegrityChecker was running, it would fail because it can't hash memory content against source dir.
    # The server logic skips IntegrityChecker.verify.
    # So the dummy hash should be accepted (as long as it matches regex schema).

    response = client.post("/validate", json=VALID_MANIFEST)
    assert response.status_code == 200
    assert response.json()["valid"] is True


def test_server_health_check_exception(client: TestClient) -> None:
    # Mock open() to raise Exception when reading policy
    # We need to ensure we are patching the correct open call
    # The code uses 'with open(...)'.
    with patch("builtins.open", side_effect=Exception("Disk Error")):
         response = client.get("/health")
         assert response.status_code == 200
         data = response.json()
         assert data["status"] == "active"
         assert data["policy_version"] == "unknown"


def test_server_lifespan_failure_missing_policy() -> None:
    # We must start a fresh client/app to trigger lifespan again
    # Use patch to hide all policy files
    with patch("pathlib.Path.exists", return_value=False):
        # Also hide resources
        with patch("importlib.resources.files") as mock_files:
             mock_files.return_value.joinpath.return_value.is_file.return_value = False

             with pytest.raises(RuntimeError, match="Could not locate compliance.rego"):
                  with TestClient(app):
                      pass


def test_server_lifespan_resource_fallback() -> None:
    # Mock Path.exists to return False so we hit the resource fallback
    with patch("pathlib.Path.exists", return_value=False):
        with patch("importlib.resources.files") as mock_files:
             # Mock the resource lookup
             mock_ref = MagicMock()
             mock_ref.is_file.return_value = True
             mock_files.return_value.joinpath.return_value = mock_ref

             # Mock as_file context manager
             mock_ctx = MagicMock()
             mock_ctx.__enter__.return_value = Path("/tmp/mock_policy.rego")

             with patch("importlib.resources.as_file", return_value=mock_ctx):
                  # Mock ManifestEngineAsync to prevent real initialization failure
                  with patch("coreason_manifest.server.ManifestEngineAsync") as MockEngine:
                       mock_engine_instance = MockEngine.return_value
                       # Mock engine context manager
                       mock_engine_instance.__aenter__.return_value = mock_engine_instance
                       mock_engine_instance.__aexit__.return_value = None

                       with TestClient(app) as c:
                           # Trigger startup
                           pass

                       # Verify context manager usage
                       mock_ctx.__enter__.assert_called()
                       mock_ctx.__exit__.assert_called()


def test_server_lifespan_resource_fallback_exception() -> None:
    # Mock Path.exists to return False
    with patch("pathlib.Path.exists", return_value=False):
        with patch("importlib.resources.files") as mock_files:
             mock_ref = MagicMock()
             mock_ref.is_file.return_value = True
             mock_files.return_value.joinpath.return_value = mock_ref

             # Mock as_file to raise exception
             with patch("importlib.resources.as_file", side_effect=Exception("Resource Error")):
                  # Should fail to locate policy
                  with pytest.raises(RuntimeError, match="Could not locate compliance.rego"):
                       with TestClient(app):
                           pass
