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
from coreason_manifest.v2.io import dump_to_yaml, load_from_yaml
from coreason_manifest.v2.spec.definitions import ManifestV2


def test_top_level_exports() -> None:
    """Verify that key components are exported from the top-level package (V2)."""
    # Verify Manifest export
    assert hasattr(coreason_manifest, "Manifest")
    assert coreason_manifest.Manifest is ManifestV2

    # Verify Recipe export (alias)
    assert hasattr(coreason_manifest, "Recipe")
    assert coreason_manifest.Recipe is ManifestV2

    # Verify load/dump
    assert hasattr(coreason_manifest, "load")
    assert coreason_manifest.load is load_from_yaml
    assert hasattr(coreason_manifest, "dump")
    assert coreason_manifest.dump is dump_to_yaml

    # Verify version
    assert hasattr(coreason_manifest, "__version__")

    # Check __all__
    expected = ["Manifest", "Recipe", "load", "dump", "__version__"]
    for item in expected:
        assert item in coreason_manifest.__all__


def test_legacy_exports_removed() -> None:
    """Verify that legacy V1 components are NOT exported from root."""
    assert not hasattr(coreason_manifest, "AgentStatus")
    assert not hasattr(coreason_manifest, "AgentDefinition")
    assert not hasattr(coreason_manifest, "RecipeManifest")
