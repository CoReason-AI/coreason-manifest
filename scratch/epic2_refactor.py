# Copyright (c) 2026 CoReason, Inc
#
# This software is proprietary and dual-licensed
# Licensed under the Prosperity Public License 3.0 (the "License")
# A copy of the license is available at <https://prosperitylicense.com/versions/3.0.0>
# For details, see the LICENSE file
# Commercial use beyond a 30-day trial requires a separate license
#
# Source Code: <https://github.com/CoReason-AI/coreason-manifest>

import re

with open("src/coreason_manifest/spec/ontology.py", encoding="utf-8") as f:
    content = f.read()

# ============================================================
# ACTION 1: Delete ephemeral class/type definitions
# ============================================================

# 1a. Delete class ComputeTierProfile(StrEnum): ... (lines 250-262 area)
content = re.sub(
    r'\nclass ComputeTierProfile\(StrEnum\):.*?ORACLE = "ORACLE"\n',
    "\n",
    content,
    flags=re.DOTALL,
)

# 1b. Delete class AcceleratorProfile(StrEnum): ... (lines 265-278 area)
content = re.sub(
    r'\nclass AcceleratorProfile\(StrEnum\):.*?CUDA_FP32 = "CUDA_FP32"\n',
    "\n",
    content,
    flags=re.DOTALL,
)

# 1c. Delete class SubstrateDialectProfile(StrEnum): ...
content = re.sub(
    r'\nclass SubstrateDialectProfile\(StrEnum\):.*?ZERO_KNOWLEDGE_PROVER = "ZERO_KNOWLEDGE_PROVER"\n',
    "\n",
    content,
    flags=re.DOTALL,
)

# 1d. Delete type AttestationMechanismProfile = Literal[...]
content = re.sub(
    r'type AttestationMechanismProfile = Literal\["fido2_webauthn", "zk_snark_groth16", "pqc_ml_dsa"\]\n',
    "",
    content,
)

# ============================================================
# ACTION 2: Replace field types with URN pattern
# ============================================================

# 2.1 SpatialHardwareProfile - compute_tier
content = re.sub(
    r"    compute_tier: ComputeTierProfile = Field\(\n"
    r"        default=ComputeTierProfile\.KINETIC,\n"
    r'        description="The discrete architectural boundary of the node \(KINETIC for edge/consumer, ORACLE for datacenter\)\."\,\n'
    r"    \)",
    '    compute_tier: Annotated[str, StringConstraints(pattern=r"^urn:coreason:.*$")] = Field(\n'
    '        description="The discrete architectural boundary of the node."\n'
    "    )",
    content,
)

# 2.1 SpatialHardwareProfile - accelerator_type
content = re.sub(
    r"    accelerator_type: AcceleratorProfile = Field\(\n"
    r"        default=AcceleratorProfile\.BF16_TENSOR,\n"
    r'        description="The rigid silicon precision format required to execute this node\'s neural circuits\."\,\n'
    r"    \)",
    '    accelerator_type: Annotated[str, StringConstraints(pattern=r"^urn:coreason:.*$")] = Field(\n'
    '        description="The rigid silicon precision format required to execute this node\'s neural circuits."\n'
    "    )",
    content,
)

# 2.2 ExecutionSubstrateProfile - dialect
content = content.replace(
    '    dialect: SubstrateDialectProfile = Field(description="The discrete open-source engine identifier.")',
    '    dialect: Annotated[str, StringConstraints(pattern=r"^urn:coreason:.*$")] = Field(description="The discrete open-source engine URN identifier.")',
)

# 2.3 CognitiveHumanNodeProfile - required_attestation
content = content.replace(
    "    required_attestation: AttestationMechanismProfile = Field(\n"
    '        description="The mandatory cryptographic attestation required to verify the human operator\'s identity."\n'
    "    )",
    '    required_attestation: Annotated[str, StringConstraints(pattern=r"^urn:coreason:.*$")] = Field(\n'
    '        description="The mandatory cryptographic attestation URN required to verify the human operator\'s identity."\n'
    "    )",
)

# 2.4 WetwareAttestationContract - mechanism
content = content.replace(
    "    mechanism: AttestationMechanismProfile = Field(\n"
    '        ..., description="The SOTA cryptographic mechanism used to generate the proof."\n'
    "    )",
    '    mechanism: Annotated[str, StringConstraints(pattern=r"^urn:coreason:.*$")] = Field(\n'
    '        ..., description="The SOTA cryptographic mechanism URN used to generate the proof."\n'
    "    )",
)

# 2.5 EnvironmentalSpoofingProfile - tls_cipher_permutation
content = content.replace(
    '    tls_cipher_permutation: Literal["chrome_windows", "safari_macos", "firefox_macos", "android_webview"] = Field(\n'
    '        default="chrome_windows",\n'
    '        description="The JA3/JA4 TLS Client Hello fingerprint to project during handshake emulation.",\n'
    "    )",
    '    tls_cipher_permutation: Annotated[str, StringConstraints(pattern=r"^urn:coreason:.*$")] | None = Field(\n'
    '        default=None, description="The JA3/JA4 TLS Client Hello fingerprint URN to project during handshake emulation."\n'
    "    )",
)

# ============================================================
# ACTION 3: Clean up Macro Manifest Defaults
# ============================================================
content = content.replace(
    'required_attestation="fido2_webauthn"',
    'required_attestation="urn:coreason:attestation:fido2_webauthn"',
)

# ============================================================
# Update docstrings that reference deleted types
# ============================================================
content = content.replace(
    "The literal enumerations ComputeTierProfile and AcceleratorProfile mathematically prevent the hallucination of non-existent silicon.",
    "The URN-patterned compute_tier and accelerator_type fields provide extensible silicon identification without ephemeral enumeration coupling.",
)

content = content.replace(
    "(AttestationMechanismProfile), authorizing",
    "(URN-patterned attestation mechanism), authorizing",
)

with open("src/coreason_manifest/spec/ontology.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Epic 2 refactoring complete!")
