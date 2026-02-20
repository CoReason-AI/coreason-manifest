import pytest
from pydantic import TypeAdapter, ValidationError

from coreason_manifest.spec.core.flow import AnyNode
from coreason_manifest.spec.core.nodes import AgentNode, HumanNode, SwarmNode


def test_semantic_routing_nodes() -> None:
    """
    Test that a list of mixed node types is parsed correctly into their specific classes.
    """
    nodes_data = [
        {
            "type": "human",
            "id": "human_step_1",
            "prompt": "Approve?",
            "interaction_mode": "blocking",
            "timeout_seconds": 60,
        },
        {
            "type": "agent",
            "id": "agent_step_1",
            "profile": "researcher_profile",
            "tools": ["web_search"],
        },
        {
            "type": "swarm",
            "id": "swarm_step_1",
            "worker_profile": "worker_v1",
            "workload_variable": "data_list",
            "distribution_strategy": "sharded",
            "max_concurrency": 10,
            "reducer_function": "concat",
            "output_variable": "result",
        },
    ]

    adapter = TypeAdapter(list[AnyNode])
    nodes = adapter.validate_python(nodes_data)

    assert len(nodes) == 3
    assert isinstance(nodes[0], HumanNode)
    assert nodes[0].type == "human"
    assert nodes[0].id == "human_step_1"

    assert isinstance(nodes[1], AgentNode)
    assert nodes[1].type == "agent"
    assert nodes[1].profile == "researcher_profile"

    assert isinstance(nodes[2], SwarmNode)
    assert nodes[2].type == "swarm"
    assert nodes[2].distribution_strategy == "sharded"


def test_semantic_routing_failure() -> None:
    """
    Test that an invalid type raises a ValidationError.
    """
    nodes_data = [{"type": "invalid_type", "id": "bad_node"}]
    adapter = TypeAdapter(list[AnyNode])
    with pytest.raises(ValidationError) as excinfo:
        adapter.validate_python(nodes_data)

    assert "Input tag 'invalid_type' found using 'type' does not match any of the expected tags" in str(excinfo.value)
