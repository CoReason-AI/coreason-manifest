# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from typing import Literal

from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel

type AttackVector = Literal[
    "semantic_hijacking",
    "system_prompt_extraction",
    "sabotage",
    "deception",
    "data_exfiltration",
]


class AdversaryProfile(CoreasonBaseModel):
    persona: str = Field(description="The assigned persona or character the attacker agent must adopt.")
    attack_vector: AttackVector = Field(description="The method or angle of the adversarial attack.")
    goal: str = Field(description="The explicit adversarial goal (e.g., 'Extract the adjudicator system prompt').")


class AiTMStrategy(CoreasonBaseModel):
    source_node_id: str = Field(description="The node originating the intercepted message.")
    target_node_id: str = Field(description="The node intended to receive the message.")
    mutation_instruction: str = Field(
        description="The instruction dictating how the red-team agent should subtly "
        "corrupt the intercepted state event."
    )
