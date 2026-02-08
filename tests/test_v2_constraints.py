from coreason_manifest.spec.v2.definitions import ManifestMetadata
from coreason_manifest.spec.v2.recipe import AgentNode, Constraint, GraphTopology, RecipeDefinition, RecipeInterface


def test_constraint_evaluate_operators() -> None:
    """Test various operators for constraint evaluation."""
    context = {"val": 10, "list": [1, 2, 3], "str": "hello world"}

    # eq
    assert Constraint(variable="val", operator="eq", value=10).evaluate(context) is True
    assert Constraint(variable="val", operator="eq", value=5).evaluate(context) is False

    # neq
    assert Constraint(variable="val", operator="neq", value=5).evaluate(context) is True
    assert Constraint(variable="val", operator="neq", value=10).evaluate(context) is False

    # gt
    assert Constraint(variable="val", operator="gt", value=5).evaluate(context) is True
    assert Constraint(variable="val", operator="gt", value=10).evaluate(context) is False

    # gte
    assert Constraint(variable="val", operator="gte", value=10).evaluate(context) is True
    assert Constraint(variable="val", operator="gte", value=11).evaluate(context) is False

    # lt
    assert Constraint(variable="val", operator="lt", value=15).evaluate(context) is True
    assert Constraint(variable="val", operator="lt", value=10).evaluate(context) is False

    # lte
    assert Constraint(variable="val", operator="lte", value=10).evaluate(context) is True
    assert Constraint(variable="val", operator="lte", value=9).evaluate(context) is False

    # in
    assert Constraint(variable="val", operator="in", value=[10, 20]).evaluate(context) is True
    assert Constraint(variable="val", operator="in", value=[20, 30]).evaluate(context) is False

    # contains
    assert Constraint(variable="list", operator="contains", value=2).evaluate(context) is True
    assert Constraint(variable="list", operator="contains", value=5).evaluate(context) is False
    assert Constraint(variable="str", operator="contains", value="world").evaluate(context) is True
    assert Constraint(variable="str", operator="contains", value="python").evaluate(context) is False


def test_constraint_nested_path() -> None:
    """Test path resolution for nested dictionaries."""
    context = {"data": {"nested": {"value": 42}}}

    assert Constraint(variable="data.nested.value", operator="eq", value=42).evaluate(context) is True
    assert Constraint(variable="data.nested.value", operator="gt", value=40).evaluate(context) is True

    # Path not found
    assert Constraint(variable="data.missing.value", operator="eq", value=42).evaluate(context) is False
    assert Constraint(variable="missing.path", operator="eq", value=42).evaluate(context) is False

    # Path traversing non-dict
    assert Constraint(variable="data.nested.value.sub", operator="eq", value=42).evaluate(context) is False


def test_constraint_type_safety() -> None:
    """Test that type mismatches do not crash."""
    context = {"val": "string"}

    # Comparing string > int should return False, not raise TypeError
    assert Constraint(variable="val", operator="gt", value=10).evaluate(context) is False

    # Comparing int in string (where string is the container but we pass int as item)
    # 10 in "string" -> TypeError
    assert Constraint(variable="val", operator="contains", value=10).evaluate(context) is False


def test_recipe_check_feasibility() -> None:
    """Test check_feasibility method on RecipeDefinition."""

    # Setup minimal valid recipe
    node = AgentNode(id="start", agent_ref="agent1")
    topology = GraphTopology(nodes=[node], edges=[], entry_point="start")
    interface = RecipeInterface()
    metadata = ManifestMetadata(name="Test Recipe")

    # Case 1: All constraints pass
    recipe = RecipeDefinition(
        metadata=metadata,
        interface=interface,
        topology=topology,
        requirements=[
            Constraint(variable="user.role", operator="eq", value="admin"),
            Constraint(variable="system.ready", operator="eq", value=True),
        ],
    )

    context = {"user": {"role": "admin"}, "system": {"ready": True}}
    feasible, errors = recipe.check_feasibility(context)
    assert feasible is True
    assert len(errors) == 0

    # Case 2: Required constraint fails
    context_fail = {"user": {"role": "user"}, "system": {"ready": True}}
    feasible, errors = recipe.check_feasibility(context_fail)
    assert feasible is False
    assert len(errors) == 1
    assert "Constraint failed" in errors[0]

    # Case 3: Optional constraint fails (should not fail feasibility)
    recipe_optional = RecipeDefinition(
        metadata=metadata,
        interface=interface,
        topology=topology,
        requirements=[Constraint(variable="user.role", operator="eq", value="admin", required=False)],
    )

    feasible, errors = recipe_optional.check_feasibility(context_fail)
    assert feasible is True
    assert len(errors) == 0

    # Case 4: Custom error message
    recipe_custom_msg = RecipeDefinition(
        metadata=metadata,
        interface=interface,
        topology=topology,
        requirements=[
            Constraint(variable="user.role", operator="eq", value="admin", error_message="User must be admin")
        ],
    )

    feasible, errors = recipe_custom_msg.check_feasibility(context_fail)
    assert feasible is False
    assert errors[0] == "User must be admin"
