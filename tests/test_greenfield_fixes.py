import pytest
from pydantic import BaseModel

from coreason_manifest.builder import AgentBuilder, NewLinearFlow
from coreason_manifest.spec.core.flow import (
    DataSchema,
    FlowDefinitions,
    FlowInterface,
    FlowMetadata,
    Graph,
    GraphFlow,
    LinearFlow,
)
from coreason_manifest.spec.core.governance import ToolAccessPolicy
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile
from coreason_manifest.spec.core.resilience import (
    ErrorDomain,
    ErrorHandler,
    EscalationStrategy,
    FallbackStrategy,
    ReflexionStrategy,
    SupervisionPolicy,
)
from coreason_manifest.utils.integrity import _recursive_sort_and_sanitize, compute_hash
from coreason_manifest.utils.io import SecurityViolationError


def test_tool_access_policy_defaults() -> None:
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


def test_granular_governance_structure() -> None:
    from coreason_manifest.spec.core.governance import Governance

    gov = Governance(
        tool_policy={
            "sql_tool": ToolAccessPolicy(risk_level="critical"),
            "calc_tool": ToolAccessPolicy(risk_level="minimal"),
        },
        default_tool_policy=ToolAccessPolicy(risk_level="standard"),
    )
    assert gov.tool_policy is not None
    assert gov.tool_policy["sql_tool"].require_auth is True
    assert gov.tool_policy["calc_tool"].require_auth is False

    assert gov.default_tool_policy is not None
    assert gov.default_tool_policy.risk_level == "standard"


def test_graph_flow_draft_mode() -> None:
    # Create invalid graph (missing tool)
    brain = CognitiveProfile(role="assistant", persona="helper", reasoning=None, fast_path=None)
    definitions = FlowDefinitions(profiles={"my-brain": brain})
    agent = AgentNode(
        id="agent-1",
        type="agent",
        profile="my-brain",
        tools=["missing-tool"],
        metadata={},
        resilience=None,
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
        tools=[],  # Valid
        metadata={},
        resilience=None,
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


def test_security_violation_error() -> None:
    e = SecurityViolationError("Path bad", code="SEC_001")
    assert str(e) == "Security Error: [SEC_001] Path bad"

    e2 = SecurityViolationError("Path bad")
    assert str(e2) == "Security Error: Path bad"


class MockModel(BaseModel):
    name: str
    integrity_hash: str | None = None
    signature: str | None = None

    _hash_exclude_ = {"integrity_hash", "signature"}


def test_compute_hash_pydantic_exclusion() -> None:
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
    def model_dump(self, exclude_none: bool = True) -> dict[str, int]:
        if exclude_none:
            return {"a": 1}
        return {"a": 1}


def test_compute_hash_generic_dumpable() -> None:
    # Covers line 58 in integrity.py
    obj = MockDumpable()
    h = compute_hash(obj)
    assert h == compute_hash({"a": 1})


def test_coverage_agent_builder_recovery() -> None:
    """Test AgentBuilder.with_resilience and default create_resilience logic."""
    # Test fallback to escalate (lines 65-70)
    builder = AgentBuilder("agent-rec")
    builder.with_identity("r", "p")
    # Using 'escalate' default implied if not 'retry' or 'fallback'
    builder.with_resilience(retries=0, strategy="custom_escalate")

    agent = builder.build()
    assert isinstance(agent.resilience, EscalationStrategy)
    assert agent.resilience.notification_level == "warning"


def test_coverage_flow_builder_template() -> None:
    """Test define_supervision_template."""
    # Even if unused by nodes, the method exists
    lf = NewLinearFlow("Template Test")
    policy = SupervisionPolicy(handlers=[], default_strategy=None)
    lf.define_supervision_template("tpl", policy)
    assert lf._supervision_templates["tpl"] == policy


def test_coverage_linear_flow_published() -> None:
    """Test LinearFlow with status='published' to hit validate_integrity."""
    brain = CognitiveProfile(role="assistant", persona="helper", reasoning=None, fast_path=None)
    definitions = FlowDefinitions(profiles={"my-brain": brain})
    agent = AgentNode(
        id="agent-1",
        type="agent",
        profile="my-brain",
        tools=[],
        metadata={},
        resilience=None,
    )

    # Should pass validation
    LinearFlow(
        kind="LinearFlow",
        status="published",
        metadata=FlowMetadata(name="test", version="1", description="", tags=[]),
        definitions=definitions,
        sequence=[agent],
    )


def test_coverage_validator_reflexion_mismatch() -> None:
    """Test ReflexionStrategy on non-supported node type (via bypass)."""
    # Create invalid AgentNode type manually
    node = AgentNode.model_construct(
        id="a1",
        type="invalid_type",  # type: ignore
        resilience=ReflexionStrategy(max_attempts=3, critic_model="gpt-4", critic_prompt="fix", include_trace=True),
        metadata={},
        profile="p",
        tools=[],
    )

    # Run validation logic manually
    from coreason_manifest.utils.validator import _validate_supervision

    errors = _validate_supervision(node, set())
    # Note: _validate_supervision checks node.resilience, which we set.
    assert any("uses ReflexionStrategy but is of type 'invalid_type'" in e for e in errors)


def test_coverage_validator_escalation_empty_queue() -> None:
    """Test EscalationStrategy with empty queue via bypass."""
    # EscalationStrategy model validation prevents empty string if we used min_length=1.
    # So we use model_construct.

    esc = EscalationStrategy.model_construct(
        type="escalate", queue_name="", notification_level="info", timeout_seconds=10
    )

    node = AgentNode(id="a1", metadata={}, type="agent", profile="p", tools=[], resilience=esc)

    from coreason_manifest.utils.validator import _validate_supervision

    errors = _validate_supervision(node, set())
    assert any("empty queue_name" in e for e in errors)


def test_supervision_policy_complex_validation() -> None:
    """Test validation of SupervisionPolicy (complex) in resilience field."""
    # Create a complex policy with a fallback strategy that points to a missing node
    complex_policy = SupervisionPolicy(
        handlers=[
            ErrorHandler(
                match_domain=[ErrorDomain.SYSTEM], strategy=FallbackStrategy(fallback_node_id="missing_handler")
            )
        ],
        default_strategy=FallbackStrategy(fallback_node_id="missing_default"),
    )

    node = AgentNode(id="a1", metadata={}, type="agent", profile="p", tools=[], resilience=complex_policy)

    from coreason_manifest.utils.validator import _validate_supervision

    errors = _validate_supervision(node, {"a1"})

    # Should catch both missing IDs
    assert any("missing ID 'missing_handler'" in e for e in errors)
    assert any("missing ID 'missing_default'" in e for e in errors)


def test_validator_string_reference_skip() -> None:
    """Test that string references skip validation in _validate_supervision."""
    node = AgentNode(id="a1", metadata={}, type="agent", profile="p", tools=[], resilience="ref:template")
    from coreason_manifest.utils.validator import _validate_supervision

    errors = _validate_supervision(node, set())
    assert len(errors) == 0


def test_fallback_cycle_complex_policy() -> None:
    """Test cycle detection with SupervisionPolicy (complex)."""
    from coreason_manifest.utils.validator import _validate_fallback_cycles

    # A -> B (via default)
    # B -> A (via handler)

    policy_a = SupervisionPolicy(handlers=[], default_strategy=FallbackStrategy(fallback_node_id="b"))

    policy_b = SupervisionPolicy(
        handlers=[ErrorHandler(match_domain=[ErrorDomain.SYSTEM], strategy=FallbackStrategy(fallback_node_id="a"))],
        default_strategy=None,
    )

    node_a = AgentNode(id="a", metadata={}, type="agent", profile="p", tools=[], resilience=policy_a)
    node_b = AgentNode(id="b", metadata={}, type="agent", profile="p", tools=[], resilience=policy_b)

    errors = _validate_fallback_cycles([node_a, node_b])
    assert any("Fallback cycle detected" in e for e in errors)

def test_recursive_schema_repair() -> None:
    """Ensure schema repair traverses nested properties."""
    from coreason_manifest.spec.core.flow import DataSchema

    # Schema with nested invalid default (type string, default null)
    nested_schema = {
        "type": "object",
        "properties": {
            "user": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "default": None}  # Invalid
                }
            }
        }
    }

    from unittest.mock import patch
    from jsonschema.exceptions import SchemaError

    with patch("jsonschema.Draft7Validator.check_schema") as mock_check:
        mock_check.side_effect = [SchemaError("Simulated"), None]

        with pytest.warns(UserWarning, match="Schema repaired"):
            ds = DataSchema(json_schema=nested_schema)

    # Assert repair happened deep in the tree
    user_props = ds.json_schema["properties"]["user"]["properties"]
    assert "default" not in user_props["name"]


