import json
from typing import Any

from coreason_manifest.spec.interop.telemetry import NodeExecution


def to_otel_attributes(execution: NodeExecution) -> dict[str, Any]:
    """
    Maps a NodeExecution event to OpenTelemetry Semantic Conventions.
    """
    attributes: dict[str, Any] = {
        "gen_ai.system": execution.node_id,
        # OTel attributes must be primitives or arrays of primitives.
        # Inputs/Outputs are dicts, so we serialize them to JSON strings.
        "gen_ai.request.content": json.dumps(execution.inputs, default=str),
        "gen_ai.response.content": json.dumps(execution.outputs, default=str),
        "duration": execution.duration_ms,
    }

    if execution.error:
        attributes["error.message"] = execution.error
        attributes["error.type"] = "NodeExecutionError"  # Generic error type

    # Merge custom attributes
    # We might need to handle naming collisions, but for now we trust the user/recorder.
    # Also ensure types are compatible with OTel (str, bool, int, float).
    if execution.attributes:
        attributes.update(execution.attributes)

    return attributes
