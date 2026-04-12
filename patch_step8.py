with open("src/coreason_manifest/spec/ontology.py") as f:
    content = f.read()


# Add CausalPropagationIntent and RDFSerializationIntent to AnyIntent
old_anyintent = """type AnyIntent = Annotated[
    SemanticIntent
    | DraftingIntent
    | AdjudicationIntent
    | EscalationIntent
    | SemanticDiscoveryIntent
    | TaxonomicRestructureIntent
    | LatentProjectionIntent
    | LatentSchemaInferenceIntent
    | HumanDirectiveIntent
    | ContextualSemanticResolutionIntent
    | ContinuousSpatialMutationIntent
    | System2RemediationIntent
    | OntologyDiscoveryIntent
    | SemanticMappingHeuristicIntent
    | TopologicalProjectionIntent
    | AnyInterventionState
    | MCPClientIntent
    | NeurosymbolicInferenceIntent,
    Field(discriminator="topology_class", description="A discriminated union of system intents."),
]"""

new_anyintent = """type AnyIntent = Annotated[
    SemanticIntent
    | DraftingIntent
    | AdjudicationIntent
    | EscalationIntent
    | SemanticDiscoveryIntent
    | TaxonomicRestructureIntent
    | LatentProjectionIntent
    | LatentSchemaInferenceIntent
    | HumanDirectiveIntent
    | ContextualSemanticResolutionIntent
    | ContinuousSpatialMutationIntent
    | System2RemediationIntent
    | OntologyDiscoveryIntent
    | SemanticMappingHeuristicIntent
    | TopologicalProjectionIntent
    | AnyInterventionState
    | MCPClientIntent
    | NeurosymbolicInferenceIntent
    | CausalPropagationIntent
    | RDFSerializationIntent,
    Field(discriminator="topology_class", description="A discriminated union of system intents."),
]"""

content = content.replace(old_anyintent, new_anyintent)

# Add BeliefModulationReceipt and RDFExportReceipt to AnyStateEvent
old_anystateevent = """type AnyStateEvent = Annotated[
    ObservationEvent
    | BeliefMutationEvent
    | SystemFaultEvent
    | AtomicPropositionState
    | PostCoordinatedSemanticState
    | HypothesisGenerationEvent
    | BargeInInterruptEvent
    | CounterfactualRegretEvent
    | ToolInvocationEvent
    | EpistemicPromotionEvent
    | NormativeDriftEvent
    | PersistenceCommitReceipt
    | TokenBurnReceipt
    | BudgetExhaustionEvent
    | EpistemicTelemetryEvent
    | CognitivePredictionReceipt
    | EpistemicAxiomVerificationReceipt
    | CognitiveRewardEvaluationReceipt
    | EpistemicFlowStateReceipt
    | CausalExplanationEvent
    | IntentClassificationReceipt
    | SemanticRelationalVectorState
    | OntologicalReificationReceipt
    | CircuitBreakerEvent
    | ExogenousEpistemicEvent
    | EpistemicLogEvent
    | InterventionReceipt
    | AdjudicationReceipt
    | CustodyReceipt
    | DefeasibleAttackEvent
    | EpistemicRejectionReceipt,
    Field(discriminator="topology_class", description="A discriminated union of state events."),
]"""

new_anystateevent = """type AnyStateEvent = Annotated[
    ObservationEvent
    | BeliefMutationEvent
    | SystemFaultEvent
    | AtomicPropositionState
    | PostCoordinatedSemanticState
    | HypothesisGenerationEvent
    | BargeInInterruptEvent
    | CounterfactualRegretEvent
    | ToolInvocationEvent
    | EpistemicPromotionEvent
    | NormativeDriftEvent
    | PersistenceCommitReceipt
    | TokenBurnReceipt
    | BudgetExhaustionEvent
    | EpistemicTelemetryEvent
    | CognitivePredictionReceipt
    | EpistemicAxiomVerificationReceipt
    | CognitiveRewardEvaluationReceipt
    | EpistemicFlowStateReceipt
    | CausalExplanationEvent
    | IntentClassificationReceipt
    | SemanticRelationalVectorState
    | OntologicalReificationReceipt
    | CircuitBreakerEvent
    | ExogenousEpistemicEvent
    | EpistemicLogEvent
    | InterventionReceipt
    | AdjudicationReceipt
    | CustodyReceipt
    | DefeasibleAttackEvent
    | EpistemicRejectionReceipt
    | BeliefModulationReceipt
    | RDFExportReceipt,
    Field(discriminator="topology_class", description="A discriminated union of state events."),
]"""

content = content.replace(old_anystateevent, new_anystateevent)

# Add DocumentKnowledgeGraphManifest to AnyTopologyManifest
old_anytopologymanifest = """type AnyTopologyManifest = Annotated[
    DAGTopologyManifest
    | CouncilTopologyManifest
    | SwarmTopologyManifest
    | EvolutionaryTopologyManifest
    | SMPCTopologyManifest
    | EvaluatorOptimizerTopologyManifest
    | DigitalTwinTopologyManifest
    | AdversarialMarketTopologyManifest
    | ConsensusFederationTopologyManifest
    | CapabilityForgeTopologyManifest
    | IntentElicitationTopologyManifest
    | NeurosymbolicVerificationTopologyManifest
    | DiscourseTreeManifest,
    Field(discriminator="topology_class", description="A discriminated union of workflow topologies."),
]"""

new_anytopologymanifest = """type AnyTopologyManifest = Annotated[
    DAGTopologyManifest
    | CouncilTopologyManifest
    | SwarmTopologyManifest
    | EvolutionaryTopologyManifest
    | SMPCTopologyManifest
    | EvaluatorOptimizerTopologyManifest
    | DigitalTwinTopologyManifest
    | AdversarialMarketTopologyManifest
    | ConsensusFederationTopologyManifest
    | CapabilityForgeTopologyManifest
    | IntentElicitationTopologyManifest
    | NeurosymbolicVerificationTopologyManifest
    | DiscourseTreeManifest
    | DocumentKnowledgeGraphManifest,
    Field(discriminator="topology_class", description="A discriminated union of workflow topologies."),
]"""

content = content.replace(old_anytopologymanifest, new_anytopologymanifest)

# Add model rebuilds
rebuilds = """DocumentKnowledgeGraphManifest.model_rebuild()
CausalPropagationIntent.model_rebuild()
BeliefModulationReceipt.model_rebuild()
RDFSerializationIntent.model_rebuild()
RDFExportReceipt.model_rebuild()
SchemaDrivenExtractionSLA.model_rebuild()
EvidentiaryGroundingSLA.model_rebuild()
"""

# Append rebuilds to the end of the file
content += "\n" + rebuilds

with open("src/coreason_manifest/spec/ontology.py", "w") as f:
    f.write(content)
