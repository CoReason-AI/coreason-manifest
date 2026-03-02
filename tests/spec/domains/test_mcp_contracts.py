def test_mcp_operation_with_canvas_import_artifact():
    from coreason_manifest.core.domains.mcp_contracts import MCPOperation, MCPToolName

    op = MCPOperation(
        operation_id="op-123",
        tool_name=MCPToolName.CANVAS_IMPORT_ARTIFACT,
        parameters={"uri": "s3://some/bucket/naked.svg", "x": 100, "y": 200},
    )
    assert op.tool_name == "CANVAS_IMPORT_ARTIFACT"
    assert op.parameters["uri"] == "s3://some/bucket/naked.svg"
from coreason_manifest.core.domains.mcp_contracts import (
    MCPOperation,
    MCPOperationSequence,
    MCPToolName,
)


def test_mcp_operation_serialization() -> None:
    operation = MCPOperation(
        operation_id="op_1",
        tool_name=MCPToolName.CANVAS_ADD_MATH_NODE,
        target_element_id="math_node_1",
        parameters={"latex": "\\sum x", "mode": "display"},
    )

    assert operation.tool_name == "CANVAS_ADD_MATH_NODE"

    json_str = operation.model_dump_json()
    assert "CANVAS_ADD_MATH_NODE" in json_str

    parsed_op = MCPOperation.model_validate_json(json_str)
    assert parsed_op.tool_name == MCPToolName.CANVAS_ADD_MATH_NODE


def test_mcp_operation_sequence() -> None:
    seq = MCPOperationSequence(
        sequence_id="seq_1",
        operations=[
            MCPOperation(
                operation_id="op_1",
                tool_name=MCPToolName.CANVAS_ADD_MATH_NODE,
                parameters={"latex": "E = mc^2"},
            ),
            MCPOperation(
                operation_id="op_2",
                tool_name=MCPToolName.CANVAS_UPDATE_MATH_NODE,
                target_element_id="node_1",
                parameters={"latex": "E = mc^2 + \\epsilon"},
            ),
        ],
        transaction_mode="atomic_commit",
    )

    assert len(seq.operations) == 2
    assert seq.operations[0].tool_name == MCPToolName.CANVAS_ADD_MATH_NODE
    assert seq.operations[1].tool_name == MCPToolName.CANVAS_UPDATE_MATH_NODE
