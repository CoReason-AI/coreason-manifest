import json
from typing import Any

from coreason_manifest.spec.interop.telemetry import NodeExecution


def to_otel_attributes(execution: NodeExecution) -> dict[str, Any]:
    """
    Maps a NodeExecution event to OpenTelemetry Semantic Conventions.
    """
    attributes: dict[str, Any] = {
        "gen_ai.system": execution.node_id,
        "gen_ai.request.content": json.dumps(execution.inputs, default=str),
        "gen_ai.response.content": json.dumps(execution.outputs, default=str),
        "duration": execution.duration_ms,
    }

    if execution.error:
        attributes["error.message"] = execution.error
        attributes["error.type"] = "NodeExecutionError"

    # Lineage support: Propagate trace IDs if present in attributes
    # The caller is responsible for ensuring 'trace_id' or 'parent_span_id' are in execution.attributes if needed.

    if execution.attributes:
        # Filter/Redact attributes here if necessary, though ObservableModel handles its own redaction.
        attributes.update(execution.attributes)

    # SOTA: Diagnosis Report Attachment
    # If a diagnosis report is present in attributes (e.g. from resilience), ensure it's serialized properly
    if "diagnosis_report" in attributes and not isinstance(
        attributes["diagnosis_report"], (str, int, float, bool)
    ):
        attributes["diagnosis_report"] = json.dumps(attributes["diagnosis_report"], default=str)

    return attributes
