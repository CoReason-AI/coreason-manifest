from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from coreason_manifest.definitions.request import AgentRequest, ClientCapabilities


def test_agent_request_defaults() -> None:
    session_id = uuid4()
    req = AgentRequest(session_id=session_id, payload={"input": "test"})

    assert req.request_id is not None
    assert req.session_id == session_id
    # Default logic: if root is None and parent is None -> root = request_id
    assert req.root_request_id == req.request_id
    assert req.parent_request_id is None
    assert isinstance(req.timestamp, datetime)
    assert req.payload == {"input": "test"}
    assert req.metadata == {}


def test_agent_request_full_trace() -> None:
    request_id = uuid4()
    session_id = uuid4()
    root_id = uuid4()
    parent_id = uuid4()

    req = AgentRequest(
        request_id=request_id, session_id=session_id, root_request_id=root_id, parent_request_id=parent_id, payload={}
    )

    assert req.request_id == request_id
    assert req.root_request_id == root_id
    assert req.parent_request_id == parent_id


def test_agent_request_missing_root_with_parent_error_wrapped() -> None:
    session_id = uuid4()
    parent_id = uuid4()

    with pytest.raises(ValidationError) as excinfo:
        AgentRequest(session_id=session_id, parent_request_id=parent_id, payload={})

    assert "Root ID missing while Parent ID is present" in str(excinfo.value)


def test_agent_request_json_serialization() -> None:
    session_id = uuid4()
    req = AgentRequest(session_id=session_id, payload={"foo": "bar"})

    json_str = req.to_json()
    assert str(session_id) in json_str
    assert "foo" in json_str

    # Test round trip
    data = req.dump()
    req2 = AgentRequest(**data)
    assert req2.request_id == req.request_id
    assert req2.root_request_id == req.root_request_id


def test_immutability() -> None:
    session_id = uuid4()
    req = AgentRequest(session_id=session_id, payload={})

    # Pydantic v2 frozen models raise ValidationError on assignment
    with pytest.raises(ValidationError):
        req.payload = {"new": "val"}  # type: ignore[misc]


def test_client_capabilities_serialization() -> None:
    session_id = uuid4()
    capabilities = ClientCapabilities(
        supported_events=["CITATION_BLOCK", "MEDIA_CAROUSEL"],
        prefers_markdown=False,
        image_resolution="high",
    )
    req = AgentRequest(
        session_id=session_id,
        payload={"input": "test"},
        capabilities=capabilities,
    )

    # Serialize
    json_str = req.to_json()
    assert "CITATION_BLOCK" in json_str
    assert "MEDIA_CAROUSEL" in json_str
    assert "high" in json_str

    # Deserialize
    data = req.dump()
    req2 = AgentRequest(**data)
    assert req2.capabilities is not None
    assert req2.capabilities.supported_events == ["CITATION_BLOCK", "MEDIA_CAROUSEL"]
    assert req2.capabilities.prefers_markdown is False
    assert req2.capabilities.image_resolution == "high"

    # Test defaults
    req_default = AgentRequest(session_id=session_id, payload={})
    assert req_default.capabilities is None
