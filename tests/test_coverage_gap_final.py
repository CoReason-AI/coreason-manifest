from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel, ValidationError

from coreason_manifest.builder import AgentBuilder, BaseFlowBuilder
from coreason_manifest.spec.core.engines import ModelCriteria
from coreason_manifest.spec.core.flow import GraphFlow
from coreason_manifest.spec.core.governance import Governance, ToolAccessPolicy
from coreason_manifest.spec.core.resilience import EscalationStrategy, ReflexionStrategy, ResilienceStrategy
from coreason_manifest.spec.core.tools import ToolCapability
from coreason_manifest.spec.core.types import RiskLevel
from coreason_manifest.utils.validator import _validate_kill_switch

# --- Builder Coverage ---


def test_base_builder_abstract_methods() -> None:
    # Test that calling abstract methods raises NotImplementedError
    builder = BaseFlowBuilder(name="t", version="1", description="d")
    with pytest.raises(NotImplementedError):
        builder._register_node(MagicMock())
    with pytest.raises(NotImplementedError):
        builder._create_flow_instance()


def test_agent_builder_partial() -> None:
    # Test AgentBuilder partially built state logic
    ab = AgentBuilder("a1")
    ab.with_identity("role", "persona")
    # Missing reasoning/fast_path is allowed by constructor but let's check basic build
    node = ab.build()
    from coreason_manifest.spec.core.nodes import CognitiveProfile

    assert isinstance(node.profile, CognitiveProfile)
    assert node.profile.role == "role"


# --- Governance Coverage ---


def test_tool_access_policy_require_auth_defaults() -> None:
    # Case 1: Critical -> require_auth must be True (defaulting)
    t1 = ToolAccessPolicy.model_validate({"risk_level": RiskLevel.CRITICAL})
    assert t1.require_auth is True

    # Case 2: Critical + require_auth=False -> Error
    with pytest.raises(ValueError, match="Critical tools must require authentication"):
        ToolAccessPolicy.model_validate({"risk_level": RiskLevel.CRITICAL, "require_auth": False})

    # Case 3: Standard -> require_auth defaults to False if None
    t3 = ToolAccessPolicy.model_validate({"risk_level": RiskLevel.STANDARD})
    assert t3.require_auth is False


# --- Resilience Coverage ---


def test_resilience_strategy_name_slug_validation() -> None:
    # Valid
    ResilienceStrategy(name="valid-slug_1")
    # Invalid
    with pytest.raises(ValueError, match="Strategy name must be lowercase"):
        ResilienceStrategy(name="Invalid Slug")


def test_escalation_template_warning() -> None:
    # Warning logic coverage (no {{ }})
    # Since it's a pass in code, just ensuring it runs without error
    EscalationStrategy(queue_name="q", notification_level="info", timeout_seconds=10, template="static string")


def test_reflexion_capabilities_validation() -> None:
    # ReflexionStrategy validates critic_model capabilities if schema present

    # Fail case - capabilities enum requires 'function_calling' not 'chat'
    # Actually, we want to fail because 'json_mode' is missing.
    # ModelCriteria capabilities are Literal['vision', 'coding', 'json_mode', 'function_calling']
    # So we pass a valid capability that isn't json_mode
    model_crit = ModelCriteria(capabilities=["function_calling"])
    with pytest.raises(ValueError, match="does not explicitly require 'json_mode'"):
        ReflexionStrategy(
            max_attempts=1,
            critic_model=model_crit,
            critic_prompt="p",
            critic_schema={"type": "object", "properties": {}},
        )


# --- Integrity Coverage ---


def test_integrity_float_success() -> None:
    from coreason_manifest.utils.integrity import compute_hash

    # compute_hash on float invokes is_finite check
    assert isinstance(compute_hash(1.5), str)


# --- Validator Coverage ---


def test_validator_kill_switch_weight_check() -> None:
    # Cover the specific line: obj.risk_level.weight > max_risk.weight
    # Need a tool with CRITICAL risk vs Governance STANDARD

    # Critical tools require description
    tool = ToolCapability(name="nuke", risk_level=RiskLevel.CRITICAL, description="Nukes the DB")
    # Mocking just enough
    GraphFlow.model_construct(
        governance=Governance(max_risk_level=RiskLevel.STANDARD),
        graph=None,  # type: ignore # Mocking
    )

    # We call the internal validator helper via public API if possible, or mock
    # Public API validate_flow -> _validate_kill_switch
    # But to target the exact line, we can rely on existing test_risk_governance.py which covers this.
    # If coverage missed it, maybe it wasn't hitting the 'isinstance(obj, ToolCapability)' branch?
    # Let's ensure we pass a ToolCapability object into the recursion.

    # Construct a flow that DEFINES a tool capability in definitions
    from coreason_manifest.spec.core.flow import FlowDefinitions
    from coreason_manifest.spec.core.tools import ToolPack

    defs = FlowDefinitions(
        tool_packs={"p": ToolPack(kind="ToolPack", namespace="ns", tools=[tool], dependencies=[], env_vars=[])}
    )

    # Mock get_unified_topology to return nothing so we focus on definitions scan
    with patch("coreason_manifest.utils.validator.get_unified_topology", return_value=([], [])):
        errors = _validate_kill_switch(
            GraphFlow.model_construct(
                governance=Governance(max_risk_level=RiskLevel.STANDARD),
                definitions=defs,
                graph=None,  # type: ignore # Mocking
            )
        )

    assert any("exceeds the global max_risk_level" in e.message for e in errors)


