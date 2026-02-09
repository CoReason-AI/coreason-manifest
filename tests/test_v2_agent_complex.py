# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import pytest
import yaml
from pydantic import ValidationError

from coreason_manifest.spec.v2.definitions import (
    AgentDefinition,
    ManifestV2,
    ToolDefinition,
)


def test_mixed_definitions_typo_tolerance() -> None:
    """Test mixing valid types and 'typo' types should raise ValidationError."""
    yaml_content = """
apiVersion: coreason.ai/v2
kind: Agent
metadata:
  name: Mixed Bag
workflow:
  start: s
  steps: {s: {type: logic, id: s, code: pass}}
definitions:
  valid_tool:
    type: tool
    id: t1
    name: T1
    uri: mcp://t1
    risk_level: safe

  valid_agent:
    type: agent
    id: a1
    name: A1
    role: R1
    goal: G1

  typo_thing:
    type: unknown_type
    id: u1
    name: Unknown
"""
    with pytest.raises(ValidationError):
        ManifestV2(**yaml.safe_load(yaml_content))
