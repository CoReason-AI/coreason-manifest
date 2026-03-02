from typing import Any

from hypothesis import given
from hypothesis import strategies as st

from coreason_manifest.core.domains.mcp_contracts import (
    MCPOperation,
    MCPOperationSequence,
    MCPToolName,
)
from coreason_manifest.spec.domains.scivis_provenance import ActorIdentity, ActorType


@st.composite
def actor_identity_strategy(draw: st.DrawFn) -> ActorIdentity:
    return ActorIdentity(
        actor_type=draw(st.sampled_from(list(ActorType))),
        actor_version_or_id=draw(st.text(min_size=1)),
    )


@st.composite
def json_strategy(draw: st.DrawFn) -> Any:
    # A simplified JSON strategy for parameters
    return draw(
        st.recursive(
            st.none() | st.booleans() | st.floats(allow_nan=False, allow_infinity=False) | st.text(),
            lambda children: st.lists(children, max_size=3) | st.dictionaries(st.text(), children, max_size=3),
            max_leaves=5,
        )
    )


@st.composite
def mcp_operation_strategy(draw: st.DrawFn) -> MCPOperation:
    return MCPOperation(
        operation_id=draw(st.text(min_size=1)),
        tool_name=draw(st.sampled_from(list(MCPToolName))),
        target_element_id=draw(st.one_of(st.none(), st.text(min_size=1))),
        parameters=draw(st.dictionaries(st.text(), json_strategy(), max_size=3)),
        actor=draw(st.one_of(st.none(), actor_identity_strategy())),
    )


@st.composite
def mcp_operation_sequence_strategy(draw: st.DrawFn) -> MCPOperationSequence:
    return MCPOperationSequence(
        sequence_id=draw(st.text(min_size=1)),
        operations=draw(st.lists(mcp_operation_strategy(), max_size=5)),
        transaction_mode=draw(st.sampled_from(["atomic_commit", "sequential_best_effort"])),
        expected_canvas_state_hash=draw(st.one_of(st.none(), st.text(min_size=1))),
    )


@given(mcp_operation_strategy())
def test_mcp_operation_round_trip(operation: MCPOperation) -> None:
    json_data = operation.model_dump_json()
    loaded_operation = MCPOperation.model_validate_json(json_data)
    assert operation == loaded_operation


@given(mcp_operation_sequence_strategy())
def test_mcp_operation_sequence_round_trip(sequence: MCPOperationSequence) -> None:
    json_data = sequence.model_dump_json()
    loaded_sequence = MCPOperationSequence.model_validate_json(json_data)
    assert sequence == loaded_sequence
