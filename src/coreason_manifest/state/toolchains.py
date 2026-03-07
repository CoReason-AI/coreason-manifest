# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

import re
from typing import Annotated, Literal

from pydantic import Field, field_validator

from coreason_manifest.core.base import CoreasonBaseModel


class TerminalStateSnapshot(CoreasonBaseModel):
    cwd: str = Field(description="The current working directory of the terminal environment.")
    stdout_buffer: str = Field(max_length=10000, description="The buffered standard output captured from execution.")
    last_exit_code: int | None = Field(default=None, description="The exit code of the last executed command, if any.")

    @field_validator("cwd")
    @classmethod
    def validate_cwd(cls, v: str) -> str:
        if ".." in v or "\0" in v:
            raise ValueError("Path traversal or null bytes are strictly forbidden in cwd.")
        if v.startswith("/") or re.match(r"^[A-Za-z]:[\\/]", v):
            raise ValueError("Absolute paths are strictly forbidden in cwd.")
        return v


class BrowserStateSnapshot(CoreasonBaseModel):
    current_url: str = Field(pattern=r"^https?://", description="The current active URL being viewed in the browser.")
    dom_hash: str = Field(description="A cryptographic hash representing the current DOM structure.")


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


AnyToolchainState = Annotated[
    BrowserDOMState | TerminalBufferState,
    Field(discriminator="type", description="A discriminated union of immutable external toolchain states."),
]
