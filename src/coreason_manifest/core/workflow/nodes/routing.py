# Prosperity-3.0
from typing import Literal

from pydantic import Field

from coreason_manifest.core.primitives.registry import register_node
from coreason_manifest.core.primitives.types import NodeID, VariableID

from .base import Node


@register_node
class SwitchNode(Node):
    """A node that routes execution based on the value of a blackboard variable."""

    type: Literal["switch"] = Field("switch", description="The type of the node.", examples=["switch"])
    variable: VariableID = Field(..., description="The blackboard variable to evaluate.", examples=["user_sentiment"])
    cases: dict[str, NodeID] = Field(
        ...,
        description="Map of variable values to next node IDs.",
        examples=[{"positive": "thank_user", "negative": "apologize"}],
    )
    default: NodeID = Field(..., description="Default next node ID if no case matches.", examples=["default_handler"])
