# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from pathlib import Path

import pytest
import yaml

from coreason_manifest import (
    Manifest,
    ManifestRecursionError,
    SecurityViolationError,
    load,
)
from coreason_manifest.v2.spec.definitions import GenericDefinition, ToolDefinition


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
        SecurityViolationError,
        match="Security Error: Reference '../secret.yaml' escapes the root directory.",
    ):
        load(exploit_path, root_dir=root_dir)


def test_secure_loader_cycle_detection(tmp_path: Path) -> None:
    """Test that circular dependencies raise ManifestRecursionError."""
    # a.yaml -> b.yaml
    a_manifest = {"definitions": {"ref_b": {"$ref": "b.yaml"}}}

    # b.yaml -> a.yaml
    b_manifest = {"definitions": {"ref_a": {"$ref": "a.yaml"}}}

    (tmp_path / "a.yaml").write_text(yaml.dump(a_manifest), encoding="utf-8")
    (tmp_path / "b.yaml").write_text(yaml.dump(b_manifest), encoding="utf-8")

    with pytest.raises(ManifestRecursionError, match="Circular dependency detected"):
        load(tmp_path / "a.yaml")


def test_secure_loader_diamond_dependency(tmp_path: Path) -> None:
    """Test that diamond dependencies (A->C, B->C) are supported."""
    # C (Leaf)
    # Using Generic definition structure (no type) to allow definitions if needed,
    # but here C is just a value.
    dict_c = {"val": "C"}
    (tmp_path / "c.yaml").write_text(yaml.dump(dict_c), encoding="utf-8")

    # A -> C
    dict_a = {"val": "A", "definitions": {"ref_c": {"$ref": "c.yaml"}}}
    (tmp_path / "a.yaml").write_text(yaml.dump(dict_a), encoding="utf-8")

    # B -> C
    dict_b = {"val": "B", "definitions": {"ref_c": {"$ref": "c.yaml"}}}
    (tmp_path / "b.yaml").write_text(yaml.dump(dict_b), encoding="utf-8")

    # Main -> A, B
    main_manifest = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Diamond"},
        "workflow": {
            "start": "s",
            "steps": {"s": {"id": "s", "type": "logic", "code": "pass"}},
        },
        "definitions": {
            "def_a": {"$ref": "a.yaml"},
            "def_b": {"$ref": "b.yaml"},
        },
    }
    main_path = tmp_path / "main.yaml"
    main_path.write_text(yaml.dump(main_manifest), encoding="utf-8")

    # This should succeed without ManifestRecursionError
    manifest = load(main_path)

    # Verify content
    # definitions are GenericDefinition
    def_a = manifest.definitions["def_a"]
    def_b = manifest.definitions["def_b"]

    assert isinstance(def_a, GenericDefinition)
    assert isinstance(def_b, GenericDefinition)

    assert def_a.model_extra is not None
    assert def_b.model_extra is not None

    assert def_a.model_extra["val"] == "A"
    assert def_b.model_extra["val"] == "B"

    # Verify nested resolution (accessed via model_extra because it's dynamic)
    assert isinstance(def_a.model_extra["definitions"], dict)
    assert isinstance(def_b.model_extra["definitions"], dict)

    assert def_a.model_extra["definitions"]["ref_c"]["val"] == "C"
    assert def_b.model_extra["definitions"]["ref_c"]["val"] == "C"
