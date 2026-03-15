from coreason_manifest.spec.ontology import (
    ActionSpaceManifest,
    PermissionBoundaryPolicy,
    SideEffectProfile,
    ToolManifest,
)
from coreason_manifest.utils.algebra import compile_action_space_to_openai_tools


def test_compile_action_space_to_openai_tools():
    """Test the compilation of ActionSpaceManifest to OpenAI tool format."""
    manifest = ActionSpaceManifest(
        action_space_id="test-action-space",
        native_tools=[
            ToolManifest(
                tool_name="test_tool",
                description="A test tool",
                input_schema={"type": "object", "properties": {"param1": {"type": "string"}}, "required": ["param1"]},
                side_effects=SideEffectProfile(is_idempotent=True, mutates_state=False),
                permissions=PermissionBoundaryPolicy(network_access=False, file_system_mutation_forbidden=True),
            )
        ],
    )

    tools_payload = compile_action_space_to_openai_tools(manifest)

    assert isinstance(tools_payload, list)
    assert len(tools_payload) == 1
    assert tools_payload[0] == {
        "type": "function",
        "function": {
            "name": "test_tool",
            "description": "A test tool",
            "parameters": {"type": "object", "properties": {"param1": {"type": "string"}}, "required": ["param1"]},
        },
    }


def test_compile_action_space_to_openai_tools_empty():
    """Test the compilation of an empty ActionSpaceManifest to OpenAI tool format."""
    manifest = ActionSpaceManifest(action_space_id="test-action-space-empty", native_tools=[])

    tools_payload = compile_action_space_to_openai_tools(manifest)

    assert isinstance(tools_payload, list)
    assert len(tools_payload) == 0
