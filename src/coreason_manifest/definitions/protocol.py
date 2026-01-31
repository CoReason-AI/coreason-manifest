# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator

from typing import Dict, List

from .base import CoReasonBaseModel


class OntologyTerm(CoReasonBaseModel):
    id: str
    label: str
    code: str
    vocab_source: str


class PicoBlock(CoReasonBaseModel):
    description: str
    terms: List[OntologyTerm]


class ProtocolDefinition(CoReasonBaseModel):
    """The rigorous study design object."""

    id: str
    research_question: str
    pico_structure: Dict[str, PicoBlock]  # Keys usually: P, I, C, O
    status: str  # e.g., DRAFT, APPROVED
