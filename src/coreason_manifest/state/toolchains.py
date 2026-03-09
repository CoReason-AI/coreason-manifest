# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION: This file maps the immutable toolchain schemas. This is a STRICTLY EPISTEMIC BOUNDARY.
These schemas represent the append-only cognitive ledger of the swarm. YOU ARE EXPLICITLY FORBIDDEN from introducing
monotonic logic, standard CRUD database paradigms, or kinetic execution parameters. These models represent computable
geometric graphs of cognition and causal inference."""

import re
from typing import Annotated, Literal

from pydantic import Field, field_validator

from coreason_manifest.core.base import CoreasonBaseModel


class BrowserDOMState(CoreasonBaseModel):
    type: Literal["browser"] = Field(
        default="browser", description="Discriminator for Causal Actuators representing structural shifts."
    )
    current_url: str = Field(description="Spatial Execution Bounds where the agent interacts.")
    viewport_size: tuple[int, int] = Field(description="Capability Perimeters detailing bounding coordinates.")
    dom_hash: str = Field(description="The SHA-256 hash acting as the structural manifestation vector.")
    accessibility_tree_hash: str = Field(
        description="The SHA-256 hash of the accessibility tree defining Exogenous Perturbations to the state space."
    )
    screenshot_cid: str | None = Field(
        default=None,
        description="A Content Identifier (CID) acting as a cryptographic Lineage Watermark for the snapshot "
        "representation.",
    )


class TerminalBufferState(CoreasonBaseModel):
    type: Literal["terminal"] = Field(
        default="terminal", description="Discriminator for Causal Actuators on structural buffers."
    )
    working_directory: str = Field(description="Capability Perimeters defining context bounds.")
    stdout_hash: str = Field(description="The SHA-256 hash of the Exogenous Perturbations captured.")
    stderr_hash: str = Field(description="The SHA-256 hash tracking structural deviation anomalies.")
    env_variables_hash: str = Field(description="The SHA-256 hash of the state-space context matrix.")

    @field_validator("working_directory")
    @classmethod
    def _enforce_sandboxed_path(cls, v: str) -> str:
        """
        AGENT INSTRUCTION: Strictly confine path geometry.
        Reject arbitrary absolute paths and traversal tokens purely mathematically.
        """
        if ".." in v:
            raise ValueError("Path traversal sequences ('..') are strictly forbidden to preserve sandbox geometry.")
        if v.startswith(("/", "\\")):
            raise ValueError("Absolute Unix/Windows root paths are strictly forbidden.")
        if re.match(r"^[a-zA-Z]:", v):
            raise ValueError("Windows drive letter absolute paths are strictly forbidden.")
        return v


# =========================================================================
# AGENT INSTRUCTION: WARNING - POLYMORPHIC ROUTER
# If you create a new class above, you MUST append it to the AnyToolchainState union below.
# Failure to do so will result in a fatal Pydantic discriminator crash at runtime,
# creating a 'Dangling Class' that the orchestrator cannot deserialize.
# =========================================================================

type AnyToolchainState = Annotated[
    BrowserDOMState | TerminalBufferState,
    Field(
        discriminator="type",
        description="A discriminated union of Causal Actuators defining "
        "strict perimeters for Exogenous Perturbations to the causal graph.",
    ),
]
