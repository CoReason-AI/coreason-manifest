## 2026-05-15 - [SSRF Bypass Mitigation]
**Vulnerability:** Magic DNS services (e.g., xip.io, nip.io, vcap.me, localtest.me) resolve to internal/loopback IPs.
**Learning:** The application possessed a blocklist for Bogon domains and IP spaces, but `xip.io`, `vcap.me`, and `localtest.me` were omitted from the explicit string checks on the HTTP URI hostnames. This allowed an attacker to bypass the initial string-based topology filter if they crafted a URL like `http://127.0.0.1.xip.io`.
**Prevention:** Add `xip.io`, `vcap.me`, and `localtest.me` (both exact and `.endswith()` suffix checks) to the host quarantine blocklist to enforce zero-trust bounds against SSRF.
## 2024-05-24 - [Critical] Fix Arbitrary Code Execution bypass in DynamicLayoutManifest
**Vulnerability:** A vulnerability in `DynamicLayoutManifest.validate_tstring` allowed Arbitrary Code Execution (ACE) via template string injection. `ast.parse(v, mode="exec")` would throw a `SyntaxError` for strings containing braces (like `}os.system('id'){`), causing the validation to silently `pass`. If the string was later evaluated as an f-string, the malicious payload would execute.
**Learning:** `ast.parse` in `exec` mode is insufficient for validating template strings that will be interpolated later, as syntax errors can hide malicious embedded expressions.
**Prevention:** Always validate template strings by also wrapping them in an f-string structure (e.g., `f"f'''{v_escaped}'''"`) and parsing with `mode="eval"` to ensure embedded expressions are traversed and validated by the AST visitor.
