# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason_validator


import hashlib
import json

from pydantic import BaseModel, ConfigDict


class CoReasonBaseModel(BaseModel):
    """
    Base model for all CoReason schemas.
    Provides canonical hashing for integrity verification.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    def canonical_hash(self) -> str:
        """
        Computes a SHA-256 hash of the canonically serialized model.
        1. Validates the object (implied by being a model instance).
        2. Converts to JSON-compatible dict (handling dates, UUIDs, etc).
        3. Sorts keys alphabetically.
        4. Removes non-semantic whitespace.
        5. Returns SHA-256 hex digest.
        """
        # 1. Convert to dict (mode='json' handles serialization of types like datetime)
        data = self.model_dump(mode="json")

        # 2. Serialize to JSON with sorted keys and no whitespace separators
        # ensure_ascii=False ensures Unicode characters are preserved as-is, not escaped
        json_str = json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))

        # 3. Hash the UTF-8 bytes
        return hashlib.sha256(json_str.encode("utf-8")).hexdigest()
