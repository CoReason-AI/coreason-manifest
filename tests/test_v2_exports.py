# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

import pytest

import coreason_manifest as cm
from coreason_manifest.spec.v2.definitions import ManifestV2
from coreason_manifest.spec.v2.recipe import RecipeDefinition
from coreason_manifest.utils.v2.io import load_from_yaml


def test_v2_defaults() -> None:
    assert cm.Manifest is ManifestV2
    assert cm.Recipe is RecipeDefinition
    assert cm.load is load_from_yaml


def test_v1_removed_from_root() -> None:
    # RecipeManifest was V1, should definitely be gone.
    with pytest.raises(AttributeError):
        _ = cm.RecipeManifest  # type: ignore[attr-defined]

    # AgentDefinition is now V2 and exported, so we don't check for its absence.
