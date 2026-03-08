# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION:

This file maps the mechanistic audit and cryptographic extraction schemas. This is a STRICTLY REGULATORY BOUNDARY.
These schemas define the Zero-Trust information flow constraints of the swarm.
DO NOT inject kinetic execution logic here.
All policies must be declarative, deterministic, and capable of severing memory access instantly.
"""

from typing import Literal

from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel


class MechanisticAuditContract(CoreasonBaseModel):
    trigger_conditions: list[Literal["on_tool_call", "on_belief_update", "on_quarantine", "on_falsification"]] = Field(
        min_length=1,
        description="The specific architectural events that authorize the orchestrator to "
        "halt generation and extract internal activations.",
    )
    target_layers: list[int] = Field(
        min_length=1,
        description="The specific transformer block indices the execution engine must read from.",
    )
    max_features_per_layer: int = Field(
        gt=0,
        description="The top-k features to extract, preventing memory overflow.",
    )
    require_zk_commitments: bool = Field(
        default=True,
        description="If True, the orchestrator MUST generate cryptographic latent state proofs "
        "alongside the activation reads.",
    )
