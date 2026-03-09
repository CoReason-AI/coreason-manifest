# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION:
This file defines the dynamic layout template grammar. This is a STRICTLY PROJECTION BOUNDARY.
These schemas govern how multi-dimensional agent knowledge is collapsed and encoded for human perception.
YOU ARE EXPLICITLY FORBIDDEN from adding state-mutation or backend logic here.
Think purely in terms of declarative graphical grammars (Marks, Channels, Scales).
"""

import ast

from pydantic import Field, field_validator

from coreason_manifest.core.base import CoreasonBaseModel


class DynamicLayoutTemplate(CoreasonBaseModel):
    """Schema representing a template for dynamic grid layouts."""

    layout_tstring: str = Field(
        description="A Python 3.14 t-string template definition for dynamic UI grid evaluation."
    )

    @field_validator("layout_tstring", mode="after")
    @classmethod
    def validate_tstring(cls, v: str) -> str:
        """
        AGENT INSTRUCTION: Mathematically prove the absence of kinetic execution
        bleed by parsing the layout string into an Abstract Syntax Tree.
        """
        try:
            tree = ast.parse(v, mode="exec")
        except SyntaxError:
            pass  # If it mathematically cannot parse as Python, it cannot execute.
        else:
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    raise ValueError("Kinetic execution bleed detected: AST contains function calls.")
        return v
