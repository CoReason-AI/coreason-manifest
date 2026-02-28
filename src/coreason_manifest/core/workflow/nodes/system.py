# Prosperity-3.0
from typing import Literal

from pydantic import Field

from coreason_manifest.core.primitives.registry import register_node
from coreason_manifest.core.primitives.types import CoercibleStringList

from .base import Node


@register_node
class PlaceholderNode(Node):
    type: Literal["placeholder"] = "placeholder"
    required_capabilities: CoercibleStringList = Field(
        ..., description="List of required capabilities.", examples=[["image_generation"]]
    )
