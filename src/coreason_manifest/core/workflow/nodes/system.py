# Prosperity-3.0
from typing import Literal

from pydantic import Field

from coreason_manifest.core.primitives.types import CoercibleStringList

from .base import Node


class PlaceholderNode(Node):
    """A node that acts as a placeholder requiring specific capabilities to be fulfilled."""

    type: Literal["placeholder"] = Field("placeholder", description="The type of the node.", examples=["placeholder"])
    required_capabilities: CoercibleStringList = Field(
        ..., description="List of required capabilities.", examples=[["image_generation"]]
    )