# --- Visualizer Coverage ---


def test_to_mermaid_unknown_flow_type() -> None:
    from coreason_manifest.utils.visualizer import to_mermaid
    # Pass a mock object that isn't Linear/GraphFlow
    # Actually, we need to pass the type check, or trick it.
    # to_mermaid types hint GraphFlow | LinearFlow.
    # If we pass MagicMock, it will fail runtime isinstance checks and return "".
    # But wait, topology.get_unified_topology raises ValueError for unknown types first!
    # So we need to mock get_unified_topology to return nodes/edges,
    # then let to_mermaid hit the isinstance(flow, ...) checks.

    with patch("coreason_manifest.utils.visualizer.get_unified_topology", return_value=([], [])):
        # Now it proceeds to isinstance check
        # We pass a mock that is NOT GraphFlow/LinearFlow
        assert to_mermaid(MagicMock()) == ""


# --- Additional Coverage ---


def test_error_handler_regex_validation() -> None:
    from coreason_manifest.spec.core.resilience import ErrorHandler, RetryStrategy

    # Valid
    ErrorHandler(match_pattern=r"^Error.*", strategy=RetryStrategy(max_attempts=1))

    # Invalid Regex
    with pytest.raises(ValueError, match="Invalid regex pattern"):
        ErrorHandler(match_pattern="[", strategy=RetryStrategy(max_attempts=1))


def test_error_handler_security_retry() -> None:
    from coreason_manifest.spec.core.resilience import ErrorDomain, ErrorHandler, RetryStrategy

    # Security + Retry = Forbidden
    with pytest.raises(ValueError, match="Security Policy Violation"):
        ErrorHandler(match_domain=[ErrorDomain.SECURITY], strategy=RetryStrategy(max_attempts=1))


def test_supervision_limits_validation() -> None:
    from coreason_manifest.spec.core.resilience import ErrorDomain, ErrorHandler, RetryStrategy, SupervisionPolicy

    # Strategy max_attempts > Global max_cumulative_actions
    s = RetryStrategy(max_attempts=10)
    h = ErrorHandler(match_domain=[ErrorDomain.SYSTEM], strategy=s)

    with pytest.raises(ValueError, match="SupervisionPolicy global limit"):
        SupervisionPolicy(handlers=[h], max_cumulative_actions=5)


def test_builder_circuit_breaker_update() -> None:
    from coreason_manifest.builder import NewLinearFlow
    from coreason_manifest.spec.core.governance import Governance

    # Init with governance None
    b = NewLinearFlow("t")
    assert b.governance is None

    # Set CB creates governance
    b.set_circuit_breaker(1, 1)
    assert b.governance is not None
    assert b.governance.circuit_breaker is not None

    # Set CB updates existing governance
    # Manually set a different field first
    b.governance = Governance(max_risk_level=RiskLevel.SAFE, circuit_breaker=None)
    b.set_circuit_breaker(5, 5)
    assert b.governance.max_risk_level == RiskLevel.SAFE
    assert b.governance.circuit_breaker.error_threshold_count == 5


def test_validator_governance_fallback_check() -> None:
    # utils/validator.py line 350
    # Condition: gov.circuit_breaker is set, but fallback_node_id is NOT in valid_ids

    from coreason_manifest.spec.core.governance import CircuitBreaker

    # Governance with fallback "b" (missing)
    gov = Governance(
        circuit_breaker=CircuitBreaker(error_threshold_count=1, reset_timeout_seconds=1, fallback_node_id="b")
    )

    # The issue might be that validate_flow does not call _validate_governance properly
    # or valid_ids is not what we expect.
    # GraphFlow logic constructs valid_ids from get_unified_topology.
    # We will invoke the helper directly to confirm it catches the error given the inputs.
    from coreason_manifest.utils.validator import _validate_governance

    errors = _validate_governance(gov, valid_ids={"a"})
    assert any(e.code == "ERR_GOV_CIRCUIT_FALLBACK_MISSING" for e in errors)


class SecretModel(BaseModel):
    public: int
    secret: int
    _hash_exclude_ = {"secret"}


