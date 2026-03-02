from typing import Literal

from coreason_manifest.core.common.suspense import SuspenseConfig
from coreason_manifest.core.telemetry.stream_base import BaseEnvelope
from coreason_manifest.core.telemetry.custody import EpistemicEnvelope, EpistemicLedger
from coreason_manifest.core.telemetry.telemetry_schemas import HardwareFingerprint


from pydantic import ConfigDict

class StreamSuspenseEnvelope(BaseEnvelope):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid", strict=True, frozen=True)

    op: Literal["suspense_mount"]
    p: SuspenseConfig
    target_node_id: str | None = None
    reasoning_trace: str | None = None
    epistemic_envelope: EpistemicEnvelope | None = None
    hardware_fingerprint: HardwareFingerprint | None = None
    epistemic_ledger: EpistemicLedger | None = None
