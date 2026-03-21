# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

from typing import Generic, TypeVar, Any
from pydantic import Field, ConfigDict

from coreason_manifest.spec.ontology import CoreasonBaseState
from coreason_manifest.causality import TraceContext
from coreason_manifest.state import StateVector

T = TypeVar("T")

class ExecutionEnvelope(CoreasonBaseState, Generic[T]):
    """
    AGENT INSTRUCTION: Implements the mathematical Reader/Writer/State (RWS) Monad, completely enveloping execution inside pure functions.

    CAUSAL AFFORDANCE: The envelope functor that maps a pure value into a computational context.

    EPISTEMIC BOUNDS: Strictly prevents external keys. Must consist solely of trace_context, state_vector, and payload.
    """

    model_config = ConfigDict(extra="forbid")

    trace_context: TraceContext = Field(
        description="Represents the Reader/Writer monad for causality and recursion."
    )
    state_vector: StateVector = Field(
        description="Represents the State monad of Labeled Transition Systems."
    )
    payload: T = Field(
        description="Represents the pure value payload data structure, domain-specific."
    )
