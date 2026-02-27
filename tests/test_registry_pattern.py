import pytest
from typing import Literal
from pydantic import Field, ValidationError

from coreason_manifest.spec.core.nodes import Node, AnyNode
from coreason_manifest.spec.core.registry import register_node, resolve_node_union, _NODE_REGISTRY

def test_dynamic_node_registration():
    # 1. Define a new custom node type
    @register_node
    class CustomNode(Node):
        type: Literal["custom_plugin"] = "custom_plugin"
        custom_field: str = Field(..., description="A custom field")

    # 2. Verify it's in the registry
    assert "CustomNode" in _NODE_REGISTRY
    assert _NODE_REGISTRY["CustomNode"] == CustomNode

    # 3. Resolve the union.
    # NOTE: AnyNode imported from spec.core.nodes is statically defined at import time.
    # To see the update, we must re-resolve or use resolve_node_union() directly.
    # However, existing models (like GraphFlow) that use AnyNode won't automatically update
    # unless we rebuild them or if AnyNode uses a deferred resolution mechanism (which Pydantic V2 doesn't support natively for runtime updates easily).

    # In this specific implementation, `AnyNode = resolve_node_union()` happens at module level in `nodes.py`.
    # So `AnyNode` is frozen at import time of `nodes.py`.
    # To support dynamic plugins, we would need to reload `nodes.py` or `flow.py`, or
    # use a mechanism where AnyNode is a TypeAdapter that we update.

    # But for this task, "Introduce a dynamic registry pattern... allowing downstream packages to inject new Node types without altering the coreason-manifest core files".
    # If the downstream package imports `register_node` and registers their node BEFORE importing `AnyNode` (or `GraphFlow`),
    # then `AnyNode` will include it.

    # But if `AnyNode` is already imported, it won't.
    # Let's verify that `resolve_node_union()` returns a union containing CustomNode.

    NewAnyNode = resolve_node_union()

    # 4. Instantiate the new node via the new union
    from pydantic import TypeAdapter
    ta = TypeAdapter(NewAnyNode)

    data = {
        "id": "c1",
        "type": "custom_plugin",
        "custom_field": "hello"
    }

    obj = ta.validate_python(data)
    assert isinstance(obj, CustomNode)
    assert obj.custom_field == "hello"

def test_registry_persistence():
    # Verify standard nodes are present
    assert "AgentNode" in _NODE_REGISTRY
    assert "SwitchNode" in _NODE_REGISTRY
