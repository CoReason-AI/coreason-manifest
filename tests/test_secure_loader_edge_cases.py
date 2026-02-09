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


