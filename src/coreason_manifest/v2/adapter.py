# Copyright (c) 2025 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

"""Adapter module for backward compatibility with V1 Runtime."""

from uuid import uuid4

from coreason_manifest.definitions.topology import StateDefinition
from coreason_manifest.recipes import PolicyConfig, RecipeInterface, RecipeManifest
from coreason_manifest.v2.compiler import compile_to_topology
from coreason_manifest.v2.spec.definitions import ManifestV2


def v2_to_recipe(manifest: ManifestV2) -> RecipeManifest:
    """Convert a V2 Manifest into a V1 RecipeManifest.

    Args:
        manifest: The V2 manifest to convert.

    Returns:
        The converted RecipeManifest compatible with the V1 engine.
    """
    # Generate a random ID as V2 manifests don't strictly require one at the root
    # In a real system, this might be consistent or derived from name/version
    recipe_id = str(uuid4())

    # Compile the topology
    topology = compile_to_topology(manifest)

    # Convert metadata
    # We dump to dict to handle potential Pydantic model vs dict
    design_metadata = {}
    if manifest.metadata.design_metadata:
        design_metadata = manifest.metadata.design_metadata.model_dump(by_alias=True, exclude_none=True)

    # Determine persistence
    backend = (manifest.state.backend or "ephemeral").lower()
    # If explicitly not ephemeral/memory, treat as persistent (e.g., redis, sql)
    persistence = "persistent" if backend not in ("ephemeral", "memory") else "ephemeral"

    # Construct the RecipeManifest
    return RecipeManifest(
        id=recipe_id,
        version="0.1.0",  # Default version
        name=manifest.metadata.name,
        description=None,
        interface=RecipeInterface(inputs=manifest.interface.inputs, outputs=manifest.interface.outputs),
        state=StateDefinition(schema_=manifest.state.schema_, persistence=persistence),
        policy=PolicyConfig(
            max_steps=manifest.policy.max_steps,
            max_retries=manifest.policy.max_retries,
            timeout=manifest.policy.timeout,
            human_in_the_loop=manifest.policy.human_in_the_loop,
        ),
        parameters=manifest.definitions,
        topology=topology,
        metadata=design_metadata,
    )
