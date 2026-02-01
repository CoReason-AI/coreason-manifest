# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

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

from pydantic import ConfigDict, Field

from .definitions.agent import VersionStr
from .definitions.base import CoReasonBaseModel
from .definitions.topology import GraphTopology, StateDefinition


class RecipeInterface(CoReasonBaseModel):
    """Defines the input/output contract for a Recipe.

    Attributes:
        inputs: JSON Schema defining valid entry arguments.
        outputs: JSON Schema defining the guaranteed structure of the final result.
    """

    model_config = ConfigDict(extra="forbid")

    inputs: Dict[str, Any] = Field(..., description="JSON Schema defining valid entry arguments.")
    outputs: Dict[str, Any] = Field(
        ..., description="JSON Schema defining the guaranteed structure of the final result."
    )


class RecipeManifest(CoReasonBaseModel):
    """The executable specification for the MACO engine.

    Attributes:
        id: Unique identifier for the recipe.
        version: Version of the recipe.
        name: Human-readable name of the recipe.
        description: Detailed description of the recipe.
        interface: Defines the input/output contract for the Recipe.
        state: Defines the internal state (memory) of the Recipe.
        parameters: Dictionary of build-time constants.
        topology: The topology definition of the workflow.
        integrity_hash: SHA256 hash of the canonical JSON representation of the topology.
        metadata: Container for design-time data.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Unique identifier for the recipe.")
    version: VersionStr = Field(..., description="Version of the recipe.")
    name: str = Field(..., description="Human-readable name of the recipe.")
    description: Optional[str] = Field(None, description="Detailed description of the recipe.")
    interface: RecipeInterface = Field(..., description="Defines the input/output contract for the Recipe.")
    state: StateDefinition = Field(..., description="Defines the internal state (memory) of the Recipe.")
    parameters: Dict[str, Any] = Field(..., description="Dictionary of build-time constants.")
    topology: GraphTopology = Field(..., description="The topology definition of the workflow.")
    integrity_hash: Optional[str] = Field(
        default=None,
        description=(
            "SHA256 hash of the canonical JSON representation of the topology. "
            "Enforced by Builder, verified by Runtime."
        ),
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Container for design-time data (UI coordinates, resolution logs, draft status) to support re-hydration."
        ),
    )
