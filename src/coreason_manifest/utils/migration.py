# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from ..spec.common.graph_events import GraphEvent
from ..spec.common.observability import CloudEvent, EventContentType


class ExtendedCloudEvent(CloudEvent):
    """
    Internal subclass of CloudEvent to support frontend-specific extensions.
    This ensures that when dumped, the extra fields are included.
    """

    com_coreason_ui_cue: str | None = None


def migrate_graph_event_to_cloud_event(event: GraphEvent) -> CloudEvent:
    """
    Migrates a strict internal GraphEvent to a standard CloudEvent for external observability.
    """
    # 1. Map Type: Convert NODE_START -> ai.coreason.node.start
    # We replace underscores with dots and lowercase everything.
    event_type_suffix = event.event_type.lower().replace("_", ".")
    ce_type = f"ai.coreason.{event_type_suffix}"

    # 2. Map Source: urn:node:{event.node_id}
    source = f"urn:node:{event.node_id}"

    # 3. Map Content Type and Data
    content_type = EventContentType.JSON
    data: dict[str, Any] = {}

    if event.event_type == "NODE_STREAM":
        content_type = EventContentType.STREAM
        data = {"chunk": event.chunk}
    elif event.event_type == "ERROR":
        content_type = EventContentType.ERROR
        data = {
            "error_message": event.error_message,
            "stack_trace": event.stack_trace,
        }
    elif event.event_type == "ARTIFACT_GENERATED":
        content_type = EventContentType.ARTIFACT
        data = {"artifact_type": event.artifact_type, "url": event.url}
    elif event.event_type == "NODE_START":
        data = event.payload
    elif event.event_type == "NODE_DONE":
        data = event.output
    elif event.event_type == "COUNCIL_VOTE":
        data = {"votes": event.votes}
    elif event.event_type == "NODE_RESTORED":
        data = {"status": event.status}

    # 4. Extensions
    # Map trace_id -> traceparent
    # Map visual_cue -> com_coreason_ui_cue

    # We generate a unique ID for the CloudEvent as GraphEvent only has run_id/trace_id
    event_id = str(uuid4())

    return ExtendedCloudEvent(
        id=event_id,
        source=source,
        type=ce_type,
        time=datetime.fromtimestamp(event.timestamp, tz=UTC),
        datacontenttype=content_type,
        data=data,
        traceparent=event.trace_id,
        com_coreason_ui_cue=event.visual_cue,
    )
