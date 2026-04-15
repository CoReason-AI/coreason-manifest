import re

with open("src/coreason_manifest/spec/ontology.py", encoding="utf-8") as f:
    content = f.read()

# Action 1: Broad Replacement of Arbitrary le= Bounds
replacements = {
    "le=86400000": "le=18446744073709551615",
    "le=86400": "le=18446744073709551615",
    "le=3600": "le=18446744073709551615",
    "le=100000000000": "le=18446744073709551615",
    "le=1000000000.0": "le=18446744073709551615.0",
    "le=1000000000": "le=18446744073709551615",
    "le=10000.0": "le=18446744073709551615.0",
    "le=65536": "le=18446744073709551615",
}

for k, v in replacements.items():
    content = content.replace(k, v)

# Action 2: Update Hardcoded Validator Clamps
content = content.replace("min(val, 86400000)", "min(val, 18446744073709551615)")
content = content.replace("min(val, 1000000000)", "min(val, 18446744073709551615)")
content = content.replace("min(val_float, 10000.0)", "min(val_float, 18446744073709551615.0)")
content = content.replace(
    'min(values.get("escrow_locked_magnitude", 0), 1000000000)',
    'min(values.get("escrow_locked_magnitude", 0), 18446744073709551615)',
)

content = content.replace(
    'min(values.get("max_budget", 0), 1000000000)', 'min(values.get("max_budget", 0), 18446744073709551615)'
)
content = content.replace(
    'min(values["input_tokens"], 1000000000)', 'min(values["input_tokens"], 18446744073709551615)'
)
content = content.replace(
    'min(values["output_tokens"], 1000000000)', 'min(values["output_tokens"], 18446744073709551615)'
)
content = content.replace(
    'min(values["burn_magnitude"], 1000000000)', 'min(values["burn_magnitude"], 18446744073709551615)'
)
content = content.replace("min(mc_int, 1000000000)", "min(mc_int, 18446744073709551615)")

# Action 3: Purge the enforce_deployment_physics Validator
validator_code = """
    @model_validator(mode="after")
    def enforce_deployment_physics(self) -> Self:
        \"\"\"
        AGENT INSTRUCTION: The Formal Verification Matrix.
        Enforces Thermodynamic, Sovereign Execution, and Network Topology paradox traps.
        \"\"\"

        if self.hardware.compute_tier == ComputeTierProfile.KINETIC and self.hardware.min_vram_gb > 24.0:
            raise ValueError(
                "Thermodynamic Constraint Violated: KINETIC tier cannot exceed 24.0 GB VRAM. Escalate to ORACLE tier."
            )

        if self.security.epistemic_security == EpistemicSecurityPolicy.CONFIDENTIAL and not set(
            self.hardware.provider_whitelist
        ).issubset(_TRUSTED_ENVIRONMENTS):
            invalid_targets = set(self.hardware.provider_whitelist) - _TRUSTED_ENVIRONMENTS
            raise ValueError(
                f"Sovereign Execution Violated: CONFIDENTIAL workloads cannot be routed to "
                f"untrusted peer-to-peer providers. Invalid targets found: {invalid_targets}"
            )

        if self.security.egress_obfuscation and not self.security.network_isolation:
            raise ValueError(
                "Topology Routing Violated: Egress Mixnet obfuscation mathematically requires strict Network Isolation to be True."
            )

        return self
"""
# The exact indentation matters! Wait, ruff might have formatted it, let's use regex to find and remove it.
# It starts with \s*@model_validator.*enforce_deployment_physics.*return self
regex_validator = re.compile(
    r'\s+@model_validator\(mode="after"\)\s+def enforce_deployment_physics\(self\).*?return self', re.DOTALL
)

new_content = regex_validator.sub("", content)

if new_content == content:
    print("Warning: regex failed to find enforce_deployment_physics validator block")

with open("src/coreason_manifest/spec/ontology.py", "w", encoding="utf-8") as f:
    f.write(new_content)

print("Replaced!")
