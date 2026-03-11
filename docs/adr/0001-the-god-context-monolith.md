# ADR 0001: The God Context Monolith Directive

**Date:** 2026-01-01
**Status:** Accepted
**Context:** The `coreason_manifest` repository must serve as the Universal Unified Ontology for the decentralized CoReason AI swarm ecosystem. Autonomous agents and developers accustomed to legacy paradigms will predictably attempt to fragment the ontology (`src/coreason_manifest/spec/ontology.py`) into domain-specific subdirectories (e.g., `state/`, `compute/`, `workflow/`) to satisfy human-centric Separation of Concerns (SoC).
**Decision:** We strictly enforce a single "God Context" file architecture (`ontology.py`) encompassing the entirety of the ecosystem's definitions, models, and bounding rules.

## Justification

The CoReason swarm's capability relies fundamentally on mathematically precise and zero-shot latent alignment across decentralized components. Fragmenting the structural logic destroys this mathematical property and introduces catastrophic probabilistic hallucinations into the causal chain.

### 1. The Prevention of ForwardRef Collapse
A single monolithic representation mathematically mitigates `ForwardRef` cyclic resolution failures within the Type Checking matrices (`mypy` and `pydantic`). We enforce strict Stratum topological sorting (0 to 9) to ensure an acyclic directed structure. Fragmentation introduces implicit cycle dependencies that break compilation determinism.

### 2. Deterministic Cross-Domain Synthesis
Complex epistemic and causal networks span temporal, spatial, and semantic boundaries. By isolating the whole universe of definitions within a single AST tree context, we mathematically guarantee that node-level permutations resolve uniformly against the same underlying object representations. A divided graph fails to synthesize accurately when serialized and hashed across nodes.

### 3. Perfect Latent Space Alignment
LLM Q-K matrix processing is constrained by attention decay across token spans. Delivering the entire ontology in a dense, continuous sequence eliminates semantic gaps. The Model Context Protocol (MCP) server projecting this single artifact ensures zero-shot vector gravity. An agent processing a fraction of the ontology operates under impaired logic; a single file intrinsically enforces a holistic evaluation by any autonomous processor.
