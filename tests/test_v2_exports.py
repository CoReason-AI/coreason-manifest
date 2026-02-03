# Copyright (c) 2025 CoReason, Inc.

import pytest

import coreason_manifest as cm
from coreason_manifest.v2.io import load_from_yaml
from coreason_manifest.v2.spec.definitions import ManifestV2


def test_v2_defaults() -> None:
    """Test that the top-level package exports V2 objects by default."""
    assert cm.Manifest is ManifestV2
    assert cm.load is load_from_yaml


def test_v1_removed_from_root() -> None:
    """Test that V1 objects are no longer available at the root."""
    with pytest.raises(AttributeError):
        _ = cm.RecipeManifest  # type: ignore[attr-defined, unused-ignore]


def test_v1_fallback_access() -> None:
    """Test that V1 objects can still be imported from the v1 namespace."""
    from coreason_manifest.recipes import RecipeManifest as OriginalRecipeManifest
    from coreason_manifest.v1 import RecipeManifest

    assert RecipeManifest is OriginalRecipeManifest
