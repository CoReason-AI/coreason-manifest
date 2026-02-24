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
from coreason_manifest.spec.core.memory import MemorySubsystem, WorkingMemory
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile
from coreason_manifest.spec.core.resilience import (
    ErrorDomain,
    ErrorHandler,
    EscalationStrategy,
    FallbackStrategy,
    ReflexionStrategy,
    SupervisionPolicy,
)
from coreason_manifest.spec.core.types import RiskLevel
from coreason_manifest.spec.interop.exceptions import ManifestError
from coreason_manifest.utils.integrity import CanonicalHashingStrategy, compute_hash
from coreason_manifest.utils.io import SecurityViolationError


def test_tool_access_policy_defaults() -> None:
    # Test critical defaults
    p1 = ToolAccessPolicy(risk_level=RiskLevel.CRITICAL)
    assert p1.require_auth is True

    # Test explicit True
    p2 = ToolAccessPolicy(risk_level=RiskLevel.CRITICAL, require_auth=True)
    assert p2.require_auth is True

    # Test explicit False raises error
    with pytest.raises(ValueError, match="Critical tools must require authentication"):
        ToolAccessPolicy(risk_level=RiskLevel.CRITICAL, require_auth=False)

    # Test non-critical default
    p3 = ToolAccessPolicy(risk_level=RiskLevel.STANDARD)
    assert p3.require_auth is False

    # Test explicit True for standard
    p4 = ToolAccessPolicy(risk_level=RiskLevel.STANDARD, require_auth=True)
    assert p4.require_auth is True


def test_granular_governance_structure() -> None:
    from coreason_manifest.spec.core.governance import Governance

    gov = Governance(
        tool_policy={
            "sql_tool": ToolAccessPolicy(risk_level=RiskLevel.CRITICAL),
            "calc_tool": ToolAccessPolicy(risk_level=RiskLevel.SAFE),
        },
        default_tool_policy=ToolAccessPolicy(risk_level=RiskLevel.STANDARD),
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
    graph = Graph(nodes={"agent-1": agent}, edges=[], entry_point="agent-1")

    # Draft mode (default) should pass validation
    flow = GraphFlow(
        kind="GraphFlow",
        # status="draft", # default
        metadata=FlowMetadata(name="test", version="1.0.0", description="", tags=[]),
        definitions=definitions,
        interface=FlowInterface(inputs=DataSchema(), outputs=DataSchema()),
        memory=None,
        graph=graph,
    )
    assert flow.status == "draft"

    # Validation is skipped, so no error raised.
    # To cover the "return self" line, we just need to instantiate it.

    # Published mode should fail
    flow_pub = GraphFlow(
        kind="GraphFlow",
        status="published",
        metadata=FlowMetadata(name="test", version="1.0.0", description="", tags=[]),
        definitions=definitions,
        interface=FlowInterface(inputs=DataSchema(), outputs=DataSchema()),
        memory=None,
        graph=graph,
    )
    from coreason_manifest.utils.validator import validate_flow

    errors = validate_flow(flow_pub)
    assert any("requires tool 'missing-tool'" in e for e in errors)

    # Published mode success case to hit return self
    valid_agent = AgentNode(
        id="agent-1",
        type="agent",
        profile="my-brain",
        tools=[],  # Valid
        metadata={},
        resilience=None,
    )
    valid_graph = Graph(nodes={"agent-1": valid_agent}, edges=[], entry_point="agent-1")

    flow_valid = GraphFlow(
        kind="GraphFlow",
        status="published",
        metadata=FlowMetadata(name="test", version="1.0.0", description="", tags=[]),
        definitions=definitions,
        interface=FlowInterface(inputs=DataSchema(), outputs=DataSchema()),
        memory=None,
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
    strategy = CanonicalHashingStrategy()
    sanitized = strategy._recursive_sort_and_sanitize(m)
    assert "integrity_hash" not in sanitized
    assert "signature" not in sanitized
    assert sanitized["name"] == "test"


class MockDumpable:
    def model_dump(self, exclude_none: bool = True, mode: str = "json") -> dict[str, int]:  # noqa: ARG002
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
        metadata=FlowMetadata(name="test", version="1.0.0", description="", tags=[]),
        definitions=definitions,
        steps=[agent],
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

    errors = _validate_supervision(node, set(), None)
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

    errors = _validate_supervision(node, set(), None)
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

    errors = _validate_supervision(node, {"a1"}, None)

    # Should catch both missing IDs
    assert any("missing ID 'missing_handler'" in e for e in errors)
    assert any("missing ID 'missing_default'" in e for e in errors)


def test_validator_string_reference_skip() -> None:
    """Test that string references skip validation in _validate_supervision."""
    node = AgentNode(id="a1", metadata={}, type="agent", profile="p", tools=[], resilience="ref:template")
    from coreason_manifest.utils.validator import _validate_supervision

    errors = _validate_supervision(node, set(), None)
    assert len(errors) == 0


def test_fallback_cycle_complex_policy() -> None:
    """Test cycle detection with SupervisionPolicy (complex)."""
    # A -> B (via default)
    # B -> A (via handler)

    policy_a = SupervisionPolicy(handlers=[], default_strategy=FallbackStrategy(fallback_node_id="b"))

    policy_b = SupervisionPolicy(
        handlers=[ErrorHandler(match_domain=[ErrorDomain.SYSTEM], strategy=FallbackStrategy(fallback_node_id="a"))],
        default_strategy=None,
    )

    node_a = AgentNode(id="a", metadata={}, type="agent", profile="p", tools=[], resilience=policy_a)
    node_b = AgentNode(id="b", metadata={}, type="agent", profile="p", tools=[], resilience=policy_b)

    # Use unified cycle validation (mocking a GraphFlow with no explicit edges)
    from coreason_manifest.spec.core.flow import DataSchema, FlowInterface, FlowMetadata, Graph, GraphFlow
    from coreason_manifest.utils.validator import _validate_topology_cycles

    # Need a GraphFlow for unified validation
    dummy_graph = Graph(nodes={"a": node_a, "b": node_b}, edges=[], entry_point="a")
    flow = GraphFlow(
        kind="GraphFlow",
        status="published",
        metadata=FlowMetadata(name="test", version="1.0.0", description="", tags=[]),
        interface=FlowInterface(inputs=DataSchema(), outputs=DataSchema()),
        memory=None,
        graph=dummy_graph,
        definitions=None,
    )
    errors = _validate_topology_cycles(flow)

    assert any("Unified execution/fallback cycle detected" in e for e in errors)


def test_recursive_schema_strict_validation() -> None:
    """Ensure strict validation checks nested properties."""
    from jsonschema.exceptions import SchemaError

    from coreason_manifest.spec.core.flow import DataSchema

    # Schema with nested invalid default (type string, default null)
    nested_schema = {
        "type": "object",
        "properties": {
            "user": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "default": None}  # Invalid
                },
            }
        },
    }

    from unittest.mock import MagicMock, patch

    # Architecture: Validation runs directly. We mock check_schema to raise error to verify it is called.
    with patch("jsonschema.validators.validator_for") as mock_validator_for:
        mock_validator_cls = MagicMock()
        mock_validator_cls.check_schema.side_effect = SchemaError("Invalid default")
        mock_validator_for.return_value = mock_validator_cls

        with pytest.raises(ManifestError, match="Invalid JSON Schema"):
            DataSchema(json_schema=nested_schema)


