# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION: This file defines the spatial and physical tool bindings. This is a STRICTLY KINETIC BOUNDARY.
These schemas represent friction, hardware limits, and physical execution. This boundary governs probabilistic
tensor logic, VRAM geometries, and exogenous spatial actuation."""

from typing import Literal, Self

from pydantic import Field, model_validator

from coreason_manifest.core.base import CoreasonBaseModel


class NormalizedCoordinate(CoreasonBaseModel):
    """A resolution-independent 2D spatial vector."""

    x: float = Field(ge=0.0, le=1.0, description="The normalized X-axis coordinate (0.0 = left, 1.0 = right).")
    y: float = Field(ge=0.0, le=1.0, description="The normalized Y-axis coordinate (0.0 = top, 1.0 = bottom).")


class BoundingBox(CoreasonBaseModel):
    """A resolution-independent spatial region."""

    x_min: float = Field(ge=0.0, le=1.0, description="The left boundary.")
    y_min: float = Field(ge=0.0, le=1.0, description="The top boundary.")
    x_max: float = Field(ge=0.0, le=1.0, description="The right boundary.")
    y_max: float = Field(ge=0.0, le=1.0, description="The bottom boundary.")

    @model_validator(mode="after")
    def validate_geometry(self) -> Self:
        if self.x_min > self.x_max:
            raise ValueError("x_min cannot be strictly greater than x_max.")
        if self.y_min > self.y_max:
            raise ValueError("y_min cannot be strictly greater than y_max.")
        return self


class SpatialKinematicAction(CoreasonBaseModel):
    """A mathematical declaration of an OS-level pointer or interaction trajectory."""

    action_type: Literal["click", "double_click", "drag_and_drop", "scroll", "hover", "keystroke"] = Field(
        description="The specific kinematic interaction paradigm."
    )
    target_coordinate: NormalizedCoordinate | None = Field(
        default=None, description="The primary spatial terminus for clicks or hovers."
    )
    trajectory_duration_ms: int | None = Field(
        default=None, gt=0, description="The exact temporal duration of the movement, simulating human kinematics."
    )
    bezier_control_points: list[NormalizedCoordinate] = Field(
        default_factory=list, description="Waypoints for constructing non-linear, bot-evasive movement curves."
    )
    expected_visual_concept: str | None = Field(
        default=None,
        description="The visual anchor (e.g., 'Submit Button'). The orchestrator must verify this "
        "semantic concept exists at the target_coordinate before executing the macro, preventing blind clicks.",
    )
