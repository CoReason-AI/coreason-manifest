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

from coreason_manifest import load
from coreason_manifest.v2.spec.definitions import GenericDefinition

# --- Edge Cases ---


def test_ref_not_found(tmp_path: Path) -> None:
    """Test that referencing a non-existent file raises FileNotFoundError."""
    manifest_dict = {"definitions": {"missing": {"$ref": "ghost.yaml"}}}
    path = tmp_path / "manifest.yaml"
    path.write_text(yaml.dump(manifest_dict), encoding="utf-8")

    with pytest.raises(FileNotFoundError, match="Referenced file not found"):
        load(path)


def test_ref_invalid_yaml(tmp_path: Path) -> None:
    """Test that referencing a file with invalid YAML raises ValueError."""
    (tmp_path / "bad.yaml").write_text("key: value: what?", encoding="utf-8")

    manifest_dict = {"definitions": {"broken": {"$ref": "bad.yaml"}}}
    path = tmp_path / "manifest.yaml"
    path.write_text(yaml.dump(manifest_dict), encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid YAML"):
        load(path)


def test_ref_is_directory(tmp_path: Path) -> None:
    """Test that referencing a directory raises proper error."""
    (tmp_path / "subdir").mkdir()

    manifest_dict = {"definitions": {"oops": {"$ref": "subdir"}}}
    path = tmp_path / "manifest.yaml"
    path.write_text(yaml.dump(manifest_dict), encoding="utf-8")

    # Path.open() on a directory raises IsADirectoryError on Linux/macOS
    # but raises PermissionError on Windows.
    with pytest.raises((IsADirectoryError, PermissionError)):
        load(path)


def test_ref_self_loop(tmp_path: Path) -> None:
    """Test immediate self-reference."""
    # self.yaml refs self.yaml
    manifest_dict = {"definitions": {"me": {"$ref": "self.yaml"}}}
    path = tmp_path / "self.yaml"
    path.write_text(yaml.dump(manifest_dict), encoding="utf-8")

    with pytest.raises(RecursionError, match="Circular dependency detected"):
        load(path)


# --- Complex Cases ---


def test_chain_dependency(tmp_path: Path) -> None:
    """Test deep chain A -> B -> C -> D."""
    # D
    (tmp_path / "d.yaml").write_text(yaml.dump({"val": "D"}), encoding="utf-8")

    # C -> D
    c = {"val": "C", "definitions": {"ref_d": {"$ref": "d.yaml"}}}
    (tmp_path / "c.yaml").write_text(yaml.dump(c), encoding="utf-8")

    # B -> C
    b = {"val": "B", "definitions": {"ref_c": {"$ref": "c.yaml"}}}
    (tmp_path / "b.yaml").write_text(yaml.dump(b), encoding="utf-8")

    # A -> B
    a = {"val": "A", "definitions": {"ref_b": {"$ref": "b.yaml"}}}
    (tmp_path / "a.yaml").write_text(yaml.dump(a), encoding="utf-8")

    # Main -> A
    main = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Chain"},
        "workflow": {"start": "s", "steps": {"s": {"id": "s", "type": "logic", "code": "pass"}}},
        "definitions": {"root_a": {"$ref": "a.yaml"}},
    }
    path = tmp_path / "main.yaml"
    path.write_text(yaml.dump(main), encoding="utf-8")

    manifest = load(path)
    root_a = manifest.definitions["root_a"]
    assert isinstance(root_a, GenericDefinition)
    assert root_a.model_extra is not None

    # Check chain: root_a -> ref_b -> ref_c -> ref_d
    ref_b = root_a.model_extra["definitions"]["ref_b"]
    ref_c = ref_b["definitions"]["ref_c"]
    ref_d = ref_c["definitions"]["ref_d"]

    assert ref_b["val"] == "B"
    assert ref_c["val"] == "C"
    assert ref_d["val"] == "D"


def test_multiple_refs_same_level(tmp_path: Path) -> None:
    """Test importing multiple items in the same definitions block."""
    (tmp_path / "t1.yaml").write_text(yaml.dump({"val": "1"}), encoding="utf-8")
    (tmp_path / "t2.yaml").write_text(yaml.dump({"val": "2"}), encoding="utf-8")

    main = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Multi"},
        "workflow": {"start": "s", "steps": {"s": {"id": "s", "type": "logic", "code": "pass"}}},
        "definitions": {"d1": {"$ref": "t1.yaml"}, "d2": {"$ref": "t2.yaml"}},
    }
    path = tmp_path / "main.yaml"
    path.write_text(yaml.dump(main), encoding="utf-8")

    manifest = load(path)
    d1 = manifest.definitions["d1"]
    d2 = manifest.definitions["d2"]

    assert isinstance(d1, GenericDefinition)
    assert isinstance(d2, GenericDefinition)

    assert d1.model_extra is not None
    assert d2.model_extra is not None

    assert d1.model_extra["val"] == "1"
    assert d2.model_extra["val"] == "2"


def test_recursive_false(tmp_path: Path) -> None:
    """Test load(recursive=False) loads raw references."""
    (tmp_path / "sub.yaml").write_text("val: loaded", encoding="utf-8")

    main = {
        "apiVersion": "coreason.ai/v2",
        "kind": "Recipe",
        "metadata": {"name": "Raw"},
        "workflow": {"start": "s", "steps": {"s": {"id": "s", "type": "logic", "code": "pass"}}},
        "definitions": {"sub": {"$ref": "sub.yaml"}},
    }
    path = tmp_path / "main.yaml"
    path.write_text(yaml.dump(main), encoding="utf-8")

    manifest = load(path, recursive=False)

    # Should be a GenericDefinition wrapping the raw dict {"$ref": "sub.yaml"}
    sub = manifest.definitions["sub"]
    assert isinstance(sub, GenericDefinition)
    assert sub.model_extra is not None

    assert sub.model_extra["$ref"] == "sub.yaml"
    assert "val" not in sub.model_extra
