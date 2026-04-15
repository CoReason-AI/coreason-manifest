# Causal Lexicon & Structural Glossary

**SYSTEM DIRECTIVE: STRICT CAUSAL VOCABULARY OVER TABULAR LOGIC ENFORCED**

This repository strictly implements Judea Pearl's Structural Causal Models. Legacy tabular (CRUD) language causes semantic drift, probabilistically flattens softmax distributions, and hallucinates inaccurate temporal mapping within the Q-K matrices. You MUST replace human-centric vocabulary with their Neurosymbolic equivalents.

## The Anti-CRUD Matrix

| Legacy Concept | Permissible Neurosymbolic Equivalent | Categorical Rationale / Definition |
| :--- | :--- | :--- |
| **Create** | `Transmutation` / `GenesisEvent` | Mathematical initialization mapped into topological reality; frozen and append-only. |
| **Read** | `ObservationEvent` / `OntologicalProjection` | A read-only extraction of the underlying Merkle-DAG state; strictly non-kinetic. |
| **Update** | `StateMutationIntent` / `CausalEvolution` | Defines a test-time logic vector seeking transition to an alternative valid N-dimensional coordinate. |
| **Delete** | `DefeasibleCascade` / `QuarantineOrder` | The cryptographic invalidation of a state node. Downstream vectors are mathematically severed, prohibiting execution via temporal negation. |
| **User** | `CognitiveEntity` / `FederatedPrincipal` | Eliminates human-centric semantic polysemy. Establishes a concrete spatial boundary mapping for authentication endpoints. |
| **Data** | `LatentCoordinate` / `StructuralToken` | Replaces ambiguous semantic clusters with exact multidimensional mapping vectors. |
| **List** | `TopologicalSequence` / `UnorderedSetManifest` | Clarifies the exact sorting (RFC 8785) behavior mandated for the array's underlying cryptographic hash integrity. |
| **Log** | `EpistemicTelemetryEvent` / `ObservationEvent` | Passive and deterministic record generation reflecting systemic state evolution, stripped of imperative execution. |
| **ID** | `ContentIdentifier (CID)` / `MerkleRoot` | Enforces cryptographic immutability rather than sequentially guessed database identities. |


## Developer Bridge — Ontology ↔ Standard Terms

> **For developers new to this codebase:** The table below maps CoReason's ontological terminology to standard software engineering concepts you likely already know.

### Core Types

| CoReason Term | Standard Equivalent | When You'd Use It |
| :--- | :--- | :--- |
| `CoreasonBaseState` | Immutable Pydantic `BaseModel` with `frozen=True` | Base class for all data structures in the ontology |
| `WorkflowManifest` | Workflow definition / DAG config (like Airflow, Prefect) | Defining a complete multi-agent execution plan |
| `DAGTopologyManifest` | Directed Acyclic Graph of connected nodes | Wiring agents together with parent→child edges |
| `CognitiveAgentNodeProfile` | An AI agent's configuration object | Configuring an LLM agent's capabilities and tier |
| `StateDifferentialManifest` | JSON Patch document (RFC 6902) | Describing incremental state changes |
| `EpistemicLedgerState` | Append-only event log / audit trail | Event-sourced history of all system observations |
| `EpistemicLean4Premise` | Lean 4 Theorem Prover payload | Constructive mathematical proof and universal invariants verification |
| `FalsificationContract` | Constraint Satisfaction setup | Finding a counter-model to falsify a hypothesis using ASP / Clingo |
| `PrologDeductionReceipt` | Logic programming proof artifact | Exact subgraph isomorphism and hierarchical knowledge base verification |

### Vectors & Embeddings

| CoReason Term | Standard Equivalent | When You'd Use It |
| :--- | :--- | :--- |
| `VectorEmbeddingState` | A vector embedding (what you'd store in Pinecone, Weaviate, etc.) | Representing text/image embeddings for similarity search |
| `OntologicalAlignmentPolicy` | Similarity threshold configuration | Setting minimum cosine similarity for RAG retrieval |
| `calculate_latent_alignment()` | Cosine similarity with contract enforcement | Computing similarity between two embeddings |
| `TamperFaultEvent` | Exception: similarity below threshold | Raised when semantic drift/misalignment is detected |

### Validation & Error Handling

| CoReason Term | Standard Equivalent | When You'd Use It |
| :--- | :--- | :--- |
| `verify_manifold_bounds()` | `Model.model_validate_json()` against a schema registry | Validating LLM output against a known schema |
| `synthesize_remediation_intent()` | Structured error → machine-readable fix instructions | Converting `ValidationError` to an LLM-parseable remediation |
| `System2RemediationIntent` | Structured error report for self-correction | Telling an agent exactly what fields are wrong and why |

### Hashing & Integrity

| CoReason Term | Standard Equivalent | When You'd Use It |
| :--- | :--- | :--- |
| `compute_topology_hash()` | `hashlib.sha256(canonical_json)` | Computing a deterministic fingerprint of a topology |
| `model_dump_canonical()` | RFC 8785 canonical JSON serialization | Getting a deterministic byte representation for hashing |
| `TopologyHashReceipt` | SHA-256 hex digest string | A typed alias for `^[a-f0-9]{64}$` strings |
| `verify_merkle_proof()` | Merkle DAG integrity verification | Verifying an execution trace hasn't been tampered with |
| `Topological Exemption` | Arrays bypass RFC 8785 canonical alphabetical sorting | A structural schema rule that explicitly bypasses canonical sorting on specific arrays (like ASP `answer_sets` or Prolog `variable_bindings`) to preserve the mathematical chronological sequence of the C-backed solver output. |
| `Hollow Data Plane` | Decentralized state architecture | The decentralized schema registry that enforces Proof-Carrying Data (PCD), physically separating probabilistic LLM generation from deterministic C-backed verification. |

### Semantic ETL & Knowledge Graphs

| CoReason Term | Standard Equivalent | When You'd Use It |
| :--- | :--- | :--- |
| `SemanticRelationalVectorState` | A row/record with a domain-specific payload | Representing structured telemetry with a flexible payload zone |
| `SemanticNodeState` | A node in a knowledge graph | A labeled vertex in a semantic graph with properties |
| `SemanticEdgeState` | An edge/relationship in a knowledge graph | A typed connection between two semantic nodes |
| `EpistemicTransmutationTask` | A data transformation job | A task specifying modality conversion (e.g., text → table) |

### Schema Suffixes Cheat Sheet

| Suffix | Think of it as... | Mutability |
| :--- | :--- | :--- |
| `...Event` / `...Receipt` | An immutable log entry / audit record | Append-only, never mutated |
| `...Intent` / `...Task` | A request / job to be executed | Created, then resolved |
| `...Policy` / `...Contract` / `...SLA` | A configuration rule / threshold | Read-only constraint |
| `...State` / `...Snapshot` / `...Manifest` | A frozen data object | Immutable after creation |
| `...Profile` | A type enum or config struct | Describes shape/capability |
