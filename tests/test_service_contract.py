import pytest
from pydantic import ValidationError

from coreason_manifest import AgentRequest, ServiceContract


def test_agent_request_serialization() -> None:
    req = AgentRequest(query="Hello", conversation_id="123")
    dump = req.dump()
    assert dump["query"] == "Hello"
    assert dump["conversation_id"] == "123"
    assert dump["files"] == []
    assert dump["meta"] == {}


def test_service_contract_generation() -> None:
    schema = ServiceContract.generate_openapi()
    assert isinstance(schema, dict)

    # Check structure
    post = schema["post"]
    assert post["summary"] == "Invoke Agent"

    # Check Request Body
    req_body = post["requestBody"]["content"]["application/json"]["schema"]
    # ServiceRequest has request_id, context, payload
    assert "properties" in req_body
    assert "request_id" in req_body["properties"]
    assert "payload" in req_body["properties"]

    # Check Response
    resp_200 = post["responses"]["200"]["content"]["application/json"]["schema"]
    # ServiceResponse has request_id, created_at, output
    assert "properties" in resp_200
    assert "request_id" in resp_200["properties"]
    assert "output" in resp_200["properties"]


def test_agent_request_defaults() -> None:
    """Test that default values are correctly populated."""
    req = AgentRequest(query="Just checking")
    assert req.files == []
    assert req.conversation_id is None
    assert req.meta == {}

    dump = req.dump()
    assert dump["files"] == []
    # None fields are excluded by CoReasonBaseModel.dump(exclude_none=True)
    assert "conversation_id" not in dump
    assert dump["meta"] == {}


def test_agent_request_immutability() -> None:
    """Test that AgentRequest is frozen/immutable."""
    req = AgentRequest(query="Immutable?")
    with pytest.raises(ValidationError):
        # Mypy will complain about assignment to frozen field, so we use setattr
        # or just suppress the static error if running mypy, but here we run pytest.
        # But python sees it as attribute error if using slots, or validation error if pydantic.
        # Pydantic v2 raises ValidationError.
        req.query = "Changed"  # type: ignore


def test_agent_request_complex_meta() -> None:
    """Test AgentRequest with complex nested metadata."""
    meta = {
        "user_info": {"timezone": "UTC", "role": "admin"},
        "history": [1, 2, 3],
        "flags": {"experimental": True},
    }
    req = AgentRequest(query="Complex", meta=meta)
    dump = req.dump()
    assert dump["meta"]["user_info"]["timezone"] == "UTC"
    assert dump["meta"]["history"] == [1, 2, 3]


def test_agent_request_with_files() -> None:
    """Test AgentRequest with files list."""
    files = ["s3://bucket/file1.txt", "http://example.com/image.png"]
    req = AgentRequest(query="Analyze this", files=files)
    dump = req.dump()
    assert len(dump["files"]) == 2
    assert dump["files"][0] == "s3://bucket/file1.txt"


def test_service_contract_schema_details() -> None:
    """Deep check of the generated OpenAPI schema."""
    schema = ServiceContract.generate_openapi()

    # Check Content-Type keys
    assert "application/json" in schema["post"]["requestBody"]["content"]
    assert "application/json" in schema["post"]["responses"]["200"]["content"]

    # Check that the request body schema is indeed ServiceRequest
    # We can check for a known field of ServiceRequest like 'context'
    req_schema = schema["post"]["requestBody"]["content"]["application/json"]["schema"]
    properties = req_schema.get("properties", {})
    assert "context" in properties
    assert "request_id" in properties

    # Check strictness or other attributes if present
    # Pydantic v2 schemas usually have 'title': 'ServiceRequest'
    assert req_schema.get("title") == "ServiceRequest"
