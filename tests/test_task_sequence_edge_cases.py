# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import pytest
from pydantic import ValidationError

from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.recipe import (
    AgentNode,
    EvaluatorNode,
    GraphTopology,
    HumanNode,
    RecipeDefinition,
    RecipeInterface,
    RouterNode,
)


def test_task_sequence_single_node() -> None:
    """Test a sequence with only one node (valid, no edges)."""
    step1 = AgentNode(id="solo", agent_ref="solo-agent")

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="solo-recipe", version="1.0.0"),
        interface=RecipeInterface(),
        topology=[step1],
    )

    assert isinstance(recipe.topology, GraphTopology)
    assert recipe.topology.entry_point == "solo"
    assert len(recipe.topology.nodes) == 1
    assert len(recipe.topology.edges) == 0


def test_task_sequence_empty_list_fails() -> None:
    """Test that an empty list raises a ValidationError (min_length=1)."""
    with pytest.raises(ValidationError) as excinfo:
        RecipeDefinition(
            metadata=ManifestMetadata(name="empty-recipe", version="1.0.0"),
            interface=RecipeInterface(),
            topology=[],
        )
    # Pydantic error for min_length
    assert "List should have at least 1 item" in str(excinfo.value)


def test_task_sequence_invalid_types_fails() -> None:
    """Test that a list containing non-node objects fails validation."""
    with pytest.raises(ValidationError) as excinfo:
        RecipeDefinition(
            metadata=ManifestMetadata(name="invalid-recipe", version="1.0.0"),
            interface=RecipeInterface(),
            topology=[{"invalid": "object"}],
        )
    # Pydantic V2 error for discriminated union mismatch
    # The actual error message is: "Unable to extract tag using discriminator 'type'"
    assert "Unable to extract tag using discriminator 'type'" in str(excinfo.value)


def test_task_sequence_mixed_node_types() -> None:
    """Test a sequence mixing different node types (Agent -> Human -> Router)."""
    step1 = AgentNode(id="agent1", agent_ref="ref1")
    step2 = HumanNode(id="human1", prompt="check")
    # Router in a sequence is weird (where do the routes go?) but structurally valid as a node
    # The edges will just point to the next step linearly.
    # Logic-wise, a RouterNode usually ignores the default edge and follows its 'routes'.
    # But for the purpose of GraphTopology construction, it should be allowed.
    step3 = RouterNode(
        id="router1",
        input_key="decision",
        routes={"yes": "agent1"},  # Circular ref just for valid schema
        default_route="agent1",
    )

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="mixed-recipe", version="1.0.0"),
        interface=RecipeInterface(),
        topology=[step1, step2, step3],
    )

    assert len(recipe.topology.nodes) == 3
    # Edges: agent1->human1, human1->router1
    assert len(recipe.topology.edges) == 2
    assert recipe.topology.edges[0].source == "agent1"
    assert recipe.topology.edges[0].target == "human1"
    assert recipe.topology.edges[1].source == "human1"
    assert recipe.topology.edges[1].target == "router1"


def test_task_sequence_dict_extra_fields() -> None:
    """Test that a dict with 'steps' ignores extra fields if configured to allow, or fails if strict."""
    # TaskSequence has extra="forbid"

    step1 = AgentNode(id="step1", agent_ref="ref1")

    with pytest.raises(ValidationError) as excinfo:
        RecipeDefinition(
            metadata=ManifestMetadata(name="extra-recipe", version="1.0.0"),
            interface=RecipeInterface(),
            topology={"steps": [step1], "extra_field": "should_fail"},
        )
    assert "Extra inputs are not permitted" in str(excinfo.value)


def test_complex_evaluator_sequence() -> None:
    """
    Test a complex sequence involving an Evaluator node.
    Realistically, Evaluator nodes loop back on failure.
    A linear sequence A -> Evaluator -> B implies the evaluator
    just passes through or B is the 'pass_route'?

    The TaskSequence logic just wires (i) -> (i+1).
    So Evaluator -> NextNode means there is an edge Evaluator -> NextNode.

    The EvaluatorNode schema requires 'pass_route' and 'fail_route'.
    If we use it in a TaskSequence, we must still provide those fields.
    """
    step1 = AgentNode(id="generator", agent_ref="gen-ref")

    # We point pass/fail routes to valid IDs, possibly within the sequence
    step2 = EvaluatorNode(
        id="judge",
        target_variable="output",
        evaluator_agent_ref="judge-ref",
        evaluation_profile="strict",
        pass_threshold=0.8,
        max_refinements=3,
        pass_route="publisher",  # Points to next step
        fail_route="generator",  # Loops back
        feedback_variable="critique",
    )

    step3 = AgentNode(id="publisher", agent_ref="pub-ref")

    # The automatic edge generation will add:
    # generator -> judge
    # judge -> publisher

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="eval-recipe", version="1.0.0"),
        interface=RecipeInterface(),
        topology=[step1, step2, step3],
    )

    topo = recipe.topology
    assert len(topo.edges) == 2

    # Verify the automatic edge judge->publisher exists
    assert topo.edges[1].source == "judge"
    assert topo.edges[1].target == "publisher"

    # NOTE: The EvaluatorNode logic (in runtime) might use 'pass_route' instead of the generic edge.
    # But structurally, this graph is valid.


def test_topology_dict_no_steps_no_nodes_fails() -> None:
    """Test that a dict without 'steps' AND without 'nodes' fails (ambiguous or invalid)."""
    with pytest.raises(ValidationError):
        RecipeDefinition(
            metadata=ManifestMetadata(name="bad-recipe", version="1.0.0"),
            interface=RecipeInterface(),
            topology={"something": "else"},
        )
