# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import re
from pathlib import Path

import pytest
import yaml

from coreason_manifest import Manifest, load
from coreason_manifest.spec.v2.definitions import ToolDefinition


def test_secure_loader_happy_path(tmp_path: Path) -> None:
    """Test standard modular composition."""
    tool_def = {
        "type": "tool",
        "id": "my-tool",
        "name": "My Tool",
        "uri": "https://example.com",
        "risk_level": "safe",
    }
    (tmp_path / "tool.yaml").write_text(yaml.dump(tool_def), encoding="utf-8")

    agent_manifest = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Test Agent"},
        "definitions": {"my_tool": {"$ref": "tool.yaml"}},
        "workflow": {
            "start": "step1",
            "steps": {"step1": {"id": "step1", "type": "logic", "code": "print('hello')"}},
        },
    }
    agent_path = tmp_path / "agent.yaml"
    agent_path.write_text(yaml.dump(agent_manifest), encoding="utf-8")

    manifest = load(agent_path)
    assert isinstance(manifest, Manifest)
    assert "my_tool" in manifest.definitions

    # The reference should be replaced by the tool definition
    tool = manifest.definitions["my_tool"]
    assert isinstance(tool, ToolDefinition)
    assert tool.id == "my-tool"


def test_secure_loader_security_violation(tmp_path: Path) -> None:
    """Test that referencing files outside root_dir fails."""
    # Setup jail
    root_dir = tmp_path / "jail"
    root_dir.mkdir()

    # Secret outside jail
    secret_file = tmp_path / "secret.yaml"
    secret_file.write_text("secret: true", encoding="utf-8")

    # Exploit inside jail
    exploit_manifest = {"definitions": {"hack": {"$ref": "../secret.yaml"}}}
    exploit_path = root_dir / "exploit.yaml"
    exploit_path.write_text(yaml.dump(exploit_manifest), encoding="utf-8")

    # Attempt load with root_dir set to jail
    with pytest.raises(
        ValueError,
        match=re.escape("Security Error: Reference '../secret.yaml' escapes the root directory."),
    ):
        load(exploit_path, root_dir=root_dir)


def test_secure_loader_cycle_detection(tmp_path: Path) -> None:
    """Test that circular dependencies raise RecursionError."""
    # a.yaml -> b.yaml
    a_manifest = {"definitions": {"ref_b": {"$ref": "b.yaml"}}}

    # b.yaml -> a.yaml
    b_manifest = {"definitions": {"ref_a": {"$ref": "a.yaml"}}}

    (tmp_path / "a.yaml").write_text(yaml.dump(a_manifest), encoding="utf-8")
    (tmp_path / "b.yaml").write_text(yaml.dump(b_manifest), encoding="utf-8")

    with pytest.raises(RecursionError, match="Circular dependency detected"):
        load(tmp_path / "a.yaml")


