# Copyright (c) 2025 CoReason, Inc.. All Rights Reserved
#
# This software is licensed under the Prosperity Public License 3.0.0.
# The issuer of the Prosperity Public License for this software is CoReason, Inc..
#
# For a commercial version of this software, please contact us at gowtham.rao@coreason.ai.

from coreason_manifest.adapters.mcp.schemas import (
    BoundedJSONRPCRequest,
    JSONRPCError,
    JSONRPCErrorResponse,
    MCPCapabilityWhitelist,
    MCPClientMessage,
    MCPPromptRef,
    MCPResourceList,
    MCPServerConfig,
    MCPServerManifest,
    SSETransportConfig,
    StdioTransportConfig,
)
from coreason_manifest.compute.inference import ActiveInferenceContract, AnalogicalMappingTask, InterventionalCausalTask
from coreason_manifest.compute.neuromodulation import (
    ActivationSteeringContract,
    CognitiveRoutingDirective,
    LatentSmoothingProfile,
    SaeLatentFirewall,
)
from coreason_manifest.compute.peft import PeftAdapterContract
from coreason_manifest.compute.profiles import (
    ComputeProvisioningRequest,
    ModelProfile,
    QoSClassification,
    RateCard,
    RoutingFrontier,
)
from coreason_manifest.compute.stochastic import (
    CrossoverStrategy,
    CrossoverType,
    DistributionProfile,
    DistributionType,
    FitnessObjective,
    LogitSteganographyContract,
    MutationPolicy,
    OptimizationDirection,
    VerifiableEntropy,
)
from coreason_manifest.compute.symbolic import NeuroSymbolicHandoff
from coreason_manifest.compute.test_time import DynamicConvergenceSLA, EscalationContract, ProcessRewardContract
from coreason_manifest.core.base import CoreasonBaseModel
from coreason_manifest.core.identity import VerifiableCredentialPresentation
from coreason_manifest.core.primitives import (
    DataClassification,
    GitSHA,
    NodeID,
    ProfileID,
    RiskLevel,
    SemanticVersion,
    SystemRole,
    ToolID,
)
from coreason_manifest.oversight import PredictionMarketPolicy
from coreason_manifest.oversight.adjudication import AdjudicationRubric, AdjudicationVerdict, GradingCriteria
from coreason_manifest.oversight.audit import MechanisticAuditContract
from coreason_manifest.oversight.dlp import (
    InformationFlowPolicy,
    RedactionRule,
    SanitizationAction,
    SecureSubSession,
    SemanticFirewallPolicy,
)
from coreason_manifest.oversight.governance import (
    ConsensusPolicy,
    ConstitutionalRule,
    FormalVerificationContract,
    GlobalGovernance,
    GovernancePolicy,
    QuorumPolicy,
)
from coreason_manifest.oversight.intervention import (
    AnyInterventionPayload,
    BoundedInterventionScope,
    FallbackSLA,
    InterventionPolicy,
    InterventionRequest,
    InterventionVerdict,
    LifecycleTrigger,
    OverrideIntent,
)
from coreason_manifest.oversight.resilience import (
    AnyResiliencePayload,
    CircuitBreakerTrip,
    FallbackTrigger,
    QuarantineOrder,
)
from coreason_manifest.presentation.intents import (
    AdjudicationIntent,
    AnyIntent,
    AnyPresentationIntent,
    BaseIntent,
    DraftingIntent,
    EscalationIntent,
    FYIIntent,
    InformationalIntent,
    PresentationEnvelope,
)
from coreason_manifest.presentation.scivis import (
    AnyPanel,
    BasePanel,
    ChannelEncoding,
    EncodingChannel,
    FacetMatrix,
    GrammarPanel,
    InsightCard,
    MacroGrid,
    MarkType,
    ScaleDefinition,
    ScaleType,
)
from coreason_manifest.presentation.templates import DynamicLayoutTemplate
from coreason_manifest.state.argumentation import (
    ArgumentClaim,
    ArgumentGraph,
    AttackVector,
    DefeasibleAttack,
    EvidentiaryWarrant,
)
from coreason_manifest.state.cognition import CognitiveStateProfile, CognitiveUncertaintyProfile
from coreason_manifest.state.differentials import (
    DefeasibleCascade,
    MigrationContract,
    PatchOperation,
    RollbackRequest,
    StateDiff,
    StatePatch,
    TemporalCheckpoint,
    TruthMaintenancePolicy,
)
from coreason_manifest.state.embodied import EmbodiedSensoryVector
from coreason_manifest.state.events import (
    AnyStateEvent,
    BargeInInterruptEvent,
    BaseStateEvent,
    BeliefUpdateEvent,
    CausalAttribution,
    CausalDirectedEdge,
    CounterfactualRegretEvent,
    FalsificationCondition,
    HardwareEnclaveAttestation,
    HypothesisGenerationEvent,
    NeuralAuditAttestation,
    ObservationEvent,
    SaeFeatureActivation,
    StructuralCausalModel,
    SystemFaultEvent,
    ZeroKnowledgeProof,
)
from coreason_manifest.state.memory import (
    EpistemicLedger,
    EvictionPolicy,
    FederatedStateSnapshot,
    TheoryOfMindSnapshot,
    WorkingMemorySnapshot,
)
from coreason_manifest.state.scratchpad import LatentScratchpadTrace, ThoughtBranch
from coreason_manifest.state.semantic import (
    CausalInterval,
    DimensionalProjectionContract,
    HomomorphicEncryptionProfile,
    LineageWatermark,
    MemoryProvenance,
    MemoryTier,
    OntologicalHandshake,
    SalienceProfile,
    SemanticEdge,
    SemanticNode,
    SpatialAnchor,
    TemporalBounds,
    VectorEmbedding,
)
from coreason_manifest.state.toolchains import AnyToolchainState, BrowserDOMState, TerminalBufferState
from coreason_manifest.telemetry.custody import CustodyRecord, ExecutionNode, TamperError
from coreason_manifest.telemetry.schemas import (
    ExecutionSpan,
    LogEnvelope,
    MetadataDict,
    ObservabilityPolicy,
    SpanEvent,
    SpanKind,
    SpanStatusCode,
    SpanTrace,
    TelemetryScalar,
    TraceExportBatch,
)
from coreason_manifest.telemetry.ux import AmbientSignal, SuspenseEnvelope
from coreason_manifest.testing.chaos import ChaosExperiment, FaultInjectionProfile, FaultType, SteadyStateHypothesis
from coreason_manifest.testing.red_team import AdversarialSimulationProfile
from coreason_manifest.tooling.environments import ActionSpace, MCPClientBinding, MCPTransport
from coreason_manifest.tooling.schemas import ExecutionSLA, PermissionBoundary, SideEffectProfile, ToolDefinition
from coreason_manifest.tooling.spatial import BoundingBox, NormalizedCoordinate, SpatialKinematicAction
from coreason_manifest.workflow import HypothesisStake, MarketResolution, PredictionMarketState
from coreason_manifest.workflow.auctions import (
    AgentBid,
    AuctionPolicy,
    AuctionState,
    AuctionType,
    EscrowPolicy,
    TaskAnnouncement,
    TaskAward,
    TieBreaker,
)
from coreason_manifest.workflow.constraints import InputMapping, OutputMapping
from coreason_manifest.workflow.envelope import BilateralSLA, PostQuantumSignature, WorkflowEnvelope
from coreason_manifest.workflow.nodes import (
    AgentAttestation,
    AgentNode,
    AnyNode,
    BaseNode,
    CompositeNode,
    EpistemicScanner,
    HumanNode,
    SelfCorrectionPolicy,
    System1Reflex,
    SystemNode,
)
from coreason_manifest.workflow.topologies import (
    AnyTopology,
    BackpressurePolicy,
    BaseTopology,
    CouncilTopology,
    DAGTopology,
    DiversityConstraint,
    EvolutionaryTopology,
    OntologicalAlignmentPolicy,
    SMPCTopology,
    StateContract,
    SwarmTopology,
)

