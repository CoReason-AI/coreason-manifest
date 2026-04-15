# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

files = {
    "tests/test_intents_and_topologies.py": [
        ('"fido2_webauthn"', '"urn:coreason:attestation:fido2_webauthn"'),
    ],
    "tests/contracts/test_coverage_gaps.py": [
        ('mechanism="fido2_webauthn"', 'mechanism="urn:coreason:attestation:fido2_webauthn"'),
    ],
    "tests/test_agentic_forge.py": [
        ('"fido2_webauthn"', '"urn:coreason:attestation:fido2_webauthn"'),
    ],
}
for fp, reps in files.items():
    try:
        with open(fp, encoding="utf-8") as f:
            c = f.read()
        for old, new in reps:
            c = c.replace(old, new)
        with open(fp, "w", encoding="utf-8") as f:
            f.write(c)
        print(f"Fixed {fp}")
    except FileNotFoundError:
        print(f"Skipped {fp} (not found)")
