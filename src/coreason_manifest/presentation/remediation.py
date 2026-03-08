# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION:
This file defines the System 2 Remediation Prompt schema and its deterministic adapter.
This is a STRICTLY PASSIVE BOUNDARY. It is purely for translating Pythonic execution
panics into LLM-legible geometric boundaries. DO NOT execute LLM calls or retry loops here.
"""

from typing import Self

from pydantic import Field, ValidationError, model_validator

from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.core.primitives import NodeID


class System2RemediationPrompt(CoreasonBaseModel):
    """
    A passive data envelope that deterministically maps a kinetic execution error
    (e.g., a Pydantic ValidationError) into a structurally rigid System 2 correction directive.
    """

    fault_id: str = Field(
        min_length=1, description="A cryptographic Lineage Watermark (CID) tracking this specific dimensional collapse."
    )
    target_node_id: NodeID = Field(
        description="The strict W3C DID of the agent that authored the invalid state, "
        "ensuring the fault is routed back to the exact memory partition."
    )
    failing_pointers: list[str] = Field(
        min_length=1,
        description="A strictly typed array of RFC 6902 JSON Pointers isolating "
        "the exact topological coordinate of the hallucination."
    )
    remediation_prompt: str = Field(
        min_length=1, description="The deterministic, non-monotonic natural-language constraint the agent must satisfy."
    )

    @model_validator(mode="after")
    def _sort_failing_pointers(self) -> Self:
        """Mathematically sort pointers to guarantee deterministic canonical hashing."""
        object.__setattr__(self, "failing_pointers", sorted(self.failing_pointers))
        return self


def generate_correction_prompt(error: ValidationError, target_node_id: str, fault_id: str) -> System2RemediationPrompt:
    """
    Pure functional adapter. Maps a raw Pythonic pydantic.ValidationError into a
    language-model-legible System2RemediationPrompt without triggering runtime side effects.
    """
    failing_pointers: list[str] = []
    error_messages: list[str] = []

    for err in error.errors():
        # Deterministically translate Pydantic 'loc' tuple to an RFC 6902 JSON Pointer
        loc_path = "".join(f"/{item!s}" for item in err["loc"]) if err["loc"] else "/"
        failing_pointers.append(loc_path)

        # Project strict, deterministic error directives
        err_type = err.get("type", "unknown")
        if err_type == "missing":
            error_messages.append(
                f"The required semantic boundary at '{loc_path}' is completely missing. "
                "You must project this missing dimension to satisfy the StateContract."
            )
        else:
            msg = err.get("msg", "Invalid structural payload.")
            error_messages.append(f"A structural boundary violation occurred at '{loc_path}': {msg}")

    # Remove duplicates from pointers to prevent hash collision anomalies
    failing_pointers = list(set(failing_pointers))

    remediation_prompt = (
        "CRITICAL CONTRACT BREACH: Your generated state representation violates the formal ontological boundaries "
        "of the Shared Kernel. Review the following strict topological failures and correct your JSON projection:\n"
        + "\n".join(f"- {msg}" for msg in error_messages)
    )

    return System2RemediationPrompt(
        fault_id=fault_id,
        target_node_id=target_node_id,
        failing_pointers=failing_pointers,
        remediation_prompt=remediation_prompt,
    )
