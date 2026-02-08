# src/coreason_manifest/spec/v2/agent.py

from pydantic import ConfigDict, Field

from coreason_manifest.spec.common_base import CoReasonBaseModel
from coreason_manifest.spec.v2.knowledge import RetrievalConfig


class CognitiveProfile(CoReasonBaseModel):
    """Configuration for the internal reasoning architecture of an agent."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, frozen=True)

    role: str = Field(..., description="The role or persona of the agent.")
    reasoning_mode: str = Field(..., description="The reasoning mode (e.g., 'react', 'cot').")

    # --- New Field for Archive Support ---
    memory: list[RetrievalConfig] = Field(
        default_factory=list, description="Configuration for Long-Term Memory (RAG) access."
    )

    knowledge_contexts: list[str] = Field(default_factory=list, description="List of knowledge context IDs.")
    task_primitive: str | None = Field(None, description="The task primitive to execute.")
