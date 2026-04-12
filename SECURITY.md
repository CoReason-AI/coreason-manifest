# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| Latest  | :white_check_mark: |
| < 1.0   | :x:                |

We only provide security patches for the **latest released version** on PyPI.

## Reporting a Vulnerability

**Please do NOT open a public GitHub Issue for security vulnerabilities.**

If you discover a security vulnerability in `coreason_manifest`, please report it responsibly via one of the following channels:

- **Email:** [security@coreason.ai](mailto:security@coreason.ai)
- **Alternative Contact:** [gowtham.rao@coreason.ai](mailto:gowtham.rao@coreason.ai)

### What to Include

To help us triage and respond quickly, please include:

1. **Description** of the vulnerability and its potential impact.
2. **Steps to reproduce** or a proof-of-concept.
3. **Affected versions** (if known).
4. **Suggested fix** (optional, but appreciated).

### Response Timeline

| Stage                    | Target SLA       |
| ------------------------ | ---------------- |
| Acknowledgment           | Within 48 hours  |
| Initial Triage           | Within 5 days    |
| Fix Development & Review | Within 30 days   |
| Public Disclosure         | After fix is released |

We follow [coordinated vulnerability disclosure](https://en.wikipedia.org/wiki/Coordinated_vulnerability_disclosure). We will work with you to understand the issue and coordinate a fix before any public disclosure.

### Recognition

We appreciate the efforts of security researchers. With your permission, we will credit you in the release notes and `NOTICE` file for responsibly disclosed vulnerabilities.

## Security Architecture

This repository is a **pure data library** (Hollow Data Plane) with no runtime execution surface. Key security properties:

- **No network sockets, no file writing, no global state** — importing any module triggers zero side effects.
- **Frozen immutable models** — all Pydantic schemas enforce `frozen=True`.
- **Cryptographic determinism** — canonical hashing via RFC 8785 guarantees reproducible builds.
- **SLSA Level 3 provenance** — every PyPI release includes build attestations via [Sigstore](https://sigstore.dev).
- **SBOM generation** — every release ships an SPDX Software Bill of Materials.
- **Automated dependency auditing** — `pip-audit`, `osv-scanner`, and CodeQL run on every PR and on a weekly schedule.

## Supply Chain Integrity

All releases are:

- Built deterministically and verified via reproducible build checks in CI.
- Signed with [Sigstore](https://sigstore.dev) for artifact provenance.
- Published to PyPI via OIDC Trusted Publishing (no static API tokens).
- Accompanied by SLSA Level 3 provenance attestations.
