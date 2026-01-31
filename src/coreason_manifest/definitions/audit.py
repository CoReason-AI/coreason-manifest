# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator

from datetime import datetime
from enum import Enum

from pydantic import Field

from .base import CoReasonBaseModel


class SignatureRole(str, Enum):
    AUTHOR = "AUTHOR"
    APPROVER = "APPROVER"
    QA_REVIEWER = "QA_REVIEWER"


class SignatureEvent(CoReasonBaseModel):
    """
    The immutable record of a GxP signature.
    Used by coreason-scribe to transmit proof to coreason-veritas.
    """

    document_hash: str = Field(..., description="The SHA-256 hash of the signed content")
    signer_id: str = Field(..., description="The ID of the human or agent signer")
    role: SignatureRole
    meaning: str = Field(..., description="The intent (e.g., 'I approve this protocol')")
    timestamp: datetime
    crypto_token: str = Field(..., description="The digital signature string/hash")
