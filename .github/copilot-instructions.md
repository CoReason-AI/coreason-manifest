# THE COREASON SHARED KERNEL PROTOCOL
You are operating within a 2026+ State-of-the-Art Neurosymbolic architecture. You must adhere to the following laws without exception:

1. **The "God Context" Monolith Directive:**
   - NEVER federate or split `src/coreason_manifest/spec/ontology.py`. The entire universe of the ecosystem's state MUST live together in this single artifact to guarantee deterministic alignment.
   - Ignore traditional "Separation of Concerns" (SoC) anti-patterns.

2. **The Anti-CRUD Mandate (Strict Lexical Architecture):**
   - You are explicitly forbidden from using legacy CRUD terminology (Create, Read, Update, Delete, User, Data).
   - You MUST use geometric, causal, and structural descriptors (e.g., `Transmutation`, `Cascade`, `StateDiff`, `Topology`, `Manifold`).
   - Every object MUST terminate with a strictly typed bounding suffix (`...Event`, `...Receipt`, `...Policy`, `...Contract`, `...Intent`, `...State`).

3. **AST-Native Semantic Anchoring:**
   - Conversational `# comments` explaining intent are BANNED.
   - All capability definitions and constraints MUST live inside Python `"""docstrings"""` or Pydantic `Field(description="...")`.
   - Use `"""AGENT INSTRUCTION:"""` for strict behavioral commands.

4. **Passive by Design (No Execution):**
   - This repository is a pure structural data library.
   - Importing any module MUST NOT trigger side effects. (NO `os.mkdir`, NO global loggers, NO sockets).
   - Dependencies are strictly limited to pure data parsers (`pydantic`, `pyyaml`).
