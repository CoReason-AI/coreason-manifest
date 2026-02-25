# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Any

from pydantic import Field

from coreason_manifest.spec.common_base import CoreasonModel


class CoIntelligencePolicy(CoreasonModel):
    """
    Configuration for human-AI co-intelligence interaction modes.
    Replaces the static 'HumanNode' concept with dynamic governance.
    """

    shadow_mode_enabled: bool = Field(
        False, description="If True, human observers receive live telemetry without blocking execution."
    )
    mentor_intervention_timeout_sec: int | None = Field(
        None,
        description=(
            "Timeout thresholds where the system waits for human reasoning adjustments before executing critical tools."
        ),
        examples=[300],
    )
    peer_routing_rules: dict[str, Any] | None = Field(
        None,
        description="Criteria for dynamically routing specific sub-tasks to human workers instead of agents.",
        examples=[{"criteria": "ambiguity > 0.8", "role": "expert_human"}],
    )
