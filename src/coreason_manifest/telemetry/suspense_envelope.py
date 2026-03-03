from typing import Literal

from pydantic import Field

from coreason_manifest.core.common.suspense import SuspenseConfig
from coreason_manifest.state.events import EpistemicEvent
from coreason_manifest.telemetry.stream_base import BaseEnvelope
from coreason_manifest.telemetry.telemetry_schemas import AgentSignature, HardwareFingerprint


class StreamSuspenseEnvelope(BaseEnvelope):
    op: Literal["suspense_mount"]
    p: SuspenseConfig
    target_node_id: str | None = None
    hardware_fingerprint: HardwareFingerprint | None = Field(default=None, description="Hardware fingerprint.")
    agent_signature: AgentSignature | None = Field(default=None, description="Agent footprint.")
    ledger_history_snapshot: list[EpistemicEvent] = Field(
        default_factory=list, description="Static snapshot of the ledger history."
    )
