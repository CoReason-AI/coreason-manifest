import pytest

import coreason_manifest as cm
from coreason_manifest.v2.io import load_from_yaml
from coreason_manifest.v2.spec.definitions import ManifestV2


def test_v2_defaults() -> None:
    assert cm.Manifest is ManifestV2
    assert cm.Recipe is ManifestV2
    assert cm.load is load_from_yaml


def test_v1_removed_from_root() -> None:
    with pytest.raises(AttributeError):
        _ = cm.RecipeManifest  # type: ignore[attr-defined]

    with pytest.raises(AttributeError):
        _ = cm.AgentDefinition  # type: ignore[attr-defined]
