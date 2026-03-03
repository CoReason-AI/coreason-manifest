from typing import Literal

from pydantic import ConfigDict, Field

from coreason_manifest.core.workflow.nodes.base import Node


class ExtractorNode(Node):
    """
    Watches for raw document upload events.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    type: Literal["extractor"] = Field("extractor", description="The type of the node.")


class SemanticNode(Node):
    """
    Watches for STRUCTURAL_MILESTONE events.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    type: Literal["semantic"] = Field("semantic", description="The type of the node.")


class AuditorNode(Node):
    """
    Watches for SEMANTIC_MILESTONE events.
    """

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    type: Literal["auditor"] = Field("auditor", description="The type of the node.")
