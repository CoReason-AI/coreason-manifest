from enum import StrEnum

from pydantic import Field

from coreason_manifest.core.common.base import CoreasonModel


class ActorType(StrEnum):
    SYSTEM_ORCHESTRATOR = "SYSTEM_ORCHESTRATOR"
    AI_SEMANTIC_AGENT = "AI_SEMANTIC_AGENT"
    AI_LAYOUT_SOLVER = "AI_LAYOUT_SOLVER"
    HUMAN_EXPERT = "HUMAN_EXPERT"


class ActorIdentity(CoreasonModel):
    actor_type: ActorType
    actor_version_or_id: str = Field(..., description="e.g., 'gemini-3.1-pro' or human 'user_uuid_123'")


class ElementAttribution(CoreasonModel):
    target_element_id: str
    created_by: ActorIdentity
    last_modified_by: ActorIdentity
    was_human_verified: bool = Field(default=False)


class ExecutionAudit(CoreasonModel):
    target_element_id: str
    dataset_checksum: str | None = None
    execution_script_hash: str | None = None


class StateHashLog(CoreasonModel):
    intent_hash: str
    semantic_ast_hash: str
    spatial_ast_hash: str


class ProvenanceManifest(CoreasonModel):
    manifest_id: str
    timestamp_utc: str
    state_chain: StateHashLog
    element_attributions: list[ElementAttribution]
    execution_audits: list[ExecutionAudit] = Field(default_factory=list)
    is_journal_compliant: bool = Field(
        default=False, description="Should be computed/validated true if human verified the critical nodes."
    )
