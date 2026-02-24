import os
import secrets
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from coreason_manifest.spec.core.governance import Governance
from coreason_manifest.spec.interop.telemetry import NodeExecution, NodeState
from coreason_manifest.utils.integrity import compute_hash, to_canonical_timestamp
from coreason_manifest.utils.privacy import PrivacySentinel

# Process-scoped fallback salt for consistent intra-process correlation
_PROCESS_FALLBACK_SALT = secrets.token_hex(16)


class BlackBoxRecorder:
    """
    The main entry point for logging agent execution events.
    Handles data sanitization (Privacy), integrity chaining (Merkle),
    and structured logging (Telemetry).
    """

    def __init__(self, privacy_sentinel: PrivacySentinel, log_payloads: bool = True) -> None:
        self.privacy = privacy_sentinel
        self.log_payloads = log_payloads

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
        Records a single execution step.
        1. Sanitizes data.
        2. Computes integrity hash (linking to previous step).
        3. Returns immutable record.
        """
        if timestamp is None:
            timestamp = datetime.now(UTC)

        if attributes is None:
            attributes = {}

        # 0. Enforce Audit Policy: Omit Payloads
        # This happens BEFORE sanitization and BEFORE hashing.
        if not self.log_payloads:
            omitted_marker = {"_omitted": "policy_log_payloads_false"}
            inputs = omitted_marker
            outputs = omitted_marker

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
        # It MUST include parent_hashes (sorted for determinism) to enforce the chain.
        # We exclude execution_hash (which we are computing) and signature (optional/external).

        # Architecture: Generate Trace IDs explicitly to ensure hash consistency.
        # NodeExecution would auto-generate them, but we need them for the hash calculation.
        resolved_request_id = request_id or str(uuid4())
        # Default behavior: If we don't know parent, we are root.
        resolved_root_request_id = root_request_id or resolved_request_id

        payload = {
            "node_id": node_id,
            "state": state,
            "inputs": safe_inputs,
            "outputs": safe_outputs,
            "error": error,
            "timestamp": to_canonical_timestamp(timestamp),
            "duration_ms": duration_ms,
            "attributes": attributes,
            "parent_hashes": sorted(parent_hashes),
            "hash_version": "v2",
            "request_id": resolved_request_id,
            "root_request_id": resolved_root_request_id,
            "parent_request_id": parent_request_id,
            "traceparent": traceparent,
            "tracestate": tracestate,
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
            parent_hashes=sorted(parent_hashes),
            execution_hash=execution_hash,
            request_id=resolved_request_id,
            parent_request_id=parent_request_id,
            root_request_id=resolved_root_request_id,
            traceparent=traceparent,
            tracestate=tracestate,
        )


def create_recorder(governance_config: Governance | None = None, system_salt: str | None = None) -> BlackBoxRecorder:
    """
    Factory function to create a BlackBoxRecorder with strict dependency injection.
    Resolves the privacy configuration from the Governance model.
    """
    # Fail-Safe Default: Most restrictive posture
    redact_pii = True
    log_payloads = False  # Default to False if strict/missing

    if governance_config:
        if governance_config.safety:
            redact_pii = governance_config.safety.pii_redaction
        if governance_config.audit:
            log_payloads = governance_config.audit.log_payloads

    # Salt Resolution Logic
    # 1. Use system_salt if provided
    # 2. Else, try OS env var
    # 3. Else, use process-scoped fallback
    final_salt = system_salt or os.getenv("COREASON_AUDIT_SALT") or _PROCESS_FALLBACK_SALT

    # Instantiate Sentinel with explicit configuration
    sentinel = PrivacySentinel(redact_pii=redact_pii, redact_secrets=True, hashing_salt=final_salt)

    # Return Recorder injected with the sentinel
    return BlackBoxRecorder(privacy_sentinel=sentinel, log_payloads=log_payloads)
