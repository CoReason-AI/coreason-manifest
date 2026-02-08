import logging
import pytest
from coreason_manifest.spec.v2.recipe import Constraint, RecipeDefinition, AgentNode, GraphTopology, RecipeInterface
from coreason_manifest.spec.v2.definitions import ManifestMetadata

def test_constraint_contains_non_iterable() -> None:
    """Test 'contains' operator on a non-iterable value."""
    context = {"val": 123} # Integer is not iterable
    # 1 in 123 -> TypeError
    assert Constraint(variable="val", operator="contains", value=1).evaluate(context) is False

def test_constraint_numeric_edge_cases() -> None:
    """Test float comparisons and mixed numeric types."""
    context = {"val": 10.5}

    assert Constraint(variable="val", operator="gt", value=10).evaluate(context) is True
    assert Constraint(variable="val", operator="lt", value=11).evaluate(context) is True
    assert Constraint(variable="val", operator="eq", value=10.5).evaluate(context) is True

    # String vs Float
    # "10.5" > 10.0 -> TypeError (False)
    context_str = {"val": "10.5"}
    assert Constraint(variable="val", operator="gt", value=10.0).evaluate(context_str) is False

def test_constraint_list_traversal_fail() -> None:
    """Test that traversing a list via dot notation fails gracefully (current implementation behavior)."""
    context = {"users": [{"name": "alice"}, {"name": "bob"}]}

    # "users.0.name" - users is list, '0' is not in list dict
    # Logic: isinstance(current, dict) will be False when current is the list
    # Wait, variable is "users.0.name"
    # 1. part="users" -> current = list
    # 2. part="0" -> isinstance(current, dict) is False -> returns False
    assert Constraint(variable="users.0.name", operator="eq", value="alice").evaluate(context) is False

def test_optional_constraint_logging(caplog: pytest.LogCaptureFixture) -> None:
    """Verify that failing optional constraints log a warning."""
    caplog.set_level(logging.WARNING)

    node = AgentNode(id="start", agent_ref="agent1")
    topology = GraphTopology(nodes=[node], edges=[], entry_point="start")

    recipe = RecipeDefinition(
        metadata=ManifestMetadata(name="Logging Test"),
        interface=RecipeInterface(),
        topology=topology,
        requirements=[
            Constraint(variable="missing.key", operator="eq", value=1, required=False, error_message="Custom Warning")
        ]
    )

    context: dict[str, object] = {}
    feasible, errors = recipe.check_feasibility(context)

    assert feasible is True
    assert len(errors) == 0

    # Check log
    assert "Optional constraint warning: Custom Warning" in caplog.text
