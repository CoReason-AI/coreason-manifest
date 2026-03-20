## 2026-05-15 - [SSRF Bypass Mitigation]
**Vulnerability:** Magic DNS services (e.g., xip.io, nip.io, vcap.me, localtest.me) resolve to internal/loopback IPs.
**Learning:** The application possessed a blocklist for Bogon domains and IP spaces, but `xip.io`, `vcap.me`, and `localtest.me` were omitted from the explicit string checks on the HTTP URI hostnames. This allowed an attacker to bypass the initial string-based topology filter if they crafted a URL like `http://127.0.0.1.xip.io`.
**Prevention:** Add `xip.io`, `vcap.me`, and `localtest.me` (both exact and `.endswith()` suffix checks) to the host quarantine blocklist to enforce zero-trust bounds against SSRF.
