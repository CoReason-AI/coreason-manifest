from pydantic import Field

from coreason_manifest.spec.common_base import CoreasonModel
from coreason_manifest.spec.core.types import StrictJson


class SkillDefinition(CoreasonModel):
    """
    Definition of a procedural skill.
    """

    description: str | None = Field(None, description="Description of the skill.")
    parameters: dict[str, StrictJson] = Field(default_factory=dict, description="Parameters for the skill.")