__all__ = [
    "ActionSpace",
    "ActivationSteeringContract",
    "ActiveInferenceContract",
    "AdjudicationIntent",
    "AdjudicationRubric",
    "AdjudicationVerdict",
    "AdversarialSimulationProfile",
    "AgentAttestation",
    "AgentBid",
    "AgentNode",
    "AmbientSignal",
    "AnalogicalMappingTask",
    "AnyIntent",
    "AnyInterventionPayload",
    "AnyNode",
    "AnyPanel",
    "AnyPresentationIntent",
    "AnyResiliencePayload",
    "AnyStateEvent",
    "AnyToolchainState",
    "AnyTopology",
    "ArgumentClaim",
    "ArgumentGraph",
    "AttackVector",
    "AuctionPolicy",
    "AuctionState",
    "AuctionType",
    "BackpressurePolicy",
    "BargeInInterruptEvent",
    "BaseIntent",
    "BaseNode",
    "BasePanel",
    "BaseStateEvent",
    "BaseTopology",
    "BeliefUpdateEvent",
    "BilateralSLA",
    "BoundedInterventionScope",
    "BoundedJSONRPCRequest",
    "BoundingBox",
    "BrowserDOMState",
    "CausalAttribution",
    "CausalDirectedEdge",
    "CausalInterval",
    "ChannelEncoding",
    "ChaosExperiment",
    "CircuitBreakerTrip",
    "CognitiveRoutingDirective",
    "CognitiveStateProfile",
    "CognitiveUncertaintyProfile",
    "CompositeNode",
    "ComputeProvisioningRequest",
    "ConsensusPolicy",
    "ConstitutionalRule",
    "CoreasonBaseModel",
    "CouncilTopology",
    "CounterfactualRegretEvent",
    "CrossoverStrategy",
    "CrossoverType",
    "CustodyRecord",
    "DAGTopology",
    "DataClassification",
    "DefeasibleAttack",
    "DefeasibleCascade",
    "DimensionalProjectionContract",
    "DistributionProfile",
    "DistributionType",
    "DiversityConstraint",
    "DraftingIntent",
    "DynamicConvergenceSLA",
    "DynamicLayoutTemplate",
    "EmbodiedSensoryVector",
    "EncodingChannel",
    "EpistemicLedger",
    "EpistemicScanner",
    "EscalationContract",
    "EscalationIntent",
    "EscrowPolicy",
    "EvictionPolicy",
    "EvidentiaryWarrant",
    "EvolutionaryTopology",
    "ExecutionNode",
    "ExecutionSLA",
    "ExecutionSpan",
    "FYIIntent",
    "FacetMatrix",
    "FallbackSLA",
    "FallbackTrigger",
    "FalsificationCondition",
    "FaultInjectionProfile",
    "FaultType",
    "FederatedStateSnapshot",
    "FitnessObjective",
    "FormalVerificationContract",
    "GitSHA",
    "GlobalGovernance",
    "GovernancePolicy",
    "GradingCriteria",
    "GrammarPanel",
    "HardwareEnclaveAttestation",
    "HomomorphicEncryptionProfile",
    "HumanNode",
    "HypothesisGenerationEvent",
    "HypothesisStake",
    "InformationFlowPolicy",
    "InformationalIntent",
    "InputMapping",
    "InsightCard",
    "InterventionPolicy",
    "InterventionRequest",
    "InterventionVerdict",
    "InterventionalCausalTask",
    "JSONRPCError",
    "JSONRPCErrorResponse",
    "LatentScratchpadTrace",
    "LatentSmoothingProfile",
    "LifecycleTrigger",
    "LineageWatermark",
    "LogEnvelope",
    "LogitSteganographyContract",
    "MCPCapabilityWhitelist",
    "MCPClientBinding",
    "MCPClientMessage",
    "MCPPromptRef",
    "MCPResourceList",
    "MCPServerConfig",
    "MCPServerManifest",
    "MCPTransport",
    "MacroGrid",
    "MarkType",
    "MarketResolution",
    "MechanisticAuditContract",
    "MemoryProvenance",
    "MemoryTier",
    "MetadataDict",
    "MigrationContract",
    "ModelProfile",
    "MutationPolicy",
    "NeuralAuditAttestation",
    "NeuroSymbolicHandoff",
    "NodeID",
    "NormalizedCoordinate",
    "ObservabilityPolicy",
    "ObservationEvent",
    "OntologicalAlignmentPolicy",
    "OntologicalHandshake",
    "OptimizationDirection",
    "OutputMapping",
    "OverrideIntent",
    "PatchOperation",
    "PeftAdapterContract",
    "PermissionBoundary",
    "PostQuantumSignature",
    "PredictionMarketPolicy",
    "PredictionMarketState",
    "PresentationEnvelope",
    "ProcessRewardContract",
    "ProfileID",
    "QoSClassification",
    "QuarantineOrder",
    "QuorumPolicy",
    "RateCard",
    "RedactionRule",
    "RiskLevel",
    "RollbackRequest",
    "RoutingFrontier",
    "SMPCTopology",
    "SSETransportConfig",
    "SaeFeatureActivation",
    "SaeLatentFirewall",
    "SalienceProfile",
    "SanitizationAction",
    "ScaleDefinition",
    "ScaleType",
    "SecureSubSession",
    "SelfCorrectionPolicy",
    "SemanticEdge",
    "SemanticFirewallPolicy",
    "SemanticNode",
    "SemanticVersion",
    "SideEffectProfile",
    "SpanEvent",
    "SpanKind",
    "SpanStatusCode",
    "SpanTrace",
    "SpatialAnchor",
    "SpatialKinematicAction",
    "StateContract",
    "StateDiff",
    "StatePatch",
    "StdioTransportConfig",
    "SteadyStateHypothesis",
    "StructuralCausalModel",
    "SuspenseEnvelope",
    "SwarmTopology",
    "System1Reflex",
    "SystemFaultEvent",
    "SystemNode",
    "SystemRole",
    "TamperError",
    "TaskAnnouncement",
    "TaskAward",
    "TelemetryScalar",
    "TemporalBounds",
    "TemporalCheckpoint",
    "TerminalBufferState",
    "TheoryOfMindSnapshot",
    "ThoughtBranch",
    "TieBreaker",
    "ToolDefinition",
    "ToolID",
    "TraceExportBatch",
    "TruthMaintenancePolicy",
    "VectorEmbedding",
    "VerifiableCredentialPresentation",
    "VerifiableEntropy",
    "WorkflowEnvelope",
    "WorkingMemorySnapshot",
    "ZeroKnowledgeProof",
]


def _rebuild_ontology() -> None:
    """
    Dynamically resolves all Pydantic forward references strictly at the end of module initialization.
    This prevents circular import death spirals by guaranteeing the entire ontology is loaded
    into sys.modules before compilation begins.
    """
    import typing

    from coreason_manifest.workflow.topologies import AnyTopology

    _ = AnyTopology

    for _name in __all__:
        _obj = globals().get(_name)
        if isinstance(_obj, type) and issubclass(_obj, CoreasonBaseModel) and _obj is not CoreasonBaseModel:
            typing.cast("type[CoreasonBaseModel]", _obj).model_rebuild()


# Execute immediately upon module load
_rebuild_ontology()
