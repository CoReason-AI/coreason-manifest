from datetime import datetime
from typing import Any, Protocol

from coreason_manifest.core.telemetry.telemetry_schemas import NodeExecution, NodeState


class TelemetryRecorder(Protocol):
    """
    Protocol defining the contract for observability pipelines to record execution traces.
    """

    def record(
        self,
        node_id: str,
        state: NodeState,
        inputs: dict[str, Any],
        outputs: dict[str, Any],
        duration_ms: float,
        parent_hashes: list[str],
        timestamp: datetime | None = None,
        error: str | None = None,
        attributes: dict[str, Any] | None = None,
        *,  # Force Keyword-Only Args for Trace Context
        request_id: str | None = None,
        parent_request_id: str | None = None,
        root_request_id: str | None = None,
        traceparent: str | None = None,
        tracestate: str | None = None,
    ) -> NodeExecution:
        """
        Records a single step or execution trace, returning a structured summary instance.
        """
        ...
