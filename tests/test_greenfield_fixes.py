
import pytest
from pydantic import ValidationError
from datetime import datetime

from coreason_manifest.spec.core.governance import ToolAccessPolicy, Governance
from coreason_manifest.spec.core.flow import GraphFlow, FlowMetadata, FlowDefinitions, FlowInterface, DataSchema, Blackboard, Graph, AgentNode, CognitiveProfile
from coreason_manifest.utils.io import SecurityViolationError
from coreason_manifest.utils.integrity import compute_hash, _recursive_sort_and_sanitize
from pydantic import BaseModel

def test_tool_access_policy_defaults():
    # Test critical defaults
    p1 = ToolAccessPolicy(risk_level="critical")
    assert p1.require_auth is True

    # Test explicit True
    p2 = ToolAccessPolicy(risk_level="critical", require_auth=True)
    assert p2.require_auth is True

    # Test explicit False raises error
    with pytest.raises(ValueError, match="Critical tools must require authentication"):
        ToolAccessPolicy(risk_level="critical", require_auth=False)

    # Test non-critical default
    p3 = ToolAccessPolicy(risk_level="standard")
    assert p3.require_auth is False

    # Test explicit True for standard
    p4 = ToolAccessPolicy(risk_level="standard", require_auth=True)
    assert p4.require_auth is True

def test_graph_flow_draft_mode():
    # Create invalid graph (missing tool)
    brain = CognitiveProfile(role="assistant", persona="helper", reasoning=None, fast_path=None)
    definitions = FlowDefinitions(profiles={"my-brain": brain})
    agent = AgentNode(
        id="agent-1",
        type="agent",
        profile="my-brain",
        tools=["missing-tool"],
        metadata={},
        supervision=None,
    )
    graph = Graph(nodes={"agent-1": agent}, edges=[])

    # Draft mode (default) should pass validation
    flow = GraphFlow(
        kind="GraphFlow",
        # status="draft", # default
        metadata=FlowMetadata(name="test", version="1", description="", tags=[]),
        definitions=definitions,
        interface=FlowInterface(inputs=DataSchema(), outputs=DataSchema()),
        blackboard=None,
        graph=graph,
    )
    assert flow.status == "draft"

    # Validation is skipped, so no error raised.
    # To cover the "return self" line, we just need to instantiate it.

    # Published mode should fail
    with pytest.raises(ValueError, match="requires missing tool"):
        GraphFlow(
            kind="GraphFlow",
            status="published",
            metadata=FlowMetadata(name="test", version="1", description="", tags=[]),
            definitions=definitions,
            interface=FlowInterface(inputs=DataSchema(), outputs=DataSchema()),
            blackboard=None,
            graph=graph,
        )

    # Published mode success case to hit return self
    valid_agent = AgentNode(
        id="agent-1",
        type="agent",
        profile="my-brain",
        tools=[], # Valid
        metadata={},
        supervision=None,
    )
    valid_graph = Graph(nodes={"agent-1": valid_agent}, edges=[])

    flow_valid = GraphFlow(
        kind="GraphFlow",
        status="published",
        metadata=FlowMetadata(name="test", version="1", description="", tags=[]),
        definitions=definitions,
        interface=FlowInterface(inputs=DataSchema(), outputs=DataSchema()),
        blackboard=None,
        graph=valid_graph,
    )
    assert flow_valid.status == "published"

def test_security_violation_error():
    e = SecurityViolationError("Path bad", code="SEC_001")
    assert str(e) == "Security Error: [SEC_001] Path bad"

    e2 = SecurityViolationError("Path bad")
    assert str(e2) == "Security Error: Path bad"

class MockModel(BaseModel):
    name: str
    integrity_hash: str | None = None
    signature: str | None = None

def test_compute_hash_pydantic_exclusion():
    m = MockModel(name="test", integrity_hash="hash123", signature="sig456")

    # Compute hash should match hash of {"name": "test"}
    h1 = compute_hash(m)

    # Manual dict without excluded fields
    h2 = compute_hash({"name": "test"})

    assert h1 == h2

    # Ensure integrity_hash would change hash if included
    # We can verify _recursive_sort_and_sanitize logic
    sanitized = _recursive_sort_and_sanitize(m)
    assert "integrity_hash" not in sanitized
    assert "signature" not in sanitized
    assert sanitized["name"] == "test"

class MockDumpable:
    def model_dump(self, exclude_none=True):
        return {"a": 1}

def test_compute_hash_generic_dumpable():
    # Covers line 58 in integrity.py
    obj = MockDumpable()
    h = compute_hash(obj)
    assert h == compute_hash({"a": 1})
