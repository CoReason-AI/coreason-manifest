# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any, Dict, Literal, Optional, Union
from pydantic import ConfigDict
from ..common import CoReasonBaseModel


class GraphEventBase(CoReasonBaseModel):
    model_config = ConfigDict(frozen=True)

    run_id: str
    trace_id: str
    node_id: str
    timestamp: float
    sequence_id: Optional[int] = None
    visual_cue: Optional[str] = None


class GraphEventNodeStart(GraphEventBase):
    event_type: Literal["NODE_START"] = "NODE_START"
    payload: Dict[str, Any]


class GraphEventNodeStream(GraphEventBase):
    event_type: Literal["NODE_STREAM"] = "NODE_STREAM"
    chunk: str


class GraphEventNodeDone(GraphEventBase):
    event_type: Literal["NODE_DONE"] = "NODE_DONE"
    output: Dict[str, Any]


class GraphEventError(GraphEventBase):
    event_type: Literal["ERROR"] = "ERROR"
    error_message: str
    stack_trace: Optional[str] = None


class GraphEventCouncilVote(GraphEventBase):
    event_type: Literal["COUNCIL_VOTE"] = "COUNCIL_VOTE"
    votes: Dict[str, Any]


class GraphEventNodeRestored(GraphEventBase):
    event_type: Literal["NODE_RESTORED"] = "NODE_RESTORED"
    status: str


class GraphEventArtifactGenerated(GraphEventBase):
    event_type: Literal["ARTIFACT_GENERATED"] = "ARTIFACT_GENERATED"
    artifact_type: str
    url: str


GraphEvent = Union[
    GraphEventNodeStart,
    GraphEventNodeStream,
    GraphEventNodeDone,
    GraphEventError,
    GraphEventCouncilVote,
    GraphEventNodeRestored,
    GraphEventArtifactGenerated,
]
