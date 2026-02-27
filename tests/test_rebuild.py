from typing import Annotated, Literal

from pydantic import Field, ValidationError

from coreason_manifest.spec.core.flow import GraphFlow
from coreason_manifest.spec.core.nodes import Node, register_node
from coreason_manifest.spec.core.rebuild import rebuild_manifest


# 1. Define a custom node
@register_node
class CustomTestNode(Node):
    type: Literal["custom_test"] = "custom_test"
    custom_field: str = Field(..., description="A custom field")


def test_rebuild_manifest():
    # 2. Construct a manifest payload using the custom node
    manifest_data = {
        "type": "graph",
        "kind": "GraphFlow",
        "metadata": {
            "name": "Test Flow",
            "version": "1.0.0"
        },
        "interface": {}, # Fix: Added interface
        "graph": {
            "nodes": {
                "node_1": {
                    "id": "node_1",
                    "type": "custom_test",
                    "custom_field": "hello world"
                }
            },
            "edges": []
        }
    }

    print("Attempting validation (expecting failure)...")
    try:
        GraphFlow.model_validate(manifest_data)
        print("UNEXPECTED SUCCESS: Validation passed without rebuild.")
        failed = False
    except ValidationError as e:
        print("Expected Failure caught:")
        print(e)
        failed = True

        # Verify it failed because of the union tag, not just missing field
        error_str = str(e)
        if "union_tag_invalid" not in error_str:
            print("WARNING: Validation failed but not due to union tag invalidity?")
            raise e

    if not failed:
        raise AssertionError("Validation should have failed before rebuild.")

    # 4. Rebuild the manifest
    print("Rebuilding manifest...")
    rebuild_manifest()

    # 5. Validation should SUCCEED now
    print("Attempting validation (expecting success)...")
    try:
        flow = GraphFlow.model_validate(manifest_data)
        print("SUCCESS: Validation passed after rebuild.")
        # Access the node to ensure it is typed correctly
        node = flow.graph.nodes["node_1"]
        # Since the static type checker doesn't know about CustomTestNode being in AnyNode union,
        # we check at runtime.
        assert node.type == "custom_test"
        assert getattr(node, "custom_field") == "hello world"
    except ValidationError as e:
        print("UNEXPECTED FAILURE after rebuild:")
        print(e)
        raise e

if __name__ == "__main__":
    test_rebuild_manifest()
