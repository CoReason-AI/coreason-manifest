# Prosperity-3.0
import pytest
import os
from pathlib import Path
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from coreason_manifest.server import app, get_policy_path
from coreason_manifest.errors import PolicyViolationError, ManifestSyntaxError

client = TestClient(app)

# Sample valid manifest data
VALID_MANIFEST = {
    "metadata": {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "version": "1.0.0",
        "name": "Test Agent",
        "author": "Tester",
        "created_at": "2023-01-01T00:00:00Z"
    },
    "interface": {
        "inputs": {},
        "outputs": {}
    },
    "topology": {
        "steps": [
            {"id": "step1", "description": "Start"}
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
    "integrity_hash": "a" * 64
}

@patch("coreason_manifest.server.policy_enforcer")
def test_validate_manifest_success(mock_policy_enforcer):
    if mock_policy_enforcer:
        mock_policy_enforcer.evaluate.return_value = None

    response = client.post("/validate/manifest", json={"manifest": VALID_MANIFEST})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["tbom_id"] == VALID_MANIFEST["integrity_hash"]
    assert data["errors"] is None

def test_validate_manifest_schema_error():
    manifest = {**VALID_MANIFEST, "metadata": "invalid"}
    response = client.post("/validate/manifest", json={"manifest": manifest})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert any("Schema Error" in e for e in data["errors"])

def test_validate_manifest_model_error():
    with patch("coreason_manifest.server.ManifestLoader.load_from_dict") as mock_load:
        mock_load.side_effect = ManifestSyntaxError("Model Bad")
        response = client.post("/validate/manifest", json={"manifest": VALID_MANIFEST})
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "Model Error: Model Bad" in data["errors"]

@patch("coreason_manifest.server.policy_enforcer")
def test_validate_manifest_policy_violation(mock_policy_enforcer):
    mock_policy_enforcer.evaluate.side_effect = PolicyViolationError("Failed", violations=["Bad Tool"])
    response = client.post("/validate/manifest", json={"manifest": VALID_MANIFEST})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert "Policy Violation: Bad Tool" in data["errors"]

@patch("coreason_manifest.server.policy_enforcer")
def test_validate_manifest_policy_runtime_error(mock_policy_enforcer):
    mock_policy_enforcer.evaluate.side_effect = Exception("OPA Down")
    response = client.post("/validate/manifest", json={"manifest": VALID_MANIFEST})
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert "Policy Check Error: OPA Down" in data["errors"]

def test_validate_manifest_no_policy_enforcer():
    with patch("coreason_manifest.server.policy_enforcer", None):
        response = client.post("/validate/manifest", json={"manifest": VALID_MANIFEST})
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "Policy Enforcement unavailable" in data["errors"][0]

def test_get_schema():
    response = client.get("/schema/latest")
    assert response.status_code == 200
    schema = response.json()
    assert "$id" in schema

def test_get_policy_path_env():
    with patch.dict(os.environ, {"POLICY_PATH": "/tmp/env.rego"}):
        assert get_policy_path() == Path("/tmp/env.rego")

def test_get_policy_path_local():
    # Ensure env var is missing
    with patch.dict(os.environ, {}, clear=True):
        # We expect it to find the local one if it exists
        # In this env, src/coreason_manifest/policies/compliance.rego likely exists
        path = get_policy_path()
        assert path.name == "compliance.rego"
        assert "src" in str(path) or "site-packages" in str(path) or "policies" in str(path)

def test_get_policy_path_docker():
    # We clear env var so it doesn't match first check
    with patch.dict(os.environ, {}, clear=True):
        # We assume running on Linux where Path is PosixPath
        target = "pathlib.PosixPath.exists" if os.name == "posix" else "pathlib.WindowsPath.exists"
        # Actually easier to patch pathlib.Path.exists but purely relying on autospec=True to get self

        with patch("pathlib.Path.exists", autospec=True) as mock_exists:
            def side_effect(self):
                s = str(self)
                # Local check: usually contains "policies/compliance.rego" and parent check
                # We want local to fail
                if "compliance.rego" in s and ("src" in s or "site-packages" in s):
                    return False
                # Docker check
                if s == "/app/policies/compliance.rego":
                    return True
                return False

            mock_exists.side_effect = side_effect

            path = get_policy_path()
            assert str(path) == "/app/policies/compliance.rego"

def test_get_policy_path_not_found():
    with patch.dict(os.environ, {}, clear=True):
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(FileNotFoundError):
                get_policy_path()
