# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from pydantic import ConfigDict

from coreason_manifest.spec.common_base import ManifestBaseModel


class ReasoningEngine(ManifestBaseModel):
    """Configures 'System 2' slow thinking."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class Reflex(ManifestBaseModel):
    """Configures 'System 1' fast response."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class Supervision(ManifestBaseModel):
    """Configures retries, fallbacks, and failure handling."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


class Optimizer(ManifestBaseModel):
    """Configures self-improvement via teacher models."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)
