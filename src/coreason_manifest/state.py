# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

from typing import Annotated

from pydantic import Field, StringConstraints

from coreason_manifest.spec.ontology import CoreasonBaseState, JsonPrimitiveState


class StateVector(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Implements Labeled Transition System (LTS) Determinism.

    CAUSAL AFFORDANCE: Forces all hidden LLM contexts into an explicitly typed data structure,
    making the agent a Markov Process with Full Observability.

    EPISTEMIC BOUNDS: Bounded dictionary mapping of explicit schemas or primitives for both read and write state.
    """

    read_only_context: dict[Annotated[str, StringConstraints(max_length=255)], JsonPrimitiveState] = Field(
        default_factory=dict,
        description="Immutable behavior directives (e.g., global personas, fixed dataset schemas, boundary rules)."
    )
    mutable_memory: dict[Annotated[str, StringConstraints(max_length=255)], JsonPrimitiveState] | None = Field(
        default=None,
        description="The agent's scratchpad, chat history, and any writable states."
    )
    is_delta: bool = Field(
        default=False,
        description="A flag allowing the output to only return the keys in mutable_memory that changed, rather than forcing the entire array back up the network."
    )
