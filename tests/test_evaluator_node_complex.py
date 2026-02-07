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


def test_edge_case_zero_max_refinements() -> None:
    """Test that max_refinements can be 0 (fail immediately on first reject)."""
    node = EvaluatorNode(
        id="strict-judge",
        target_variable="content",
        evaluator_agent_ref="judge-v1",
        evaluation_profile="strict-profile",
        pass_threshold=0.9,
        max_refinements=0,
        pass_route="success",
        fail_route="failure",
        feedback_variable="critique",
    )
    assert node.max_refinements == 0


def test_edge_case_boundary_thresholds() -> None:
    """Test that pass_threshold accepts 0.0 and 1.0."""
    node_low = EvaluatorNode(
        id="easy-judge",
        target_variable="content",
        evaluator_agent_ref="judge-v1",
        evaluation_profile="easy-profile",
        pass_threshold=0.0,
        max_refinements=1,
        pass_route="success",
        fail_route="failure",
        feedback_variable="critique",
    )
    assert node_low.pass_threshold == 0.0

    node_high = EvaluatorNode(
        id="impossible-judge",
        target_variable="content",
        evaluator_agent_ref="judge-v1",
        evaluation_profile="hard-profile",
        pass_threshold=1.0,
        max_refinements=1,
        pass_route="success",
        fail_route="failure",
        feedback_variable="critique",
    )
    assert node_high.pass_threshold == 1.0


def test_complex_circular_dependency() -> None:
    """Test a valid circular dependency: Generator -> Evaluator -> Generator."""
    data = {
        "nodes": [
            {
                "type": "agent",
                "id": "gen",
                "agent_ref": "writer",
                "inputs_map": {"feedback": "critique"},
            },
            {
                "type": "evaluator",
                "id": "eval",
                "target_variable": "draft",
                "evaluator_agent_ref": "judge",
                "evaluation_profile": "profile-1",
                "pass_threshold": 0.8,
                "max_refinements": 5,
                "pass_route": "end",
                "fail_route": "gen",  # Cycle back
                "feedback_variable": "critique",
            },
            {
                "type": "agent",
                "id": "end",
                "agent_ref": "publisher",
            },
        ],
        "edges": [],
        "entry_point": "gen",
    }
    topology = GraphTopology.model_validate(data)
    assert len(topology.nodes) == 3


def test_complex_two_stage_evaluation() -> None:
    """Test a linear chain of two evaluators: Gen -> Eval1 -> Eval2 -> End."""
    data = {
        "nodes": [
            {
                "type": "agent",
                "id": "gen",
                "agent_ref": "writer",
            },
            {
                "type": "evaluator",
                "id": "eval-grammar",
                "target_variable": "draft",
                "evaluator_agent_ref": "grammar-check",
                "evaluation_profile": "grammar-strict",
                "pass_threshold": 0.9,
                "max_refinements": 2,
                "pass_route": "eval-tone",
                "fail_route": "gen",
                "feedback_variable": "grammar_errors",
            },
            {
                "type": "evaluator",
                "id": "eval-tone",
                "target_variable": "draft",
                "evaluator_agent_ref": "tone-check",
                "evaluation_profile": "tone-friendly",
                "pass_threshold": 0.8,
                "max_refinements": 2,
                "pass_route": "end",
                "fail_route": "gen",
                "feedback_variable": "tone_feedback",
            },
            {
                "type": "agent",
                "id": "end",
                "agent_ref": "publisher",
            },
        ],
        "edges": [],
        "entry_point": "gen",
    }
    topology = GraphTopology.model_validate(data)
    assert len(topology.nodes) == 4

    eval1 = next(n for n in topology.nodes if n.id == "eval-grammar")
    assert isinstance(eval1, EvaluatorNode)
    assert eval1.pass_route == "eval-tone"


def test_complex_branching_evaluation() -> None:
    """Test branching logic before evaluation: Gen -> Router -> (Eval A | Eval B)."""
    data = {
        "nodes": [
            {
                "type": "agent",
                "id": "gen",
                "agent_ref": "writer",
            },
            {
                "type": "router",
                "id": "router",
                "input_key": "content_type",
                "routes": {
                    "technical": "eval-tech",
                    "creative": "eval-creative",
                },
                "default_route": "eval-creative",
            },
            {
                "type": "evaluator",
                "id": "eval-tech",
                "target_variable": "draft",
                "evaluator_agent_ref": "tech-judge",
                "evaluation_profile": "tech-specs",
                "pass_threshold": 0.95,
                "max_refinements": 3,
                "pass_route": "end",
                "fail_route": "gen",
                "feedback_variable": "tech_critique",
            },
            {
                "type": "evaluator",
                "id": "eval-creative",
                "target_variable": "draft",
                "evaluator_agent_ref": "creative-judge",
                "evaluation_profile": "creative-flow",
                "pass_threshold": 0.8,
                "max_refinements": 5,
                "pass_route": "end",
                "fail_route": "gen",
                "feedback_variable": "creative_critique",
            },
            {
                "type": "agent",
                "id": "end",
                "agent_ref": "publisher",
            },
        ],
        "edges": [
            {"source": "gen", "target": "router"},
            # Edges from router are implicit in routes, but GraphTopology validator might check explicit edges.
            # Wait, GraphTopology validation checks dangling edges in `edges` list.
            # It does NOT check if all `routes` targets are connected via explicit `edges`.
            # But let's add them for completeness if needed.
            # Actually, `routes` targets are just node IDs.
            # The `edges` list is optional for flow definition but mandatory for visualization if used.
            # I will add router->eval edges to be safe.
            {"source": "router", "target": "eval-tech"},
            {"source": "router", "target": "eval-creative"},
        ],
        "entry_point": "gen",
    }
    topology = GraphTopology.model_validate(data)
    assert len(topology.nodes) == 5


def test_invalid_evaluation_profile_type() -> None:
    """Test that evaluation_profile rejects invalid types (e.g. integer)."""
    with pytest.raises(ValidationError) as excinfo:
        EvaluatorNode(
            id="bad-profile",
            target_variable="content",
            evaluator_agent_ref="judge",
            evaluation_profile=123,
            pass_threshold=0.9,
            max_refinements=3,
            pass_route="end",
            fail_route="start",
            feedback_variable="critique",
        )
    assert "evaluation_profile" in str(excinfo.value)
