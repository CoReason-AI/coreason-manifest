with open("src/coreason_manifest/spec/ontology.py", "r") as f:
    content = f.read()

types_to_insert = """
type CoreRoutingIntent = Literal["informational_inform", "directive_instruct", "semantic_discovery", "taxonomic_restructure"]
CORE_ROUTING_SEMANTICS = {
    "informational_inform": "Provide information.",
    "directive_instruct": "Issue an instruction.",
    "semantic_discovery": "Discover semantics.",
    "taxonomic_restructure": "Restructure taxonomy."
}

type CoreEBNFConstruct = Literal["terminal", "non_terminal", "production_rule", "quantifier"]
CORE_EBNF_SEMANTICS = {
    "terminal": "Terminal symbol.",
    "non_terminal": "Non-terminal symbol.",
    "production_rule": "Production rule.",
    "quantifier": "Quantifier."
}

type CoreTokenMergeMetric = Literal["cosine_similarity", "euclidean_distance", "manhattan_distance"]
CORE_TOKEN_MERGE_SEMANTICS = {
    "cosine_similarity": "Cosine similarity metric.",
    "euclidean_distance": "Euclidean distance metric.",
    "manhattan_distance": "Manhattan distance metric."
}

type CoreComputeStrategyTier = Literal["speed_single_pass", "precision_token_class", "reasoning_ensemble"]
CORE_COMPUTE_STRATEGY_SEMANTICS = {
    "speed_single_pass": "Fast single-pass strategy.",
    "precision_token_class": "High-precision token processing.",
    "reasoning_ensemble": "Complex reasoning ensemble."
}

type CoreClinicalAssertion = Literal["present", "absent", "possible", "history", "family"]
CORE_CLINICAL_ASSERTION_SEMANTICS = {
    "present": "Assertion is present.",
    "absent": "Assertion is absent.",
    "possible": "Assertion is possible.",
    "history": "Historical assertion.",
    "family": "Family history assertion."
}

type CoreOBORelationEdge = Literal["is_a", "part_of", "has_part"]
CORE_OBO_RELATION_SEMANTICS = {
    "is_a": "Is-a relationship.",
    "part_of": "Part-of relationship.",
    "has_part": "Has-part relationship."
}

type CoreCognitiveMemoryDomain = Literal["working", "episodic", "semantic"]
CORE_COGNITIVE_MEMORY_SEMANTICS = {
    "working": "Working memory domain.",
    "episodic": "Episodic memory domain.",
    "semantic": "Semantic memory domain."
}

type CoreDisfluencyRole = Literal["reparandum", "interregnum", "repair"]
CORE_DISFLUENCY_SEMANTICS = {
    "reparandum": "The original speech error.",
    "interregnum": "The interruption phase.",
    "repair": "The corrected speech."
}

type CoreCacheEviction = Literal["lru", "lfu", "fifo"]
CORE_CACHE_EVICTION_SEMANTICS = {
    "lru": "Least Recently Used eviction.",
    "lfu": "Least Frequently Used eviction.",
    "fifo": "First In First Out eviction."
}

type CoreDefeasibleEdgeType = Literal["rebuttal", "undercut", "undermine"]
CORE_DEFEASIBLE_EDGE_SEMANTICS = {
    "rebuttal": "Rebuttal edge.",
    "undercut": "Undercutting edge.",
    "undermine": "Undermining edge."
}

type CoreIEEEAnomalyClass = Literal["logic_flaw", "data_fault", "interface_defect", "computation_error"]
CORE_IEEE_ANOMALY_SEMANTICS = {
    "logic_flaw": "Logic flaw anomaly.",
    "data_fault": "Data fault anomaly.",
    "interface_defect": "Interface defect anomaly.",
    "computation_error": "Computation error anomaly."
}

type CoreSMTSolverOutcome = Literal["sat", "unsat", "unknown"]
CORE_SMT_SOLVER_SEMANTICS = {
    "sat": "Satisfiable outcome.",
    "unsat": "Unsatisfiable outcome.",
    "unknown": "Unknown outcome."
}

type ValidRoutingIntent = CoreRoutingIntent | DomainExtensionString
type EBNFConstruct = CoreEBNFConstruct | DomainExtensionString
type TokenMergeMetric = CoreTokenMergeMetric | DomainExtensionString
type ComputeStrategyTier = CoreComputeStrategyTier | DomainExtensionString
type ClinicalAssertionState = CoreClinicalAssertion | DomainExtensionString
type OBORelationEdge = CoreOBORelationEdge | DomainExtensionString
type CognitiveMemoryDomain = CoreCognitiveMemoryDomain | DomainExtensionString
type DisfluencyRole = CoreDisfluencyRole | DomainExtensionString
type CacheEviction = CoreCacheEviction | DomainExtensionString
type DefeasibleEdgeType = CoreDefeasibleEdgeType | DomainExtensionString
type IEEEAnomalyClass = CoreIEEEAnomalyClass | DomainExtensionString
type SMTSolverOutcome = CoreSMTSolverOutcome | DomainExtensionString

"""

target = "type JsonPrimitiveState ="

if target in content:
    new_content = content.replace(target, types_to_insert + target)
    with open("src/coreason_manifest/spec/ontology.py", "w") as f:
        f.write(new_content)
    print("Success")
else:
    print("Target not found")
