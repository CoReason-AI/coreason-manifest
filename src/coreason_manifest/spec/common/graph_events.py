# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any, Literal

from pydantic import ConfigDict, Field

from ..common_base import CoReasonBaseModel


class GraphEventBase(CoReasonBaseModel):
    model_config = ConfigDict(frozen=True)

    run_id: str
    trace_id: str
    node_id: str
    timestamp: float
    sequence_id: int | None = None
    visual_cue: str | None = None


class GraphEventNodeStart(GraphEventBase):
    event_type: Literal["NODE_START"] = "NODE_START"
    payload: dict[str, Any]


class GraphEventNodeStream(GraphEventBase):
    event_type: Literal["NODE_STREAM"] = "NODE_STREAM"
    chunk: str
    stream_id: str = Field("default", description="The logical stream ID.")


class GraphEventStreamStart(GraphEventBase):
    event_type: Literal["STREAM_START"] = "STREAM_START"
    stream_id: str
    name: str | None = None
    content_type: str


class GraphEventStreamEnd(GraphEventBase):
    event_type: Literal["STREAM_END"] = "STREAM_END"
    stream_id: str


class GraphEventNodeDone(GraphEventBase):
    event_type: Literal["NODE_DONE"] = "NODE_DONE"
    output: dict[str, Any]


class GraphEventError(GraphEventBase):
    event_type: Literal["ERROR"] = "ERROR"
    error_message: str
    stack_trace: str | None = None


class GraphEventCouncilVote(GraphEventBase):
    event_type: Literal["COUNCIL_VOTE"] = "COUNCIL_VOTE"
    votes: dict[str, Any]


class GraphEventNodeRestored(GraphEventBase):
    event_type: Literal["NODE_RESTORED"] = "NODE_RESTORED"
    status: str


class GraphEventArtifactGenerated(GraphEventBase):
    event_type: Literal["ARTIFACT_GENERATED"] = "ARTIFACT_GENERATED"
    artifact_type: str
    url: str


GraphEvent = (
    GraphEventNodeStart
    | GraphEventNodeStream
    | GraphEventStreamStart
    | GraphEventStreamEnd
    | GraphEventNodeDone
    | GraphEventError
    | GraphEventCouncilVote
    | GraphEventNodeRestored
    | GraphEventArtifactGenerated
)
