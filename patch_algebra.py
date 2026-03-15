with open("src/coreason_manifest/utils/algebra.py", "r") as f:
    content = f.read()

registry_code = """class SemanticResource(BaseModel):
    uri: str
    name: str
    description: str
    semantics: dict[str, str]

class ManifestSemanticRegistry:
    \"\"\"
    A DX-friendly registry designed to be directly mounted by an MCP Server.
    Exposes the core mathematical and semantic boundaries of the CoReason kernel.
    \"\"\"
    _RESOURCES = {
        "mcp://coreason/semantics/routing": SemanticResource(
            uri="mcp://coreason/semantics/routing",
            name="Core Routing Intents",
            description="ISO 24617-2 and Schema.org semantic routing classifications.",
            semantics=ontology.CORE_ROUTING_SEMANTICS
        ),
        "mcp://coreason/semantics/ebnf_construct": SemanticResource(
            uri="mcp://coreason/semantics/ebnf_construct",
            name="Core EBNF Constructs",
            description="Core EBNF syntax constructs.",
            semantics=ontology.CORE_EBNF_SEMANTICS
        ),
        "mcp://coreason/semantics/token_merge_metric": SemanticResource(
            uri="mcp://coreason/semantics/token_merge_metric",
            name="Core Token Merge Metrics",
            description="Metrics for token merging.",
            semantics=ontology.CORE_TOKEN_MERGE_SEMANTICS
        ),
        "mcp://coreason/semantics/compute_strategy_tier": SemanticResource(
            uri="mcp://coreason/semantics/compute_strategy_tier",
            name="Core Compute Strategy Tiers",
            description="Compute strategy tiers.",
            semantics=ontology.CORE_COMPUTE_STRATEGY_SEMANTICS
        ),
        "mcp://coreason/semantics/clinical_assertion": SemanticResource(
            uri="mcp://coreason/semantics/clinical_assertion",
            name="Core Clinical Assertions",
            description="Core clinical assertions.",
            semantics=ontology.CORE_CLINICAL_ASSERTION_SEMANTICS
        ),
        "mcp://coreason/semantics/obo_relation_edge": SemanticResource(
            uri="mcp://coreason/semantics/obo_relation_edge",
            name="Core OBO Relation Edges",
            description="Core OBO relation edges.",
            semantics=ontology.CORE_OBO_RELATION_SEMANTICS
        ),
        "mcp://coreason/semantics/cognitive_memory_domain": SemanticResource(
            uri="mcp://coreason/semantics/cognitive_memory_domain",
            name="Core Cognitive Memory Domains",
            description="Domains for cognitive memory.",
            semantics=ontology.CORE_COGNITIVE_MEMORY_SEMANTICS
        ),
        "mcp://coreason/semantics/disfluency_role": SemanticResource(
            uri="mcp://coreason/semantics/disfluency_role",
            name="Core Disfluency Roles",
            description="Roles for disfluency handling.",
            semantics=ontology.CORE_DISFLUENCY_SEMANTICS
        ),
        "mcp://coreason/semantics/cache_eviction": SemanticResource(
            uri="mcp://coreason/semantics/cache_eviction",
            name="Core Cache Evictions",
            description="Cache eviction strategies.",
            semantics=ontology.CORE_CACHE_EVICTION_SEMANTICS
        ),
        "mcp://coreason/semantics/defeasible_edge_type": SemanticResource(
            uri="mcp://coreason/semantics/defeasible_edge_type",
            name="Core Defeasible Edge Types",
            description="Types of defeasible edges.",
            semantics=ontology.CORE_DEFEASIBLE_EDGE_SEMANTICS
        ),
        "mcp://coreason/semantics/ieee_anomalies": SemanticResource(
            uri="mcp://coreason/semantics/ieee_anomalies",
            name="IEEE 1044 Anomaly Classifications",
            description="Standard classifications for structural and logical software faults.",
            semantics=ontology.CORE_IEEE_ANOMALY_SEMANTICS
        ),
        "mcp://coreason/semantics/smt_solver_outcome": SemanticResource(
            uri="mcp://coreason/semantics/smt_solver_outcome",
            name="Core SMT Solver Outcomes",
            description="Outcomes for SMT solvers.",
            semantics=ontology.CORE_SMT_SOLVER_SEMANTICS
        )
    }

    @classmethod
    def list_resources(cls) -> list[SemanticResource]:
        \"\"\"Returns all available semantic resources for MCP discovery.\"\"\"
        return list(cls._RESOURCES.values())

    @classmethod
    def read_resource(cls, uri: str) -> SemanticResource | None:
        \"\"\"Returns the specific semantic dictionary for LLM context injection.\"\"\"
        return cls._RESOURCES.get(uri)

"""

if "ManifestSemanticRegistry" not in content:
    content += "\n" + registry_code
    with open("src/coreason_manifest/utils/algebra.py", "w") as f:
        f.write(content)
    print("Semantic Registry injected")
