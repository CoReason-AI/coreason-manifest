# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from typing import Literal

from pydantic import Field, model_validator

from coreason_manifest.core.base import CoreasonBaseModel

type RuntimeEngine = Literal["wasm", "gvisor", "firecracker", "bpf"]


class ResourceCeilings(CoreasonBaseModel):
    """Hardware-level limits."""

    max_memory_bytes: int = Field(description="The absolute memory ceiling for the sandbox.")
    max_instruction_cycles: int | None = Field(
        default=None, description="Optional limit on CPU instructions to prevent infinite loops."
    )


class SyscallBoundary(CoreasonBaseModel):
    """The operating system interface boundary."""

    allowed_syscalls: list[str] = Field(
        default_factory=list, description="A strict allowlist of POSIX system calls permitted by the sandbox."
    )

    @model_validator(mode="after")
    def sort_syscalls(self) -> SyscallBoundary:
        object.__setattr__(self, "allowed_syscalls", sorted(self.allowed_syscalls))
        return self


class NetworkNamespace(CoreasonBaseModel):
    """The isolated network namespace."""

    allow_egress: bool = Field(
        default=False, description="Whether the sandbox can initiate outbound network connections."
    )
    allowed_hosts: list[str] = Field(default_factory=list, description="A strict allowlist of external domains/IPs.")

    @model_validator(mode="after")
    def sort_hosts(self) -> NetworkNamespace:
        object.__setattr__(self, "allowed_hosts", sorted(self.allowed_hosts))
        return self
