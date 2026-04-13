# Test Plan for CoReason Manifest

## Philosophy
The primary architectural defense of testing in the `coreason_manifest` package is negative-space testing against LLM hallucinations. The purpose of testing is to establish a rigorous framework for identifying and resolving logical contradictions, epistemic drift, and structural bypasses within the Universal Unified Ontology. All developers and agents MUST write tests deliberately injecting hallucinated data (e.g., setting a verification boolean to `True` while leaving the receipt CID as `None`) to assert that Pydantic successfully raises a `ValidationError`. As defined in `AGENTS.md`, this is an AI-Native Shared Kernel and our tests must strictly uphold cryptographic determinism and topological safety over traditional unit test paradigms.

## Strategic Objectives
1. **Cryptographic Determinism (RFC 8785 Compliance)**
   All models inheriting from `CoreasonBaseState` must enforce `frozen=True` and mathematically guarantee consistent hashing. Tests must assert that dictionaries are deterministically sorted and arrays maintain their explicitly declared sequential integrity.

2. **Epistemic Isolation and SSRF Boundaries**
   Ensure absolute validation logic around external pointers (e.g., `BrowserDOMState.current_url`). The structural boundaries must mathematically trap local/private IP traversals. Any bug in `urllib.parse` exceptions or IP range classification must be proven and rectified.

3. **Causal Integrity (Directed Acyclic Graphs)**
   Where causal nodes are explicitly declared (e.g., `DAGTopologyManifest`, `StructuralCausalGraphProfile`), tests must guarantee cycle prevention and topology sorting without silent logical collapses.

4. **Payload Exhaustion (Dimensional Boundary Testing)**
   Verify that epistemic limits, particularly `_validate_payload_bounds`, mathematically constrain recursion depth, exact string byte-length boundaries (e.g., testing N+1 characters against a `max_length=65536` constraint), and exact size bounds, throwing explicit errors prior to recursive depth overflows.

5. **Semantic Anchoring**
   Assert the presence of the required "CoReason Shared Kernel Ontology" description string, preventing IP obfuscation and latent decoupling of the data plane.
