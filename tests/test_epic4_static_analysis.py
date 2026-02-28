from coreason_manifest.spec.core import CognitiveProfile, FlowDefinitions, PlannerNode, StandardReasoning
from coreason_manifest.spec.core.workflow.nodes import SwarmNode
from coreason_manifest.utils.validator import _validate_data_flow


def test_planner_node_static_analysis_success() -> None:
    planner = PlannerNode(
        id="planner_1",
        goal="Generate ideas",
        output_schema={"type": "object", "properties": {"ideas_list": {"type": "array"}}},
    )

    swarm = SwarmNode(
        id="swarm_1",
        worker_profile="worker",
        workload_variable="ideas_list",
        distribution_strategy="sharded",
        max_concurrency=5,
        reducer_function="concat",
        output_variable="final_ideas",
        operational_policy=None,
    )

    symbol_table = {"ideas_list": "array", "final_ideas": "string"}

    # We must provide adjacency map for topological validation!
    # planner connects to swarm
    adj_map = {"planner_1": {"swarm_1"}}

    errors = _validate_data_flow(
        [planner, swarm],
        symbol_table,
        definitions=FlowDefinitions(
            profiles={"worker": CognitiveProfile(role="W", persona="W", reasoning=StandardReasoning(model="test"))}
        ),
        adj_map=adj_map,
    )

    type_errors = [e for e in errors if e.code == "ERR_CAP_TYPE_MISMATCH"]
    assert len(type_errors) == 0  # noqa: S101


def test_planner_node_static_analysis_type_failure() -> None:
    planner = PlannerNode(
        id="planner_1",
        goal="Generate ideas",
        output_schema={
            "type": "object",
            "properties": {
                "ideas_list": {"type": "string"}  # Incorrect! Swarm expects array
            },
        },
    )

    swarm = SwarmNode(
        id="swarm_1",
        worker_profile="worker",
        workload_variable="ideas_list",
        distribution_strategy="sharded",
        max_concurrency=5,
        reducer_function="concat",
        output_variable="final_ideas",
        operational_policy=None,
    )

    symbol_table = {"ideas_list": "array", "final_ideas": "string"}
    adj_map = {"planner_1": {"swarm_1"}}

    errors = _validate_data_flow(
        [planner, swarm],
        symbol_table,
        definitions=FlowDefinitions(
            profiles={"worker": CognitiveProfile(role="W", persona="W", reasoning=StandardReasoning(model="test"))}
        ),
        adj_map=adj_map,
    )

    type_errors = [e for e in errors if e.code == "ERR_CAP_TYPE_MISMATCH"]

    assert len(type_errors) >= 1  # noqa: S101
    assert "ideas_list" in type_errors[0].message  # noqa: S101
    assert "string" in type_errors[0].message  # noqa: S101
    assert "array" in type_errors[0].message  # noqa: S101


def test_planner_node_static_analysis_missing_field_failure() -> None:
    planner = PlannerNode(
        id="planner_1",
        goal="Generate ideas",
        output_schema={
            "type": "object",
            "properties": {
                # missing ideas_list entirely
                "other_field": {"type": "string"}
            },
        },
    )

    swarm = SwarmNode(
        id="swarm_1",
        worker_profile="worker",
        workload_variable="ideas_list",
        distribution_strategy="sharded",
        max_concurrency=5,
        reducer_function="concat",
        output_variable="final_ideas",
        operational_policy=None,
    )

    symbol_table = {"ideas_list": "array", "final_ideas": "string"}
    adj_map = {"planner_1": {"swarm_1"}}

    errors = _validate_data_flow(
        [planner, swarm],
        symbol_table,
        definitions=FlowDefinitions(
            profiles={"worker": CognitiveProfile(role="W", persona="W", reasoning=StandardReasoning(model="test"))}
        ),
        adj_map=adj_map,
    )

    type_errors = [e for e in errors if e.code == "ERR_CAP_TYPE_MISMATCH"]

    assert len(type_errors) >= 1  # noqa: S101
    assert "ideas_list" in type_errors[0].message  # noqa: S101
    assert "missing required property" in type_errors[0].message.lower()  # noqa: S101
