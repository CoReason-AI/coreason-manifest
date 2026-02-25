from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.core.flow import Edge, FlowDefinitions, FlowInterface, FlowMetadata, Graph, GraphFlow
from coreason_manifest.spec.core.governance import CircuitBreaker, CircuitState, ToolAccessPolicy, check_circuit
from coreason_manifest.spec.core.nodes import AgentNode, CognitiveProfile
from coreason_manifest.spec.core.resilience import SupervisionPolicy
from coreason_manifest.spec.interop.exceptions import ManifestError
from coreason_manifest.utils.integrity import compute_hash, reconstruct_payload, verify_merkle_proof
from coreason_manifest.utils.io import SecurityViolationError
from coreason_manifest.utils.loader import load_agent_from_ref


def test_ast_whitelist() -> None:
    # Allowed
    Edge(from_node="a", to_node="b", condition="1 + 1 == 2")
    Edge(from_node="a", to_node="b", condition="x > 10 and y < 5")
    Edge(from_node="a", to_node="b", condition="not (a in b)")

    # Blocked by whitelist
    with pytest.raises((ValidationError, SecurityViolationError), match="forbidden AST node ListComp"):
        Edge(from_node="a", to_node="b", condition="[x for x in range(10)]")

    with pytest.raises((ValidationError, SecurityViolationError), match="forbidden AST node Dict"):
        Edge(from_node="a", to_node="b", condition="{'a': 1}")


def test_loader_recursion_bypass(tmp_path: Path) -> None:
    import yaml

    from coreason_manifest.utils.loader import load_flow_from_file

    # Create recursive structure using different relative paths
    (tmp_path / "a.yaml").write_text(yaml.dump({"$include": "./b.yaml"}))
    (tmp_path / "b.yaml").write_text(yaml.dump({"$include": "../" + tmp_path.name + "/a.yaml"}))

    with pytest.raises(RecursionError, match="Circular dependency detected"):
        load_flow_from_file(str(tmp_path / "a.yaml"), strict_security=False)


def test_partial_dag_verification() -> None:
    # A -> B -> C
    # We only have C in trace, but B's hash is trusted

    # Construct nodes
    node_a = {"id": "A", "parent_hashes": [], "hash_version": "v2"}
    h_a = compute_hash(reconstruct_payload(node_a))

    node_b = {"id": "B", "parent_hashes": [h_a], "hash_version": "v2"}
    h_b = compute_hash(reconstruct_payload(node_b))

    node_c = {"id": "C", "parent_hashes": [h_b], "hash_version": "v2"}
    h_c = compute_hash(reconstruct_payload(node_c))
    node_c["execution_hash"] = h_c

    trace = [node_c]

    # Should fail without trusted parent
    assert verify_merkle_proof(trace) is False

    # Should pass with trusted parent
    assert verify_merkle_proof(trace, trusted_parent_hashes={h_b}) is True


def test_resilience_reference_validation(
    flow_metadata: FlowMetadata, agent_node_factory: Callable[..., AgentNode]
) -> None:
    # Node refers to missing template
    node = agent_node_factory("a1", resilience="ref:missing_template")

    graph = Graph(nodes={"a1": node}, edges=[], entry_point="a1")

    flow = GraphFlow(kind="GraphFlow", metadata=flow_metadata, interface=FlowInterface(), graph=graph)
    from coreason_manifest.utils.validator import validate_flow

    errors = validate_flow(flow)
    # Matches message in validator.py
    assert any("references undefined supervision template" in e.message for e in errors)

    # Valid reference
    # Must use full valid SupervisionPolicy
    # handlers is list[ErrorHandler]
    from coreason_manifest.spec.core.resilience import ErrorDomain, ErrorHandler, RetryStrategy

    strategy = RetryStrategy(max_attempts=3)
    handler = ErrorHandler(match_domain=[ErrorDomain.SYSTEM], strategy=strategy)

    policy = SupervisionPolicy(handlers=[handler], default_strategy=strategy)
    defs = FlowDefinitions(supervision_templates={"my_template": policy})

    # We must construct node WITH valid resilience ID since field is frozen/validated?
    # Or create a new node
    valid_node = agent_node_factory("a1", resilience="my_template")
    valid_graph = Graph(nodes={"a1": valid_node}, edges=[], entry_point="a1")

    GraphFlow(kind="GraphFlow", metadata=flow_metadata, interface=FlowInterface(), graph=valid_graph, definitions=defs)


def test_enum_case_insensitivity() -> None:
    # Uppercase "CRITICAL"
    data = {"risk_level": "CRITICAL", "require_auth": False}

    # Should raise error because require_auth=False is not allowed for CRITICAL
    # If case sensitivity was broken, it would bypass the check.
    with pytest.raises(ValueError, match="Critical tools must require authentication"):
        ToolAccessPolicy.model_validate(data)

    # Lowercase "critical"
    data2 = {"risk_level": "critical", "require_auth": False}
    with pytest.raises(ValueError, match="Critical tools must require authentication"):
        ToolAccessPolicy.model_validate(data2)


def test_circuit_breaker_exception_type() -> None:
    import time

    policy = CircuitBreaker(error_threshold_count=1, reset_timeout_seconds=100)
    # Use current time so timeout (current - last) < 100
    state_store: dict[str, Any] = {"n1": CircuitState(state="open", last_failure_time=time.time())}

    # Should raise ManifestError, not CircuitOpenError
    with pytest.raises(ManifestError) as exc:
        check_circuit("n1", policy, state_store)

    assert exc.value.fault.error_code == "CRSN-EXEC-CIRCUIT-OPEN"


def test_module_namespace_clean(tmp_path: Path) -> None:
    # File with invalid chars
    agent_file = tmp_path / "v1.2-agent.py"
    agent_file.write_text("class MyAgent: pass")
    agent_file.chmod(0o600)

    # Load
    cls = load_agent_from_ref(f"{agent_file.name}:MyAgent", root_dir=tmp_path)

    # Check module name in sys.modules
    # It should not contain "v1.2-agent"

    # We verify the module was registered with the hashed name
    # The loading function registers it, then potentially unregisters it or it stays in the jailed context
    # But load_agent_from_ref registers it in sys.modules inside the sandbox context
    # It returns the class. The class's __module__ should be the hashed name.

    assert "v1.2-agent" not in cls.__module__
    assert cls.__module__.startswith("_jail_")

    # We can check if it is importable (if context persists or if we are just checking the string)
    # The test failed with KeyError because the module might be cleaned up if it was only temporary?
    # SandboxedPathFinder keeps modules in _jail_modules_var.
    # But load_agent_from_ref cleans up:
    # "if module_name in sys.modules: del sys.modules[module_name]"
    # So we CANNOT access sys.modules[cls.__module__] after return.

    # The class still holds the module name reference.
