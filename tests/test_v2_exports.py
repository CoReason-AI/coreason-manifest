# Copyright (c) 2025 CoReason, Inc.

import pytest
import coreason_manifest as cm
from coreason_manifest.v2.spec.definitions import ManifestV2
from coreason_manifest.v2.io import load_from_yaml

def test_v2_defaults():
    """Test that the top-level package exports V2 objects by default."""
    assert cm.Manifest is ManifestV2
    assert cm.load is load_from_yaml

def test_v1_removed_from_root():
    """Test that V1 objects are no longer available at the root."""
    with pytest.raises(AttributeError):
        _ = cm.RecipeManifest

def test_v1_fallback_access():
    """Test that V1 objects can still be imported from the v1 namespace."""
    from coreason_manifest.v1 import RecipeManifest
    from coreason_manifest.recipes import RecipeManifest as OriginalRecipeManifest

    assert RecipeManifest is OriginalRecipeManifest
