from fastapi.testclient import TestClient

from coreason_manifest.server import app

client = TestClient(app)


def test_validate_shared_valid() -> None:
    """Test the /validate/shared endpoint with valid data."""
    valid_payload = {
        "schema_version": "1.0",
        "name": "test-agent",
        "version": "1.0.0",
        "model_config": "gpt-4",
        "max_cost_limit": 10.0,
        "temperature": 0.5,
        "topology": "path/to/topology.yaml",
    }
    response = client.post("/validate/shared", json=valid_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["agent_id"] == "test-agent"
    assert data["version"] == "1.0.0"


def test_validate_shared_invalid() -> None:
    """Test the /validate/shared endpoint with invalid data."""
    invalid_payload = {
        "schema_version": "1.0",
        "name": "Invalid_Name",  # Bad name regex
        "version": "1.0.0",
        "model_config": "gpt-4",
        "max_cost_limit": 10.0,
        "topology": "path/to/topology.yaml",
    }
    response = client.post("/validate/shared", json=invalid_payload)
    # The endpoint catches ValidationError and returns 422
    assert response.status_code == 422
    data = response.json()
    assert data["valid"] is False
    assert "Schema Error" in data["policy_violations"][0]


def test_validate_shared_invalid_json() -> None:
    """Test the /validate/shared endpoint with malformed JSON."""
    response = client.post("/validate/shared", content="invalid-json")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid JSON body"
