# src/coreason_manifest/spec/core/registry.py

from typing import TYPE_CHECKING, Annotated, Any, TypeVar, Union

from pydantic import Field

if TYPE_CHECKING:
    from coreason_manifest.spec.core.engines import BaseReasoning
    from coreason_manifest.spec.core.nodes import Node


TNode = TypeVar("TNode", bound="Node")
TEngine = TypeVar("TEngine", bound="BaseReasoning")

# Global registries
_NODE_REGISTRY: dict[str, type["Node"]] = {}
_ENGINE_REGISTRY: dict[str, type["BaseReasoning"]] = {}


def register_node(node_type: type["Node"]) -> type["Node"]:
    """
    Register a new Node type.
    """
    # We rely on the 'type' literal field for discrimination
    # Pydantic models usually have this field defined as a Literal.
    # We inspect the model to find the 'type' field default or annotation.

    # However, Pydantic V2 models don't easily expose the literal value without instantiation
    # or deep inspection of model_fields.
    # We assume the user follows the convention of defining `type: Literal["my_type"] = "my_type"`

    # Let's instantiate a dummy if possible? No, fields might be required.
    # Let's check model_fields['type'].default

    type_field = node_type.model_fields.get("type")
    if not type_field:
        raise ValueError(f"Node {node_type.__name__} must have a 'type' field.")

    # In Pydantic V2, default might be the value.
    # If it is a Literal, the annotation might tell us.
    discriminator_value = type_field.default

    # If default is PydanticUndefined, maybe it is required?
    # But for a discriminated union, it should be a Literal with a single value (or we use the class name?)
    # The existing codebase uses `type: Literal["agent"] = "agent"`.

    if discriminator_value is None or discriminator_value is ...:
        # Try to infer from annotation if it is a Literal
        # This is getting complicated.
        # Let's trust that we can key by the value that will be used in the discriminator.
        # But for registration we need the key.
        pass

    # Actually, we don't strictly need the key for the registry dict if we build the Union from values.
    # But it's good to have.

    # Simpler approach: We register the class. The Union will be `Union[*_NODE_REGISTRY.values()]`.
    # We key by class name to avoid duplicates.
    _NODE_REGISTRY[node_type.__name__] = node_type
    return node_type


def register_engine(engine_type: type["BaseReasoning"]) -> type["BaseReasoning"]:
    """
    Register a new Reasoning Engine type.
    """
    _ENGINE_REGISTRY[engine_type.__name__] = engine_type
    return engine_type


def resolve_node_union() -> Any:
    """
    Returns a Pydantic-compatible Union of all registered Node types,
    discriminated by 'type'.
    """
    # Create a union of all registered types
    # Note: We need to handle the case where registry is empty? (Shouldn't happen if core nodes are registered)

    nodes = list(_NODE_REGISTRY.values())
    if not nodes:
        return Any

    union_type = Union[tuple(nodes)]  # type: ignore  # noqa: UP007

    return Annotated[union_type, Field(discriminator="type")]


def resolve_engine_union() -> Any:
    """
    Returns a Pydantic-compatible Union of all registered Engine types,
    discriminated by 'type'.
    """
    engines = list(_ENGINE_REGISTRY.values())
    if not engines:
        return Any

    union_type = Union[tuple(engines)]  # type: ignore  # noqa: UP007

    return Annotated[union_type, Field(discriminator="type")]
