## 2025-04-14 - Fix AST Evaluation Blacklist Bypass
**Vulnerability:** Found a critical vulnerability in `EpistemicZeroTrustContract.validate_ast_safety` where a blacklist approach was used to prevent Arbitrary Code Execution (ACE) during AST evaluation. Blacklists are easily bypassed via dunder methods (e.g., `().__class__.__bases__[0].__subclasses__()`) or via `ast.Pow` for CPU exhaustion (DoS).
**Learning:** AST evaluation in Python is dangerous even when trying to restrict execution. A default-deny (whitelist) approach must be used.
**Prevention:** Switch to a strict whitelist of safe AST node types, explicitly reject `ast.Pow`, and ensure any allowed function calls (`ast.Call`) are restricted to a safe, hardcoded list of basic names (`len`, `sum`, etc.).
