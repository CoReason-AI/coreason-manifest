# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION: This file maps the immutable toolchain schemas. This is a STRICTLY EPISTEMIC BOUNDARY.
These schemas represent the append-only cognitive ledger of the swarm. YOU ARE EXPLICITLY FORBIDDEN from introducing
mutable state loops, standard CRUD database paradigms, or downstream business logic. Focus purely on cryptographic
event sourcing, hardware attestations, and non-monotonic belief updates."""

from typing import Annotated, Literal

from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel


class BrowserDOMState(CoreasonBaseModel):
    type: Literal["browser"] = Field(default="browser", description="Discriminator for browser state snapshots.")
    current_url: str = Field(description="The exact URI the headless browser was positioned at.")
    viewport_size: tuple[int, int] = Field(description="The [width, height] dimensions of the rendered viewport.")
    dom_hash: str = Field(description="The SHA-256 hash of the complete, rendered HTML Document Object Model.")
    accessibility_tree_hash: str = Field(
        description="The SHA-256 hash of the parsed Chrome/Firefox Accessibility Tree."
    )
    screenshot_cid: str | None = Field(
        default=None, description="The Content Identifier (CID) or URI pointing to the visual snapshot in cold storage."
    )


class TerminalBufferState(CoreasonBaseModel):
    type: Literal["terminal"] = Field(default="terminal", description="Discriminator for terminal state snapshots.")
    working_directory: str = Field(description="The absolute path of the active shell context.")
    stdout_hash: str = Field(description="The SHA-256 hash of the standard output buffer at the moment of observation.")
    stderr_hash: str = Field(description="The SHA-256 hash of the standard error buffer.")
    env_variables_hash: str = Field(description="The SHA-256 hash of the active environment variables matrix.")


# =========================================================================
# AGENT INSTRUCTION: WARNING - POLYMORPHIC ROUTER
# If you create a new class above, you MUST append it to the AnyToolchainState union below.
# Failure to do so will result in a fatal Pydantic discriminator crash at runtime,
# creating a 'Dangling Class' that the orchestrator cannot deserialize.
# =========================================================================

type AnyToolchainState = Annotated[
    BrowserDOMState | TerminalBufferState,
    Field(discriminator="type", description="A discriminated union of immutable external toolchain states."),
]
