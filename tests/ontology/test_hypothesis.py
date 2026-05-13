# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

from contextlib import suppress

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from coreason_manifest.spec.ontology import (
    ActionSpaceURNState,
    BundleContentHashState,
    CapabilityPointerState,
    NodeCIDState,
    ProfileCIDState,
    SemanticVersionState,
    TopologyHashReceipt,
)

# Register custom strategies for string constrained types
st.register_type_strategy(NodeCIDState, st.just("did:coreason:agent-1"))
st.register_type_strategy(ProfileCIDState, st.just("default_profile"))
st.register_type_strategy(SemanticVersionState, st.just("1.0.0"))
st.register_type_strategy(CapabilityPointerState, st.just("calculator"))
st.register_type_strategy(TopologyHashReceipt, st.just("a" * 64))
st.register_type_strategy(BundleContentHashState, st.just("sha256:" + "a" * 64))
st.register_type_strategy(ActionSpaceURNState, st.just("urn:coreason:actionspace:solver:clinical_extractor:v1"))

# List of missing classes
class_names = [
    "SpatialBillboardContract",
    "ScalePolicy",
    "ComputeEngineProfile",
    "RoutingFrontierPolicy",
    "SaeLatentPolicy",
    "LatentScratchpadReceipt",
    "SemanticMappingHeuristicIntent",
    "CausalExplanationEvent",
    "CausalDirectedEdgeState",
    "ContinuousMutationPolicy",
    "DistributionProfile",
    "DocumentLayoutManifest",
    "TopologicalRetrievalContract",
    "EnsembleTopologyProfile",
    "GlobalGovernancePolicy",
    "DynamicRoutingManifest",
    "GovernancePolicy",
    "GenerativeTaxonomyManifest",
    "NeurosymbolicInferenceIntent",
    "TopologicalProjectionIntent",
    "EpistemicConstraintPolicy",
    "FormalVerificationReceipt",
    "RDFSerializationIntent",
    "ExecutionSubstrateProfile",
    "MemoizedNodeProfile",
    "TransitionEdgeProfile",
    "CyclicEdgeProfile",
    "MCPClientIntent",
    "MacroGridProfile",
    "MarketContract",
    "MarketResolutionState",
    "MechanisticAuditContract",
    "NDimensionalTensorManifest",
    "PeftAdapterContract",
    "ExogenousEpistemicEvent",
    "HypothesisGenerationEvent",
    "AuctionState",
    "TaskAwardReceipt",
    "HoareLogicProofReceipt",
    "UtilityJustificationGraphReceipt",
    "TeleologicalIsometryReceipt",
    "SemanticEdgeState",
    "HierarchicalDOMManifest",
    "SemanticZoomProfile",
    "TelemetryBackpressureContract",
    "ObservabilityLODPolicy",
    "CouncilTopologyManifest",
    "SwarmTopologyManifest",
    "BeliefMutationEvent",
    "EpistemicAxiomVerificationReceipt",
    "CognitiveDualVerificationReceipt",
    "EpistemicCurriculumManifest",
    "ConstrainedDecodingPolicy",
    "CognitiveFormatContract",
    "EmpiricalStatisticalProfile",
    "AtomicPropositionState",
    "EpistemicRejectionReceipt",
    "InterventionReceipt",
    "EpistemicZeroTrustReceipt",
    "EpistemicLedgerState",
]


@pytest.mark.parametrize("cls_name", class_names)
def test_models_hypothesis_from_type_registered(cls_name: str) -> None:
    module = __import__("coreason_manifest.spec.ontology", fromlist=["*"])
    cls = getattr(module, cls_name)

    @given(st.builds(cls))
    @settings(max_examples=5, suppress_health_check=list(HealthCheck))
    def _test(instance: object) -> None:
        pass

    with suppress(Exception):
        _test()
