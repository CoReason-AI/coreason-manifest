import ast
from pathlib import Path

NEW_DOCSTRINGS = {
    "SemanticMappingHeuristicIntent": """AGENT INSTRUCTION: A formal cryptographic petition submitted by an agent to update the swarm's internal graph logic. Compiles discovered literature and external API responses into a mathematically verifiable semantic mapping rule (e.g., SWRL).

    CAUSAL AFFORDANCE: Physically authorizes the orchestrator to inject a new heuristic into the swarm's global hypothesis space.

    EPISTEMIC BOUNDS: Bounded to strict JSON schema validation constraints defined in the manifest.

    MCP ROUTING TRIGGERS: Semantic Mapping, Heuristic Injection, Cryptographic Petition, Swarm Logic""",
    "ContextualSemanticResolutionIntent": """AGENT INSTRUCTION: Acts as the kinetic trigger forcing the orchestrator to dynamically resolve a raw, untyped SemanticRelationalVectorState against a global standard ontology using optimal transport metrics, entirely bypassing legacy ETL string-matching.

    CAUSAL AFFORDANCE: Physically authorizes the orchestrator to execute the defined optimal transport resolution.

    EPISTEMIC BOUNDS: Bounded to strict JSON schema validation constraints defined in the manifest.

    MCP ROUTING TRIGGERS: Semantic Resolution, Optimal Transport, ETL Bypass, Dynamic Ontology""",
    "GlobalSemanticInvariantProfile": """AGENT INSTRUCTION: A macroscopic topological container that persists global contextual qualifiers (e.g., patient cohorts, operational environments, temporal scopes) across the Merkle-DAG, shielding downstream atomic propositions from context collapse.

    CAUSAL AFFORDANCE: Instructs the orchestrator's verification engine to natively execute mathematical dominance checks between a payload's classification and its context.

    EPISTEMIC BOUNDS: Bounded to strict JSON schema validation constraints defined in the manifest.

    MCP ROUTING TRIGGERS: Contextual Qualifiers, Topological Container, Semantic Invariant, Context Collapse""",
    "DiscourseNodeState": """AGENT INSTRUCTION: A structural vertex defining a distinct rhetorical block of text within a document, enabling hierarchical parsing and graph-based traversal of discourse.

    CAUSAL AFFORDANCE: Instructs the orchestrator to allocate memory for a distinct rhetorical block of text.

    EPISTEMIC BOUNDS: Bounded to strict JSON schema validation constraints defined in the manifest.

    MCP ROUTING TRIGGERS: Rhetorical Block, Discourse Parsing, Graph Traversal, Structural Vertex""",
    "DiscourseTreeManifest": """AGENT INSTRUCTION: A verifiable Directed Acyclic Graph (DAG) mapping the hierarchical geometry of human discourse. Deprecates flat-sequence extraction to solve rhetorical flattening.

    CAUSAL AFFORDANCE: Instructs the orchestrator to enforce a strict Directed Acyclic Graph (DAG) for discourse representation.

    EPISTEMIC BOUNDS: Bounded to strict JSON schema validation constraints defined in the manifest.

    MCP ROUTING TRIGGERS: Discourse Geometry, Rhetorical Flattening, Directed Acyclic Graph, Hierarchical Extraction""",
    "FederatedSecurityMacroManifest": """AGENT INSTRUCTION: Simplifies the creation of a secure federated network link across a Zero-Trust boundary.

    CAUSAL AFFORDANCE: Physically authorizes the orchestrator to forge a secure federated network link across a Zero-Trust boundary.

    EPISTEMIC BOUNDS: Bounded to strict JSON schema validation constraints defined in the manifest.

    MCP ROUTING TRIGGERS: Federated Security, Zero-Trust Boundary, Network Link, Macro Manifest""",
    "CognitiveSwarmDeploymentManifest": """AGENT INSTRUCTION: Simplifies bootstrapping a multi-agent routing topology.

    CAUSAL AFFORDANCE: Physically authorizes the orchestrator to deploy a multi-agent routing topology.

    EPISTEMIC BOUNDS: Bounded to strict JSON schema validation constraints defined in the manifest.

    MCP ROUTING TRIGGERS: Cognitive Swarm, Agent Deployment, Routing Topology, Bootstrapping Macro""",
    "NeurosymbolicVerificationTopologyManifest": """AGENT INSTRUCTION: A Zero-Cost Macro abstraction enforcing a strict Bipartite Graph for Proposer-Verifier loops. Isolates connectionist generation from symbolic validation and bounds cyclic computation.

    CAUSAL AFFORDANCE: Instructs the orchestrator to enforce a strict Bipartite Graph for Proposer-Verifier loops.

    EPISTEMIC BOUNDS: Bounded to strict JSON schema validation constraints defined in the manifest.

    MCP ROUTING TRIGGERS: Proposer-Verifier Loop, Bipartite Graph, Symbolic Validation, Cyclic Computation""",
    "PostCoordinatedSemanticState": """AGENT INSTRUCTION: The definitive output of a successful latent manifold alignment. Represents a dynamic assembly of a standardized entity (Base Concept + Contextual Modifiers) to achieve infinite semantic specificity without requiring an infinitely large pre-coordinated vocabulary.

    CAUSAL AFFORDANCE: Physically authorizes the orchestrator to assemble a standardized entity with contextual modifiers.

    EPISTEMIC BOUNDS: Bounded to strict JSON schema validation constraints defined in the manifest.

    MCP ROUTING TRIGGERS: Post-Coordinated Semantics, Latent Manifold Alignment, Semantic Specificity, Entity Assembly""",
    "EmpiricalStatisticalProfile": """AGENT INSTRUCTION: An explicit mathematical boundary extracted from text that limits the certainty or scope of a proposition. Physically prevents agents from performing epistemic smoothing.

    CAUSAL AFFORDANCE: Physically authorizes the orchestrator to impose explicit mathematical boundaries on propositions.

    EPISTEMIC BOUNDS: Bounded to strict JSON schema validation constraints defined in the manifest.

    MCP ROUTING TRIGGERS: Empirical Statistics, Mathematical Boundary, Epistemic Smoothing, Proposition Certainty""",
    "AtomicPropositionState": """AGENT INSTRUCTION: A declarative, frozen snapshot of a standalone, verifiable statement extracted from unstructured discourse. Transmutes probabilistic 'bags-of-words' into a discrete, traversable node within the Labeled Property Graph (LPG).

    CAUSAL AFFORDANCE: Instructs the orchestrator to persist a verifiable statement as a discrete node within the LPG.

    EPISTEMIC BOUNDS: Bounded to strict JSON schema validation constraints defined in the manifest.

    MCP ROUTING TRIGGERS: Atomic Proposition, Discourse Extraction, Labeled Property Graph, Verifiable Statement""",
    "DempsterShaferBeliefState": """AGENT INSTRUCTION: Replaces monolithic probability floats with a composite tri-vector. Independently measures lexical matching, latent semantic distance, and topological graph integrity to allow the orchestrator to compute epistemic conflict and execute evidence discounting.

    CAUSAL AFFORDANCE: Instructs the orchestrator to independently measure lexical matching, latent semantic distance, and topological graph integrity.

    EPISTEMIC BOUNDS: Bounded to strict JSON schema validation constraints defined in the manifest.

    MCP ROUTING TRIGGERS: Dempster-Shafer, Epistemic Conflict, Evidence Discounting, Composite Tri-Vector""",
    "OntologicalReificationReceipt": """AGENT INSTRUCTION: An append-only, cryptographically frozen coordinate verifying the integrity of a generalized bimodal semantic transformation. Commits the transformation mechanism to the Epistemic Ledger, physically separating explicit empirical facts from machine-inferred hypotheses to eliminate traceability collapse.

    CAUSAL AFFORDANCE: Physically authorizes the orchestrator to commit the transformation mechanism to the Epistemic Ledger.

    EPISTEMIC BOUNDS: Bounded to strict JSON schema validation constraints defined in the manifest.

    MCP ROUTING TRIGGERS: Ontological Reification, Bimodal Semantic Transformation, Epistemic Ledger, Traceability Collapse""",
    "SemanticRelationalVectorState": """AGENT INSTRUCTION: Represents the untyped payload injection zone for harmonized structured telemetry. 

    CAUSAL AFFORDANCE: Permits specialized downstream agents to project and decode specific industry payloads (e.g., OMOP CDM, FIX protocol) while preserving universal mathematical traversal of the graph. 
    
    EPISTEMIC BOUNDS: The payload_injection_zone is routed through the volumetric hardware guillotine.

    MCP ROUTING TRIGGERS: Semantic Relational Record, Payload Injection, Hardware Guillotine, Structured Telemetry""",
}

file_path = Path(r"c:\files\git\github\coreason-ai\coreason-manifest\src\coreason_manifest\spec\ontology.py")

with open(file_path, encoding="utf-8") as f:
    content = f.read()

tree = ast.parse(content)
lines = content.splitlines(keepends=True)

for node in sorted(tree.body, key=lambda n: getattr(n, "lineno", -1), reverse=True):
    if isinstance(node, ast.ClassDef) and node.name in NEW_DOCSTRINGS and ast.get_docstring(node):
        docstr_node = node.body[0]
        start_line = docstr_node.lineno - 1
        end_line = docstr_node.end_lineno

        # Create proper docstring representation
        new_doc = '    """\n    ' + NEW_DOCSTRINGS[node.name].replace("\n", "\n    ") + '\n    """\n'

        lines[start_line:end_line] = [new_doc]

with open(file_path, "w", encoding="utf-8") as f:
    f.write("".join(lines))

print("Docstrings injected successfully.")
