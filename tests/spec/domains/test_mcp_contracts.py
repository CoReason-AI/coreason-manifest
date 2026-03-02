import pytest
from coreason_manifest.core.domains.mcp_contracts import MCPToolName, MCPOperation

def test_mcp_tool_name_serialization() -> None:
    # Existing tool test
    op = MCPOperation(
        operation_id="op-1",
        tool_name=MCPToolName.CANVAS_ADD_ELEMENT,
        parameters={}
    )
    assert op.tool_name == "CANVAS_ADD_ELEMENT"

def test_mcp_tool_name_canvas_import_artifact() -> None:
    # Ensure CANVAS_IMPORT_ARTIFACT tool is serialized correctly
    op = MCPOperation(
        operation_id="op-import",
        tool_name=MCPToolName.CANVAS_IMPORT_ARTIFACT,
        target_element_id="node-123",
        parameters={
            "uri": "s3://bucket/artifacts/chart.svg"
        }
    )
    assert op.operation_id == "op-import"
    assert op.tool_name == "CANVAS_IMPORT_ARTIFACT"
    assert op.target_element_id == "node-123"
    assert op.parameters["uri"] == "s3://bucket/artifacts/chart.svg"

    # Serialization check
    serialized = op.model_dump()
    assert serialized["tool_name"] == "CANVAS_IMPORT_ARTIFACT"

    # Deserialization check
    deserialized = MCPOperation(**serialized)
    assert deserialized == op
