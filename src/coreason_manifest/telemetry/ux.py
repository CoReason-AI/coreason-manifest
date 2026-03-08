# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION: This file maps the UI/UX telemetry schemas. This is a STRICTLY OBSERVABILITY BOUNDARY.
These models govern the distributed tracing and cryptographic audit trails of the swarm. Do NOT write standard
text-logging or web-analytics schemas here. Focus entirely on tamper-evident spans, Merkle custody records, and
cross-node span contexts."""

from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel


class AmbientSignal(CoreasonBaseModel):
    """
    Lightweight UX signal for UI rendering of progress.
    """

    status_message: str = Field(description="A human-readable status message for the current task.")
    progress: float | None = Field(
        default=None, description="The progress ratio from 0.0 to 1.0, or None if indeterminate."
    )


class SuspenseEnvelope(CoreasonBaseModel):
    """
    Indicates that the swarm is waiting on a long-running process or human input.
    """
