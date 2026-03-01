from typing import Literal

from coreason_manifest.core.common.suspense import SuspenseConfig
from coreason_manifest.core.telemetry.stream import BaseEnvelope


class StreamSuspenseEnvelope(BaseEnvelope):
    op: Literal["suspense_mount"]
    p: SuspenseConfig
    target_node_id: str | None = None
