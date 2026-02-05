# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from typing import Optional

from pydantic import ConfigDict

from coreason_manifest.common import CoReasonBaseModel


class LineageMetadata(CoReasonBaseModel):
    """Metadata for tracking request lineage across boundaries."""

    model_config = ConfigDict(frozen=True)

    root_request_id: str
    parent_interaction_id: Optional[str] = None


class Interaction(CoReasonBaseModel):
    """External boundary interaction model."""

    model_config = ConfigDict(frozen=True)

    id: str
    lineage: Optional[LineageMetadata] = None
