import pytest
from pydantic import ValidationError
from coreason_manifest.spec.core.nodes import HumanNode, SwarmNode
from coreason_manifest.spec.core.flow import GraphFlow, Graph, DataSchema, FlowMetadata, FlowInterface, Blackboard
from coreason_manifest.spec.core.exceptions import DomainValidationError
from coreason_manifest.utils.gatekeeper import validate_policy
from coreason_manifest.spec.interop.compliance import ErrorCatalog

def test_magic_number_coercion_human_node():
    """Directive 1: -1 should be coerced to 'infinite'."""
    node = HumanNode(
        id="h1",
        metadata={},
        type="human",
        prompt="test",
        timeout_seconds=-1,
        interaction_mode="blocking"
    )
    assert node.timeout_seconds == "infinite"

    node_shadow = HumanNode(
        id="h2",
        metadata={},
        type="human",
        prompt="test",
        timeout_seconds=300,
        interaction_mode="shadow",
        shadow_timeout_seconds=-1
    )
    assert node_shadow.shadow_timeout_seconds == "infinite"

def test_magic_number_coercion_swarm_node():
    """Directive 1: -1 should be coerced to 'infinite' in SwarmNode."""
    node = SwarmNode(
        id="s1",
        metadata={},
        type="swarm",
        worker_profile="profile_1",
        workload_variable="tasks",
        distribution_strategy="sharded",
        max_concurrency=-1,
        reducer_function="concat",
        output_variable="results"
    )
    assert node.max_concurrency == "infinite"

def test_domain_validation_error_remediation():
    """Directive 4: DomainValidationError should contain remediation."""
    # When validating during model creation, Pydantic wraps custom exceptions in ValidationError.
    # We need to catch ValidationError and inspect the underlying error.
    with pytest.raises(ValidationError) as excinfo:
        HumanNode(
            id="h1",
            metadata={},
            type="human",
            prompt="test",
            timeout_seconds=300,
            interaction_mode="shadow",
            shadow_timeout_seconds=None # Missing required field for shadow mode
        )

    # Extract the original exception
    # Pydantic V2 stores errors in .errors(), but the original exception object might be in 'ctx' if available,
    # or we might need to rely on the message.
    # However, 'DomainValidationError' should be raised directly if we use a validator that raises it?
    # No, Pydantic always wraps validator exceptions in ValidationError.

    errors = excinfo.value.errors()
    assert len(errors) == 1
    err = errors[0]
    # In Pydantic V2, the original exception is in 'ctx' key of the error dict if it's a value error.
    # But usually it's easier to check the message or type if accessible.

    # Wait, 'ctx' key contains the exception object?
    # Let's inspect what we get.
    # If we can't easily access the DomainValidationError object, we at least check the message.

    # Actually, for the purpose of this test, verifying the message contains remediation description is good.
    assert "Set 'shadow_timeout_seconds' to a valid value" in err['msg']
    assert "[Remediation:" in err['msg']

def test_healing_ingestion_stub():
    """Directive 3: Invalid schema should raise DomainValidationError with repair attempt context."""
    invalid_schema = {"type": "unknown_type"}

    with pytest.raises(ValidationError) as excinfo:
        DataSchema(json_schema=invalid_schema)

    errors = excinfo.value.errors()
    assert len(errors) == 1
    err = errors[0]

    # Check message for healing/invalid schema
    assert "Invalid JSON Schema" in err['msg']
    # If DomainValidationError is wrapped, its __str__ includes the message.

def test_topology_tolerance_and_gatekeeper():
    """Directive 2: GraphFlow should allow islands, Gatekeeper should flag them."""
    # Create a graph with an unreachable node (island)
    # Entry point is 'n1', 'n2' is isolated.

    nodes = {
        "n1": HumanNode(id="n1", metadata={}, type="human", prompt="entry", timeout_seconds=10),
        "n2": HumanNode(id="n2", metadata={}, type="human", prompt="island", timeout_seconds=10)
    }

    graph = Graph(
        nodes=nodes,
        edges=[],
        entry_point="n1"
    )

    flow = GraphFlow(
        kind="GraphFlow",
        status="published",
        metadata=FlowMetadata(name="test", version="1.0", description="test", tags=[]),
        interface=FlowInterface(inputs=DataSchema(), outputs=DataSchema()),
        blackboard=None,
        graph=graph
    )

    # Validation should PASS (no ValueError raised by GraphFlow validation)
    assert flow.status == "published"

    # Now run Gatekeeper
    reports = validate_policy(flow)

    # Check for orphan warning
    orphan_reports = [r for r in reports if r.code == ErrorCatalog.ERR_TOPOLOGY_ORPHAN_001]
    assert len(orphan_reports) == 1
    assert orphan_reports[0].node_id == "n2"
    assert orphan_reports[0].severity == "warning"
    assert orphan_reports[0].remediation.type == "prune_node"
