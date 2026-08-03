## 2025-05-24 - Fix SSRF Bypasses via Obfuscated IP Formats
**Vulnerability:** The application was vulnerable to SSRF bypasses via obfuscated IP formats (e.g., octal `0177.0.0.1`, hex `0x7f000001`, dword `2130706433`, URL-encoded `%31%32%37%2e%30%2e%30%2e%31`).
**Learning:** `ipaddress.ip_address` strictly parses standard IP formats and rejects obfuscated ones, while underlying system libc networking stacks accept them. This mismatch allows bypasses.
**Prevention:** Use `urllib.parse.unquote` to decode the hostname, and use `socket.inet_aton` as a fallback parser to normalize non-standard IP formats before enforcing SSRF bounds.
