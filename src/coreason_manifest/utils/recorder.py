from datetime import UTC, datetime
from typing import Any

from coreason_manifest.spec.interop.telemetry import NodeExecution, NodeState
from coreason_manifest.utils.integrity import compute_hash
from coreason_manifest.utils.privacy import PrivacySentinel


class BlackBoxRecorder:
    """
    The main entry point for logging agent execution events.
    Handles data sanitization (Privacy), integrity chaining (Merkle),
    and structured logging (Telemetry).
    """

    def __init__(self, privacy_sentinel: PrivacySentinel | None = None) -> None:
        self.privacy = privacy_sentinel or PrivacySentinel()

    def record(
        self,
        node_id: str,
        state: NodeState,
        inputs: dict[str, Any],
        outputs: dict[str, Any],
        duration_ms: float,
        previous_hashes: list[str],
        timestamp: datetime | None = None,
        error: str | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> NodeExecution:
        """
        Records a single execution step.
        1. Sanitizes data.
        2. Computes integrity hash (linking to previous step).
        3. Returns immutable record.
        """
        if timestamp is None:
            timestamp = datetime.now(UTC)

        if attributes is None:
            attributes = {}

        # 1. Sanitize
        safe_inputs = self.privacy.sanitize(inputs)
        safe_outputs = self.privacy.sanitize(outputs)

        # Ensure sanitized data is dict (sanitize returns Any)
        if not isinstance(safe_inputs, dict):
            safe_inputs = {"_sanitized_value": safe_inputs}
        if not isinstance(safe_outputs, dict):
            safe_outputs = {"_sanitized_value": safe_outputs}

        # 2. Prepare payload for hashing
        # We construct a partial model or dict to hash.
        # It MUST include previous_hashes (sorted for determinism) to enforce the chain.
        # We exclude execution_hash (which we are computing) and signature (optional/external).
        payload = {
            "node_id": node_id,
            "state": state,
            "inputs": safe_inputs,
            "outputs": safe_outputs,
            "error": error,
            "timestamp": timestamp.isoformat(),  # Normalize datetime for consistent hashing
            "duration_ms": duration_ms,
            "attributes": attributes,
            "previous_hashes": sorted(previous_hashes),
        }

        # 3. Compute Hash
        execution_hash = compute_hash(payload)

        # 4. Construct Immutable Record
        return NodeExecution(
            node_id=node_id,
            state=state,
            inputs=safe_inputs,
            outputs=safe_outputs,
            error=error,
            timestamp=timestamp,
            duration_ms=duration_ms,
            attributes=attributes,
            previous_hashes=sorted(previous_hashes),
            execution_hash=execution_hash,
        )