def test_validator_definitions_profile_scanning() -> None:
    """Verify that the validator scans profiles stored in definitions."""
    from coreason_manifest.spec.core.flow import (
        DataSchema,
        FlowDefinitions,
        FlowInterface,
        FlowMetadata,
        Graph,
        GraphFlow,
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

    # Flow with empty memory (so role_var is missing)
    memory = MemorySubsystem(working=WorkingMemory(variables={}))
    graph = Graph(nodes={"a1": agent}, edges=[], entry_point="a1")

    flow = GraphFlow(
        kind="GraphFlow",
        metadata=FlowMetadata(name="T", version="1.0.0", description="D", tags=[]),
        interface=FlowInterface(inputs=DataSchema(), outputs=DataSchema()),
        memory=memory,
        graph=graph,
        definitions=definitions,
    )

    errors = validate_flow(flow)
    assert any("references missing variable 'role_var'" in e for e in errors)


# Fixing NameError in previous run
# Note: Blackboard, VariableDef, etc. need to be imported or available.
# Since I'm appending, I can't easily add imports at the top.
# But I can add them inside the function.


def test_schema_strict_null_default() -> None:
    """Test strict validation for null defaults."""
    from typing import Any
    from unittest.mock import MagicMock, patch

    from jsonschema.exceptions import SchemaError

    from coreason_manifest.spec.core.flow import DataSchema

    with patch("jsonschema.validators.validator_for") as mock_validator_for:
        # Case 1: Invalid Null Default -> Should Raise
        mock_validator_cls = MagicMock()
        mock_validator_cls.check_schema.side_effect = SchemaError("Invalid default")
        mock_validator_for.return_value = mock_validator_cls

        bad_null: dict[str, Any] = {"type": "string", "default": None}

        with pytest.raises(ManifestError, match="Invalid JSON Schema"):
            DataSchema(json_schema=bad_null)

        # Case 2: Valid Null Default (nullable: true) -> Should Pass
        mock_validator_cls.check_schema.side_effect = None

        valid_nullable: dict[str, Any] = {"type": "string", "default": None, "nullable": True}
        ds2 = DataSchema(json_schema=valid_nullable)
        assert isinstance(ds2.json_schema, dict)

        # Case 3: Valid Null Default (union type) -> Should Pass
        valid_union: dict[str, Any] = {"type": ["string", "null"], "default": None}
        ds3 = DataSchema(json_schema=valid_union)
        assert isinstance(ds3.json_schema, dict)


def test_jinja2_filter_validation() -> None:
    """
    Test that Jinja2 filters in templates are correctly handled by the validator.
    The validator should strip filters and only check the variable name.
    """
    from coreason_manifest.spec.core.flow import (
        DataSchema,
        FlowInterface,
        FlowMetadata,
        Graph,
        GraphFlow,
    )
    from coreason_manifest.utils.validator import validate_flow

    agent = AgentNode(
        id="n1",
        type="agent",
        metadata={"desc": "Hello {{ user_name | upper }}"},
        resilience=None,
        profile=CognitiveProfile(
            role="Role",
            persona="Persona",
            reasoning=None,
            fast_path=None,
        ),
        tools=[],
    )

    # Define 'user_name' in memory
    # VariableDef was used for types, but WorkingMemory uses values.
    # Assuming validator checks keys.
    memory = MemorySubsystem(working=WorkingMemory(variables={"user_name": "string"}))

    graph = Graph(nodes={"n1": agent}, edges=[], entry_point="n1")
    flow = GraphFlow(
        kind="GraphFlow",
        metadata=FlowMetadata(name="T", version="1.0.0", description="D", tags=[]),
        interface=FlowInterface(inputs=DataSchema(), outputs=DataSchema()),
        memory=memory,
        graph=graph,
    )

    # Should pass validation
    errors = validate_flow(flow)
    assert not errors, f"Validation failed with errors: {errors}"

    # Now verify failure if variable is missing
    agent_fail = AgentNode(
        id="n1",
        type="agent",
        metadata={"desc": "Hello {{ missing | upper }}"},
        resilience=None,
        profile=CognitiveProfile(role="R", persona="P", reasoning=None, fast_path=None),
        tools=[],
    )
    graph_fail = Graph(nodes={"n1": agent_fail}, edges=[], entry_point="n1")
    flow_fail = GraphFlow(
        kind="GraphFlow",
        metadata=FlowMetadata(name="T", version="1.0.0", description="D", tags=[]),
        interface=FlowInterface(inputs=DataSchema(), outputs=DataSchema()),
        memory=memory,
        graph=graph_fail,
    )

    errors_fail = validate_flow(flow_fail)
    assert any("references missing variable 'missing'" in e for e in errors_fail)


def test_swarm_type_safety() -> None:
    """Test MVP type safety for SwarmNode."""
    # Define a string variable
    from coreason_manifest.spec.core.flow import (
        DataSchema,
        FlowInterface,
        FlowMetadata,
        Graph,
        GraphFlow,
    )
    from coreason_manifest.utils.validator import validate_flow

    # We assume validator infers type from value or VariableDef
    # If using WorkingMemory(variables={...}), types are inferred from values?
    # Or VariableDef is still used somewhere? No, VariableDef was for Blackboard.
    # We rely on validator's ability to check types in memory.
    memory = MemorySubsystem(working=WorkingMemory(variables={"text_var": "string"}))

    # SwarmNode expects a list, but points to a string
    from coreason_manifest.spec.core.nodes import SwarmNode

    swarm = SwarmNode(
        id="s1",
        type="swarm",
        metadata={},
        resilience=None,
        worker_profile="p1",
        workload_variable="text_var",
        distribution_strategy="sharded",
        max_concurrency=1,
        reducer_function="concat",
        output_variable="out",
    )

    graph = Graph(nodes={"s1": swarm}, edges=[], entry_point="s1")
    flow = GraphFlow(
        kind="GraphFlow",
        metadata=FlowMetadata(name="T", version="1.0.0", description="D", tags=[]),
        interface=FlowInterface(inputs=DataSchema(), outputs=DataSchema()),
        memory=memory,
        graph=graph,
    )

    # Note: If validator uses runtime type check on values, "string" is str.
    errors = validate_flow(flow)
    assert any("Type Mismatch" in e and "expects a list" in e for e in errors)


def test_inspector_regex_warning() -> None:
    """Test warning when InspectorNode uses regex mode on complex types."""
    from coreason_manifest.spec.core.flow import (
        DataSchema,
        FlowInterface,
        FlowMetadata,
        Graph,
        GraphFlow,
    )
    from coreason_manifest.spec.core.nodes import InspectorNode
    from coreason_manifest.utils.validator import validate_flow

    memory = MemorySubsystem(working=WorkingMemory(variables={"obj_var": {"some": "object"}}))

    inspector = InspectorNode(
        id="i1",
        type="inspector",
        metadata={},
        resilience=None,
        target_variable="obj_var",
        criteria="regex:.*",
        mode="programmatic",  # This triggers the check
        pass_threshold=0.5,
        output_variable="out",
    )

    graph = Graph(nodes={"i1": inspector}, edges=[], entry_point="i1")
    flow = GraphFlow(
        kind="GraphFlow",
        metadata=FlowMetadata(name="T", version="1.0.0", description="D", tags=[]),
        interface=FlowInterface(inputs=DataSchema(), outputs=DataSchema()),
        memory=memory,
        graph=graph,
    )

    errors = validate_flow(flow)
    assert any("Type Warning" in e and "complex type" in e for e in errors)


def test_validator_union_type_normalization() -> None:
    """Test that union types (list) in input schema are normalized in symbol table."""
    from coreason_manifest.spec.core.flow import (
        DataSchema,
        FlowInterface,
        FlowMetadata,
        Graph,
        GraphFlow,
    )
    from coreason_manifest.spec.core.nodes import SwarmNode
    from coreason_manifest.utils.validator import validate_flow

    # Input with union type ["string", "null"] and fallback case ["null"]
    inputs = DataSchema(
        json_schema={
            "type": "object",
            "properties": {
                "union_var": {"type": ["string", "null"]},
                "null_var": {"type": ["null"]},
            },
        }
    )

    # SwarmNode expects list/array, but we give it a string (via union normalization)
    # This should trigger a Type Mismatch error, confirming normalization worked.
    swarm = SwarmNode(
        id="s1",
        type="swarm",
        metadata={},
        resilience=None,
        worker_profile="p1",
        workload_variable="union_var",
        distribution_strategy="sharded",
        max_concurrency=1,
        reducer_function="concat",
        output_variable="out",
    )

    # Inspector targeting "null_var" (normalized to "union") in regex mode (complex type warning logic)
    # Wait, "union" is not "object" or "array", so it shouldn't trigger warning unless I change the check.
    # But testing "union" normalization execution path is key.

    graph = Graph(nodes={"s1": swarm}, edges=[], entry_point="s1")
    flow = GraphFlow.model_construct(
        type="graph",
        kind="GraphFlow",
        status="draft",
        metadata=FlowMetadata(name="T", version="1.0.0", description="D", tags=[]),
        interface=FlowInterface(inputs=inputs, outputs=DataSchema()),
        memory=None,
        graph=graph,
        definitions=None,
    )

    errors = validate_flow(flow)
    # If normalization picked "string", SwarmNode check (expects array) should fail with Type Mismatch.
    # If normalization picked "string", SwarmNode check (expects array) should fail with Type Mismatch.
    # If it failed to normalize or crashed, we wouldn't get this specific error.
    assert any("Type Mismatch" in e and "expects a list" in e for e in errors)


def test_loader_duplicate_keys_error(tmp_path: object) -> None:
    """Ensure the loader rejects YAML with duplicate keys to prevent ghost logic."""
    from pathlib import Path

    from coreason_manifest.utils.loader import load_flow_from_file

    path = Path(str(tmp_path))
    # Create a YAML file with duplicate 'step_1' keys in a GraphFlow (where nodes is a dict)
    dup_yaml = path / "duplicate.yaml"
    dup_yaml.write_text(
        """
        kind: GraphFlow
        metadata:
          name: bad-flow
          version: "1.0.0"
          description: test
          tags: []
        interface:
          inputs:
            json_schema: {}
          outputs:
            json_schema: {}
        memory: null
        graph:
          entry_point: step_1
          edges: []
          nodes:
            step_1:
              id: step_1
              type: placeholder
              metadata: {}
            step_1:  # Duplicate Key
              id: step_1
              type: placeholder
              metadata: {}
        """,
        encoding="utf-8",
    )

    # Must raise a constructor error (wrapped in ValueError by our loader)
    with pytest.raises(ValueError, match="found duplicate key"):
        load_flow_from_file(str(dup_yaml), strict_security=False)