def test_integrity_pydantic_exclude() -> None:
    # integrity.py line 90: excludes = getattr(obj, "_hash_exclude_", None)
    from coreason_manifest.utils.integrity import compute_hash

    m = SecretModel(public=1, secret=999)
    # Hash should only include public
    h1 = compute_hash(m)

    m2 = SecretModel(public=1, secret=888)  # Different secret
    h2 = compute_hash(m2)

    assert h1 == h2


class MockDuckModel:
    def model_dump(self, **_kwargs: dict[str, Any]) -> dict[str, bool]:
        return {"duck": True}


def test_integrity_duck_typing() -> None:
    # integrity.py line 90: hasattr(obj, "model_dump") without inheriting BaseModel
    from coreason_manifest.utils.integrity import compute_hash

    obj = MockDuckModel()
    h = compute_hash(obj)
    h2 = compute_hash({"duck": True})
    assert h == h2


def test_builder_resilience_helper_strategies() -> None:
    # builder.py 63, 67, 73
    from coreason_manifest.builder import create_resilience
    from coreason_manifest.spec.core.resilience import EscalationStrategy, FallbackStrategy, RetryStrategy

    # Test Retry
    r1 = create_resilience(3, strategy="retry", backoff=1.5, delay=0.1)
    assert isinstance(r1, RetryStrategy)
    assert r1.max_attempts == 3

    # Test Fallback
    r2 = create_resilience(1, strategy="fallback", fallback_id="fb")
    assert isinstance(r2, FallbackStrategy)
    assert r2.fallback_node_id == "fb"

    # Test Fallback missing ID (ValueError)
    with pytest.raises(ValueError, match="fallback_id is required"):
        create_resilience(1, strategy="fallback")

    # Test Default (Escalate)
    r3 = create_resilience(1, strategy="unknown")
    assert isinstance(r3, EscalationStrategy)


def test_telemetry_request_id_gen() -> None:
    # telemetry.py line 92
    from datetime import datetime

    from coreason_manifest.spec.interop.telemetry import NodeExecution, NodeState

    # Missing request_id -> auto-generated
    ne = NodeExecution(
        node_id="n1", state=NodeState.COMPLETED, inputs={}, outputs={}, timestamp=datetime.now(), duration_ms=1
    )
    assert ne.request_id is not None
    assert len(ne.request_id) > 0


def test_integrity_hash_none_strip() -> None:
    # integrity.py line 90
    from coreason_manifest.utils.integrity import compute_hash

    # Dict with None value -> Key should be stripped before hashing
    # Hash of {"a": 1, "b": None} should equal hash of {"a": 1}
    h1 = compute_hash({"a": 1, "b": None})
    h2 = compute_hash({"a": 1})
    assert h1 == h2


def test_error_handler_empty_criteria() -> None:
    # resilience.py 194-200
    # ErrorHandler must have at least one matching criterion
    from coreason_manifest.spec.core.resilience import ErrorHandler, RetryStrategy

    with pytest.raises(ValueError, match="must specify at least one matching criterion"):
        ErrorHandler(
            match_domain=None, match_pattern=None, match_error_code=None, strategy=RetryStrategy(max_attempts=1)
        )


def test_validator_kill_switch_no_governance() -> None:
    # utils/validator.py line 773
    # Call _validate_kill_switch with governance=None

    flow = GraphFlow.model_construct(governance=None, graph=None)  # type: ignore # Mocking

    errors = _validate_kill_switch(flow)
    assert len(errors) == 0


def test_error_handler_criteria_missing() -> None:
    # resilience.py 194-200
    # ErrorHandler must have at least one criteria
    from coreason_manifest.spec.core.resilience import ErrorHandler, RetryStrategy

    with pytest.raises(ValueError, match="must specify at least one matching criterion"):
        ErrorHandler(strategy=RetryStrategy(max_attempts=1))


def test_resilience_json_schema_validation() -> None:
    # resilience.py 95, 97, 105
    # ReflexionStrategy critic_schema validation

    # Valid
    ReflexionStrategy(
        max_attempts=1,
        critic_model=ModelCriteria(capabilities=["json_mode"]),
        critic_prompt="p",
        critic_schema={"type": "object", "properties": {"a": {}}},
    )

    # Invalid: missing type/properties/$ref
    with pytest.raises(ValueError, match="must be a valid JSON Schema"):
        ReflexionStrategy(
            max_attempts=1,
            critic_model=ModelCriteria(capabilities=["json_mode"]),
            critic_prompt="p",
            critic_schema={"invalid": "schema"},
        )

    # Invalid: object without properties
    with pytest.raises(ValueError, match="properties' are required"):
        ReflexionStrategy(
            max_attempts=1,
            critic_model=ModelCriteria(capabilities=["json_mode"]),
            critic_prompt="p",
            critic_schema={"type": "object"},
        )


