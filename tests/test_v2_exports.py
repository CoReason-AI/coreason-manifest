import pytest

import coreason_manifest as cm
from coreason_manifest.spec.v2.definitions import ManifestV2
from coreason_manifest.utils.v2.io import load_from_yaml


def test_v2_defaults() -> None:
    assert cm.Manifest is ManifestV2
    assert cm.Recipe is ManifestV2
    assert cm.load is load_from_yaml


def test_v1_removed_from_root() -> None:
    # RecipeManifest was V1, should definitely be gone.
    with pytest.raises(AttributeError):
        _ = cm.RecipeManifest  # type: ignore[attr-defined]

    # AgentDefinition is now V2 and exported, so we don't check for its absence.
