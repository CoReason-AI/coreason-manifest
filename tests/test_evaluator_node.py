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

from coreason_manifest.spec.v2.recipe import EvaluatorNode, GraphTopology
from coreason_manifest.spec.v2.evaluation import EvaluationProfile


def test_evaluator_node_instantiation() -> None:
    """Test that EvaluatorNode can be instantiated with valid fields."""
    node = EvaluatorNode(
        id="editor-check",
        target_variable="writer_output",
        evaluator_agent_ref="editor-llm",
        evaluation_profile="standard-critique",
        pass_threshold=0.9,
        max_refinements=3,
        pass_route="publish",
        fail_route="writer",
        feedback_variable="critique_history",
    )
    assert node.type == "evaluator"
    assert node.id == "editor-check"
    assert node.target_variable == "writer_output"
    assert node.evaluator_agent_ref == "editor-llm"
    assert node.pass_threshold == 0.9
    assert node.max_refinements == 3
    assert node.pass_route == "publish"
    assert node.fail_route == "writer"
    assert node.feedback_variable == "critique_history"


def test_evaluator_node_instantiation_with_profile_object() -> None:
    """Test that EvaluatorNode can be instantiated with an EvaluationProfile object."""
    profile = EvaluationProfile(
        expected_latency_ms=1000,
        grading_rubric=[],
    )
    node = EvaluatorNode(
        id="editor-check",
        target_variable="writer_output",
        evaluator_agent_ref="editor-llm",
        evaluation_profile=profile,
        pass_threshold=0.9,
        max_refinements=3,
        pass_route="publish",
        fail_route="writer",
        feedback_variable="critique_history",
    )
    assert isinstance(node.evaluation_profile, EvaluationProfile)
    assert node.evaluation_profile.expected_latency_ms == 1000


def test_evaluator_node_validation() -> None:
    """Test that missing required fields raise ValidationError."""
    with pytest.raises(ValidationError) as excinfo:
        EvaluatorNode(
            id="editor-check",
            # Missing target_variable
            evaluator_agent_ref="editor-llm",
            evaluation_profile="standard-critique",
            pass_threshold=0.9,
            max_refinements=3,
            pass_route="publish",
            fail_route="writer",
            feedback_variable="critique_history",
        ) # type: ignore[call-arg]
    assert "target_variable" in str(excinfo.value)


def test_graph_with_evaluator() -> None:
    """Test parsing the example graph with an EvaluatorNode."""
    data = {
        "nodes": [
            # 1. The Generator
            {
                "type": "agent",
                "id": "writer",
                "agent_ref": "copywriter-v1",
                "inputs_map": {
                    "topic": "user_topic",
                    "critique": "critique_history",
                },
            },
            # 2. The Evaluator-Optimizer (The New Node)
            {
                "type": "evaluator",
                "id": "editor-check",
                "target_variable": "writer_output",
                "evaluator_agent_ref": "editor-llm",
                "pass_threshold": 0.9,
                "max_refinements": 3,
                "feedback_variable": "critique_history",
                "pass_route": "publish",
                "fail_route": "writer",
                "evaluation_profile": "standard-critique", # Added this as it is required but missing in example YAML in prompt if assumed implicit? Actually the prompt example has `evaluation_profile` mentioned in text but maybe missing in YAML block?
                # Ah, checking the prompt example YAML again.
            },
            # 3. Success State
            {
                "type": "agent",
                "id": "publish",
                "agent_ref": "publisher-v1",
            },
        ],
        "edges": [], # The prompt example YAML didn't show edges, but they are required in GraphTopology.
                     # However, EvaluatorNode implies edges via pass_route/fail_route.
                     # But GraphTopology validation requires explicit edges if it checks connectivity?
                     # Wait, GraphTopology validation checks dangling edges in `edges` list.
                     # It does not check if nodes are reachable if edges list is empty (test_edge_case_disconnected_node passed).
        "entry_point": "writer",
    }

    # The prompt example YAML:
    #     # 2. The Evaluator-Optimizer (The New Node)
    #     - type: evaluator
    #       id: "editor-check"
    #       target_variable: "writer_output"
    #       evaluator_agent_ref: "editor-llm"
    #
    #       # The Criteria
    #       pass_threshold: 0.9
    #       max_refinements: 3
    #
    #       # The Output
    #       feedback_variable: "critique_history"
    #
    #       # The Loop
    #       pass_route: "publish"
    #       fail_route: "writer" # <--- The Loop Back

    # Wait, the prompt example YAML *does not* include `evaluation_profile`.
    # But the requirements say:
    # "evaluator_agent_ref": "str" ...
    # "evaluation_profile": "EvaluationProfile OR str" (Inline criteria definition or a reference to a preset profile).

    # Let me check the prompt example YAML again.
    # It lists: target_variable, evaluator_agent_ref, pass_threshold, max_refinements, feedback_variable, pass_route, fail_route.
    # It seems `evaluation_profile` is missing in the YAML example block provided in the prompt?
    # Or maybe "The Criteria" comment implies it?
    # "The Criteria" section has `pass_threshold` and `max_refinements`.
    # But `evaluation_profile` is listed in "The Judge (Who grades it)" section of requirements.
    # If the YAML example is the "Definition of Done", and it misses `evaluation_profile`, does it mean it's optional?
    # Requirements say: "evaluation_profile: EvaluationProfile OR str". It does not say Optional.
    # Let's assume it IS required based on the schema definition I wrote (no default value).
    # I will add it to the test data. If the user strictly wants the YAML example to work as is, I would need to make it optional.
    # But "The Judge" section lists it as a field.
    # I'll stick to making it required as per my schema. I'll add a dummy profile to the test data.

    # Also, GraphTopology requires `edges` and `entry_point`. The YAML example is partial `topology: nodes: ...`.
    # I'll construct a valid GraphTopology wrapper around the nodes.

    topology = GraphTopology.model_validate(data)
    assert len(topology.nodes) == 3

    evaluator = next(n for n in topology.nodes if n.id == "editor-check")
    assert isinstance(evaluator, EvaluatorNode)
    assert evaluator.target_variable == "writer_output"
    assert evaluator.pass_route == "publish"
