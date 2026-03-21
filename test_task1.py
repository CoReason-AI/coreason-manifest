from coreason_manifest.spec.ontology import ActionSpaceManifest, ToolManifest, PermissionBoundaryPolicy, SideEffectProfile
from pydantic import ValidationError

try:
    ActionSpaceManifest(
        action_space_id="test_id",
        native_tools=[
            ToolManifest(
                tool_name="test_tool",
                description="test tool",
                input_schema={
                    "type": "object",
                    "properties": {
                        "trace_context": {},
                        "state_vector": {},
                        "payload": {},
                        "system_prompt": {"type": "string"}
                    }
                },
                side_effects=SideEffectProfile(is_idempotent=True, mutates_state=False),
                permissions=PermissionBoundaryPolicy(network_access=False, file_system_mutation_forbidden=True)
            )
        ]
    )
    print("FAILED: Did not raise ValidationError on root leakage")
except ValidationError as e:
    print(f"SUCCESS: Caught ValidationError: {e}")
except Exception as e:
    print(f"FAILED: Caught unexpected exception: {e}")
