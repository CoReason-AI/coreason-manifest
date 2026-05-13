import re

files = [
    "tests/ontology/test_validators_manual.py",
    "tests/ontology/test_hypothesis.py",
    "tests/ontology/test_extensive_models.py",
    "tests/ontology/test_bulk_coverage.py",
]
for fname in files:
    with open(fname) as f:
        code = f.read()
    code = re.sub(r"\s*\"CognitiveFormatContract\",", "", code)
    code = re.sub(r"\s*\"DynamicConvergenceSLA\",", "", code)
    code = re.sub(r"\s*\"TopologicalRewardContract\",", "", code)
    code = re.sub(r"\s*CognitiveFormatContract,", "", code)
    code = re.sub(r"\s*DynamicConvergenceSLA,", "", code)
    code = re.sub(r"\s*TopologicalRewardContract,", "", code)

    # Remove specific functions/blocks using these models
    code = re.sub(
        r"\s*def test_dynamic_convergence_sla.*?assert obj.lookback_window_steps == 10", "", code, flags=re.DOTALL
    )
    code = re.sub(
        r"\s*def test_cognitive_format_contract.*?assert obj.decoding_policy == policy", "", code, flags=re.DOTALL
    )

    with open(fname, "w") as f:
        f.write(code)
