# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import coreason_manifest.v1 as v1_manifest
from coreason_manifest.definitions.agent import AgentDefinition


def test_v1_exports() -> None:
    """Verify that key components are exported from the v1 package."""
    # Verify AgentDefinition export
    assert hasattr(v1_manifest, "AgentDefinition")
    assert v1_manifest.AgentDefinition is AgentDefinition

    # Check __all__ contains AgentDefinition
    assert "AgentDefinition" in v1_manifest.__all__
