# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_maco

from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field

from .definitions.agent import VersionStr
from .definitions.topology import GraphTopology


class RecipeManifest(BaseModel):
    """The executable specification for the MACO engine.

    Attributes:
        id: Unique identifier for the recipe.
        version: Version of the recipe.
        name: Human-readable name of the recipe.
        description: Detailed description of the recipe.
        inputs: Schema defining global variables this recipe accepts.
        graph: The topology definition of the workflow.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Unique identifier for the recipe.")
    version: VersionStr = Field(..., description="Version of the recipe.")
    name: str = Field(..., description="Human-readable name of the recipe.")
    description: Optional[str] = Field(None, description="Detailed description of the recipe.")
    inputs: Dict[str, Any] = Field(..., description="Schema defining global variables this recipe accepts.")
    graph: GraphTopology = Field(..., description="The topology definition of the workflow.")
