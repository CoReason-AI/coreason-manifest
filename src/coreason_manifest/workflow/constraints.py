# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

"""AGENT INSTRUCTION: This file defines the orchestration constraint schemas. This is a STRICTLY TOPOLOGICAL BOUNDARY.

These schemas dictate the multi-agent graph geometry and decentralized routing mechanics. DO NOT inject procedural
execution code or synchronous blocking loops. Think purely in terms of graph theory, Byzantine fault tolerance, and
multi-agent market dynamics."""

from pydantic import Field

from coreason_manifest.core.base import CoreasonBaseModel


class InputMapping(CoreasonBaseModel):
    """
    Dictates how keys from a parent's shared_state_contract map to a nested topology's state.
    """

    parent_key: str = Field(description="The key in the parent's shared state contract.")
    child_key: str = Field(description="The mapped key in the nested topology's state contract.")


class OutputMapping(CoreasonBaseModel):
    """
    Dictates how keys from a nested topology's state map back to a parent's shared_state_contract.
    """

    child_key: str = Field(description="The key in the nested topology's state contract.")
    parent_key: str = Field(description="The mapped key in the parent's shared state contract.")
