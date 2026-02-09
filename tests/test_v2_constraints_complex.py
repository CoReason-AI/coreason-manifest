# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.recipe import AgentNode, Constraint, GraphTopology, RecipeDefinition, RecipeInterface


def test_recipe_complex_mixed_constraints() -> None:
    """Test complex scenario with multiple mixed required and optional constraints."""
    node = AgentNode(id="start", agent_ref="agent1")
    topology = GraphTopology(nodes=[node], edges=[], entry_point="start")
    interface = RecipeInterface()
    metadata = ManifestMetadata(name="Complex Recipe")

    requirements = [
        Constraint(variable="env", operator="eq", value="prod", required=True),
        Constraint(variable="user.tier", operator="in", value=["gold", "platinum"], required=True),
        Constraint(variable="feature.beta", operator="eq", value=True, required=False),  # Optional, fails
        Constraint(variable="quota.remaining", operator="gte", value=100, required=True),
    ]

    recipe = RecipeDefinition(metadata=metadata, interface=interface, topology=topology, requirements=requirements)

    # Scenario 1: All required pass, optional fails
    context_pass = {"env": "prod", "user": {"tier": "gold"}, "feature": {"beta": False}, "quota": {"remaining": 500}}
    feasible, errors = recipe.check_feasibility(context_pass)
    assert feasible is True
    assert len(errors) == 0

    # Scenario 2: One required fails, optional fails
    context_fail = {
        "env": "prod",
        "user": {"tier": "silver"},  # Fail
        "feature": {"beta": False},
        "quota": {"remaining": 500},
    }
    feasible, errors = recipe.check_feasibility(context_fail)
    assert feasible is False
    assert len(errors) == 1
    assert "Constraint failed" in errors[0]
    assert "user.tier" in errors[0]


def test_constraint_mutable_context() -> None:
    """Test evaluating constraints against mutable context objects."""

    class MutableObj:
        def __init__(self, val: int):
            self.val = val

        def __eq__(self, other: object) -> bool:
            if isinstance(other, int):
                return self.val == other
            return False

    # This won't work with current logic because it expects dict traversal
    # But if the mutable object IS the value (not the container), it should work
    context = {"obj": MutableObj(10)}

    # Resolving "obj" gets the MutableObj instance
    # Comparing instance == 10
    assert Constraint(variable="obj", operator="eq", value=10).evaluate(context) is True

    context["obj"].val = 5
    assert Constraint(variable="obj", operator="eq", value=10).evaluate(context) is False


def test_constraint_large_scale() -> None:
    """Test a large number of constraints."""
    requirements = [
        Constraint(variable=f"var_{i}", operator="eq", value=i)
        for i in range(100)
    ]

    context = {f"var_{i}": i for i in range(100)}

    # Just checking logic doesn't choke
    # Evaluating individual constraints
    for req in requirements:
        assert req.evaluate(context) is True

    # Check feasibility
    node = AgentNode(id="start", agent_ref="agent1")
    topology = GraphTopology(nodes=[node], edges=[], entry_point="start")
    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Large Recipe"),
        interface=RecipeInterface(),
        topology=topology,
        requirements=requirements,
    )

    feasible, errors = recipe.check_feasibility(context)
    assert feasible is True

    # Invalidate one
    context["var_50"] = 999
    feasible, errors = recipe.check_feasibility(context)
    assert feasible is False
    assert len(errors) == 1


def test_constraint_deep_nesting_and_mixed_types() -> None:
    """Test deeply nested paths and non-JSON standard types."""
    # Deep nesting
    context = {"l1": {"l2": {"l3": {"l4": {"val": "found"}}}}}
    assert Constraint(variable="l1.l2.l3.l4.val", operator="eq", value="found").evaluate(context) is True
    assert Constraint(variable="l1.l2.missing.val", operator="eq", value="found").evaluate(context) is False

    # Mixed types (set, tuple)
    # Note: JSON serialization usually doesn't handle these, but the context is a raw python dict
    context_mixed = {"set_val": {1, 2, 3}, "tuple_val": (1, 2)}

    # Set contains
    assert Constraint(variable="set_val", operator="contains", value=2).evaluate(context_mixed) is True
    assert Constraint(variable="set_val", operator="contains", value=4).evaluate(context_mixed) is False

    # Tuple comparison
    assert Constraint(variable="tuple_val", operator="eq", value=(1, 2)).evaluate(context_mixed) is True
    assert Constraint(variable="tuple_val", operator="in", value=[(1, 2), (3, 4)]).evaluate(context_mixed) is True
