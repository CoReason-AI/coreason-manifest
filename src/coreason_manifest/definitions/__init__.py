# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from .agent import AgentDefinition, AgentRuntimeConfig, Persona
from .deployment import DeploymentConfig, Protocol
from .events import (
    ArtifactGenerated,
    ArtifactGeneratedPayload,
    CouncilVote,
    CouncilVotePayload,
    EdgeTraversed,
    EdgeTraversedPayload,
    GraphEvent,
    NodeCompleted,
    NodeCompletedPayload,
    NodeInit,
    # Export Aliases too
    NodeInitPayload,
    NodeRestored,
    NodeSkipped,
    NodeSkippedPayload,
    NodeStarted,
    NodeStartedPayload,
    NodeStream,
    NodeStreamPayload,
    WorkflowError,
    WorkflowErrorPayload,
)
from .identity import Identity
from .interfaces import (
    IAgentRuntime,
    IResponseHandler,
    ISession,
    IStreamEmitter,
    LifecycleInterface,
)
from .presentation import (
    CitationBlock,
    CitationItem,
    MediaCarousel,
    MediaItem,
    PresentationEvent,
    PresentationEventType,
    ProgressUpdate,
)
from .request import AgentRequest
from .service import DEFAULT_ENDPOINT_PATH, ServerSentEvent, ServiceContract
from .session import Interaction, SessionState

__all__ = [
    "Identity",
    "AgentRequest",
    "ServerSentEvent",
    "ServiceContract",
    "DEFAULT_ENDPOINT_PATH",
    "AgentRuntimeConfig",
    "AgentDefinition",
    "IAgentRuntime",
    "IResponseHandler",
    "ISession",
    "IStreamEmitter",
    "LifecycleInterface",
    "Persona",
    "DeploymentConfig",
    "Protocol",
    "GraphEvent",
    "NodeInit",
    "NodeStarted",
    "NodeCompleted",
    "NodeRestored",
    "NodeSkipped",
    "NodeStream",
    "ArtifactGenerated",
    "EdgeTraversed",
    "CouncilVote",
    "WorkflowError",
    "NodeInitPayload",
    "NodeStartedPayload",
    "NodeCompletedPayload",
    "NodeSkippedPayload",
    "NodeStreamPayload",
    "EdgeTraversedPayload",
    "ArtifactGeneratedPayload",
    "CouncilVotePayload",
    "WorkflowErrorPayload",
    "Interaction",
    "SessionState",
    "PresentationEventType",
    "CitationItem",
    "CitationBlock",
    "ProgressUpdate",
    "MediaItem",
    "MediaCarousel",
    "PresentationEvent",
]
