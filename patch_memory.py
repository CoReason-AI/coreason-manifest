from pydantic import Field
from coreason_manifest.core.base import CoreasonBaseModel

class TheoryOfMindSnapshot(CoreasonBaseModel):
    target_agent_id: str = Field(min_length=1, description="The ID of the agent whose mind is being modeled.")
    assumed_shared_beliefs: list[str] = Field(description="A list of SemanticNode IDs that the modeling agent assumes the target already possesses.")
    identified_knowledge_gaps: list[str] = Field(description="Specific topics or logical premises the target agent is assumed to be missing.")
    empathy_confidence_score: float = Field(ge=0.0, le=1.0, description="The mathematical confidence (0.0 to 1.0) the agent has in its model of the target's mind.")