def test_validator_definitions_profile_scanning() -> None:
    """Verify that the validator scans profiles stored in definitions."""
    from coreason_manifest.spec.core.flow import (
        Blackboard,
        DataSchema,
        FlowDefinitions,
        FlowInterface,
        FlowMetadata,
        Graph,
        GraphFlow,
        VariableDef,
    )
    from coreason_manifest.utils.validator import validate_flow

    # Define a profile with a variable
    definitions = FlowDefinitions(
        profiles={
            "my-profile": CognitiveProfile(
                role="Role {{ role_var }}",
                persona="Persona",
                reasoning=None,
                fast_path=None,
            )
        }
    )

    # Agent referencing that profile
    agent = AgentNode(
        id="a1",
        type="agent",
        metadata={},
        resilience=None,
        profile="my-profile",
        tools=[],
    )

    # Flow with empty blackboard (so role_var is missing)
    blackboard = Blackboard(variables={}, persistence=False)
    graph = Graph(nodes={"a1": agent}, edges=[])

    flow = GraphFlow(
        kind="GraphFlow",
        metadata=FlowMetadata(name="T", version="1", description="D", tags=[]),
        interface=FlowInterface(inputs=DataSchema(), outputs=DataSchema()),
        blackboard=blackboard,
        graph=graph,
        definitions=definitions
    )

    errors = validate_flow(flow)
    assert any("references missing variable 'role_var'" in e for e in errors)

# Fixing NameError in previous run
# Note: Blackboard, VariableDef, etc. need to be imported or available.
# Since I'm appending, I can't easily add imports at the top.
# But I can add them inside the function.
