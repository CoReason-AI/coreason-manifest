# Copyright (c) 2026 CoReason, Inc.
#
# This software is proprietary and dual-licensed.
# Licensed under the Prosperity Public License 3.0 (the "License").
# A copy of the license is available at https://prosperitylicense.com/versions/3.0.0
# For details, see the LICENSE file.
# Commercial use beyond a 30-day trial requires a separate license.
#
# Source Code: https://github.com/CoReason-AI/coreason-manifest

from coreason_manifest.spec.ontology import EnvironmentContextManifest


def test_deterministic_hashing_environment_context() -> None:
    """Prove that two identical EnvironmentContextManifest instances generated in
    different memory locations yield the exact same RFC 8785 canonical hash.
    """
    env1 = EnvironmentContextManifest(
        os_version="Ubuntu 22.04",
        python_version="3.14.2",
        active_dependencies={"pydantic": "123456", "hypothesis": "abcdef"},
        gpu_vram=24000,
        random_seed_state=42
    )

    env2 = EnvironmentContextManifest(
        os_version="Ubuntu 22.04",
        python_version="3.14.2",
        # Notice the keys are conceptually the same, ordering here is just definition
        active_dependencies={"hypothesis": "abcdef", "pydantic": "123456"},
        gpu_vram=24000,
        random_seed_state=42
    )

    assert env1 == env2
    assert hash(env1) == hash(env2)
    assert env1.model_dump_canonical() == env2.model_dump_canonical()
