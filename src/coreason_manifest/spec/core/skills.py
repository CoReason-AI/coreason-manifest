from pydantic import Field

from coreason_manifest.spec.common_base import CoreasonModel
from coreason_manifest.spec.core.types import JsonDict


class SkillDefinition(CoreasonModel):
    """
    Definition of a procedural skill.
    """

    description: str | None = Field(None, description="Description of the skill.")
    parameters: JsonDict = Field(default_factory=dict, description="Parameters for the skill.")
