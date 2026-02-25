# Interoperability: Cryptographic Integrity

In high-stakes environments (finance, healthcare, defense), it is not enough to know *what* an agent did; you must be able to **prove** it.

`coreason-manifest` includes a dedicated integrity layer (`src/coreason_manifest/utils/integrity.py`) that uses cryptographic hashing to guarantee the structural validity and execution lineage of an agent.

---

## `CanonicalHashingStrategy`

To hash a JSON object (like a Manifest or an Execution Record) reliably, you must ensure that the JSON serialization is **deterministic**. A standard `json.dumps()` is insufficient because key order is undefined, and floating-point representation varies across platforms.

The `CanonicalHashingStrategy` implements an approximation of **RFC 8785 (JSON Canonicalization Scheme)**:
1.  **Key Sorting**: Dictionary keys are always sorted lexicographically.
2.  **Whitespace Removal**: No spaces after separators (`var:val`, not `var: val`).
3.  **Strict Float Handling**: Rejects `NaN` and `Infinity`.
4.  **UTF-8 Enforcement**: Ensures consistent byte representation.

This guarantees that `hash(manifest_on_linux) == hash(manifest_on_windows)`.

---

## Merkle DAG Proofs

Execution integrity is tracked using a **Merkle Directed Acyclic Graph (DAG)**.

As each node executes:
1.  Its inputs, outputs, and configuration are gathered into a payload.
2.  The **hashes of its parent nodes** (`parent_hashes`) are included in that payload.
3.  The entire payload is hashed to generate the node's `execution_hash`.

### Verification
This chains every step of the agent's reasoning to the steps before it. If a malicious actor tries to tamper with the output of "Step 2" in a trace, the hash of "Step 3" (which includes Step 2's hash) will no longer match.

The `verify_merkle_proof` utility allows auditors to cryptographically verify a trace:
```python
is_valid = verify_merkle_proof(
    trace=full_execution_trace,
    trusted_root_hash=known_start_hash
)
```

---

## Privacy & Redaction

Integrity must coexist with privacy. The `PrivacySentinel` schema (documented in Governance) interacts strictly with the integrity layer.

**The Rule:** PII Redaction happens **before** hashing.
*   If a tool output contains a credit card number, the `Safety` policy redacts it to `[REDACTED]`.
*   The *redacted* string is what gets hashed.
*   This ensures that the public audit log allows verification of the *process* without leaking sensitive *data*.
