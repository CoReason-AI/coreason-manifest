# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import coreason_manifest
from coreason_manifest.definitions.agent import AgentDefinition, AgentStatus


def test_top_level_exports() -> None:
    """Verify that key components are exported from the top-level package."""
    # Verify AgentStatus export
    assert hasattr(coreason_manifest, "AgentStatus")
    assert coreason_manifest.AgentStatus is AgentStatus

    # Verify AgentDefinition export
    assert hasattr(coreason_manifest, "AgentDefinition")
    assert coreason_manifest.AgentDefinition is AgentDefinition

    # Check __all__ contains AgentStatus
    assert "AgentStatus" in coreason_manifest.__all__
