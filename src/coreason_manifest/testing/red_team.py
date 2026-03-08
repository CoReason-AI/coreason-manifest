# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION:

This file defines the Adversarial Simulation schemas. This is a STRICTLY ADVERSARIAL BOUNDARY.
These models are not unit tests; they are systemic fault injectors designed to perturb the live
swarm topology (e.g., node latency, memory corruption, topological severing).
Do not write standard QA schemas here. Focus entirely on Blast Radius and Steady-State Hypotheses.
"""

from typing import Any, Literal

from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel


class AdversarialSimulationProfile(CoreasonBaseModel):
    """
    A deterministic red-team configuration defining a structural attack vector

    to continuously validate semantic firewalls and execution bounds.
    """

    simulation_id: str = Field(description="The unique identifier for this red-team experiment.")
    target_node_id: str = Field(description="The exact NodeID the 'Judas Node' will attempt to compromise.")
    attack_vector: Literal["prompt_extraction", "data_exfiltration", "semantic_hijacking", "tool_poisoning"] = Field(
        description="The mathematically predictable category of structural sabotage being simulated."
    )
    synthetic_payload: dict[str, Any] | str = Field(
        description="The raw poisoned text or malicious JSON-RPC schema injected into the target's context window."
    )
    expected_firewall_trip: str | None = Field(
        default=None,
        description="The exact rule_id of the InformationFlowPolicy or Governance bound expected "
        "to block this attack. Used for automated test assertions.",
    )
