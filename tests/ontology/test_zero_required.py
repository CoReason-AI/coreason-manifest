# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

"""Auto-instantiation tests for models with zero required fields.

Directly instantiates models that have no required fields, exercising all
model_validator and field_validator hooks that fire on default values.
"""

from coreason_manifest.spec.ontology import (
    CoreasonBaseState,
    CryptographicProvenancePolicy,
    EpistemicSecurityProfile,
    FacetMatrixProfile,
    FYIIntent,
    MCPCapabilityWhitelistPolicy,
    MultimodalTokenAnchorState,
    OpticalParsingSLA,
    SpatialHardwareProfile,
    SpatialRenderMaterial,
    StateVectorProfile,
    TerminalConditionContract,
)


class TestZeroRequiredFieldModels:
    """Instantiate every model with no required fields to exercise defaults."""

    def test_coreason_base_state(self) -> None:
        obj = CoreasonBaseState()
        assert obj is not None

    def test_cryptographic_provenance_policy(self) -> None:
        obj = CryptographicProvenancePolicy()
        assert obj is not None

    def test_epistemic_security_profile(self) -> None:
        obj = EpistemicSecurityProfile()
        assert obj is not None

    def test_fyi_intent(self) -> None:
        obj = FYIIntent()
        assert obj is not None

    def test_facet_matrix_profile(self) -> None:
        obj = FacetMatrixProfile()
        assert obj is not None

    def test_federated_state_snapshot(self) -> None:
        obj = FederatedStateSnapshot()
        assert obj is not None

    def test_mcp_capability_whitelist_policy(self) -> None:
        obj = MCPCapabilityWhitelistPolicy()
        assert obj is not None

    def test_multimodal_token_anchor_state(self) -> None:
        obj = MultimodalTokenAnchorState()
        assert obj is not None

    def test_optical_parsing_sla(self) -> None:
        obj = OpticalParsingSLA()
        assert obj is not None

    def test_spatial_hardware_profile(self) -> None:
        obj = SpatialHardwareProfile()
        assert obj is not None

    def test_spatial_render_material(self) -> None:
        obj = SpatialRenderMaterial(material_urn="urn:coreason:material:default")
        assert obj is not None

    def test_state_vector_profile(self) -> None:
        obj = StateVectorProfile()
        assert obj is not None

    def test_terminal_condition_contract(self) -> None:
        obj = TerminalConditionContract()
        assert obj is not None