def test_visualizer_label_fallback() -> None:
    # visualizer.py 60-61
    # Node without presentation label -> Fallback logic

    from coreason_manifest.spec.common.presentation import PresentationHints
    from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile
    from coreason_manifest.utils.visualizer import _render_mermaid_node

    # Node with presentation but NO label
    node = AgentNode(
        id="a1",
        type="agent",
        metadata={},
        profile=CognitiveProfile(role="r", persona="p"),
        tools=[],
        presentation=PresentationHints(icon="icon"),  # No label
    )

    label = _render_mermaid_node(node)
    # Check that fallback ID is used and type is appended
    assert "a1" in label
    assert "(Agent)" in label


def test_builder_additional_methods() -> None:
    # Coverage for builder.py: with_reasoning, with_fast_path etc.
    # Lines 55-73, 96-97, 101-102 etc.
    from coreason_manifest.builder import AgentBuilder
    from coreason_manifest.spec.core.engines import FastPath, StandardReasoning
    from coreason_manifest.spec.core.nodes import CognitiveProfile
    from coreason_manifest.spec.core.resilience import FallbackStrategy, RetryStrategy

    ab = AgentBuilder("a1").with_identity("r", "p")
    ab.with_reasoning("gpt-4", 10, 0.9)
    ab.with_fast_path("gpt-3.5", 500, False)
    ab.with_tools(["t1", "t2"])

    # with_resilience with all options
    ab.with_resilience(retries=3, strategy="retry", backoff=1.5, delay=0.5)

    node = ab.build()

    assert isinstance(node.profile, CognitiveProfile)
    assert isinstance(node.profile.reasoning, StandardReasoning)
    assert node.profile.reasoning.thoughts_max == 10
    assert isinstance(node.profile.fast_path, FastPath)
    assert node.profile.fast_path.caching is False
    assert "t1" in node.tools
    assert isinstance(node.resilience, RetryStrategy)
    assert node.resilience.max_attempts == 3

    # Test fallback strategy
    ab2 = AgentBuilder("a2").with_identity("r", "p")
    ab2.with_resilience(retries=0, strategy="fallback", fallback_id="fb")
    node2 = ab2.build()
    assert isinstance(node2.resilience, FallbackStrategy)
    assert node2.resilience.fallback_node_id == "fb"


def test_visualizer_human_node_options_fallback() -> None:
    # visualizer.py 60-61
    # HumanNode with options but no explicit presentation label
    from coreason_manifest.spec.core.nodes import HumanNode
    from coreason_manifest.utils.visualizer import _render_mermaid_node

    node = HumanNode(id="h1", type="human", metadata={}, prompt="p", timeout_seconds=10, options=["yes", "no"])

    label = _render_mermaid_node(node)
    assert "[yes, no]" in label


def test_telemetry_parent_hash_migration() -> None:
    # telemetry.py line 92: if prev_hashes is None: data["parent_hashes"] = [p_hash]
    from datetime import datetime

    from coreason_manifest.spec.interop.telemetry import NodeExecution, NodeState

    # Input has parent_hash but NO parent_hashes
    data = {
        "node_id": "n1",
        "state": NodeState.COMPLETED,
        "inputs": {},
        "outputs": {},
        "timestamp": datetime.now(),
        "duration_ms": 1,
        "parent_hash": "h1",
        # parent_hashes missing
    }

    ne = NodeExecution.model_validate(data)
    assert ne.parent_hashes == ["h1"]


def test_resilience_normalize_error_codes() -> None:
    # resilience.py 196-200
    from coreason_manifest.spec.core.resilience import ErrorDomain, ErrorHandler, RetryStrategy

    s = RetryStrategy(max_attempts=1)

    # Int input -> string list
    eh1 = ErrorHandler(match_error_code=404, strategy=s)  # type: ignore # Testing validation logic
    assert eh1.match_error_code == ["404"]

    # List input -> string list
    eh2 = ErrorHandler(match_error_code=[404, "500"], strategy=s)  # type: ignore # Testing validation logic
    assert eh2.match_error_code == ["404", "500"]

    # None input
    eh3 = ErrorHandler(match_domain=[ErrorDomain.SYSTEM], strategy=s)
    assert eh3.match_error_code is None

    # Invalid input type (coverage for 'return v' fallback)
    with pytest.raises(ValidationError):
        ErrorHandler(match_error_code=3.14, strategy=s)  # type: ignore # Testing validation logic


def test_resilience_trace_config() -> None:
    # resilience.py line 105: include_trace=False -> max_trace_turns=None
    from coreason_manifest.spec.core.resilience import ReflexionStrategy

    rs = ReflexionStrategy(
        max_attempts=1,
        critic_model="gpt-4",
        critic_prompt="p",
        include_trace=False,
        max_trace_turns=10,  # Should be ignored/reset
    )

    assert rs.max_trace_turns is None
