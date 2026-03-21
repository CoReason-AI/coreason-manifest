# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

from pydantic import Field, model_validator
from typing import Self

from coreason_manifest.spec.ontology import CoreasonBaseState

class TraceContext(CoreasonBaseState):
    """
    AGENT INSTRUCTION: Implements Distributed Causality using Vector Clocks and rho-calculus.

    CAUSAL AFFORDANCE: Acts as a Causal Graph Identifier, ensuring deterministic traceability
    and state boundary enforcement without relying on hidden states.

    EPISTEMIC BOUNDS: Relies on ULID or UUIDv7 string identifiers for strict topological ordering.
    """

    trace_id: str = Field(
        min_length=26,
        max_length=36,
        pattern=r"^[0-9A-HJKMNP-TV-Z]{26}$|^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
        description="Globally unique ID generated once at the root user prompt. Must be a ULID or UUIDv7."
    )
    span_id: str = Field(
        min_length=26,
        max_length=36,
        pattern=r"^[0-9A-HJKMNP-TV-Z]{26}$|^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
        description="Unique identifier for the specific execution of this actionSpaceId. Must be a ULID or UUIDv7."
    )
    parent_span_id: str | None = Field(
        default=None,
        min_length=26,
        max_length=36,
        pattern=r"^[0-9A-HJKMNP-TV-Z]{26}$|^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
        description="The span_id of the caller. If null, this node is the mathematically proven root."
    )
    causal_clock: int = Field(
        default=0,
        ge=0,
        description="Tracks the recursion depth/vector clock required for compute budget decay."
    )

    @model_validator(mode="after")
    def verify_span_topology(self) -> Self:
        """Mathematically prevents superficial infinite self-pointers."""
        if self.parent_span_id is not None and self.span_id == self.parent_span_id:
            raise ValueError("Topological Violation: span_id cannot equal parent_span_id.")
        return self
