# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from pydantic import Field, field_validator

from coreason_manifest.core.base import CoreasonBaseModel


class DynamicLayoutTemplate(CoreasonBaseModel):
    """Schema representing a template for dynamic grid layouts."""

    layout_tstring: str = Field(
        description="A Python 3.14 t-string template definition for dynamic UI grid evaluation."
    )

    @field_validator("layout_tstring")
    @classmethod
    def validate_tstring(cls, v: str) -> str:
        """Reject any string containing Python execution patterns."""
        forbidden_patterns = [
            "__import__",
            "eval",
            "exec",
            "open",
            "os.system",
            "__class__",
            "__mro__",
            "__subclasses__",
            "__globals__",
            "__builtins__",
        ]
        for pattern in forbidden_patterns:
            if pattern in v:
                raise ValueError(f"Forbidden execution pattern detected: {pattern}")
        return v
