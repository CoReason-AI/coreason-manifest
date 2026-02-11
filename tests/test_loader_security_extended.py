# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import os
import stat
import sys
from pathlib import Path

import pytest

from coreason_manifest.spec.v2.definitions import ManifestV2
from coreason_manifest.utils.loader import load_agent_from_ref


def test_loader_path_traversal_rejection(tmp_path: Path) -> None:
    """Test that loading a file outside the allowed root is rejected."""

    # Create a safe root directory
    safe_root = tmp_path / "safe_root"
    safe_root.mkdir()

    # Create a file outside the safe root
    outside_file = tmp_path / "outside.py"
    outside_file.write_text("agent = 'malicious'", encoding="utf-8")

    # Create a valid file inside safe root
    inside_file = safe_root / "inside.py"
    inside_file.write_text(
        """
from coreason_manifest.spec.v2.definitions import ManifestV2
agent = ManifestV2(
    apiVersion="coreason.ai/v2",
    kind="Agent",
    metadata={"name": "SafeAgent"},
    definitions={},
    workflow={"start": "a", "steps":{}}
)
""",
        encoding="utf-8",
    )

    # 1. Attempt to load outside file with safe_root as allowed_root_dir
    ref = f"{outside_file}:agent"
    with pytest.raises(ValueError, match=r"Security Violation: File .* is outside allowed root"):
        load_agent_from_ref(ref, allowed_root_dir=safe_root)

    # 2. Attempt to load inside file should succeed
    ref_safe = f"{inside_file}:agent"
    agent = load_agent_from_ref(ref_safe, allowed_root_dir=safe_root)
    assert isinstance(agent, ManifestV2)


def test_loader_world_writable_rejection(tmp_path: Path) -> None:
    """Test that loading a world-writable file is rejected on POSIX."""
    if os.name != "posix":
        pytest.skip("Skipping POSIX permission test on non-POSIX system")

    safe_root = tmp_path / "safe_root"
    safe_root.mkdir()

    unsafe_file = safe_root / "unsafe.py"
    unsafe_file.write_text(
        """
from coreason_manifest.spec.v2.definitions import ManifestV2
agent = ManifestV2(
    apiVersion="coreason.ai/v2",
    kind="Agent",
    metadata={"name": "UnsafeAgent"},
    definitions={},
    workflow={"start": "a", "steps":{}}
)
""",
        encoding="utf-8",
    )

    # Make it world-writable
    mode = unsafe_file.stat().st_mode
    unsafe_file.chmod(mode | stat.S_IWOTH)

    ref = f"{unsafe_file}:agent"

    with pytest.raises(ValueError, match=r"Security Violation: File .* is world-writable"):
        load_agent_from_ref(ref, allowed_root_dir=safe_root)


def test_loader_sys_path_cleanup(tmp_path: Path) -> None:
    """Test that sys.path is cleaned up after loading."""
    safe_root = tmp_path / "safe_root"
    safe_root.mkdir()

    module_file = safe_root / "module.py"
    module_file.write_text(
        """
from coreason_manifest.spec.v2.definitions import ManifestV2
agent = ManifestV2(
    apiVersion="coreason.ai/v2",
    kind="Agent",
    metadata={"name": "Agent"},
    definitions={},
    workflow={"start": "a", "steps":{}}
)
""",
        encoding="utf-8",
    )

    ref = f"{module_file}:agent"

    # Check sys.path before
    # original_sys_path_len = len(sys.path)

    load_agent_from_ref(ref, allowed_root_dir=safe_root)

    # Check sys.path after
    assert str(safe_root) not in sys.path
