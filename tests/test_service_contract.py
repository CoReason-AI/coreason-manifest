import pytest
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
