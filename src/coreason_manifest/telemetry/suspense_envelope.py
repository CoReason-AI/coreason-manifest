from typing import Literal

from pydantic import Field

from coreason_manifest.presentation.streaming import SuspenseConfig
from coreason_manifest.state.events import EpistemicEvent
from coreason_manifest.telemetry.stream_base import BaseEnvelope
from coreason_manifest.telemetry.telemetry_schemas import AgentSignature, HardwareFingerprint


class StreamSuspenseEnvelope(BaseEnvelope):
    op: Literal["suspense_mount"] = Field("suspense_mount", description="Discriminator field.")
    p: SuspenseConfig = Field(..., description="Suspense config payload.")
    target_node_id: str | None = Field(default=None, description="Optional target node ID.")
    hardware_fingerprint: HardwareFingerprint | None = Field(default=None, description="Hardware fingerprint.")
    agent_signature: AgentSignature | None = Field(default=None, description="Agent footprint.")
    ledger_history_snapshot: list[EpistemicEvent] = Field(
        default_factory=list, description="Static snapshot of the ledger history."
    )
