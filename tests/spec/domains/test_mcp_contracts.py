def test_mcp_operation_with_canvas_import_artifact():
    from coreason_manifest.core.domains.mcp_contracts import MCPOperation, MCPToolName

    op = MCPOperation(
        operation_id="op-123",
        tool_name=MCPToolName.CANVAS_IMPORT_ARTIFACT,
        parameters={"uri": "s3://some/bucket/naked.svg", "x": 100, "y": 200},
    )
    assert op.tool_name == "CANVAS_IMPORT_ARTIFACT"
    assert op.parameters["uri"] == "s3://some/bucket/naked.svg"
