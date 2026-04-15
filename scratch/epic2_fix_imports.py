# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>


files_to_fix = {
    # Remove AttestationMechanismProfile from __init__.py exports
    "src/coreason_manifest/__init__.py": [
        ("    AttestationMechanismProfile,\n", ""),
        ('    "AttestationMechanismProfile",\n', ""),
    ],
    "src/coreason_manifest/spec/__init__.py": [
        ("    AttestationMechanismProfile,\n", ""),
        ('    "AttestationMechanismProfile",\n', ""),
    ],
    # Fix test_ontology_validators.py
    "tests/contracts/test_ontology_validators.py": [
        ("    ComputeTierProfile,\n", ""),
        (
            "    assert agent.hardware.compute_tier == ComputeTierProfile.KINETIC\n",
            '    assert agent.hardware.compute_tier == "urn:coreason:compute:kinetic"\n',
        ),
    ],
    # Fix test_substrate_hydration.py
    "tests/test_substrate_hydration.py": [
        ("    SubstrateDialectProfile,\n", ""),
        (
            "        dialect=SubstrateDialectProfile.SYMBOLIC_AI_DBC,",
            '        dialect="urn:coreason:substrate:symbolic_ai_dbc",',
        ),
        (
            "        dialect=SubstrateDialectProfile.NATIVE_PYTHON,",
            '        dialect="urn:coreason:substrate:native_python",',
        ),
    ],
}

for filepath, replacements in files_to_fix.items():
    with open(filepath, encoding="utf-8") as f:
        content = f.read()
    for old, new in replacements:
        if old in content:
            content = content.replace(old, new)
            print(f"  Fixed: {filepath}: removed/replaced '{old.strip()[:60]}...'")
        else:
            print(f"  WARNING: Not found in {filepath}: '{old.strip()[:60]}...'")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

print("\nImport/reference fixes complete!")
