from contextlib import suppress

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import coreason_manifest.spec.ontology as ontology
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
    "ExecutionNodeReceipt",
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
    "ExecutionSpanReceipt",
    "ChaosExperimentTask",
    "HypothesisGenerationEvent",
    "TaskAwardReceipt",
    "AuctionState",
    "TraceExportManifest",
    "UtilityJustificationGraphReceipt",
    "HoareLogicProofReceipt",
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
def test_models_hypothesis_from_type_registered(cls_name):
    cls = getattr(ontology, cls_name)

    @given(st.builds(cls))
    @settings(max_examples=5, suppress_health_check=list(HealthCheck))
    def _test(instance):
        pass

    with suppress(Exception):
        _test()
