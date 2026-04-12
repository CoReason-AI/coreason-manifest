import pytest
from coreason_manifest.spec.ontology import (
    ExecutionSubstrateProfile,
    SubstrateDialectProfile,
    SubstrateHydrationManifest
)

def test_execution_substrate_profile_canonical_sort():
    profile = ExecutionSubstrateProfile(
        dialect=SubstrateDialectProfile.SYMBOLIC_AI_DBC,
        required_package_signatures=["b==2.0", "a==1.0", "c==3.0"],
        vram_overhead_mb=100,
        supports_lazy_hydration=True
    )
    # Testing that _enforce_canonical_sort gets called and works
    assert profile.required_package_signatures == ["a==1.0", "b==2.0", "c==3.0"]

def test_substrate_hydration_manifest_creation():
    profile = ExecutionSubstrateProfile(
        dialect=SubstrateDialectProfile.NATIVE_PYTHON,
        required_package_signatures=["xyz==1.0"],
        vram_overhead_mb=50,
        supports_lazy_hydration=False
    )
    manifest = SubstrateHydrationManifest(
        target_node_cid="did:coreason:somenodeid",
        substrate_profile=profile,
        cryptographic_checksums={
            "xyz": "abc123hash"
        }
    )
    assert manifest.target_node_cid == "did:coreason:somenodeid"
    assert manifest.topology_class == "substrate_hydration"
