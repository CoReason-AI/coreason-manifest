# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

import re

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
