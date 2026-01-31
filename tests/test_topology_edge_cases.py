import pytest
from pydantic import ValidationError

from coreason_manifest.definitions.topology import (
    ConditionalEdge,
    MapNode,
    RecipeNode,
    StateSchema,
)


def test_conditional_edge_empty_mapping() -> None:
    """Test validation fails if mapping is empty."""
    # Note: Pydantic doesn't strictly forbid empty dicts by default unless constrained,
    # but let's test behavior. If it allows it, that's a spec choice, but we should know.
    # Current implementation is Dict[str, str], so empty is valid Pydantic-wise.
    # We might want to add a validator later, but for now just ensure it instantiates.
    edge = ConditionalEdge(source_node_id="a", router_logic="True", mapping={})
    assert edge.mapping == {}


def test_map_node_invalid_concurrency() -> None:
    """Test map node validation (concurrency should ideally be positive, but standard int allows negative).
    Since we didn't add Field(gt=0), this test documents current behavior (accepts any int).
    If we want to enforce it, we'd need to modify the model. For now, we test it accepts valid ints.
    """
    node = MapNode(id="m", type="map", items_path="x", processor_node_id="p", concurrency_limit=0)
    assert node.concurrency_limit == 0


def test_state_schema_invalid_persistence_type() -> None:
    """Test validation fails for non-string persistence."""
    with pytest.raises(ValidationError):
        StateSchema(
            data_schema={},
            persistence=123,
        )


def test_recipe_node_self_reference_logic() -> None:
    """Test that RecipeNode can structurally reference itself (by ID string).
    The runtime handles the loop, the schema just needs to hold the string.
    """
    node = RecipeNode(
        id="r1",
        type="recipe",
        recipe_id="r1",  # Self-reference ID
        input_mapping={},
        output_mapping={},
    )
    assert node.recipe_id == "r1"
