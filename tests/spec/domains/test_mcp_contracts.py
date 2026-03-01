from typing import Any

from hypothesis import given
from hypothesis import strategies as st

from coreason_manifest.spec.domains.mcp_contracts import MCPOperation, MCPOperationSequence, MCPToolName


def test_mcp_tool_name_serialization() -> None:
    """Validate JSON serialization of the MCPToolName enum."""

    class DummyModel(MCPOperation):
        pass

    op = MCPOperation(
        operation_id="123", tool_name=MCPToolName.CANVAS_ADD_ELEMENT, target_element_id="abc", parameters={"x": 10}
    )

    json_str = op.model_dump_json()
    assert '"CANVAS_ADD_ELEMENT"' in json_str

    deserialized = MCPOperation.model_validate_json(json_str)
    assert deserialized.tool_name == MCPToolName.CANVAS_ADD_ELEMENT


# Strategy to generate valid JSON-like parameters
# The parameters must be a dictionary, so we wrap the recursive strategy in a dictionary.
json_types = st.text() | st.integers() | st.floats(allow_nan=False, allow_infinity=False) | st.booleans() | st.none()
json_recursive = st.recursive(
    json_types,
    lambda children: st.dictionaries(st.text(), children) | st.lists(children),
    max_leaves=10,
)
json_dict_strategy = st.dictionaries(st.text(), json_recursive)


@given(
    operation_id=st.text(min_size=1),
    tool_name=st.sampled_from(MCPToolName),
    target_element_id=st.one_of(st.none(), st.text(min_size=1)),
    parameters=json_dict_strategy,
)
def test_mcp_operation_fuzzing(
    operation_id: str,
    tool_name: MCPToolName,
    target_element_id: str | None,
    parameters: dict[str, Any],
) -> None:
    """Fuzz the generation of MCPOperation payloads."""
    op = MCPOperation(
        operation_id=operation_id,
        tool_name=tool_name,
        target_element_id=target_element_id,
        parameters=parameters,
    )

    # Test serialization and deserialization
    json_str = op.model_dump_json()
    deserialized = MCPOperation.model_validate_json(json_str)

    assert deserialized.operation_id == operation_id
    assert deserialized.tool_name == tool_name
    assert deserialized.target_element_id == target_element_id
    assert deserialized.parameters == parameters


@given(
    sequence_id=st.text(min_size=1),
    operations=st.lists(
        st.builds(
            MCPOperation,
            operation_id=st.text(min_size=1),
            tool_name=st.sampled_from(MCPToolName),
            target_element_id=st.one_of(st.none(), st.text(min_size=1)),
            parameters=json_dict_strategy,
        ),
        min_size=0,
        max_size=5,
    ),
    transaction_mode=st.sampled_from(["atomic_commit", "sequential_best_effort"]),
    expected_canvas_state_hash=st.one_of(st.none(), st.text(min_size=1)),
)
def test_mcp_operation_sequence_fuzzing(
    sequence_id: str,
    operations: list[MCPOperation],
    transaction_mode: str,
    expected_canvas_state_hash: str | None,
) -> None:
    """Fuzz the generation of MCPOperationSequence payloads."""
    seq = MCPOperationSequence(
        sequence_id=sequence_id,
        operations=operations,
        transaction_mode=transaction_mode,
        expected_canvas_state_hash=expected_canvas_state_hash,
    )

    json_str = seq.model_dump_json()
    deserialized = MCPOperationSequence.model_validate_json(json_str)

    assert deserialized.sequence_id == sequence_id
    assert len(deserialized.operations) == len(operations)
    assert deserialized.transaction_mode == transaction_mode
    assert deserialized.expected_canvas_state_hash == expected_canvas_state_hash
