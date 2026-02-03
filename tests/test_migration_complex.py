# Copyright (c) 2025 CoReason, Inc.

import importlib
from typing import Any, cast

import coreason_manifest


def test_mixed_namespace_usage() -> None:
    """
    Edge Case: Verify that V2 and V1 objects can coexist in the same runtime
    without type conflicts.
    """
    # V2 Import
    from coreason_manifest import Manifest

    # V1 Import
    from coreason_manifest.v1 import RecipeManifest

    # Ensure they are distinct types from different modules
    assert Manifest.__module__.startswith("coreason_manifest.v2")
    assert RecipeManifest.__module__.startswith("coreason_manifest.recipes")

    # Assert no namespace pollution
    assert not hasattr(Manifest, "capabilities")  # V1 field
    assert not hasattr(RecipeManifest, "apiVersion")  # V2 field


def test_wildcard_import_safety() -> None:
    """
    Edge Case: Verify that 'from coreason_manifest import *' does not leak V1 objects.
    This is hard to test directly inside a function, so we inspect __all__.
    """
    all_exports = coreason_manifest.__all__

    # Allowed V2 exports
    assert "Manifest" in all_exports
    assert "load" in all_exports

    # Forbidden V1 exports
    assert "RecipeManifest" not in all_exports
    assert "AgentDefinition" not in all_exports
    assert "Topology" not in all_exports


def test_reload_resilience() -> None:
    """
    Complex Case: Verify that reloading the module preserves the new V2 defaults.
    """
    importlib.reload(coreason_manifest)

    assert coreason_manifest.Manifest.__name__ == "ManifestV2"
    assert not hasattr(coreason_manifest, "RecipeManifest")


def test_submodule_aliasing() -> None:
    """
    Edge Case: Ensure that accessing submodules directly still works and doesn't
    confuse the root namespace.
    """
    import coreason_manifest.definitions.agent as agent_def_module

    # The class should be the same as the one exposed in v1
    from coreason_manifest.v1 import AgentDefinition

    assert agent_def_module.AgentDefinition is AgentDefinition


def test_v1_v2_name_collision_handling() -> None:
    """
    Complex Case: Both V1 and V2 have a concept of 'Recipe'.
    Ensure the root 'Recipe' alias points to V2, while V1 'Recipe' is explicit.
    """
    # Root alias
    from coreason_manifest import Recipe as RecipeV2Alias

    # V1 alias
    from coreason_manifest.v1 import Recipe as RecipeV1Alias

    assert RecipeV2Alias is coreason_manifest.v2.spec.definitions.ManifestV2
    assert RecipeV1Alias is coreason_manifest.recipes.RecipeManifest

    # Suppress overlap error or use cast
    assert cast(Any, RecipeV2Alias) is not cast(Any, RecipeV1Alias)


def test_manifest_load_consistency() -> None:
    """
    Edge Case: Verify that `cm.load` is strictly the V2 loader and rejects
    V1-style JSON if it doesn't match V2 YAML schema (which it won't).
    """
    # This just asserts identity, real loading tests are in test_v2_io.py
    from coreason_manifest.v2.io import load_from_yaml

    assert coreason_manifest.load is load_from_yaml
